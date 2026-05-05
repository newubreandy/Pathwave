"""PR #63 — POST /api/auth/change-password 테스트.

시나리오:
1. 가입 + 로그인
2. 인증 없이 호출 → 401
3. 현재 비번 누락 → 400
4. 잘못된 현재 비번 → 401
5. 새 비번 == 현재 비번 → 400
6. 약한 새 비번 → 400
7. 정상 변경 → 200, 새 비번으로 로그인 가능
8. 옛 비번으로 로그인 → 실패
"""
import os, json, sqlite3, tempfile, sys
from datetime import datetime, timedelta

# 임시 DB
tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name
os.environ['PATHWAVE_AES_KEY'] = 'YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU='

import models.database as _dbmod  # noqa: E402
def _patched_get_db():
    c = sqlite3.connect(os.environ['PATHWAVE_DB'])
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c
_dbmod.get_db = _patched_get_db

sys.modules.pop('app', None)
from app import app  # noqa: E402
from models.rate_limit import limiter as _limiter  # noqa: E402

# 테스트 간 rate-limit 초기화 (5/min 등으로 시나리오 7~8 도달 못 하는 문제 방지)
_limiter.enabled = False

c = app.test_client()


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


# ── [1] 가입 + 로그인 ────────────────────────────────────────────────────
print('\n[1] 가입 + 로그인')
db = _patched_get_db()
db.execute(
    "INSERT INTO email_codes (email, code, expires_at) VALUES (?,?,?)",
    ('chpw@test.kr', '111111',
     (datetime.utcnow() + timedelta(minutes=5)).isoformat())
)
db.commit()
db.close()

r = c.post('/api/auth/register', json={
    'email': 'chpw@test.kr', 'code': '111111', 'password': 'OldPass1!',
    'birth_year': 1990,
    'consents': [
        {'kind': k, 'version': '1.0.0', 'accepted': True}
        for k in ['age14','terms','privacy','location','camera','storage','push','third_party']
    ],
})
data = r.get_json() or {}
token = data.get('token')
_ok('가입 → 200 + token', r.status_code == 200 and token, data)


# ── [2] 인증 없이 호출 → 401 ─────────────────────────────────────────────
print('\n[2] 인증 없이 → 401')
r = c.post('/api/auth/change-password', json={
    'current_password': 'OldPass1!', 'new_password': 'NewPass1!',
})
_ok(f'401 (got {r.status_code})', r.status_code == 401)


# ── [3] 현재 비번 누락 → 400 ─────────────────────────────────────────────
print('\n[3] 현재 비번 누락 → 400')
r = c.post('/api/auth/change-password',
           json={'new_password': 'NewPass1!'},
           headers={'Authorization': f'Bearer {token}'})
_ok(f'400 (got {r.status_code})', r.status_code == 400)


# ── [4] 잘못된 현재 비번 → 401 ───────────────────────────────────────────
print('\n[4] 잘못된 현재 비번 → 401')
r = c.post('/api/auth/change-password',
           json={'current_password': 'WrongPw1!', 'new_password': 'NewPass1!'},
           headers={'Authorization': f'Bearer {token}'})
_ok(f'401 (got {r.status_code})', r.status_code == 401)


# ── [5] 새 비번 == 현재 비번 → 400 ───────────────────────────────────────
print('\n[5] 새 비번 == 현재 비번 → 400')
r = c.post('/api/auth/change-password',
           json={'current_password': 'OldPass1!', 'new_password': 'OldPass1!'},
           headers={'Authorization': f'Bearer {token}'})
_ok(f'400 (got {r.status_code})', r.status_code == 400)


# ── [6] 약한 새 비번 → 400 ───────────────────────────────────────────────
print('\n[6] 약한 새 비번 (4자) → 400')
r = c.post('/api/auth/change-password',
           json={'current_password': 'OldPass1!', 'new_password': 'abc1'},
           headers={'Authorization': f'Bearer {token}'})
_ok(f'400 (got {r.status_code})', r.status_code == 400)


# ── [7] 정상 변경 → 200 ──────────────────────────────────────────────────
print('\n[7] 정상 변경 → 200')
r = c.post('/api/auth/change-password',
           json={'current_password': 'OldPass1!', 'new_password': 'NewPass2!'},
           headers={'Authorization': f'Bearer {token}'})
data = r.get_json() or {}
_ok(f'200 (got {r.status_code})', r.status_code == 200, data)
_ok('성공 메시지', data.get('success') is True, data)


# ── [8] 새 비번으로 로그인 OK / 옛 비번 실패 ─────────────────────────────
print('\n[8] 새 비번으로 로그인 / 옛 비번 거부')
r = c.post('/api/auth/login', json={'email': 'chpw@test.kr', 'password': 'NewPass2!'})
_ok(f'새 비번 로그인 → 200 (got {r.status_code})', r.status_code == 200)

r = c.post('/api/auth/login', json={'email': 'chpw@test.kr', 'password': 'OldPass1!'})
_ok(f'옛 비번 로그인 → 401 (got {r.status_code})', r.status_code == 401)


print('\n✅ 모든 시나리오 통과')

os.unlink(tmp.name)
