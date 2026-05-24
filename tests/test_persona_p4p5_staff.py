"""C-3 R1 — Persona P4 (중대형 매장 사장) + P5 (직원) end-to-end.

P3 가 검증한 기본 매장 흐름 위에서 직원 초대/수락/권한 분리 흐름을 검증.

다루는 시나리오 (페르소나 테스트 계획 §4-C, §4-D)
-----------------------------------------------
P4 (owner)
- P4-1  직원 초대 코드 발급 (/api/staff/invite)
- P4-2  같은 이메일 재초대 → 409 (이미 진행 중)
- P4-3  내 초대 목록 조회 (/api/staff GET)
- P4-4  초대 revoke

P5 (staff)
- P5-1  초대 토큰으로 accept (/api/staff/accept) → staff_accounts row
- P5-2  staff login + /me 조회
- P5-3  staff 토큰으로 매장 WiFi 조회 가능 (사장 ↔ 직원 공유)
- P5-4  staff 토큰으로 owner-only 작업 (WiFi 등록) → 403
"""
import os
import sqlite3
import tempfile

_tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); _tmp.close()
os.environ['PATHWAVE_DB']          = _tmp.name
os.environ['TRANSLATION_PROVIDER'] = 'stub'
os.environ['BOOTSTRAP_SUPER_ADMIN_EMAIL']    = 'admin@persona_p4.test'
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


def _delete(path, token=None):
    h = {}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.delete(path, headers=h)
    return r.status_code, (r.get_json() or {})


def _db():
    db = sqlite3.connect(_tmp.name); db.row_factory = sqlite3.Row
    return db


# ════════════════════════════════════════════════════════════════════════════
# [사전] admin 로그인 + 사장 가입+승인 + 매장 등록
# ════════════════════════════════════════════════════════════════════════════
print('\n[사전] admin + 사장 + 매장 준비')
sc, body = _post('/api/admin/login',
                 {'email': 'admin@persona_p4.test', 'password': 'SuperAdmin123!'})
admin_token = body['access_token']

# 사장 가입
_post('/api/facility/send-code', {'email': 'owner@persona_p4.test'})
db = _db()
code = db.execute(
    "SELECT code FROM email_codes WHERE email='owner@persona_p4.test' ORDER BY id DESC LIMIT 1"
).fetchone()['code']
db.close()

sc, body = _post('/api/facility/register', {
    'email': 'owner@persona_p4.test',
    'code':  code,
    'password': 'Owner1234!',
    'company_name':  '중대형 매장 본점',
    'business_no':   '222-33-44444',
    'manager_name':  '김사장',
    'manager_phone': '010-9999-8888',
    'manager_email': 'kim@persona_p4.test',
    'consents': [
        {'kind': 'terms_facility',   'version': 'v', 'accepted': True},
        {'kind': 'privacy_facility', 'version': 'v', 'accepted': True},
    ],
})
_ok(f'owner register → 201 (got {sc})', sc == 201, body)

# admin verify
sc, body = _get('/api/admin/facility-accounts?status=pending', token=admin_token)
aid = body['accounts'][0]['id']
_post(f'/api/admin/facility-accounts/{aid}/verify', {}, token=admin_token)

# owner login + 매장 등록
sc, body = _post('/api/facility/login',
                 {'email': 'owner@persona_p4.test', 'password': 'Owner1234!'})
owner_token = body['access_token']

sc, body = _post('/api/facilities', {
    'name': '중대형 매장 본점',
    'address': '서울시 종로구 1',
    'phone': '02-3333-4444',
}, token=owner_token)
facility_id = body['facility']['id']
_ok(f'매장 등록 fid={facility_id}', sc == 201)


# ════════════════════════════════════════════════════════════════════════════
# [P4-1] 직원 초대 발송
# ════════════════════════════════════════════════════════════════════════════
print('\n[P4-1] 직원 초대 발송')
sc, body = _post('/api/staff/invite', {
    'email': 'staff1@persona_p4.test',
    'role':  'staff',
}, token=owner_token)
_ok(f'invite → 201 (got {sc})', sc == 201, body)
invite_id = body['invitation']['id']
_ok('status=pending', body['invitation']['status'] == 'pending')
# invite_token 은 API 응답에 노출되지 않음 (보안) — DB 에서 가져옴
db = _db()
invite_token = db.execute(
    "SELECT invite_token FROM staff_invitations WHERE id=?", (invite_id,)
).fetchone()['invite_token']
db.close()
_ok('invite_token DB 에 발급됨', isinstance(invite_token, str) and len(invite_token) > 20)


# ════════════════════════════════════════════════════════════════════════════
# [P4-2] 같은 이메일 재초대 → 409
# ════════════════════════════════════════════════════════════════════════════
print('\n[P4-2] 같은 이메일 재초대')
sc, body = _post('/api/staff/invite', {
    'email': 'staff1@persona_p4.test',
    'role':  'staff',
}, token=owner_token)
_ok(f'중복 초대 → 409 (got {sc})', sc == 409, body)


