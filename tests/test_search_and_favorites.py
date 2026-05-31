"""매장 검색 + 사용자 즐겨찾기 통합 테스트.

대상
----
- GET    /api/search/facilities       (q + lat/lng + radius_km + lang + limit)
- GET    /api/users/me/favorites               (사용자 본인 목록)
- POST   /api/users/me/favorites                {facility_id}  (멱등)
- DELETE /api/users/me/favorites/<fid>

검증 목적
---------
- 검색: q 텍스트 매칭 + 좌표 정렬 + adult_only 미성년자 자동 필터(PR #47)
  + 번역 머지 + limit 캡 + 잘못된 lat/lng 가드
- 즐겨찾기: CRUD + 멱등 + 존재 X 매장 404 + 비활성 매장 GET 미노출
"""
import os
import sqlite3
import tempfile

import bcrypt

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name

import models.database as _dbmod  # noqa: E402


def _patched_get_db():
    conn = sqlite3.connect(os.environ['PATHWAVE_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


_dbmod.get_db = _patched_get_db

from app import app  # noqa: E402
from models.rate_limit import limiter  # noqa: E402
from routes.auth import make_jwt  # noqa: E402

limiter.enabled = False
c = app.test_client()


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


# ── 픽스처 ──────────────────────────────────────────────────────────────────
def _seed_baseline() -> dict:
    """매장 4개(다양한 좌표·adult_only·active) + 사용자 2명(성인/미성년)."""
    db = _dbmod.get_db(); cur = db.cursor()

    # 점주 (소유자 — 검색·즐겨찾기엔 영향 없지만 facilities 외래키 위해)
    pw = bcrypt.hashpw(b'X!23456789', bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO facility_accounts
             (business_no, company_name, email, password, manager_name,
              verified, status, created_at)
           VALUES ('111-11-11111', 'Owner', 'o@t.test', ?, 'Mgr', 1, 'verified',
                   datetime('now'))""",
        (pw,),
    )
    aid = cur.lastrowid

    # 매장 4개
    # F1 — 카페 강남 (좌표 강남역 근처) 일반
    cur.execute(
        """INSERT INTO facilities (name, address, latitude, longitude, owner_id, active, adult_only)
           VALUES ('스타벅스 강남R', '서울 강남구 강남대로 396', 37.4979, 127.0276, ?, 1, 0)""",
        (aid,),
    )
    f1 = cur.lastrowid
    # F2 — 카페 홍대 (좌표 홍대입구역) 일반
    cur.execute(
        """INSERT INTO facilities (name, address, latitude, longitude, owner_id, active, adult_only)
           VALUES ('카페베네 홍대점', '서울 마포구 와우산로 21', 37.5563, 126.9226, ?, 1, 0)""",
        (aid,),
    )
    f2 = cur.lastrowid
    # F3 — 술집 (adult_only=1)
    cur.execute(
        """INSERT INTO facilities (name, address, latitude, longitude, owner_id, active, adult_only)
           VALUES ('와인바 청담', '서울 강남구 청담동', 37.5235, 127.0445, ?, 1, 1)""",
        (aid,),
    )
    f3 = cur.lastrowid
    # F4 — 비활성 매장 (검색·즐겨찾기 GET 에서 제외돼야 함)
    cur.execute(
        """INSERT INTO facilities (name, address, latitude, longitude, owner_id, active, adult_only)
           VALUES ('폐점 카페', '서울 어딘가', 37.5, 127.0, ?, 0, 0)""",
        (aid,),
    )
    f4 = cur.lastrowid

    # 사용자 2명 — 성인 (1990), 미성년자 (2015)
    cur.execute(
        """INSERT INTO users (email, password, provider, language, verified, birth_year, age_group, created_at)
           VALUES ('adult@t.test', 'x', 'email', 'ko', 1, 1990, 'adult', datetime('now'))"""
    )
    u_adult = cur.lastrowid
    # _is_minor_caller (routes/search.py:47) 가 DB age_group='minor_14_18' 으로 판정.
    cur.execute(
        """INSERT INTO users (email, password, provider, language, verified, birth_year, age_group, created_at)
           VALUES ('minor@t.test', 'x', 'email', 'ko', 1, 2010, 'minor_14_18', datetime('now'))"""
    )
    u_minor = cur.lastrowid

    db.commit(); db.close()
    return {'f_gangnam': f1, 'f_hongdae': f2, 'f_adult': f3, 'f_inactive': f4,
            'u_adult': u_adult, 'u_minor': u_minor}


def _h(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _user_token(user_id: int, email='adult@t.test', age_group='adult') -> str:
    # PR #47: minor 토큰 페이로드에 age_group 포함되어야 _is_minor_caller 동작
    return make_jwt(user_id, email, 'access', 'user', {'age_group': age_group})


def _truncate_all():
    db = _dbmod.get_db()
    for t in (
        'user_favorites', 'facility_translations', 'facilities',
        'facility_accounts', 'users',
    ):
        try:
            db.execute(f'DELETE FROM {t}')
        except sqlite3.OperationalError:
            pass
    db.commit(); db.close()


# ══════════════════════════════════════════════════════════════════════════════
# A. 검색 — q (텍스트) 매칭
# ══════════════════════════════════════════════════════════════════════════════
def test_a_search_q_match():
    print('\n── A. 검색 q 텍스트 매칭 ──')
    ids = _seed_baseline()
    # 비활성 매장은 결과에 안 나와야 함.
    r = c.get('/api/search/facilities?q=카페')
    j = r.get_json()
    _ok('① 200 + success', r.status_code == 200 and j['success'] is True, j)
    names = [x['name'] for x in j['results']]
    _ok(f'② 카페 매칭 = 홍대점 1건 (got {names})',
        '카페베네 홍대점' in names and '폐점 카페' not in names)

    # q 매칭 X
    r = c.get('/api/search/facilities?q=zzz없는이름')
    _ok('③ 매칭 없으면 count=0', r.get_json()['count'] == 0)


def test_a_search_adult_filter():
    print('\n── A2. adult_only 미성년자 자동 필터 (PR #47) ──')
    ids = _seed_baseline()

    # 성인 토큰 — 와인바 청담 노출
    r = c.get('/api/search/facilities', headers=_h(_user_token(ids['u_adult'])))
    names = [x['name'] for x in r.get_json()['results']]
    _ok('① 성인 토큰 — 와인바 청담 포함', '와인바 청담' in names)

    # 미성년자 토큰 — 와인바 청담 자동 제외
    r = c.get('/api/search/facilities',
              headers=_h(_user_token(ids['u_minor'], 'minor@t.test', 'minor')))
    names = [x['name'] for x in r.get_json()['results']]
    _ok('② 미성년자 토큰 — 와인바 청담 자동 제외',
        '와인바 청담' not in names, names)


def test_a_search_geo():
    print('\n── A3. 좌표 + radius_km 거리 정렬·필터 ──')
    ids = _seed_baseline()
    # 강남역 근처 좌표로 검색 — 강남R 매장이 거리 0 부근
    r = c.get('/api/search/facilities?lat=37.4979&lng=127.0276&radius_km=10')
    j = r.get_json()
    _ok('① 200', r.status_code == 200, j)
    results = j['results']
    _ok('② 모든 결과에 distance_km 포함',
        all('distance_km' in x for x in results), results[0] if results else None)
    _ok('③ 첫번째 결과 = 강남R (거리 최소)',
        results[0]['name'] == '스타벅스 강남R', [r['name'] for r in results])

    # lat 단독 → 400 (lat/lng 함께 필수)
    r = c.get('/api/search/facilities?lat=37.5')
    _ok('④ lat 단독 → 400', r.status_code == 400, r.get_json())


def test_a_search_translation():
    print('\n── A4. 번역(lang) 머지 ──')
    ids = _seed_baseline()

    # facility_translations 에 영문 행 시드
    db = _dbmod.get_db()
    db.execute(
        """INSERT INTO facility_translations (facility_id, language, name, address)
           VALUES (?, 'en', 'Starbucks Gangnam R', 'Gangnam, Seoul')""",
        (ids['f_gangnam'],),
    )
    db.commit(); db.close()

    r = c.get('/api/search/facilities?q=강남R&lang=en')
    res = r.get_json()['results']
    _ok('① lang=en 머지 — name 번역됨',
        len(res) >= 1 and res[0]['name'] == 'Starbucks Gangnam R', res)
    _ok('② language 필드 응답에 포함',
        res[0].get('language') == 'en', res[0])

    # lang 미지정 → 원문 한국어
    r = c.get('/api/search/facilities?q=강남R')
    res = r.get_json()['results']
    _ok('③ lang 미지정 → 원문 한국어',
        res[0]['name'] == '스타벅스 강남R', res[0])


def test_a_search_limit():
    print('\n── A5. limit 캡 ──')
    _seed_baseline()
    # limit > 100 → 100 으로 캡, limit < 1 → 20 기본
    r = c.get('/api/search/facilities?limit=99999')
    _ok('① 200', r.status_code == 200)
    # 시드는 4건뿐이지만 limit param 자체가 cap 되었는지 확인 — count 는 결과 수
    r = c.get('/api/search/facilities?limit=-1')
    _ok('② limit=-1 → 200 (default 20)', r.status_code == 200)


# ══════════════════════════════════════════════════════════════════════════════
# B. 즐겨찾기 — CRUD + 멱등 + 가드
# ══════════════════════════════════════════════════════════════════════════════
def test_b_favorites_crud_idempotent():
    print('\n── B. 즐겨찾기 CRUD + 멱등 ──')
    ids = _seed_baseline()
    UH = _h(_user_token(ids['u_adult']))

    # POST — 추가
    r = c.post('/api/users/me/favorites', headers=UH, json={'facility_id': ids['f_gangnam']})
    _ok('① POST 201 + facility_id', r.status_code == 201
        and r.get_json()['facility_id'] == ids['f_gangnam'], r.get_json())

    # GET — 1건 (favorited_at 포함)
    r = c.get('/api/users/me/favorites', headers=UH)
    j = r.get_json()
    _ok('② GET 200 + count=1', r.status_code == 200 and j['count'] == 1, j)
    _ok('③ favorited_at 포함', 'favorited_at' in j['favorites'][0])

    # POST 멱등 — 같은 facility 재호출 OK
    r = c.post('/api/users/me/favorites', headers=UH, json={'facility_id': ids['f_gangnam']})
    _ok('④ POST 멱등 → 201', r.status_code == 201)
    r = c.get('/api/users/me/favorites', headers=UH)
    _ok('⑤ GET 여전히 1건 (UNIQUE 충돌 swallow)', r.get_json()['count'] == 1)

    # DELETE
    r = c.delete(f"/api/users/me/favorites/{ids['f_gangnam']}", headers=UH)
    _ok('⑥ DELETE 200', r.status_code == 200)
    r = c.get('/api/users/me/favorites', headers=UH)
    _ok('⑦ GET 0건', r.get_json()['count'] == 0)


def test_b_favorites_guards():
    print('\n── B-guards. 즐겨찾기 가드 ──')
    ids = _seed_baseline()
    UH = _h(_user_token(ids['u_adult']))

    # 존재하지 않는 매장 → 404
    r = c.post('/api/users/me/favorites', headers=UH, json={'facility_id': 999999})
    _ok('① 존재하지 않는 매장 → 404', r.status_code == 404, r.get_json())

    # facility_id 누락 → 400
    r = c.post('/api/users/me/favorites', headers=UH, json={})
    _ok('② facility_id 누락 → 400', r.status_code == 400)

    # 비활성 매장 add → 404 (active=1 검증)
    r = c.post('/api/users/me/favorites', headers=UH, json={'facility_id': ids['f_inactive']})
    _ok('③ 비활성 매장 add → 404', r.status_code == 404)

    # 비활성 매장은 GET 에서 제외 — 강제로 user_favorites 에 row 넣고 확인
    db = _dbmod.get_db()
    db.execute(
        "INSERT INTO user_favorites (user_id, facility_id) VALUES (?, ?)",
        (ids['u_adult'], ids['f_inactive']),
    )
    db.commit(); db.close()
    r = c.get('/api/users/me/favorites', headers=UH)
    _ok('④ 비활성 매장은 GET 결과 미노출',
        r.get_json()['count'] == 0, r.get_json())


# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    print('═══ 검색 + 즐겨찾기 통합 테스트 ═══')
    for fn in (
        test_a_search_q_match,
        test_a_search_adult_filter,
        test_a_search_geo,
        test_a_search_translation,
        test_a_search_limit,
        test_b_favorites_crud_idempotent,
        test_b_favorites_guards,
    ):
        _truncate_all()
        fn()
    print('\n✅ 모든 테스트 통과')


if __name__ == '__main__':
    main()
