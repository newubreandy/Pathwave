"""C-3 R1 — Cross-persona 시나리오 자동화.

페르소나 테스트 계획 §5 X1~X9 중 단일 페르소나 테스트에 안 들어간 흐름만
중점적으로 검증. 단일 페르소나 테스트가 이미 검증한 항목은 references 만.

이 파일이 다루는 cross 시나리오
------------------------------
- X3   매장 비콘 활성화 → 사용자가 handshake → WiFi 응답 (mock)
       (1단계 — 실 비콘 없음, 백엔드 API 만 검증)
- X5   사장이 쿠폰 발급 → 사용자가 본인 쿠폰 목록 확인 → 직원 스캔(use)
       3-party 전 흐름 한 트랜잭션

이 파일이 다루지 않는 것 (이미 단일 페르소나 테스트에서 검증)
--------------------------------------------------------
- X1 채팅 자동 번역 — tests/test_chat_translation.py (기존)
- X2 신고/차단 — tests/test_chat_block.py (기존)
- X4 약관 새 버전 + 재동의 — test_persona_p6.py (multilang 발행 검증)
- X6 스탬프 정책 변경 — 별도 PR 큐
- X7 매장 정지 노출 차단 — test_persona_p6.py (suspend 검증)
- X8 직원 해지 → 즉시 로그아웃 — test_persona_p4p5_staff.py (revoke)
- X9 결제 실패 → 노출 제한 — payments 시드 후 R2
"""
import os
import sqlite3
import tempfile

_tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); _tmp.close()
os.environ['PATHWAVE_DB']          = _tmp.name
os.environ['TRANSLATION_PROVIDER'] = 'stub'
os.environ['BOOTSTRAP_SUPER_ADMIN_EMAIL']    = 'admin@persona_x.test'
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


def _db():
    db = sqlite3.connect(_tmp.name); db.row_factory = sqlite3.Row
    return db


# ════════════════════════════════════════════════════════════════════════════
# [사전] admin + 비콘 + 사장 매장 + 사용자 가입 시드
# ════════════════════════════════════════════════════════════════════════════
print('\n[사전] 데이터 시드 (admin / 비콘 / 사장 매장 / 사용자)')

# admin 로그인
sc, body = _post('/api/admin/login',
                 {'email': 'admin@persona_x.test', 'password': 'SuperAdmin123!'})
admin_token = body['access_token']

# 비콘 입고
_post('/api/admin/beacons/import', {
    'beacons': [
        {'serial_no': 'X-BCN-001', 'uuid': '770E8400-E29B-41D4-A716-446655440001'},
    ],
}, token=admin_token)

# 사장 가입 + 승인 + 매장 + 비콘 claim + WiFi
_post('/api/facility/send-code', {'email': 'shop@persona_x.test'})
db = _db()
code = db.execute(
    "SELECT code FROM email_codes WHERE email='shop@persona_x.test' ORDER BY id DESC LIMIT 1"
).fetchone()['code']
db.close()
_post('/api/facility/register', {
    'email': 'shop@persona_x.test', 'code': code, 'password': 'Shop1234!',
    'company_name': 'Cross 매장', 'business_no': '999-99-99999',
    'manager_name': '홍사장', 'manager_phone': '010', 'manager_email': 'm@x.test',
    'consents': [
        {'kind': 'terms_facility', 'version': 'v', 'accepted': True},
        {'kind': 'privacy_facility', 'version': 'v', 'accepted': True},
    ],
})
sc, body = _get('/api/admin/facility-accounts?status=pending', token=admin_token)
_post(f'/api/admin/facility-accounts/{body["accounts"][0]["id"]}/verify', {}, token=admin_token)
sc, body = _post('/api/facility/login',
                 {'email': 'shop@persona_x.test', 'password': 'Shop1234!'})
owner_token = body['access_token']
sc, body = _post('/api/facilities', {'name': 'Cross 매장'}, token=owner_token)
facility_id = body['facility']['id']
_post(f'/api/facilities/{facility_id}/claim-beacon',
      {'serial_no': 'X-BCN-001', 'role': 'wifi'}, token=owner_token)
_post('/api/beacon/wifi', {
    'facility_id': facility_id, 'ssid': 'CrossWiFi', 'password': 'CrossPw1234!',
}, token=owner_token)

