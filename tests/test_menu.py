"""매장 메뉴(OCR + 자동번역) 통합 테스트 — C-4 USP(메뉴 자동 번역).

대상
----
- POST   /api/facilities/<fid>/menu/upload    (이미지 b64 → OCR stub)
- GET    /api/facilities/<fid>/menu            (lang 별, 공개)
- POST   /api/facilities/<fid>/menu/items      (수동 등록)
- PATCH  /api/facility-menu-items/<id>
- DELETE /api/facility-menu-items/<id>

집중 검증
---------
- ⭐ 가격 KRW 강제 (외국 통화 $·USD → 422) — USP 핵심
- GET lang 폴백: ko cache / 빈 매장 empty / lang=en 자동번역(translated, price 보존)
- OCR stub 4건 + replace 옵션
- DELETE 시 종속 번역(base_item_id) cascade 정리
- 권한 가드
"""
import base64
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

# 아무 유효 base64 (stub OCR 은 내용 무시하고 placeholder 4건 반환)
_IMG_B64 = base64.b64encode(b'fake-image-bytes').decode()


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


def _seed() -> dict:
    db = _dbmod.get_db(); cur = db.cursor()
    pw = bcrypt.hashpw(b'Owner!2345', bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO facility_accounts
             (business_no, company_name, email, password, manager_name, verified, status, created_at)
           VALUES ('111-11-11111', 'Cafe', 'o@t.test', ?, 'Mgr', 1, 'verified', datetime('now'))""",
        (pw,),
    )
    aid = cur.lastrowid
    cur.execute(
        "INSERT INTO facilities (name, owner_id, active, created_at) VALUES ('Cafe One', ?, 1, datetime('now'))",
        (aid,),
    )
    fid = cur.lastrowid
    db.commit(); db.close()
    return {'aid': aid, 'fid': fid}


def _h(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _owner(aid: int, fid: int) -> dict:
    return _h(make_jwt(aid, 'o@t.test', 'access', 'facility',
                       {'facility_id': fid, 'role': 'owner', 'owner_account_id': aid}))


def _truncate_all():
    db = _dbmod.get_db()
    for t in ('facility_menu_items', 'facility_menu_uploads', 'ai_usage_logs',
              'facilities', 'facility_accounts'):
        try:
            db.execute(f'DELETE FROM {t}')
        except sqlite3.OperationalError:
            pass
    db.commit(); db.close()


# ══════════════════════════════════════════════════════════════════════════════
# A. 수동 메뉴 등록 + KRW 강제 (USP 핵심)
# ══════════════════════════════════════════════════════════════════════════════
def test_a_create_and_krw_enforcement():
    print('\n── A. 수동 등록 + KRW 가격 강제 ──')
    ids = _seed()
    OH = _owner(ids['aid'], ids['fid'])
    fid = ids['fid']

    # 정상 등록 (숫자 → 원 정규화)
    r = c.post(f'/api/facilities/{fid}/menu/items', headers=OH,
               json={'name': '아메리카노', 'price': '4500', 'description': '뜨거운 커피'})
    body = r.get_json()
    _ok('① 등록 201 + price 정규화 "4500원"',
        r.status_code == 201 and body['item']['price'] == '4500원', body)

    # ⭐ 외국 통화 → 422 (USP 핵심)
    r = c.post(f'/api/facilities/{fid}/menu/items', headers=OH,
               json={'name': 'Latte', 'price': '$5.00'})
    _ok('② 외국 통화 $ → 422', r.status_code == 422, r.get_json())

    r = c.post(f'/api/facilities/{fid}/menu/items', headers=OH,
               json={'name': 'Tea', 'price': '10 USD'})
    _ok('③ "10 USD" → 422', r.status_code == 422)

    # name 누락 → 400
    r = c.post(f'/api/facilities/{fid}/menu/items', headers=OH, json={'price': '3000'})
    _ok('④ name 누락 → 400', r.status_code == 400)

    # 권한 없는 매장 → 404
    r = c.post('/api/facilities/99999/menu/items', headers=OH, json={'name': 'x', 'price': '1000'})
    _ok('⑤ 권한 없는 매장 → 404', r.status_code == 404)


# ══════════════════════════════════════════════════════════════════════════════
# B. PATCH / DELETE
# ══════════════════════════════════════════════════════════════════════════════
def test_b_patch_delete():
    print('\n── B. 메뉴 수정/삭제 ──')
    ids = _seed()
    OH = _owner(ids['aid'], ids['fid'])
    fid = ids['fid']

    iid = c.post(f'/api/facilities/{fid}/menu/items', headers=OH,
                 json={'name': '카페라떼', 'price': '5000'}).get_json()['item']['id']

    # PATCH price (KRW 강제 유지)
    r = c.patch(f'/api/facility-menu-items/{iid}', headers=OH, json={'price': '5500'})
    _ok('① PATCH price → "5500원"', r.status_code == 200 and r.get_json()['item']['price'] == '5500원',
        r.get_json())

    # PATCH 외국 통화 → 422
    r = c.patch(f'/api/facility-menu-items/{iid}', headers=OH, json={'price': '€6'})
    _ok('② PATCH 외국 통화 → 422', r.status_code == 422)

    # PATCH 빈 변경 → 400
    r = c.patch(f'/api/facility-menu-items/{iid}', headers=OH, json={})
    _ok('③ 빈 변경 → 400', r.status_code == 400)

    # DELETE
    r = c.delete(f'/api/facility-menu-items/{iid}', headers=OH)
    _ok('④ DELETE 200', r.status_code == 200)
    r = c.delete(f'/api/facility-menu-items/{iid}', headers=OH)
    _ok('⑤ 삭제된 항목 재DELETE → 404', r.status_code == 404)


# ══════════════════════════════════════════════════════════════════════════════
# C. GET /menu — lang 폴백 + 자동번역
# ══════════════════════════════════════════════════════════════════════════════
def test_c_get_menu_lang_fallback():
    print('\n── C. GET /menu lang 폴백 (공개 + 자동번역) ──')
    ids = _seed()
    OH = _owner(ids['aid'], ids['fid'])
    fid = ids['fid']

    # 빈 매장 → empty
    r = c.get(f'/api/facilities/{fid}/menu')
    _ok('① 빈 매장 → source=empty + items 0',
        r.status_code == 200 and r.get_json()['source'] == 'empty'
        and r.get_json()['items'] == [], r.get_json())

    # ko 2건 등록
    c.post(f'/api/facilities/{fid}/menu/items', headers=OH, json={'name': '김밥', 'price': '4000'})
    c.post(f'/api/facilities/{fid}/menu/items', headers=OH, json={'name': '라면', 'price': '5000'})

    # ko 조회 → cache
    r = c.get(f'/api/facilities/{fid}/menu?lang=ko')
    j = r.get_json()
    _ok('② ko → source=cache + 2건', j['source'] == 'cache' and len(j['items']) == 2, j)

    # 공개 (토큰 없음) 도 조회 가능
    r = c.get(f'/api/facilities/{fid}/menu')
    _ok('③ 공개 GET (토큰 없음) 200', r.status_code == 200)

    # en 조회 → 자동 번역 (translated) + price KRW 보존
    r = c.get(f'/api/facilities/{fid}/menu?lang=en')
    j = r.get_json()
    _ok('④ en → source=translated', j['source'] == 'translated', j)
    _ok('⑤ 번역본 price KRW 보존 ("4000원")',
        any(it['price'] == '4000원' for it in j['items']), j['items'])
    _ok('⑥ 번역본 base_item_id 연결',
        all(it['base_item_id'] is not None for it in j['items']), j['items'])

    # en 재조회 → 이번엔 cache (앞서 생성된 en row)
    r = c.get(f'/api/facilities/{fid}/menu?lang=en')
    _ok('⑦ en 재조회 → source=cache (캐시 적중)', r.get_json()['source'] == 'cache')


# ══════════════════════════════════════════════════════════════════════════════
# D. OCR 업로드
# ══════════════════════════════════════════════════════════════════════════════
def test_d_ocr_upload():
    print('\n── D. OCR 이미지 업로드 (stub) ──')
    ids = _seed()
    OH = _owner(ids['aid'], ids['fid'])
    fid = ids['fid']

    # image_b64 누락 → 400
    r = c.post(f'/api/facilities/{fid}/menu/upload', headers=OH, json={})
    _ok('① image_b64 누락 → 400', r.status_code == 400, r.get_json())

    # 정상 업로드 → stub 4건
    r = c.post(f'/api/facilities/{fid}/menu/upload', headers=OH, json={'image_b64': _IMG_B64})
    body = r.get_json()
    _ok('② 업로드 201 + item_count 4 (stub) + source=ocr',
        r.status_code == 201 and body['item_count'] == 4
        and all(it['source'] == 'ocr' for it in body['items']), body)

    # GET 으로 확인 — 4건 cache
    r = c.get(f'/api/facilities/{fid}/menu?lang=ko')
    _ok('③ GET ko → 4건', len(r.get_json()['items']) == 4)

    # replace=True 재업로드 → 기존 ko 비활성, 신규 4건만 active
    r = c.post(f'/api/facilities/{fid}/menu/upload', headers=OH,
               json={'image_b64': _IMG_B64, 'replace': True})
    _ok('④ replace 재업로드 201', r.status_code == 201)
    r = c.get(f'/api/facilities/{fid}/menu?lang=ko')
    _ok('⑤ replace 후에도 active 4건 (기존 비활성)', len(r.get_json()['items']) == 4,
        len(r.get_json()['items']))


# ══════════════════════════════════════════════════════════════════════════════
# E. DELETE cascade — 종속 번역 정리
# ══════════════════════════════════════════════════════════════════════════════
def test_e_delete_cascade_translations():
    print('\n── E. base item 삭제 시 종속 번역 cascade ──')
    ids = _seed()
    OH = _owner(ids['aid'], ids['fid'])
    fid = ids['fid']

    # ko 1건 등록
    ko_id = c.post(f'/api/facilities/{fid}/menu/items', headers=OH,
                   json={'name': '돈까스', 'price': '9000'}).get_json()['item']['id']

    # en 자동번역 생성 (GET lang=en)
    c.get(f'/api/facilities/{fid}/menu?lang=en')
    db = _dbmod.get_db()
    en_cnt = db.execute(
        "SELECT COUNT(*) AS n FROM facility_menu_items WHERE base_item_id=?", (ko_id,)
    ).fetchone()['n']
    db.close()
    _ok('① en 번역본 1건 생성 (base_item_id 연결)', en_cnt == 1)

    # ko(base) 삭제 → 종속 en 도 cascade 삭제
    c.delete(f'/api/facility-menu-items/{ko_id}', headers=OH)
    db = _dbmod.get_db()
    remain = db.execute(
        "SELECT COUNT(*) AS n FROM facility_menu_items WHERE id=? OR base_item_id=?",
        (ko_id, ko_id)
    ).fetchone()['n']
    db.close()
    _ok('② base 삭제 → 본체+종속번역 모두 정리 (remain=0)', remain == 0)


# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    print('═══ 매장 메뉴(OCR + 자동번역) 통합 테스트 ═══')
    for fn in (
        test_a_create_and_krw_enforcement,
        test_b_patch_delete,
        test_c_get_menu_lang_fallback,
        test_d_ocr_upload,
        test_e_delete_cascade_translations,
    ):
        _truncate_all()
        fn()
    print('\n✅ 모든 테스트 통과')


if __name__ == '__main__':
    main()
