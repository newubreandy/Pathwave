"""P15b — WiFi 관리 + 비콘↔WiFi 매핑 라우트 회귀 테스트.

검증 범위
---------
1) GET    /api/facilities/<fid>/wifis                — 매장 WiFi 목록
2) GET    /api/facilities/<fid>/wifis?include_password=1 — owner 만 평문 노출
3) PATCH  /api/facilities/<fid>/wifis/<wid>           — ssid/password/scope/credential_mode/active
4) DELETE /api/facilities/<fid>/wifis/<wid>           — soft delete (active=0)
5) GET    /api/facilities/<fid>/beacons/<bid>/wifis   — 매핑 조회
6) PUT    /api/facilities/<fid>/beacons/<bid>/wifis   — 매핑 일괄 교체 (set)
7) DELETE /api/facilities/<fid>/beacons/<bid>/wifis/<wpid> — 단일 매핑 해제
8) 다른 매장 WiFi 매핑 시도 → 400
"""
import os
import sqlite3
import tempfile
import json

import bcrypt

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name

import models.database as _dbmod
_dbmod.DB_PATH = tmp.name
_dbmod.init_db()

from app import app                                    # noqa: E402
from routes.auth import make_jwt                       # noqa: E402

c = app.test_client()


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


def _get(path, token=None):
    h = {}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.get(path, headers=h)
    return r.status_code, r.get_json()


def _patch(path, data=None, token=None):
    h = {'Content-Type': 'application/json'}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.patch(path, data=json.dumps(data or {}), headers=h)
    return r.status_code, r.get_json()


def _put(path, data=None, token=None):
    h = {'Content-Type': 'application/json'}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.put(path, data=json.dumps(data or {}), headers=h)
    return r.status_code, r.get_json()


def _post(path, data=None, token=None):
    h = {'Content-Type': 'application/json'}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.post(path, data=json.dumps(data or {}), headers=h)
    return r.status_code, r.get_json()


def _del(path, token=None):
    h = {}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.delete(path, headers=h)
    return r.status_code, r.get_json()


# ── 0. 시드 ──────────────────────────────────────────────────────────────
print('\n[0] 시드 — 매장 A/B + WiFi + 비콘')
db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
hashed = bcrypt.hashpw(b'pw', bcrypt.gensalt()).decode()
db.execute("INSERT INTO facility_accounts (business_no, company_name, email, password, verified, status) VALUES ('001','A','o@a.com',?,1,'verified')", (hashed,))
db.execute("INSERT INTO facility_accounts (business_no, company_name, email, password, verified, status) VALUES ('002','B','o@b.com',?,1,'verified')", (hashed,))
db.execute("INSERT INTO facilities (name, owner_id, active) VALUES ('Cafe A', 1, 1)")
db.execute("INSERT INTO facilities (name, owner_id, active) VALUES ('Cafe B', 2, 1)")
# A 의 WiFi 2개 + 비콘 1개
db.execute("INSERT INTO wifi_profiles (facility_id, ssid, password, scope, credential_mode, active) VALUES (1, 'A-AP1', 'pw1', 'public', 'static', 1)")
db.execute("INSERT INTO wifi_profiles (facility_id, ssid, password, scope, credential_mode, active) VALUES (1, 'A-AP2', 'pw2', 'public', 'static', 1)")
db.execute("INSERT INTO beacons (serial_no, uuid, status, facility_id, major, minor, role) VALUES ('SN-A', 'UU-A', 'active', 1, 1, 1, 'wifi')")
# B 의 WiFi 1개 (cross 검증용)
db.execute("INSERT INTO wifi_profiles (facility_id, ssid, password, scope, credential_mode, active) VALUES (2, 'B-AP1', 'pwB', 'public', 'static', 1)")
db.commit(); db.close()

token_A = make_jwt(1, 'o@a.com', sub_type='facility')
token_B = make_jwt(2, 'o@b.com', sub_type='facility')


# ── 1. GET wifis ────────────────────────────────────────────────────────
print('\n[1] GET /api/facilities/1/wifis — 매장 A 의 WiFi 2개')
status, j = _get('/api/facilities/1/wifis', token=token_A)
_ok('200 응답',                   status == 200, j)
_ok('WiFi 2개',                   len(j['wifis']) == 2, j)
_ok('password 미노출 (default)',  'password' not in j['wifis'][0], j['wifis'][0])


