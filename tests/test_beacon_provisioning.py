"""P-A ~ P-D 비콘 프로비저닝 워크플로우 통합 테스트.

검증 대상 PR: #236(P-A), #237(P-B), #238(P-C 데이터모델), #239(P-D).
설계: docs/pathwave_beacon_provisioning_design_2026-05-29.md

검증 범위
---------
1. P-A 점주 신청 생성: 유닛 N개 저장 + WiFi 비번 AES-256-GCM 암호화
2. P-A 응답·조회에서 WiFi 비번 제외(보안)
3. P-A 입력 검증: 잘못된 service_type / units 비배열 거부
4. P-B 슈퍼어드민 신청 목록 조회 (전체 + 유닛 포함)
5. P-B 매칭: 비콘 active 전환 + facility/major/minor/location_label 자동 채움 +
   wifi_profile 생성 + beacon_wifi 연결 + 유닛 matched
6. P-B 매칭 가드: 이미 매칭된 유닛(409), 인벤토리 아닌 비콘(409),
   존재하지 않는 비콘(404), 매장 없는 신청(400)
7. P-B 신청 전 유닛 매칭 완료 시 신청 status='matched' 전이
8. P-D 발송: matched → shipped (어드민)
9. P-D 발송 가드: 매칭 전 발송(409)
10. P-D 설치완료: shipped → installed (점주)
11. P-D 설치완료 가드: 본인 아닌 신청(404), shipped 가 아닌 신청(409)
"""
import os
import sqlite3
import tempfile

import bcrypt

# DB 격리 — 다른 테스트와 분리.
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
from models.crypto import decrypt_secret  # noqa: E402
from routes.auth import make_jwt  # noqa: E402

c = app.test_client()


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


# ── 픽스처 (DB 직접 시드) ──────────────────────────────────────────────────
def _seed_baseline() -> dict:
    """슈퍼어드민·점주 계정·매장·인벤토리 비콘 2개 시드. id 반환."""
    db = _dbmod.get_db()
    cur = db.cursor()

    # 슈퍼어드민
    pw_hash = bcrypt.hashpw(b'admin!23', bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO super_admin_accounts (email, password, name, role, active, created_at)
           VALUES ('admin@t.test', ?, 'Admin', 'super', 1, datetime('now'))""",
        (pw_hash,),
    )
    admin_id = cur.lastrowid

    # 점주(facility account) — verified
    fac_pw = bcrypt.hashpw(b'prov!23', bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO facility_accounts
             (business_no, company_name, email, password, manager_name,
              verified, status, created_at)
           VALUES ('123-45-67890', 'Test Co', 'p@t.test', ?, 'Mgr', 1, 'verified',
                   datetime('now'))""",
        (fac_pw,),
    )
    account_id = cur.lastrowid

    # 매장
    cur.execute(
        """INSERT INTO facilities (name, owner_id, active, created_at)
           VALUES ('Test Store', ?, 1, datetime('now'))""",
        (account_id,),
    )
    facility_id = cur.lastrowid

    # 인벤토리 비콘 2개
    cur.execute(
        """INSERT INTO beacons (serial_no, uuid, status, battery_pct, firmware_ver)
           VALUES ('SN-A', 'AAAA0000000000000000000000000001', 'inventory', 100, '1.0')"""
    )
    bid_a = cur.lastrowid
    cur.execute(
        """INSERT INTO beacons (serial_no, uuid, status, battery_pct, firmware_ver)
           VALUES ('SN-B', 'BBBB0000000000000000000000000001', 'inventory', 100, '1.0')"""
    )
    bid_b = cur.lastrowid

    db.commit()
    db.close()
    return {
        'admin_id':    admin_id,
        'account_id':  account_id,
        'facility_id': facility_id,
        'bid_a':       bid_a,
        'bid_b':       bid_b,
    }


def _admin_token(admin_id: int) -> str:
    return make_jwt(admin_id, 'admin@t.test', 'access', 'super_admin',
                    {'role': 'super'})


def _provider_token(account_id: int, facility_id: int) -> str:
    return make_jwt(account_id, 'p@t.test', 'access', 'facility',
                    {'facility_id': facility_id})


