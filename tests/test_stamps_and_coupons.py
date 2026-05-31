"""스탬프 + 쿠폰 통합 테스트 (P-D 후속, P22-d 회수 보호 포함).

라우트
------
- 스탬프 정책 GET/PUT/DELETE
- 스탬프 적립(POST) + 사용자/점주 조회(GET) + PATCH/DELETE
- 쿠폰 발급(POST 단일/배열) + 사용자 쿠폰함(GET) + 사용(POST) + 회수(DELETE)

검증 목적
---------
- 신규 DB 환경에서 회귀 방지
- P22-d 활성 쿠폰 회수 보호(403) 확인
- 권한·소유권 가드 검증
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
    """점주(facility owner) + 사용자 + 매장 시드. id 반환."""
    db = _dbmod.get_db(); cur = db.cursor()

    # 점주
    pw = bcrypt.hashpw(b'Owner!23', bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO facility_accounts
             (business_no, company_name, email, password, manager_name,
              verified, status, created_at)
           VALUES ('111-11-11111', 'Cafe', 'o@t.test', ?, 'Mgr', 1, 'verified',
                   datetime('now'))""",
        (pw,),
    )
    aid = cur.lastrowid

    # 매장
    cur.execute(
        """INSERT INTO facilities (name, owner_id, active, created_at)
           VALUES ('Cafe One', ?, 1, datetime('now'))""",
        (aid,),
    )
    fid = cur.lastrowid

    # 사용자 2명
    cur.execute(
        """INSERT INTO users
             (email, password, provider, language, verified, birth_year, age_group, created_at)
           VALUES ('u1@t.test', 'x', 'email', 'ko', 1, 1990, 'adult', datetime('now'))"""
    )
    u1 = cur.lastrowid
    cur.execute(
        """INSERT INTO users
             (email, password, provider, language, verified, birth_year, age_group, created_at)
           VALUES ('u2@t.test', 'x', 'email', 'ko', 1, 1992, 'adult', datetime('now'))"""
    )
    u2 = cur.lastrowid

    db.commit(); db.close()
    return {'account_id': aid, 'facility_id': fid, 'u1': u1, 'u2': u2}


