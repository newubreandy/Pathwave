"""PR #46 — 정책 버전 관리 + 이전 버전 보기 + 이메일 공지 통합 테스트."""
import os
import json
import sqlite3
import tempfile

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name
os.environ['BOOTSTRAP_SUPER_ADMIN_EMAIL']    = 'admin@policy.test'
os.environ['BOOTSTRAP_SUPER_ADMIN_PASSWORD'] = 'AdminPass1!'
os.environ['EMAIL_PROVIDER'] = 'console'

import models.database as _dbmod  # noqa: E402
def _patched_get_db():
    conn = sqlite3.connect(os.environ['PATHWAVE_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn
_dbmod.get_db = _patched_get_db

from app import app  # noqa: E402
import models.email_provider as _email_mod  # noqa: E402

c = app.test_client()


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


def _post(path, data, token=None):
    h = {'Content-Type': 'application/json'}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.post(path, data=json.dumps(data), headers=h)
    return r.status_code, r.get_json()


def _patch(path, data, token=None):
    h = {'Content-Type': 'application/json'}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.patch(path, data=json.dumps(data), headers=h)
    return r.status_code, r.get_json()


def _get(path, token=None):
    h = {}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.get(path, headers=h)
    return r.status_code, r.get_json()


# ── [1] 운영자 로그인 ─────────────────────────────────────────────────────
print('\n[1] super admin 로그인')
s, j = _post('/api/admin/login',
             {'email': 'admin@policy.test', 'password': 'AdminPass1!'})
_ok('200', s == 200)
admin_token = j['access_token']


# ── [2] DB 비어있을 때 GET /api/policies — file fallback ──────────────────
print('\n[2] DB 비었을 때 — static 파일 fallback')
s, j = _get('/api/policies/terms')
_ok('200', s == 200)
_ok('source = static_file (PR #45 의 파일)',
    j.get('source') == 'static_file', j)
_ok('version = unspecified', j['version'] == 'unspecified')


# ── [3] 운영자 새 버전 작성 (즉시 시행) ───────────────────────────────────
print('\n[3] 새 정책 버전 작성 (즉시 시행)')
s, j = _post('/api/admin/policies', {
    'kind':         'terms',
    'version':      '2026-05-05',
    'title':        '서비스 이용약관 v2',
    'body':         '# 새로운 약관 본문\n\n변경된 내용입니다.',
    'change_log':   '제3조 (약관의 게시) 항목 명확화',
    'effective_at': '2025-01-01T00:00:00',  # 과거 → 즉시 시행
}, token=admin_token)
_ok('201', s == 201, j)
policy_id = j['policy']['id']


# ── [4] DB 우선 — GET /api/policies/terms 가 새 버전 반환 ─────────────────
print('\n[4] DB 우선 정책 — 새 버전이 반환됨')
s, j = _get('/api/policies/terms')
_ok('200', s == 200)
_ok(f'version = 2026-05-05 (got {j["version"]})', j['version'] == '2026-05-05')
_ok('source = db', j.get('source') is None or j.get('source') == 'db')
_ok('change_log 포함', '제3조' in (j.get('change_log') or ''))


# ── [5] 이전 버전 보기 — GET /api/policies/terms/versions ────────────────
print('\n[5] 이전 버전 목록')
s, j = _get('/api/policies/terms/versions')
_ok('200', s == 200)
_ok(f'1개 버전 (got {len(j["versions"])})', len(j['versions']) == 1)
_ok('첫 버전이 v2', j['versions'][0]['version'] == '2026-05-05')


# ── [6] 미래 effective_at 으로 예약 ─────────────────────────────────────
print('\n[6] 미래 시점 예약 (pending)')
s, j = _post('/api/admin/policies', {
    'kind':         'privacy',
    'version':      '2026-06-01',
    'body':         '# 새 개인정보 방침',
    'change_log':   '제4조 제3자 제공 항목 추가',
    'effective_at': '2099-12-31T00:00:00',  # 멀리 미래
}, token=admin_token)
_ok('201', s == 201, j)
pending_id = j['policy']['id']


# ── [7] admin 목록 — active + pending ───────────────────────────────────
print('\n[7] /api/admin/policies — active + pending 분리 조회')
s, j = _get('/api/admin/policies', token=admin_token)
_ok('200', s == 200)
_ok(f'active 9개 (모든 kind, got {len(j["active"])})',
    len(j['active']) == 9)
_ok(f'pending 1개 (got {len(j["pending"])})', len(j['pending']) == 1)


# ── [8] 미시행 버전 수정 가능 ───────────────────────────────────────────
print('\n[8] pending 버전 PATCH')
s, j = _patch(f'/api/admin/policies/{pending_id}', {
    'change_log': '제4조 + 제5조 동시 갱신',
}, token=admin_token)
_ok('200', s == 200, j)
_ok('change_log 갱신', '제5조' in j['policy']['change_log'])


# ── [9] 시행된 버전 수정 거부 ───────────────────────────────────────────
print('\n[9] 시행된(active) 버전은 PATCH 거부')
s, j = _patch(f'/api/admin/policies/{policy_id}', {
    'body': 'tampered',
}, token=admin_token)
_ok(f'409 (got {s})', s == 409, j)


# ── [10] 이메일 공지 발송 (사용자 / 사장 1명씩 등록 후) ────────────────
print('\n[10] 이메일 공지')
db = _patched_get_db()
db.execute("INSERT INTO users (email, password) VALUES ('u1@policy.test', 'x')")
db.execute("""INSERT INTO facility_accounts (business_no, company_name, email,
              password, manager_name, manager_phone, manager_email,
              verified, status)
              VALUES ('111-22-33333','테스트','f1@policy.test','x','홍','010-0000-0000',
                     'f1@policy.test', 1, 'verified')""")
db.commit(); db.close()

_email_mod.ConsoleEmailProvider.sent_log.clear()
s, j = _post(f'/api/admin/policies/{policy_id}/notify',
             {'sub_type': 'all'}, token=admin_token)
_ok('200', s == 200, j)
_ok(f"발송 2건 (user 1 + facility 1, got sent={j['sent']})",
    j['sent'] == 2)
_ok(f"console log 2건 누적", len(_email_mod.ConsoleEmailProvider.sent_log) == 2)


# ── [11] 중복 발송 거부 ─────────────────────────────────────────────────
print('\n[11] 동일 정책 재공지 거부')
s, j = _post(f'/api/admin/policies/{policy_id}/notify',
             {'sub_type': 'all'}, token=admin_token)
_ok(f'409 (got {s})', s == 409)


print('\n✅ 모든 시나리오 통과')