# 사용자 가입
_post('/api/auth/send-code', {'email': 'user@persona_x.test'})
db = _db()
code = db.execute(
    "SELECT code FROM email_codes WHERE email='user@persona_x.test' ORDER BY id DESC LIMIT 1"
).fetchone()['code']
db.close()
sc, body = _post('/api/auth/register', {
    'email': 'user@persona_x.test', 'code': code, 'password': 'User1234!',
    'birth_year': 1995,
    'consents': [
        {'kind': 'age14', 'version': 'v', 'accepted': True},
        {'kind': 'terms_user', 'version': 'v', 'accepted': True},
        {'kind': 'privacy_user', 'version': 'v', 'accepted': True},
        {'kind': 'location', 'version': 'v', 'accepted': True},
    ],
})
user_token = body['access_token']
user_id = body['user']['id'] if body.get('user') else None
if not user_id:
    db = _db()
    user_id = db.execute(
        "SELECT id FROM users WHERE email='user@persona_x.test'"
    ).fetchone()['id']
    db.close()
_ok(f'사전 시드 완료 (facility_id={facility_id}, user_id={user_id})',
    facility_id and user_id)


# ════════════════════════════════════════════════════════════════════════════
# [X3] 비콘 handshake → WiFi 응답
# ════════════════════════════════════════════════════════════════════════════
print('\n[X3] 비콘 handshake → WiFi 응답 (mock)')
db = _db()
b = db.execute(
    "SELECT uuid, major, minor FROM beacons WHERE serial_no='X-BCN-001'"
).fetchone()
db.close()
# handshake — BLE 감지된 비콘 정보로 백엔드에 WiFi 정보 요청
sc, body = _post('/api/beacon/handshake', {
    'uuid':  b['uuid'],
    'major': b['major'] or 0,
    'minor': b['minor'] or 0,
}, token=user_token)
_ok(f'handshake → 200 (got {sc})', sc == 200, body)
_ok('SSID 응답 노출 (wifi / wifis)',
    bool(body.get('wifi') or body.get('wifis')),
    body)
# 사장 매장 자동 인식 (X3 의 핵심: 어떤 매장 비콘인지 응답에 포함)
_ok(f'facility 매칭 (got {body.get("facility", {}).get("id")})',
    body.get('facility', {}).get('id') == facility_id)


# ════════════════════════════════════════════════════════════════════════════
# [X5] 쿠폰 발급 → 사용자 수령 → 사장(또는 직원) 사용 처리
# ════════════════════════════════════════════════════════════════════════════
print('\n[X5] 쿠폰 발급 → 사용자 → 사장 사용 처리')

# 사장이 쿠폰 발급 (단일 사용자 대상)
sc, body = _post(f'/api/facilities/{facility_id}/coupons', {
    'title':   '10% 할인 쿠폰',
    'benefit': '본 매장 결제 10% 할인',
    'user_id': user_id,
}, token=owner_token)
_ok(f'쿠폰 발급 → 200/201 (got {sc})', sc in (200, 201), body)
coupon_ids = body.get('coupon_ids') or [c['id'] for c in body.get('coupons', [])]
_ok(f'발급된 쿠폰 1건 (got {len(coupon_ids)})', len(coupon_ids) == 1, body)
coupon_id = coupon_ids[0]

# 사용자가 본인 쿠폰 목록 확인
sc, body = _get('/api/users/me/coupons', token=user_token)
_ok(f'사용자 쿠폰 목록 → 200 (got {sc})', sc == 200, body)
my_coupons = body.get('coupons', [])
_ok(f'본인 쿠폰 1건 (got {len(my_coupons)})', len(my_coupons) >= 1, body)
_ok('상태=available (used=false)',
    any(c['id'] == coupon_id and not c.get('used') for c in my_coupons))

# 사장 (또는 직원) 이 쿠폰 사용 처리
sc, body = _post(f'/api/coupons/{coupon_id}/use', {}, token=owner_token)
_ok(f'쿠폰 use → 200 (got {sc})', sc == 200, body)

# 같은 쿠폰 재사용 → 409
sc, body = _post(f'/api/coupons/{coupon_id}/use', {}, token=owner_token)
_ok(f'재사용 → 409 (got {sc})', sc == 409, body)

# 사용자가 다시 목록 보기 → ?status=used 로 확인 (기본은 active 만 노출)
sc, body = _get('/api/users/me/coupons?status=used', token=user_token)
my_coupons = body.get('coupons', [])
used_in_list = any(c['id'] == coupon_id and c.get('status') == 'used' for c in my_coupons)
_ok(f'사용자 화면 (status=used) — 사용된 쿠폰 노출 (got {used_in_list})',
    used_in_list, my_coupons)

# 기본 active 필터에서는 제외되어야 정상
sc, body = _get('/api/users/me/coupons', token=user_token)
my_active = body.get('coupons', [])
_ok(f'사용자 화면 (기본 active) — 사용된 쿠폰 미노출 (got len={len(my_active)})',
    not any(c['id'] == coupon_id for c in my_active))


print('\n=== Cross-persona R1 시나리오 통과 ===')
os.unlink(_tmp.name)
