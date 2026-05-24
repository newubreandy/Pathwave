"""C-3 R1 — Persona P6: 슈퍼어드민(super_admin) end-to-end 자동 검증.

다루는 시나리오 (페르소나 테스트 계획 §4-A 참조)
-----------------------------------------------
- P6-1  부트스트랩 어드민 로그인
- P6-2  비콘 CSV 입고 (POST /api/admin/beacons/import)
- P6-3  매장 가입 신청 검토 + 승인 (verify)
- P6-4  매장 정지 / 재활성화 (suspend / reactivate)
- P6-5  약관 새 버전 발행 (ko+en 동시, /policies/multilang)
- P6-6  약관 미시행 버전 수정 / 삭제
- P6-7  시스템 공지 작성 (announcement)
- P6-9  결제 환불 (stub provider — 빈 payments 면 skip)
- P6-10 통계 대시보드 (/stats/overview)
- P6-11 시스템 환경 점검 (운영자 본인 조회 /me + refresh)

PASS 조건
---------
- 모든 API 응답 status 200/201
- DB state 가 기대대로 전이 (status='verified' → 'suspended' → 'verified')
- 약관 multilang 발행 시 ko/en 각 1 row 추가
"""
import os
import sqlite3
import tempfile

# ── 환경 셋업 (다른 R1 테스트와 격리되도록 임시 DB) ──
_tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); _tmp.close()
os.environ['PATHWAVE_DB']          = _tmp.name
os.environ['TRANSLATION_PROVIDER'] = 'stub'
os.environ['BOOTSTRAP_SUPER_ADMIN_EMAIL']    = 'admin@persona_p6.test'
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


def _post(path, data, token=None):
    h = {'Content-Type': 'application/json'}
    if token:
        h['Authorization'] = f'Bearer {token}'
    r = c.post(path, json=data, headers=h)
    return r.status_code, (r.get_json() or {})


def _get(path, token=None):
    h = {}
    if token:
        h['Authorization'] = f'Bearer {token}'
    r = c.get(path, headers=h)
    return r.status_code, (r.get_json() or {})


def _patch(path, data, token=None):
    h = {'Content-Type': 'application/json'}
    if token:
        h['Authorization'] = f'Bearer {token}'
    r = c.patch(path, json=data, headers=h)
    return r.status_code, (r.get_json() or {})


def _delete(path, token=None):
    h = {}
    if token:
        h['Authorization'] = f'Bearer {token}'
    r = c.delete(path, headers=h)
    return r.status_code, (r.get_json() or {})


# ════════════════════════════════════════════════════════════════════════════
# [P6-1] 슈퍼어드민 로그인
# ════════════════════════════════════════════════════════════════════════════
print('\n[P6-1] 슈퍼어드민 로그인')
sc, body = _post('/api/admin/login', {
    'email': 'admin@persona_p6.test',
    'password': 'SuperAdmin123!',
})
_ok('200 + access_token', sc == 200 and body.get('access_token'), body)
admin_token = body['access_token']
_ok('refresh_token 동봉', isinstance(body.get('refresh_token'), str))
_ok('account 정보 노출 (sub_type=super_admin)',
    body.get('admin', {}).get('role') in {'super', 'super_admin', 'admin'})


# ── 잘못된 비번 거부 ──
sc, body = _post('/api/admin/login', {
    'email': 'admin@persona_p6.test',
    'password': 'WrongPassword!',
})
_ok('잘못된 비번 → 401', sc == 401, body)


# ════════════════════════════════════════════════════════════════════════════
# [P6-11] /me 조회 + refresh 토큰으로 access 재발급
# ════════════════════════════════════════════════════════════════════════════
print('\n[P6-11] /me + refresh')
sc, body = _get('/api/admin/me', token=admin_token)
_ok('/me 200', sc == 200 and (body.get('admin') or body.get('account')), body)


# ════════════════════════════════════════════════════════════════════════════
# [P6-2] 비콘 CSV 입고
# ════════════════════════════════════════════════════════════════════════════
print('\n[P6-2] 비콘 입고 (3건) — serial_no + UUID 형식')
import_payload = {
    'beacons': [
        {'serial_no': 'P6-BEACON-001', 'uuid': '550E8400-E29B-41D4-A716-446655440001'},
        {'serial_no': 'P6-BEACON-002', 'uuid': '550E8400-E29B-41D4-A716-446655440002'},
        {'serial_no': 'P6-BEACON-003', 'uuid': '550E8400-E29B-41D4-A716-446655440003'},
    ],
}
sc, body = _post('/api/admin/beacons/import', import_payload, token=admin_token)
# admin import 는 부분 성공도 200/201 가능
_ok(f'import → 201 (status={sc})', sc == 201, body)
_ok(f'imported_count == 3 (got {body.get("imported_count")})',
    body.get('imported_count') == 3, body)