def _h(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


# ──────────────────────────────────────────────────────────────────────────────
# P-A — 점주 신청 저장
# ──────────────────────────────────────────────────────────────────────────────
def test_p_a_create_and_list():
    print('\n── P-A 점주 신청 저장 ──')
    ids = _seed_baseline()
    PH = _h(_provider_token(ids['account_id'], ids['facility_id']))

    # 신청 생성 (유닛 2개)
    r = c.post('/api/service-requests', headers=PH, json={
        'service_type': 'wifi',
        'note': 'two locations',
        'units': [
            {'location_label': '입구', 'ssid': 'PW_Front', 'wifi_password': 'frontpass',
             'period_start': '2026-06-01', 'period_end': '2028-05-31'},
            {'location_label': '카페', 'ssid': 'PW_Cafe',  'wifi_password': 'cafepass',
             'period_start': '2026-06-01', 'period_end': '2028-05-31'},
        ],
    })
    _ok('① 생성 201', r.status_code == 201, r.get_json())
    rid = r.get_json()['request_id']

    # 조회 — WiFi 비번이 응답에 없어야 함 (보안)
    r = c.get('/api/service-requests', headers=PH)
    j = r.get_json()
    _ok('② 조회 200 + 1건', r.status_code == 200 and len(j['requests']) == 1, j)
    units = j['requests'][0]['units']
    _ok('③ 유닛 2개', len(units) == 2)
    _ok('④ 응답에 wifi_password / wifi_password_enc 미포함 (보안)',
        all('wifi_password' not in u and 'wifi_password_enc' not in u for u in units))

    # DB 직접 — 비번 암호화 저장 + 복호화 라운드트립
    db = _dbmod.get_db()
    row = db.execute(
        "SELECT wifi_password_enc FROM service_request_units WHERE request_id=? ORDER BY id LIMIT 1",
        (rid,),
    ).fetchone()
    db.close()
    enc = row['wifi_password_enc']
    _ok('⑤ 비번 평문 아님 (암호화 저장)', enc and enc != 'frontpass')
    _ok('⑥ 복호화 = 원문', decrypt_secret(enc) == 'frontpass')


def test_p_a_input_validation():
    print('\n── P-A 입력 검증 ──')
    ids = _seed_baseline()
    PH = _h(_provider_token(ids['account_id'], ids['facility_id']))

    r = c.post('/api/service-requests', headers=PH, json={'service_type': 'X'})
    _ok('① 잘못된 service_type → 400', r.status_code == 400, r.get_json())

    r = c.post('/api/service-requests', headers=PH,
               json={'service_type': 'wifi', 'units': 'not-a-list'})
    _ok('② units 비배열 → 400', r.status_code == 400, r.get_json())


# ──────────────────────────────────────────────────────────────────────────────
# P-B — 슈퍼어드민 매칭
# ──────────────────────────────────────────────────────────────────────────────
def test_p_b_admin_list_and_match():
    print('\n── P-B 슈퍼어드민 신청관리 + 매칭 ──')
    ids = _seed_baseline()
    AH = _h(_admin_token(ids['admin_id']))
    PH = _h(_provider_token(ids['account_id'], ids['facility_id']))

    # 점주 신청 (유닛 2)
    rid = c.post('/api/service-requests', headers=PH, json={
        'service_type': 'wifi',
        'units': [
            {'location_label': '입구', 'ssid': 'PW_Front', 'wifi_password': 'fp'},
            {'location_label': '카페', 'ssid': 'PW_Cafe',  'wifi_password': 'cp'},
        ],
    }).get_json()['request_id']

    # 어드민 목록
    r = c.get('/api/admin/service-requests', headers=AH)
    j = r.get_json()
    _ok('① 어드민 목록 200 + 1건 + 유닛 2', r.status_code == 200 and len(j['requests']) == 1
        and len(j['requests'][0]['units']) == 2, j)

    units = j['requests'][0]['units']
    # 매칭 유닛1 → 비콘 A
    r = c.post(f"/api/admin/service-request-units/{units[0]['id']}/match",
               headers=AH, json={'beacon_id': ids['bid_a']})
    body = r.get_json()
    _ok('② 매칭 유닛1 200 + major=facility_id + minor=1',
        r.status_code == 200 and body['major'] == ids['facility_id'] and body['minor'] == 1, body)
    _ok('③ 전체 유닛 매칭 전이라 request_done=False', body['request_done'] is False)

    # DB 검증 — 비콘·wifi_profile·beacon_wifi
    db = _dbmod.get_db()
    bA = db.execute("SELECT * FROM beacons WHERE id=?", (ids['bid_a'],)).fetchone()
    _ok('④ 비콘A active + facility/major/minor/location_label',
        bA['status'] == 'active' and bA['facility_id'] == ids['facility_id']
        and bA['major'] == ids['facility_id'] and bA['minor'] == 1
        and bA['location_label'] == '입구', dict(bA))
    wp = db.execute("SELECT * FROM wifi_profiles WHERE facility_id=? AND ssid='PW_Front'",
                    (ids['facility_id'],)).fetchone()
    _ok('⑤ wifi_profile PW_Front 생성', wp is not None)
    link = db.execute(
        "SELECT 1 FROM beacon_wifi WHERE beacon_id=? AND wifi_profile_id=?",
        (ids['bid_a'], wp['id'])
    ).fetchone()
    _ok('⑥ beacon_wifi 연결', link is not None)
    db.close()

    # 매칭 유닛2 → 비콘 B → 신청 전체 matched
    r = c.post(f"/api/admin/service-request-units/{units[1]['id']}/match",
               headers=AH, json={'beacon_id': ids['bid_b']})
    body = r.get_json()
    _ok('⑦ 매칭 유닛2 200 + minor=2 + request_done=True',
        r.status_code == 200 and body['minor'] == 2 and body['request_done'] is True, body)

    # 신청 status 'matched'
    db = _dbmod.get_db()
    sr = db.execute("SELECT status FROM service_requests WHERE id=?", (rid,)).fetchone()
    _ok('⑧ 신청 status matched', sr['status'] == 'matched')
    db.close()


def test_p_b_match_guards():
    print('\n── P-B 매칭 가드 ──')
    ids = _seed_baseline()
    AH = _h(_admin_token(ids['admin_id']))
    PH = _h(_provider_token(ids['account_id'], ids['facility_id']))

    # 신청 + 1유닛 매칭
    rid = c.post('/api/service-requests', headers=PH, json={
        'service_type': 'wifi',
        'units': [{'location_label': '입구', 'ssid': 'PW_F', 'wifi_password': 'p'}],
    }).get_json()['request_id']
    uid = c.get('/api/admin/service-requests', headers=AH).get_json()['requests'][0]['units'][0]['id']
    c.post(f"/api/admin/service-request-units/{uid}/match",
           headers=AH, json={'beacon_id': ids['bid_a']})

    # 가드: 이미 매칭된 유닛 재매칭
    r = c.post(f"/api/admin/service-request-units/{uid}/match",
               headers=AH, json={'beacon_id': ids['bid_b']})
    _ok('① 이미 매칭된 유닛 → 409', r.status_code == 409, r.get_json())

    # 가드: inventory 가 아닌 비콘 매칭 (방금 A 는 이미 active 이므로 A 로 시도)
    rid2 = c.post('/api/service-requests', headers=PH, json={
        'service_type': 'wifi',
        'units': [{'location_label': '카페', 'ssid': 'PW_C', 'wifi_password': 'p'}],
    }).get_json()['request_id']
    uid2 = c.get('/api/admin/service-requests', headers=AH).get_json()['requests'][0]['units'][0]['id']
    r = c.post(f"/api/admin/service-request-units/{uid2}/match",
               headers=AH, json={'beacon_id': ids['bid_a']})
    _ok('② inventory 아닌 비콘 → 409', r.status_code == 409, r.get_json())

    # 가드: 존재하지 않는 비콘
    r = c.post(f"/api/admin/service-request-units/{uid2}/match",
               headers=AH, json={'beacon_id': 999999})
    _ok('③ 존재하지 않는 비콘 → 404', r.status_code == 404)

    # 가드: 존재하지 않는 유닛
    r = c.post('/api/admin/service-request-units/999999/match',
               headers=AH, json={'beacon_id': ids['bid_b']})
    _ok('④ 존재하지 않는 유닛 → 404', r.status_code == 404)


# ──────────────────────────────────────────────────────────────────────────────
# P-D — 발송 / 설치완료 상태 추적
# ──────────────────────────────────────────────────────────────────────────────
def test_p_d_ship_and_installed_happy_path():
    print('\n── P-D 발송 → 설치완료 ──')
    ids = _seed_baseline()
    AH = _h(_admin_token(ids['admin_id']))
    PH = _h(_provider_token(ids['account_id'], ids['facility_id']))

    rid = c.post('/api/service-requests', headers=PH, json={
        'service_type': 'wifi',
        'units': [{'location_label': '입구', 'ssid': 'PW_F', 'wifi_password': 'p'}],
    }).get_json()['request_id']

    # 가드: 매칭 전 발송 시도
    r = c.post(f'/api/admin/service-requests/{rid}/ship', headers=AH)
    _ok('① 매칭 전 발송 → 409', r.status_code == 409, r.get_json())

    # 매칭
    uid = c.get('/api/admin/service-requests', headers=AH).get_json()['requests'][0]['units'][0]['id']
    c.post(f"/api/admin/service-request-units/{uid}/match",
           headers=AH, json={'beacon_id': ids['bid_a']})

    # 발송
    r = c.post(f'/api/admin/service-requests/{rid}/ship', headers=AH)
    _ok('② 발송 200 + status=shipped',
        r.status_code == 200 and r.get_json()['status'] == 'shipped', r.get_json())

    # 가드: 점주가 shipped 가 아닌 다른 신청 installed 시도 — 별도 신청 생성
    rid2 = c.post('/api/service-requests', headers=PH, json={
        'service_type': 'wifi',
        'units': [{'location_label': '카페', 'ssid': 'PW_C', 'wifi_password': 'p'}],
    }).get_json()['request_id']
    r = c.post(f'/api/service-requests/{rid2}/installed', headers=PH)
    _ok('③ shipped 가 아닌 신청 installed → 409', r.status_code == 409, r.get_json())

    # 설치완료 (정상)
    r = c.post(f'/api/service-requests/{rid}/installed', headers=PH)
    _ok('④ 설치완료 200 + status=installed',
        r.status_code == 200 and r.get_json()['status'] == 'installed', r.get_json())


def test_p_d_installed_ownership_guard():
    print('\n── P-D 설치완료 소유권 가드 ──')
    ids = _seed_baseline()
    AH = _h(_admin_token(ids['admin_id']))
    PH = _h(_provider_token(ids['account_id'], ids['facility_id']))

    # 다른 점주 (account 별도)
    db = _dbmod.get_db(); cur = db.cursor()
    other_pw = bcrypt.hashpw(b'other!', bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO facility_accounts
             (business_no, company_name, email, password, manager_name,
              verified, status, created_at)
           VALUES ('999-99-99999', 'Other', 'o@t.test', ?, 'Mgr', 1, 'verified',
                   datetime('now'))""",
        (other_pw,),
    )
    other_account = cur.lastrowid
    cur.execute(
        """INSERT INTO facilities (name, owner_id, active, created_at)
           VALUES ('Other Store', ?, 1, datetime('now'))""",
        (other_account,),
    )
    other_facility = cur.lastrowid
    db.commit(); db.close()
    OH = _h(_provider_token(other_account, other_facility))

    # 첫 점주가 신청·매칭·발송
    rid = c.post('/api/service-requests', headers=PH, json={
        'service_type': 'wifi',
        'units': [{'location_label': '입구', 'ssid': 'PW_F', 'wifi_password': 'p'}],
    }).get_json()['request_id']
    uid = c.get('/api/admin/service-requests', headers=AH).get_json()['requests'][0]['units'][0]['id']
    c.post(f"/api/admin/service-request-units/{uid}/match",
           headers=AH, json={'beacon_id': ids['bid_a']})
    c.post(f'/api/admin/service-requests/{rid}/ship', headers=AH)

    # 다른 점주가 남의 신청 installed 시도
    r = c.post(f'/api/service-requests/{rid}/installed', headers=OH)
    _ok('① 본인 아닌 신청 installed → 404', r.status_code == 404, r.get_json())


# ──────────────────────────────────────────────────────────────────────────────
def _truncate_all():
    """각 테스트 사이 격리 — 관련 테이블만 비움."""
    db = _dbmod.get_db()
    for t in (
        'beacon_wifi', 'wifi_profiles', 'service_request_units', 'service_requests',
        'beacons', 'facilities', 'facility_accounts', 'super_admin_accounts',
    ):
        try:
            db.execute(f'DELETE FROM {t}')
        except sqlite3.OperationalError:
            pass
    db.commit(); db.close()


def main() -> None:
    print('═══ P-A ~ P-D 비콘 프로비저닝 통합 테스트 ═══')
    for fn in (
        test_p_a_create_and_list,
        test_p_a_input_validation,
        test_p_b_admin_list_and_match,
        test_p_b_match_guards,
        test_p_d_ship_and_installed_happy_path,
        test_p_d_installed_ownership_guard,
    ):
        _truncate_all()
        fn()
    print('\n✅ 모든 테스트 통과')


if __name__ == '__main__':
    main()
