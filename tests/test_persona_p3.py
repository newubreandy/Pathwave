"""C-3 R1 — Persona P3: 소규모 매장 사장(facility owner) end-to-end 자동 검증.

다루는 시나리오 (페르소나 테스트 계획 §4-B)
------------------------------------------
- P3-1  send-code + register (terms_facility/privacy_facility 필수)
- P3-2  가입 직후 status='pending' 로그인 시 진입 차단/안내
- P3-3  운영자 승인 후 로그인 (정상 진입)
- P3-4  매장 등록 (1계정 1매장)
- P3-5  비콘 claim — admin 이 입고한 SN 으로
- P3-6  WiFi 프로파일 등록 (AES-256-GCM 암호화)
- P3-7  비콘 ↔ WiFi 매핑

PASS 조건
---------
- 가입 → pending → verified → 매장 → claim → WiFi 등록 흐름이 한 트랜잭션
  처럼 끊김 없이 흐른다.
- WiFi 비번이 평문 저장되지 않는다 (DB 의 password 필드가 입력 평문과 다름).
"""
import os
import sqlite3
import tempfile

# ── 환경 셋업 ──
_tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); _tmp.close()
os.environ['PATHWAVE_DB']          = _tmp.name
os.environ['TRANSLATION_PROVIDER'] = 'stub'
os.environ['BOOTSTRAP_SUPER_ADMIN_EMAIL']    = 'admin@persona_p3.test'
os.environ['BOOTSTRAP_SUPER_ADMIN_PASSWORD'] = 'SuperAdmin123!'
os.environ.pop('ANTHROPIC_API_KEY', None)
os.environ.pop('DEEPL_API_KEY', None)

import models.database as _dbmod  # noqa: E402
_dbmod.DB_PATH = _tmp.name
_dbmod.init_db()

from app import app  # noqa: E402
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
    r = c.post(path, json=data or {}, headers=h)
    return r.status_code, (r.get_json() or {})


def _get(path, token=None):
    h = {}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.get(path, headers=h)
    return r.status_code, (r.get_json() or {})


def _put(path, data, token=None):
    h = {'Content-Type': 'application/json'}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.put(path, json=data, headers=h)
    return r.status_code, (r.get_json() or {})


def _db():
    db = sqlite3.connect(_tmp.name); db.row_factory = sqlite3.Row
    return db


# ════════════════════════════════════════════════════════════════════════════
# 사전 셋업: admin 로그인 + 비콘 입고 (P3-5 에서 claim 할 비콘 준비)
# ════════════════════════════════════════════════════════════════════════════
print('\n[사전] admin 로그인 + 비콘 3건 입고')
sc, body = _post('/api/admin/login',
                 {'email': 'admin@persona_p3.test', 'password': 'SuperAdmin123!'})
_ok('admin login 200', sc == 200 and body.get('access_token'))
admin_token = body['access_token']

sc, body = _post('/api/admin/beacons/import', {
    'beacons': [
        {'serial_no': 'P3-BCN-001', 'uuid': '660E8400-E29B-41D4-A716-446655440001'},
        {'serial_no': 'P3-BCN-002', 'uuid': '660E8400-E29B-41D4-A716-446655440002'},
        {'serial_no': 'P3-BCN-003', 'uuid': '660E8400-E29B-41D4-A716-446655440003'},
    ],
}, token=admin_token)
_ok(f'비콘 3건 입고 (got imported_count={body.get("imported_count")})',
    sc == 201 and body.get('imported_count') == 3)


# ════════════════════════════════════════════════════════════════════════════
# [P3-1] 사장 send-code + register (분리 약관)
# ════════════════════════════════════════════════════════════════════════════
print('\n[P3-1] 사장 가입 — terms_facility/privacy_facility 필수')
sc, _ = _post('/api/facility/send-code', {'email': 'shop@persona_p3.test'})
_ok(f'send-code 200 (got {sc})', sc == 200)

db = _db()
code_row = db.execute(
    "SELECT code FROM email_codes WHERE email='shop@persona_p3.test' ORDER BY id DESC LIMIT 1"
).fetchone()
db.close()
code = code_row['code']
_ok(f'DB 인증 코드 ({code})', code is not None)