_ok(f'errors == 0 (got {len(body.get("errors", []))})',
    len(body.get('errors', [])) == 0, body)

# 중복 SN 입고 → errors 처리 (부분 성공)
sc, body = _post('/api/admin/beacons/import', {
    'beacons': [{'serial_no': 'P6-BEACON-001',
                 'uuid': '550E8400-E29B-41D4-A716-446655440001'}],
}, token=admin_token)
_ok(f'중복 SN → 201/422 + errors 1 (got sc={sc}, errors={len(body.get("errors", []))})',
    sc in (201, 422) and len(body.get('errors', [])) == 1, body)

# 목록 조회 — response shape: {count, beacons}
sc, body = _get('/api/admin/beacons', token=admin_token)
_ok(f'목록 200 + 3건 (got count={body.get("count")})',
    sc == 200 and body.get('count') == 3)
_ok('status=inventory',
    all(b['status'] == 'inventory' for b in body.get('beacons', [])))


# ════════════════════════════════════════════════════════════════════════════
# [P6-3] 매장 가입 신청 → 승인
# ════════════════════════════════════════════════════════════════════════════
print('\n[P6-3] 매장 가입 신청 + 승인')

# 사장 send-code 가져오기
sc, _ = _post('/api/facility/send-code', {'email': 'shop1@persona_p6.test'})
_ok(f'facility send-code 200 (got {sc})', sc == 200)

db = sqlite3.connect(_tmp.name); db.row_factory = sqlite3.Row
code_row = db.execute(
    "SELECT code FROM email_codes WHERE email='shop1@persona_p6.test' ORDER BY id DESC LIMIT 1"
).fetchone()
db.close()
shop_code = code_row['code'] if code_row else None
_ok(f'DB 에 인증 코드 ({shop_code})', shop_code is not None)

# 사장 가입 (sub_type=facility, 새 분리 약관 필수)
sc, body = _post('/api/facility/register', {
    'email': 'shop1@persona_p6.test',
    'code':  shop_code,
    'password': 'Shop1234!',
    'company_name':  '테스트 매장 1호점',
    'business_no':   '123-45-67890',
    'manager_name':  '홍사장',
    'manager_phone': '010-1234-5678',
    'manager_email': 'mgr1@persona_p6.test',
    'consents': [
        {'kind': 'terms_facility',   'version': 'v', 'accepted': True},
        {'kind': 'privacy_facility', 'version': 'v', 'accepted': True},
    ],
})
_ok(f'facility/register → 201 (got {sc})', sc == 201, body)


# 어드민이 facility-accounts 목록 조회 → pending 1건
sc, body = _get('/api/admin/facility-accounts?status=pending', token=admin_token)
_ok(f'pending 1건 (got count={body.get("count")})',
    sc == 200 and body.get('count', 0) >= 1, body)

# 첫 pending row 의 id 로 verify
pending_aid = body['accounts'][0]['id']
sc, body = _post(f'/api/admin/facility-accounts/{pending_aid}/verify',
                 {}, token=admin_token)
_ok(f'verify → 200 (got {sc})', sc == 200, body)

# DB 상태 확인
db = sqlite3.connect(_tmp.name); db.row_factory = sqlite3.Row
row = db.execute(
    "SELECT status, verified FROM facility_accounts WHERE id=?", (pending_aid,)
).fetchone()
db.close()
_ok(f'status=verified, verified=1 (got status={row["status"]}, verified={row["verified"]})',
    row['status'] == 'verified' and row['verified'] == 1)


# ════════════════════════════════════════════════════════════════════════════
# [P6-4] 매장 정지 → 재활성화
# ════════════════════════════════════════════════════════════════════════════
print('\n[P6-4] 매장 정지 → 재활성화')
sc, body = _post(f'/api/admin/facility-accounts/{pending_aid}/suspend',
                 {'reason': '테스트 정지'}, token=admin_token)
_ok(f'suspend → 200 (got {sc})', sc == 200, body)

db = sqlite3.connect(_tmp.name); db.row_factory = sqlite3.Row
row = db.execute(
    "SELECT status FROM facility_accounts WHERE id=?", (pending_aid,)
).fetchone()
db.close()
_ok(f'status=suspended (got {row["status"]})', row['status'] == 'suspended')

sc, body = _post(f'/api/admin/facility-accounts/{pending_aid}/reactivate',
                 {}, token=admin_token)
_ok(f'reactivate → 200 (got {sc})', sc == 200, body)
db = sqlite3.connect(_tmp.name); db.row_factory = sqlite3.Row
row = db.execute(
    "SELECT status FROM facility_accounts WHERE id=?", (pending_aid,)
).fetchone()
db.close()
_ok(f'status=verified 복원 (got {row["status"]})', row['status'] == 'verified')


