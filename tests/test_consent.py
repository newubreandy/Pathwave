"""PR #45 — 회원가입 동의 시스템 통합 테스트."""
import os
import json
import sqlite3
import tempfile

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


# ── [1] 정책 메타 조회 ───────────────────────────────────────────────────
print('\n[1] GET /api/policies — 사용자용 항목 메타')
r = c.get('/api/policies?sub_type=user')
js = r.get_json()
_ok('200 OK', r.status_code == 200, js)
_ok('items 존재', isinstance(js.get('items'), list))
required_user = [it['kind'] for it in js['items'] if it['required']]
_ok(f'사용자 필수 항목 4개 (age14/terms/privacy/location) — got {required_user}',
    set(required_user) == {'age14', 'terms', 'privacy', 'location'})


# ── [2] 정책 본문 조회 (placeholder) ─────────────────────────────────────
print('\n[2] GET /api/policies/terms — placeholder body')
r = c.get('/api/policies/terms?lang=ko')
js = r.get_json()
_ok('200 OK', r.status_code == 200, js)
_ok('label = 서비스 이용약관 동의', '이용약관' in (js.get('label') or ''))
_ok('body 존재', isinstance(js.get('body'), str) and len(js['body']) > 0)

print('\n[3] GET /api/policies/unknown_kind → 404')
r = c.get('/api/policies/totally_unknown')
_ok('404', r.status_code == 404)


# ── [4] 회원가입 — 동의 누락 시 거부 ─────────────────────────────────────
print('\n[4] /api/auth/send-code → 코드 받기')
s, j = _post('/api/auth/send-code', {'email': 'consent_user@test'})
_ok('200', s == 200)

# 콘솔 출력에서 코드 직접 가져오는 게 깔끔하지 않으니 DB 에서 조회
db = _patched_get_db()
code_row = db.execute(
    "SELECT code FROM email_codes WHERE email='consent_user@test' ORDER BY id DESC LIMIT 1"
).fetchone()
db.close()
verify_code = code_row['code'] if code_row else None
_ok(f'DB 에 인증 코드 저장됨: {verify_code}', verify_code is not None)


print('\n[5] consents 누락 시 register 거부 (400)')
s, j = _post('/api/auth/register', {
    'email': 'consent_user@test',
    'code':  verify_code,
    'password': 'StrongPw1!',
    # consents 없음
})
_ok(f'400 + 메시지에 필수 항목 (got {s})', s == 400)
_ok('필수 항목 안내', '필수 동의' in (j.get('message') or ''))


print('\n[6] 필수 항목만 accepted=true 로 register → 200')
s, j = _post('/api/auth/register', {
    'email': 'consent_user@test',
    'code':  verify_code,
    'password': 'StrongPw1!',
    'consents': [
        {'kind': 'age14',   'version': '2026-05-05', 'accepted': True},
        {'kind': 'terms',   'version': '2026-05-05', 'accepted': True},
        {'kind': 'privacy', 'version': '2026-05-05', 'accepted': True},
        {'kind': 'location','version': '2026-05-05', 'accepted': True},
        {'kind': 'marketing','version': '2026-05-05', 'accepted': False},  # 선택, 거부 가능
    ],
})
_ok(f'200 + 토큰 (status={s})', s == 200, j)
_ok('access_token 존재', isinstance(j.get('access_token'), str))


print('\n[7] consents 테이블에 기록됐는지')
db = _patched_get_db()
rows = db.execute(
    "SELECT kind, accepted FROM consents WHERE sub_type='user' ORDER BY id"
).fetchall()
db.close()
kinds = {r['kind']: r['accepted'] for r in rows}
_ok(f'5건 저장 (got {len(rows)})', len(rows) == 5)
_ok('age14 accepted=1', kinds.get('age14') == 1)
_ok('marketing accepted=0', kinds.get('marketing') == 0)


print('\n[8] 사장 가입 — terms/privacy 누락 시 400')
# 사장 가입은 사업자번호 등 추가 필드 + 다른 send-code endpoint 사용.
# 간단하게: 동의 누락 시나리오만 검증 (다른 필드 채워서).
s, j = _post('/api/facility/send-code', {'email': 'consent_facility@test'})
_ok('send-code 200', s == 200)

db = _patched_get_db()
fac_code = db.execute(
    "SELECT code FROM email_codes WHERE email='consent_facility@test' ORDER BY id DESC LIMIT 1"
).fetchone()
db.close()
fcode = fac_code['code']

s, j = _post('/api/facility/register', {
    'email': 'consent_facility@test',
    'code':  fcode,
    'password': 'StrongPw1!',
    'company_name':  '테스트 매장',
    'business_no':   '123-45-67890',
    'manager_name':  '홍길동',
    'manager_phone': '010-1234-5678',
    'manager_email': 'mgr@test.com',
    # consents 없음
})
_ok(f'400 (got {s})', s == 400)
_ok('필수 동의 메시지', '필수 동의' in (j.get('message') or ''), j)


print('\n✅ 모든 시나리오 통과')
