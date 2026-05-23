"""P15a — WiFi 등록·연동 백엔드 회귀 테스트.

검증 범위
---------
1) register_wifi 확장 필드 (scope/credential_mode/bssid/country) 저장 + id 반환
2) register_wifi backward-compat (필드 누락) 도 default 적용
3) register_wifi multi=true → 기존 active 유지 (다중 WiFi)
4) register_wifi multi=false → 기존 active=0 (legacy 단일 모드)
5) claim_beacon role='cashier' 저장
6) handshake 응답에 `wifis` 배열 추가 (backward `wifi` 단일도 유지)
7) handshake beacon_id 입력 시 beacon_wifi 매핑 필터
8) beacon_wifi 매핑 없으면 facility 전체로 fallback
"""
import os
import sqlite3
import tempfile

import bcrypt
import json

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


def _post(path, data=None, token=None):
    h = {'Content-Type': 'application/json'}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.post(path, data=json.dumps(data or {}), headers=h)
    return r.status_code, r.get_json()


# ── 0. 시드 ──────────────────────────────────────────────────────────────
print('\n[0] 시드 — facility + owner + 비콘 2개 (inventory)')
db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
hashed = bcrypt.hashpw(b'pw', bcrypt.gensalt()).decode()
db.execute("INSERT INTO facility_accounts (business_no, company_name, email, password, verified, status) VALUES ('001','S','o@x.com',?,1,'verified')", (hashed,))
db.execute("INSERT INTO facilities (name, owner_id, active) VALUES ('Cafe', 1, 1)")
db.execute("INSERT INTO beacons (serial_no, uuid, status) VALUES ('SN-A', 'U1', 'inventory')")
db.execute("INSERT INTO beacons (serial_no, uuid, status) VALUES ('SN-B', 'U2', 'inventory')")
db.commit(); db.close()

facility_token = make_jwt(1, 'o@x.com', sub_type='facility')


# ── 1. register_wifi 확장 필드 ──────────────────────────────────────────
print('\n[1] register_wifi 확장 필드 저장')
status, j = _post('/api/beacon/wifi',
                  {'facility_id': 1, 'ssid': 'CAFE-AP1', 'password': 'pw123',
                   'scope': 'public', 'credential_mode': 'static',
                   'bssid': 'AA:BB:CC:DD:EE:01', 'country': 'KR'},
                  token=facility_token)
_ok('200 응답',         status == 200, j)
_ok('wifi_profile_id 반환', j.get('wifi_profile_id') is not None, j)
wp1_id = j['wifi_profile_id']

db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
row = db.execute("SELECT * FROM wifi_profiles WHERE id=?", (wp1_id,)).fetchone()
db.close()
_ok("scope = 'public'",          row['scope'] == 'public', dict(row))
_ok("credential_mode = 'static'", row['credential_mode'] == 'static', dict(row))
_ok("bssid 저장",                 row['bssid'] == 'AA:BB:CC:DD:EE:01', dict(row))
_ok("country = 'KR'",             row['country'] == 'KR', dict(row))


# ── 2. backward-compat (필드 누락) ──────────────────────────────────────
print('\n[2] register_wifi backward-compat (확장 필드 누락)')
status, j = _post('/api/beacon/wifi',
                  {'facility_id': 1, 'ssid': 'CAFE-AP-LEGACY', 'password': 'pw'},
                  token=facility_token)
_ok('200 응답',                   status == 200, j)
# legacy 모드 → 기존 active=0 (단일 WiFi). 새 row 만 active=1.
db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
actives = db.execute("SELECT COUNT(*) AS n FROM wifi_profiles WHERE facility_id=1 AND active=1").fetchone()['n']
db.close()
_ok(f'active=1 row 수 == 1 (legacy 단일 모드, 실제 {actives})', actives == 1)


# ── 3. multi=true 모드 → 기존 active 유지 ───────────────────────────────
print('\n[3] multi=true → 기존 active 유지 (다중 WiFi)')
status, j = _post('/api/beacon/wifi',
                  {'facility_id': 1, 'ssid': 'CAFE-AP2', 'password': 'pw2',
                   'multi': True, 'scope': 'public'},
                  token=facility_token)