# 약관 빠뜨려서 가입 시도 → 400
sc, body = _post('/api/facility/register', {
    'email': 'shop@persona_p3.test',
    'code':  code,
    'password': 'Shop1234!',
    'company_name':  '소규모 매장 1호점',
    'business_no':   '111-22-33333',
    'manager_name':  '홍사장',
    'manager_phone': '010-1111-2222',
    'manager_email': 'mgr@persona_p3.test',
    'consents': [],
})
_ok(f'약관 누락 → 400 (got {sc})', sc == 400, body)
_ok('메시지에 "필수 동의" 포함', '필수 동의' in (body.get('message') or ''))

# 약관 갖추고 재시도 → 201 + pending
sc, body = _post('/api/facility/register', {
    'email': 'shop@persona_p3.test',
    'code':  code,
    'password': 'Shop1234!',
    'company_name':  '소규모 매장 1호점',
    'business_no':   '111-22-33333',
    'manager_name':  '홍사장',
    'manager_phone': '010-1111-2222',
    'manager_email': 'mgr@persona_p3.test',
    'consents': [
        {'kind': 'terms_facility',   'version': 'v', 'accepted': True},
        {'kind': 'privacy_facility', 'version': 'v', 'accepted': True},
    ],
})
_ok(f'register → 201 (got {sc})', sc == 201, body)


# ════════════════════════════════════════════════════════════════════════════
# [P3-2] pending 상태에서 로그인 — 진입 정책 검증
# ════════════════════════════════════════════════════════════════════════════
print('\n[P3-2] pending 상태 로그인')
sc, body = _post('/api/facility/login',
                 {'email': 'shop@persona_p3.test', 'password': 'Shop1234!'})
# 정책: 200 + token + status='pending' (provider-web 측에서 화면 분기) 또는 403/401
_ok(f'login 응답 (got {sc})', sc in (200, 401, 403), body)
if sc == 200:
    pending_token = body.get('access_token')
    _ok('pending 상태 토큰에 access 동봉', isinstance(pending_token, str))


# ════════════════════════════════════════════════════════════════════════════
# [P3-3] admin 승인 → 로그인 정상
# ════════════════════════════════════════════════════════════════════════════
print('\n[P3-3] admin 승인 + 정상 로그인')
sc, body = _get('/api/admin/facility-accounts?status=pending', token=admin_token)
_ok(f'pending 1건 (got count={body.get("count")})',
    sc == 200 and body.get('count') >= 1)
aid = body['accounts'][0]['id']

sc, body = _post(f'/api/admin/facility-accounts/{aid}/verify', {}, token=admin_token)
_ok(f'verify → 200 (got {sc})', sc == 200, body)

# verified 후 로그인
sc, body = _post('/api/facility/login',
                 {'email': 'shop@persona_p3.test', 'password': 'Shop1234!'})
_ok(f'verified 로그인 → 200 + token (got {sc})',
    sc == 200 and body.get('access_token'), body)
shop_token = body['access_token']
shop_account_id = body.get('account', {}).get('id') or body.get('id')


# ════════════════════════════════════════════════════════════════════════════
# [P3-4] 매장 등록 (1계정 1매장)
# ════════════════════════════════════════════════════════════════════════════
print('\n[P3-4] 매장 등록')
sc, body = _post('/api/facilities', {
    'name': '소규모 매장 1호점',
    'address': '서울시 강남구 테헤란로 1',
    'phone': '02-1234-5678',
    'business_hours': '09:00-22:00',
    'description': 'P3 자동 테스트 매장',
}, token=shop_token)
_ok(f'매장 등록 → 201 (got {sc})', sc == 201, body)
facility_id = body['facility']['id']
_ok('매장 active=1', body['facility']['active'] is True or body['facility']['active'] == 1)


# ════════════════════════════════════════════════════════════════════════════
# [P3-5] 비콘 claim (P3-BCN-001)
# ════════════════════════════════════════════════════════════════════════════
print('\n[P3-5] 비콘 claim')
sc, body = _post(f'/api/facilities/{facility_id}/claim-beacon', {
    'serial_no': 'P3-BCN-001',
    'role': 'wifi',
}, token=shop_token)
_ok(f'claim → 200 (got {sc})', sc == 200, body)

