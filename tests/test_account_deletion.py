"""PR #55 — 회원 탈퇴 (Apple 5.1.1(v) / Google Play 정책) 통합 테스트."""
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


def _delete(path, data, token=None):
    h = {'Content-Type': 'application/json'}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.delete(path, data=json.dumps(data), headers=h)
    return r.status_code, r.get_json()


def _direct_code(email):
    db = _patched_get_db()
    db.execute(
        """INSERT INTO email_codes (email, code, expires_at, used)
           VALUES (?, '999999', datetime('now', '+5 minutes'), 0)""",
        (email,)
    )
    db.commit(); db.close()
    return '999999'


_USER_CONSENTS = [
    {'kind': 'age14',    'version': 'v', 'accepted': True},
    {'kind': 'terms',    'version': 'v', 'accepted': True},
    {'kind': 'privacy',  'version': 'v', 'accepted': True},
    {'kind': 'location', 'version': 'v', 'accepted': True},
]


# ── [1] 가입 + 푸시 토큰 등록 ─────────────────────────────────────────────
print('\n[1] 사용자 가입 + 푸시 토큰 등록')
code = _direct_code('user@delete.test')
s, j = _post('/api/auth/register', {
    'email': 'user@delete.test', 'code': code, 'password': 'StrongPw1!',
    'birth_year': 1990, 'consents': _USER_CONSENTS,
})
_ok('가입 → 200', s == 200, j)
user_token = j['access_token']
user_id    = j['user']['id']

db = _patched_get_db()
db.execute(
    "INSERT INTO push_tokens (user_id, token, platform) VALUES (?,?,?)",
    (user_id, 'tok-aaaa', 'fcm')
)
db.commit(); db.close()


# ── [2] 인증 없이 탈퇴 시도 → 401 ────────────────────────────────────────
print('\n[2] 인증 없이 DELETE → 401')
s, j = _delete('/api/auth/me', {})
_ok('401', s == 401)


# ── [3] 비밀번호 누락 → 400 ──────────────────────────────────────────────
print('\n[3] 이메일 가입자 — 비밀번호 누락 시 400')
s, j = _delete('/api/auth/me', {}, token=user_token)
_ok(f'400 (got {s})', s == 400, j)
_ok('비밀번호 확인 메시지', '비밀번호' in (j.get('message') or ''))


# ── [4] 잘못된 비밀번호 → 401 ────────────────────────────────────────────
print('\n[4] 잘못된 비밀번호 → 401')
s, j = _delete('/api/auth/me', {'password': 'WrongPassword!'}, token=user_token)
_ok(f'401 (got {s})', s == 401, j)


# ── [5] 정상 탈퇴 → 200 ─────────────────────────────────────────────────
print('\n[5] 올바른 비밀번호 → 탈퇴 성공')
s, j = _delete('/api/auth/me', {'password': 'StrongPw1!'}, token=user_token)
_ok(f'200 (got {s})', s == 200, j)
_ok('성공 메시지', '탈퇴' in (j.get('message') or ''))


# ── [6] DB 상태 검증 — 익명화 + 푸시 토큰 폐기 ────────────────────────────
print('\n[6] DB 상태 — 익명화 / 푸시 토큰 폐기')
db = _patched_get_db()
row = db.execute("SELECT email, deleted_at FROM users WHERE id=?", (user_id,)).fetchone()
_ok(f'deleted_at NOT NULL (got {row["deleted_at"]})', row['deleted_at'] is not None)
_ok(f'email 익명화 (got {row["email"]})',
    row['email'] == f'{user_id}+deleted@deleted.local')

push_count = db.execute(
    "SELECT COUNT(*) AS n FROM push_tokens WHERE user_id=?", (user_id,)
).fetchone()['n']
_ok(f'push_tokens 0건 (got {push_count})', push_count == 0)
db.close()


# ── [7] 이미 탈퇴된 계정 재탈퇴 시도 → 409 ───────────────────────────────
# (단, 토큰이 아직 유효한 짧은 윈도우 — 일반적으로 클라이언트가 토큰 폐기)
print('\n[7] 이미 탈퇴된 계정 재탈퇴 → 404 또는 409')
s, j = _delete('/api/auth/me', {'password': 'StrongPw1!'}, token=user_token)
# 토큰의 user_id 로 조회 → email 익명화 됐지만 row 는 존재 → deleted_at 검증으로 409
_ok(f'409 (got {s})', s == 409, j)


# ── [8] 같은 이메일로 재가입 → 200 (익명화로 UNIQUE 충돌 회피) ──────────
print('\n[8] 같은 이메일 재가입 → 200')
code2 = _direct_code('user@delete.test')
s, j = _post('/api/auth/register', {
    'email': 'user@delete.test', 'code': code2, 'password': 'NewPass2!',
    'birth_year': 1990, 'consents': _USER_CONSENTS,
})
_ok(f'재가입 200 (got {s})', s == 200, j)
new_user_id = j['user']['id']
_ok(f'새 user_id ({new_user_id}) != 옛 user_id ({user_id})',
    new_user_id != user_id)


print('\n✅ 모든 시나리오 통과')