_ok('200 응답',                   status == 200, j)
wp3_id = j['wifi_profile_id']  # active=1 wifi 의 id (매핑용)
db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
actives = db.execute("SELECT COUNT(*) AS n FROM wifi_profiles WHERE facility_id=1 AND active=1").fetchone()['n']
db.close()
_ok(f'active=1 row 수 == 2 (multi 모드, 실제 {actives})', actives == 2)


# ── 4. claim_beacon role='cashier' ──────────────────────────────────────
print('\n[4] claim_beacon role=cashier 저장')
status, j = _post('/api/facilities/1/claim-beacon',
                  {'serial_no': 'SN-A', 'role': 'cashier'},
                  token=facility_token)
_ok('200 응답',                   status == 200, j)
db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
row = db.execute("SELECT role, status FROM beacons WHERE serial_no='SN-A'").fetchone()
db.close()
_ok("role = 'cashier'",           row['role'] == 'cashier', dict(row))
_ok("status = 'active'",          row['status'] == 'active', dict(row))


# ── 5. claim_beacon role 누락 → default 'wifi' ──────────────────────────
print('\n[5] claim_beacon role 누락 → default wifi')
status, j = _post('/api/facilities/1/claim-beacon',
                  {'serial_no': 'SN-B'}, token=facility_token)
_ok('200 응답',                   status == 200, j)
db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
row = db.execute("SELECT role FROM beacons WHERE serial_no='SN-B'").fetchone()
db.close()
_ok("role = 'wifi' (default)",    row['role'] == 'wifi', dict(row))


# ── 6. handshake — wifis 묶음 반환 ──────────────────────────────────────
print('\n[6] handshake 응답에 wifis 배열 추가')
# handshake 는 사용자 토큰 또는 비로그인 (게스트). facility 토큰은 아님.
status, j = _post('/api/beacon/handshake',
                  {'uuid': 'U1', 'major': 1, 'minor': 1})
_ok('응답 200',                   status == 200, j)
_ok('wifi 단일 필드 보존',         'wifi' in j, j)
_ok('wifis 배열 추가',             isinstance(j.get('wifis'), list), j)
_ok('wifis 첫 항목에 scope',       j['wifis'] and 'scope' in j['wifis'][0], j['wifis'])
_ok("multi=true 라 wifis 2건",   len(j['wifis']) == 2, j['wifis'])


# ── 7. handshake — beacon_id 입력 시 매핑 필터 ──────────────────────────
print('\n[7] handshake beacon_id + beacon_wifi 매핑 필터')
# 비콘 1번에 wifi 1번만 매핑
db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
# SN-A 의 id 가져오기
bid = db.execute("SELECT id FROM beacons WHERE serial_no='SN-A'").fetchone()['id']
db.execute("INSERT INTO beacon_wifi (beacon_id, wifi_profile_id, priority) VALUES (?, ?, 0)", (bid, wp3_id))
db.commit(); db.close()

status, j = _post('/api/beacon/handshake',
                  {'uuid': 'U1', 'major': 1, 'minor': 1})
_ok(f"wifis 1건 (매핑된 wp3 만, 실제 {len(j.get('wifis', []))})", len(j.get('wifis', [])) == 1, j['wifis'])
_ok("wifis[0].id == wp3_id",      j['wifis'][0]['id'] == wp3_id, j['wifis'])


# ── 8. handshake — 매핑 없으면 fallback ─────────────────────────────────
print('\n[8] handshake — 매핑 없는 beacon_id → facility 전체 fallback')
# 매핑 안 한 beacon (SN-B id 찾기)
db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
bid_b = db.execute("SELECT id FROM beacons WHERE serial_no='SN-B'").fetchone()['id']
db.close()
status, j = _post('/api/beacon/handshake',
                  {'uuid': 'U2', 'major': 1, 'minor': 2})
_ok(f'fallback: wifis == 2 (전체, 실제 {len(j.get("wifis", []))})',
    len(j.get('wifis', [])) == 2, j['wifis'])


print('\n=== P15a (백엔드 — handshake/register_wifi/claim_beacon) PASS ===')
os.unlink(tmp.name)