def _h(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _owner_token(account_id: int, facility_id: int) -> str:
    return make_jwt(account_id, 'o@t.test', 'access', 'facility',
                    {'facility_id': facility_id, 'role': 'owner',
                     'owner_account_id': account_id})


def _user_token(user_id: int, email='u1@t.test') -> str:
    return make_jwt(user_id, email, 'access', 'user')


def _truncate_all():
    db = _dbmod.get_db()
    for t in (
        'coupons', 'stamps', 'stamp_policies',
        'facilities', 'facility_accounts', 'users',
    ):
        try:
            db.execute(f'DELETE FROM {t}')
        except sqlite3.OperationalError:
            pass
    db.commit(); db.close()


# ══════════════════════════════════════════════════════════════════════════════
# A. 스탬프 정책 CRUD
# ══════════════════════════════════════════════════════════════════════════════
def test_a_stamp_policy_crud():
    print('\n── A. 스탬프 정책 GET/PUT/DELETE ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['account_id'], ids['facility_id']))
    fid = ids['facility_id']

    # 초기 정책 없음 (GET 404 또는 빈 응답)
    r = c.get(f'/api/facilities/{fid}/stamp-policy', headers=OH)
    _ok('① 정책 부재 — 404 또는 빈 정책',
        r.status_code in (200, 404), r.get_json())

    # PUT 생성
    r = c.put(f'/api/facilities/{fid}/stamp-policy', headers=OH, json={
        'reward_threshold': 10,
        'reward_description': '아메리카노 1잔 무료',
        'expires_days': 90,
    })
    _ok('② PUT 정책 200 + success', r.status_code == 200 and r.get_json()['success'],
        r.get_json())

    # GET 확인
    r = c.get(f'/api/facilities/{fid}/stamp-policy', headers=OH)
    body = r.get_json()
    pol = body.get('policy') or body
    _ok('③ GET 정책 — reward_threshold=10 + 설명 저장됨',
        r.status_code == 200 and (pol.get('reward_threshold') == 10)
        and pol.get('reward_description') == '아메리카노 1잔 무료', body)

    # DELETE
    r = c.delete(f'/api/facilities/{fid}/stamp-policy', headers=OH)
    _ok('④ DELETE 200 + success', r.status_code == 200)


# ══════════════════════════════════════════════════════════════════════════════
# B. 스탬프 적립 + 조회 + PATCH/DELETE
# ══════════════════════════════════════════════════════════════════════════════
def test_b_stamp_grant_list_patch_delete():
    print('\n── B. 스탬프 적립·조회·수정·삭제 ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['account_id'], ids['facility_id']))
    UH = _h(_user_token(ids['u1']))
    fid = ids['facility_id']

    # 적립
    r = c.post(f'/api/facilities/{fid}/stamps', headers=OH,
               json={'user_id': ids['u1'], 'amount': 2, 'note': '카페 라떼 2잔'})
    body = r.get_json()
    _ok('① 적립 201 + amount=2',
        r.status_code in (200, 201) and body['stamp']['amount'] == 2, body)
    sid = body['stamp']['id']

    # 매장 스탬프 목록 (점주)
    r = c.get(f'/api/facilities/{fid}/stamps', headers=OH)
    j = r.get_json()
    _ok('② 점주 매장 스탬프 1건', r.status_code == 200 and len(j['stamps']) == 1, j)

    # 사용자 본인 스탬프 — 매장별 합계 응답 (stamps_by_facility, total_stamps=2)
    r = c.get('/api/users/me/stamps', headers=UH)
    j = r.get_json()
    by_fac = j.get('stamps_by_facility', [])
    _ok('③ 사용자 본인 스탬프 — 1매장 + total_stamps=2',
        r.status_code == 200 and len(by_fac) == 1 and by_fac[0]['total_stamps'] == 2, j)

    # PATCH amount
    r = c.patch(f'/api/stamps/{sid}', headers=OH, json={'amount': 3})
    body = r.get_json()
    _ok('④ PATCH amount=3 + stamp.amount=3', r.status_code == 200 and body['stamp']['amount'] == 3, body)

    # DELETE
    r = c.delete(f'/api/stamps/{sid}', headers=OH)
    _ok('⑤ DELETE 200', r.status_code == 200)

    r = c.get(f'/api/facilities/{fid}/stamps', headers=OH)
    _ok('⑥ 삭제 후 매장 스탬프 0건', r.status_code == 200 and len(r.get_json()['stamps']) == 0)


def test_b_stamp_grant_guards():
    print('\n── B-guards. 스탬프 적립 가드 ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['account_id'], ids['facility_id']))
    fid = ids['facility_id']

    # 존재하지 않는 user_id
    r = c.post(f'/api/facilities/{fid}/stamps', headers=OH,
               json={'user_id': 999999, 'amount': 1})
    _ok('① 존재하지 않는 user → 404', r.status_code == 404, r.get_json())

    # amount=0
    r = c.post(f'/api/facilities/{fid}/stamps', headers=OH,
               json={'user_id': ids['u1'], 'amount': 0})
    _ok('② amount=0 → 400', r.status_code == 400, r.get_json())

    # amount=음수
    r = c.post(f'/api/facilities/{fid}/stamps', headers=OH,
               json={'user_id': ids['u1'], 'amount': -1})
    _ok('③ amount=-1 → 400', r.status_code == 400)

    # 권한 없는 매장
    r = c.post(f'/api/facilities/99999/stamps', headers=OH,
               json={'user_id': ids['u1'], 'amount': 1})
    _ok('④ 권한 없는 매장 → 404', r.status_code == 404)


# ══════════════════════════════════════════════════════════════════════════════
# C. 쿠폰 발급 + 사용자 쿠폰함 + 사용 처리
# ══════════════════════════════════════════════════════════════════════════════
def test_c_coupon_issue_user_inbox_use():
    print('\n── C. 쿠폰 발급(단일/배열) + 사용자 쿠폰함 + 사용 ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['account_id'], ids['facility_id']))
    UH1 = _h(_user_token(ids['u1']))
    UH2 = _h(_user_token(ids['u2'], 'u2@t.test'))
    fid = ids['facility_id']

    # 단일 user_id 발급
    r = c.post(f'/api/facilities/{fid}/coupons', headers=OH, json={
        'title': '신규가입 환영', 'benefit': '10% 할인',
        'user_id': ids['u1'],
    })
    _ok('① 단일 발급 201', r.status_code == 201, r.get_json())

    # 다중 user_ids 발급
    r = c.post(f'/api/facilities/{fid}/coupons', headers=OH, json={
        'title': '4월 이벤트', 'benefit': '아메리카노 +1',
        'user_ids': [ids['u1'], ids['u2']],
    })
    _ok('② 다중 user_ids 201', r.status_code == 201, r.get_json())

    # u1 쿠폰함 — 2건 (단일 1 + 다중 1)
    r = c.get('/api/users/me/coupons', headers=UH1)
    n1 = len(r.get_json()['coupons'])
    _ok(f'③ u1 쿠폰함 2건 (got {n1})', n1 == 2)

    # u2 쿠폰함 — 1건
    r = c.get('/api/users/me/coupons', headers=UH2)
    n2 = len(r.get_json()['coupons'])
    _ok(f'④ u2 쿠폰함 1건 (got {n2})', n2 == 1)

    # 사용 (점주가 use 처리)
    cid = r.get_json()['coupons'][0]['id']
    r = c.post(f'/api/coupons/{cid}/use', headers=OH)
    body = r.get_json()
    _ok('⑤ 사용 처리 200 + used=True',
        r.status_code == 200 and body['coupon']['used'] is True, body)

    # 두 번째 사용 → 409
    r = c.post(f'/api/coupons/{cid}/use', headers=OH)
    _ok('⑥ 재사용 → 409', r.status_code == 409, r.get_json())


def test_c_coupon_input_validation():
    print('\n── C-guards. 쿠폰 발급 검증 ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['account_id'], ids['facility_id']))
    fid = ids['facility_id']

    # title 누락
    r = c.post(f'/api/facilities/{fid}/coupons', headers=OH,
               json={'user_id': ids['u1']})
    _ok('① title 누락 → 400', r.status_code == 400, r.get_json())

    # user 누락
    r = c.post(f'/api/facilities/{fid}/coupons', headers=OH,
               json={'title': 'X'})
    _ok('② user 정보 누락 → 400', r.status_code == 400)

    # user_ids 에 존재하지 않는 id
    r = c.post(f'/api/facilities/{fid}/coupons', headers=OH,
               json={'title': 'X', 'user_ids': [ids['u1'], 999999]})
    _ok('③ 존재하지 않는 user 포함 → 404', r.status_code == 404, r.get_json())


# ══════════════════════════════════════════════════════════════════════════════
# D. P22-d 쿠폰 회수 보호 (활성 쿠폰 점주 삭제 금지)
# ══════════════════════════════════════════════════════════════════════════════
def test_d_coupon_revoke_active_protected():
    print('\n── D. P22-d 활성 쿠폰 회수 보호 (점주 삭제 불가) ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['account_id'], ids['facility_id']))
    fid = ids['facility_id']

    # 활성 쿠폰 발급 (만료일 없음)
    r = c.post(f'/api/facilities/{fid}/coupons', headers=OH, json={
        'title': '활성 쿠폰', 'user_id': ids['u1'],
    })
    cid_active = r.get_json()['coupons'][0]['id'] if 'coupons' in r.get_json() \
        else r.get_json()['coupon']['id']

    # 활성 쿠폰 회수 → 403 + COUPON_ACTIVE_PROTECTED
    r = c.delete(f'/api/coupons/{cid_active}', headers=OH)
    body = r.get_json()
    _ok('① 활성 쿠폰 회수 → 403 + code=COUPON_ACTIVE_PROTECTED',
        r.status_code == 403 and body.get('code') == 'COUPON_ACTIVE_PROTECTED', body)

    # 사용 처리 후 → 회수 가능
    c.post(f'/api/coupons/{cid_active}/use', headers=OH)
    r = c.delete(f'/api/coupons/{cid_active}', headers=OH)
    _ok('② 사용 후 회수 → 200', r.status_code == 200, r.get_json())


def test_d_coupon_revoke_expired_allowed():
    print('\n── D2. 만료된 쿠폰 회수 허용 ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['account_id'], ids['facility_id']))
    fid = ids['facility_id']

    # 발급
    r = c.post(f'/api/facilities/{fid}/coupons', headers=OH, json={
        'title': '만료 쿠폰', 'user_id': ids['u1'],
    })
    cid = (r.get_json().get('coupons') or [r.get_json().get('coupon')])[0]['id']

    # DB 직접 — expires_at 을 과거로 설정
    db = _dbmod.get_db()
    db.execute("UPDATE coupons SET expires_at = '2020-01-01 00:00:00' WHERE id=?", (cid,))
    db.commit(); db.close()

    r = c.delete(f'/api/coupons/{cid}', headers=OH)
    _ok('① 만료된 쿠폰 회수 → 200', r.status_code == 200, r.get_json())


# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    print('═══ 스탬프 + 쿠폰 통합 테스트 ═══')
    for fn in (
        test_a_stamp_policy_crud,
        test_b_stamp_grant_list_patch_delete,
        test_b_stamp_grant_guards,
        test_c_coupon_issue_user_inbox_use,
        test_c_coupon_input_validation,
        test_d_coupon_revoke_active_protected,
        test_d_coupon_revoke_expired_allowed,
    ):
        _truncate_all()
        fn()
    print('\n✅ 모든 테스트 통과')


if __name__ == '__main__':
    main()