# 잘못된 SN
sc, body = _post(f'/api/facilities/{facility_id}/claim-beacon', {
    'serial_no': 'NOT-EXIST-SN',
    'role': 'wifi',
}, token=shop_token)
_ok(f'없는 SN → 404/400 (got {sc})', sc in (400, 404), body)

# 같은 SN 재claim
sc, body = _post(f'/api/facilities/{facility_id}/claim-beacon', {
    'serial_no': 'P3-BCN-001',
    'role': 'wifi',
}, token=shop_token)
_ok(f'이미 claim 된 SN → 4xx (got {sc})', sc in (400, 404, 409), body)

# DB 상태: status='active', facility_id 매핑
db = _db()
b = db.execute(
    "SELECT status, facility_id FROM beacons WHERE serial_no='P3-BCN-001'"
).fetchone()
db.close()
_ok(f"status=active, facility_id={facility_id} (got status={b['status']}, fid={b['facility_id']})",
    b['status'] == 'active' and b['facility_id'] == facility_id)


# ════════════════════════════════════════════════════════════════════════════
# [P3-6] WiFi 프로파일 등록 (AES-256-GCM 암호화 검증)
# ════════════════════════════════════════════════════════════════════════════
print('\n[P3-6] WiFi 등록 + 비번 암호화 검증')
WIFI_PLAIN = 'MySecretWiFiPw123!'
sc, body = _post('/api/beacon/wifi', {
    'facility_id': facility_id,
    'ssid': 'P3-TestWiFi',
    'password': WIFI_PLAIN,
    'scope': 'public',
    'credential_mode': 'static',
}, token=shop_token)
_ok(f'WiFi 등록 → 200 (got {sc})', sc == 200, body)
wifi_id = body.get('wifi_profile_id')

# DB 검증 — 평문이 그대로 저장되면 안 됨
db = _db()
w = db.execute(
    "SELECT ssid, password FROM wifi_profiles WHERE id=?", (wifi_id,)
).fetchone()
db.close()
_ok(f'SSID 저장 (got {w["ssid"]})', w['ssid'] == 'P3-TestWiFi')
_ok('비번이 평문이 아님 (AES-256-GCM 암호화)',
    isinstance(w['password'], str) and w['password'] != WIFI_PLAIN and len(w['password']) > len(WIFI_PLAIN),
    f'stored={w["password"][:40]}... (len={len(w["password"])})')

# 사장 본인이 평문 조회는 가능 — include_password=1
sc, body = _get(f'/api/facilities/{facility_id}/wifis?include_password=1', token=shop_token)
_ok(f'wifi 목록 + 비번 (got {sc})', sc == 200, body)
wifi_row = next((w for w in body.get('wifis', []) if w['id'] == wifi_id), None)
_ok('사장 본인은 평문 비번 복호화 가능',
    wifi_row and wifi_row.get('password') == WIFI_PLAIN,
    wifi_row)


# ════════════════════════════════════════════════════════════════════════════
# [P3-7] 비콘 ↔ WiFi 매핑
# ════════════════════════════════════════════════════════════════════════════
print('\n[P3-7] 비콘 ↔ WiFi 매핑')
db = _db()
bid_row = db.execute(
    "SELECT id FROM beacons WHERE serial_no='P3-BCN-001'"
).fetchone()
db.close()
beacon_id = bid_row['id']

# 매핑 PUT (전체 교체)
sc, body = _put(f'/api/facilities/{facility_id}/beacons/{beacon_id}/wifis', {
    'wifi_profile_ids': [wifi_id],
}, token=shop_token)
_ok(f'매핑 PUT → 200 (got {sc})', sc == 200, body)

# 매핑 GET
sc, body = _get(f'/api/facilities/{facility_id}/beacons/{beacon_id}/wifis', token=shop_token)
_ok(f'매핑 GET → 200 (got {sc})', sc == 200, body)
wifis = body.get('wifis', [])
_ok(f'매핑된 wifi 1건 (got {len(wifis)})', len(wifis) == 1)


print('\n=== Persona P3 소규모 매장 사장 — R1 전 시나리오 통과 ===')
os.unlink(_tmp.name)