# ════════════════════════════════════════════════════════════════════════════
# [P4-3] 내 초대 목록 조회
# ════════════════════════════════════════════════════════════════════════════
print('\n[P4-3] 내 초대 목록')
sc, body = _get('/api/staff', token=owner_token)
_ok(f'목록 → 200 (got {sc})', sc == 200, body)
items = body.get('invitations', body.get('items', []))
_ok(f'1건 이상 (got {len(items)})', len(items) >= 1)


# ════════════════════════════════════════════════════════════════════════════
# [P5-1] 직원이 초대 토큰으로 accept
# ════════════════════════════════════════════════════════════════════════════
print('\n[P5-1] 직원 accept')
# 너무 약한 비번 → 400
sc, body = _post('/api/staff/accept', {
    'invite_token': invite_token,
    'password': 'abc',
    'name': '이직원',
})
_ok(f'약한 비번 → 400 (got {sc})', sc == 400, body)

# 정상 비번
sc, body = _post('/api/staff/accept', {
    'invite_token': invite_token,
    'password': 'Staff1234!',
    'name': '이직원',
    'phone': '010-7777-6666',
})
_ok(f'accept → 200/201 (got {sc})', sc in (200, 201), body)

# DB 검증
db = _db()
sa = db.execute(
    "SELECT id, email, role, facility_account_id FROM staff_accounts WHERE email='staff1@persona_p4.test'"
).fetchone()
inv = db.execute(
    "SELECT status FROM staff_invitations WHERE id=?", (invite_id,)
).fetchone()
db.close()
_ok(f'staff_accounts row 생성 (role={sa["role"]})', sa['role'] == 'staff')
_ok(f"invitation status='accepted' (got {inv['status']})", inv['status'] == 'accepted')


# 동일 토큰 재사용 → 409
sc, body = _post('/api/staff/accept', {
    'invite_token': invite_token,
    'password': 'Staff1234!',
})
_ok(f'재사용 → 409 (got {sc})', sc == 409, body)


# ════════════════════════════════════════════════════════════════════════════
# [P5-2] 직원 login + /me
# ════════════════════════════════════════════════════════════════════════════
print('\n[P5-2] 직원 login + /me')
sc, body = _post('/api/staff/login', {
    'email':    'staff1@persona_p4.test',
    'password': 'Staff1234!',
})
_ok(f'login → 200 (got {sc})', sc == 200 and body.get('access_token'), body)
staff_token = body['access_token']

sc, body = _get('/api/staff/me', token=staff_token)
_ok(f'/me → 200 (got {sc})', sc == 200, body)


# ════════════════════════════════════════════════════════════════════════════
# [P5-3] 직원 토큰으로 매장 WiFi 목록 조회 (공유 데이터)
# ════════════════════════════════════════════════════════════════════════════
print('\n[P5-3] staff 매장 WiFi 목록')
sc, body = _get(f'/api/facilities/{facility_id}/wifis', token=staff_token)
_ok(f'wifis GET → 200 (got {sc})', sc == 200, body)


# ════════════════════════════════════════════════════════════════════════════
# [P5-4] 직원이 owner-only 작업 시도 → 403
# ════════════════════════════════════════════════════════════════════════════
print('\n[P5-4] staff 가 WiFi 등록 시도 → 403')
sc, body = _post('/api/beacon/wifi', {
    'facility_id': facility_id,
    'ssid': 'StaffShouldNotCreate',
    'password': 'X@Pw1234!',
}, token=staff_token)
_ok(f'403 (got {sc})', sc == 403, body)


# ════════════════════════════════════════════════════════════════════════════
# [P4-4] owner 가 초대 revoke 시도
#  - 이미 accepted 된 초대는 revoke 불가 (정책에 따라 4xx)
#  - 새 pending 초대 만들어서 revoke
# ════════════════════════════════════════════════════════════════════════════
print('\n[P4-4] 새 pending 초대 revoke')
sc, body = _post('/api/staff/invite', {
    'email': 'staff2@persona_p4.test',
    'role':  'admin',
}, token=owner_token)
_ok(f'두 번째 초대 → 201 (got {sc})', sc == 201, body)
new_invite_id = body['invitation']['id']

sc, body = _delete(f'/api/staff/{new_invite_id}', token=owner_token)
_ok(f'revoke → 200 (got {sc})', sc == 200, body)

db = _db()
inv2 = db.execute(
    "SELECT status FROM staff_invitations WHERE id=?", (new_invite_id,)
).fetchone()
db.close()
_ok(f"status=revoked (got {inv2['status']})", inv2['status'] == 'revoked')

# revoke 된 초대 토큰으로 accept 시도 → 410
db = _db()
rev_token = db.execute(
    "SELECT invite_token FROM staff_invitations WHERE id=?", (new_invite_id,)
).fetchone()['invite_token']
db.close()
sc, body = _post('/api/staff/accept', {
    'invite_token': rev_token,
    'password': 'NewStaff1234!',
})
_ok(f'revoked 토큰 → 410 (got {sc})', sc == 410, body)


print('\n=== Persona P4 + P5 — R1 전 시나리오 통과 ===')
os.unlink(_tmp.name)