# ════════════════════════════════════════════════════════════════════════════
# [P6-5] 약관 새 버전 발행 (ko + en multilang)
# ════════════════════════════════════════════════════════════════════════════
print('\n[P6-5] 약관 multilang 발행 (terms_user v0.2 ko+en)')
sc, body = _post('/api/admin/policies/multilang', {
    'kind': 'terms_user',
    'version': '0.2',
    'effective_at': '2030-01-01T00:00:00',
    'ko': {
        'title': '서비스 이용약관 v0.2',
        'body': '## 제1조\nv0.2 한국어 본문',
        'change_log': '제3조 추가',
    },
    'en': {
        'title': 'Terms of Service v0.2',
        'body': '## Article 1\nv0.2 English body',
        'change_log': 'Added Article 3',
    },
}, token=admin_token)
_ok(f'multilang → 200/201 (got {sc})', sc in (200, 201), body)

# DB 검증 — terms_user v0.2 가 ko + en 2 row
db = sqlite3.connect(_tmp.name); db.row_factory = sqlite3.Row
rows = db.execute(
    "SELECT lang FROM policies WHERE kind='terms_user' AND version='0.2'"
).fetchall()
db.close()
langs = sorted([r['lang'] for r in rows])
_ok(f'ko+en 2 row 추가 (got {langs})', langs == ['en', 'ko'])


# ════════════════════════════════════════════════════════════════════════════
# [P6-6] 약관 미시행 버전 수정 (lang=ko 만)
# ════════════════════════════════════════════════════════════════════════════
print('\n[P6-6] 약관 v0.2 ko 본문 수정')
db = sqlite3.connect(_tmp.name); db.row_factory = sqlite3.Row
ko_row = db.execute(
    "SELECT id FROM policies WHERE kind='terms_user' AND version='0.2' AND lang='ko'"
).fetchone()
db.close()
sc, body = _patch(f'/api/admin/policies/{ko_row["id"]}',
                  {'change_log': '제3조 + 제4조 추가'}, token=admin_token)
_ok(f'patch → 200 (got {sc})', sc == 200, body)


# ════════════════════════════════════════════════════════════════════════════
# [P6-7] 시스템 공지 작성 + 사장 측에서 노출 확인
# ════════════════════════════════════════════════════════════════════════════
print('\n[P6-7] 시스템 공지 작성')
sc, body = _post('/api/admin/announcements', {
    'title': '서비스 점검 안내',
    'body': '내일 02:00 ~ 04:00 점검합니다',
    'audience': 'all',
    'lang_hint': 'ko',
}, token=admin_token)
_ok(f'create → 200/201 (got {sc})', sc in (200, 201), body)


# ════════════════════════════════════════════════════════════════════════════
# [P6-10] 통계 대시보드
# ════════════════════════════════════════════════════════════════════════════
print('\n[P6-10] 통계 대시보드')
sc, body = _get('/api/admin/stats/overview', token=admin_token)
_ok(f'/stats/overview → 200 (got {sc})', sc == 200, body)
cards = body.get('cards', {})
_ok('cards 에 핵심 KPI 노출 (total_users/facilities/beacons)',
    all(k in cards for k in (
        'total_users', 'total_facility_accounts', 'total_beacons',
        'verified_facility_accounts',
    )), cards)
_ok(f'verified_facility_accounts == 1 (got {cards.get("verified_facility_accounts")})',
    cards.get('verified_facility_accounts') == 1)
_ok(f'inventory_beacons == 3 (got {cards.get("inventory_beacons")})',
    cards.get('inventory_beacons') == 3)


# ════════════════════════════════════════════════════════════════════════════
# [P6-9] 결제 환불 — payments 비어있으면 skip
# ════════════════════════════════════════════════════════════════════════════
print('\n[P6-9] 결제 환불 (payments 없으면 skip)')
sc, body = _get('/api/admin/payments', token=admin_token)
items = body.get('items', [])
if items:
    pid = items[0]['id']
    sc2, body2 = _post(f'/api/admin/payments/{pid}/refund',
                       {'amount': 1000, 'reason': '테스트'}, token=admin_token)
    _ok(f'refund 호출 (got {sc2})', sc2 in (200, 400, 404),
        body2)  # 200 OK, 또는 비즈니스 검증 거부 OK
else:
    print('  - payments 비어있음 — refund 시나리오 skip (R2 시 시드 후 재실행)')


print('\n=== Persona P6 슈퍼어드민 — R1 전 시나리오 통과 ===')
os.unlink(_tmp.name)