# ── 2. include_password=1 권한 ──────────────────────────────────────────
print('\n[2] include_password=1 → password 평문 노출 (owner)')
status, j = _get('/api/facilities/1/wifis?include_password=1', token=token_A)
_ok('200 응답',                   status == 200, j)
_ok('password 노출',              'password' in j['wifis'][0], j['wifis'][0])


# ── 3. PATCH wifi ───────────────────────────────────────────────────────
print('\n[3] PATCH wifi — ssid + active 수정')
wid = j['wifis'][0]['id']
status, j = _patch(f'/api/facilities/1/wifis/{wid}',
                   {'ssid': 'A-AP1-NEW', 'active': True, 'credential_mode': 'managed'},
                   token=token_A)
_ok('200 응답',                   status == 200, j)
_ok("ssid 변경",                  j['wifi']['ssid'] == 'A-AP1-NEW', j['wifi'])
_ok("credential_mode 변경",        j['wifi']['credential_mode'] == 'managed', j['wifi'])


# ── 4. PATCH 잘못된 값 → 400 ────────────────────────────────────────────
print('\n[4] PATCH 잘못된 scope → 400')
status, j = _patch(f'/api/facilities/1/wifis/{wid}',
                   {'scope': 'invalid'}, token=token_A)
_ok('400 응답',                   status == 400, j)


# ── 5. DELETE wifi (soft) ──────────────────────────────────────────────
print('\n[5] DELETE wifi — soft delete')
status, j = _del(f'/api/facilities/1/wifis/{wid}', token=token_A)
_ok('200 응답',                   status == 200, j)
db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
row = db.execute("SELECT active FROM wifi_profiles WHERE id=?", (wid,)).fetchone()
db.close()
_ok('active=0',                   row['active'] == 0, dict(row))


# ── 6. PUT 비콘↔WiFi 매핑 일괄 교체 ────────────────────────────────────
print('\n[6] PUT beacon/<bid>/wifis — 매핑 set')
# A 의 비콘 1번, A 의 WiFi 2번 (active=1)
db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
bid_A = db.execute("SELECT id FROM beacons WHERE serial_no='SN-A'").fetchone()['id']
wp2 = db.execute("SELECT id FROM wifi_profiles WHERE ssid='A-AP2'").fetchone()['id']
db.close()
status, j = _put(f'/api/facilities/1/beacons/{bid_A}/wifis',
                 {'wifi_profile_ids': [wp2]}, token=token_A)
_ok('200 응답',                   status == 200, j)
_ok('mapping 1개',                len(j['wifi_profile_ids']) == 1, j)


# ── 7. GET beacon/<bid>/wifis ───────────────────────────────────────────
print('\n[7] GET beacon/<bid>/wifis — 매핑 조회')
status, j = _get(f'/api/facilities/1/beacons/{bid_A}/wifis', token=token_A)
_ok('200 응답',                   status == 200, j)
_ok('wifis 1개',                  len(j['wifis']) == 1, j)
_ok('mapping 된 wifi id == wp2',  j['wifis'][0]['id'] == wp2, j['wifis'])


# ── 8. PUT — 다른 매장(B) WiFi 매핑 시도 → 400 ──────────────────────────
print('\n[8] 다른 매장 WiFi 매핑 시도 → 400')
db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
wp_B = db.execute("SELECT id FROM wifi_profiles WHERE ssid='B-AP1'").fetchone()['id']
db.close()
status, j = _put(f'/api/facilities/1/beacons/{bid_A}/wifis',
                 {'wifi_profile_ids': [wp_B]}, token=token_A)
_ok('400 응답',                   status == 400, j)


# ── 9. DELETE 단일 매핑 ────────────────────────────────────────────────
print('\n[9] DELETE 단일 매핑')
status, j = _del(f'/api/facilities/1/beacons/{bid_A}/wifis/{wp2}', token=token_A)
_ok('200 응답',                   status == 200, j)
status, j = _get(f'/api/facilities/1/beacons/{bid_A}/wifis', token=token_A)
_ok('매핑 0건',                   len(j['wifis']) == 0, j)


# ── 10. 권한 — 다른 매장 사장이 접근 → 404 ─────────────────────────────
print('\n[10] 다른 매장 사장 토큰 → 404')
status, j = _get('/api/facilities/1/wifis', token=token_B)
_ok('404 응답',                   status == 404, j)


print('\n=== P15b (WiFi 관리 + 비콘↔WiFi 매핑 라우트) PASS ===')
os.unlink(tmp.name)
