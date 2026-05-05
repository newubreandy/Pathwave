"""PR #37 — 휴대폰 인증 통합 테스트."""
import os, json, sqlite3, tempfile, time

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB']    = tmp.name
os.environ['JWT_SECRET']     = 'test-secret-key-32-bytes-long-ok'
os.environ['SMS_PROVIDER']   = 'stub'

import models.database as _dbmod
def _patched_get_db():
    conn = sqlite3.connect(os.environ['PATHWAVE_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn
_dbmod.get_db = _patched_get_db

from app import app                                # noqa: E402
from routes.phone import consume_phone_token       # noqa: E402

c = app.test_client()


def _ok(label, cond, payload=None):
    print(f"  {'✓' if cond else '✗'} {label}")
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


def _post(p, d):
    r = c.post(p, data=json.dumps(d), headers={'Content-Type': 'application/json'})
    return r.status_code, r.get_json()


# ── 1. 코드 발송 ──────────────────────────────────────────────────────────
print('\n[1] 휴대폰 인증 코드 발송')
sc, body = _post('/api/phone/send-code', {'phone': '010-1234-5678', 'purpose': 'register'})
_ok(f'send-code → 200', sc == 200 and body.get('success'), body)
_ok('provider=stub', body.get('provider') == 'stub', body)
_ok('expires_in_seconds=300', body.get('expires_in_seconds') == 300, body)


# ── 2. 잘못된 형식 거부 ───────────────────────────────────────────────────
print('\n[2] 잘못된 휴대폰 번호 형식')
sc, _ = _post('/api/phone/send-code', {'phone': '010-1'})
_ok('짧은 번호 → 400', sc == 400)
sc, _ = _post('/api/phone/send-code', {'phone': '02-1234-5678'})
_ok('비-휴대폰 번호 → 400', sc == 400)


# ── 3. 코드 가져와서 검증 ────────────────────────────────────────────────
print('\n[3] 코드 검증 → token 발급')
db = _patched_get_db()
row = db.execute(
    "SELECT code FROM phone_verifications WHERE phone='010-1234-5678' ORDER BY id DESC LIMIT 1"
).fetchone()
db.close()
code = row['code']

sc, body = _post('/api/phone/verify-code', {'phone': '010-1234-5678', 'code': code})
_ok(f'verify-code → 200', sc == 200 and body.get('success'), body)
_ok('token 발급됨', isinstance(body.get('token'), str) and len(body['token']) > 0, body)
token = body['token']


# ── 4. 잘못된 코드 거부 ──────────────────────────────────────────────────
print('\n[4] 잘못된 코드')
_post('/api/phone/send-code', {'phone': '010-2222-3333'})
sc, _ = _post('/api/phone/verify-code', {'phone': '010-2222-3333', 'code': '000000'})
_ok('잘못된 코드 → 400', sc == 400)


# ── 5. 하이픈 없이 입력해도 정규화 ─────────────────────────────────────────
print('\n[5] 하이픈 없는 번호 정규화')
sc, body = _post('/api/phone/send-code', {'phone': '01099998888'})
_ok('정규화 후 발송 성공', sc == 200, body)

db = _patched_get_db()
row = db.execute(
    "SELECT phone, code FROM phone_verifications WHERE phone='010-9999-8888' ORDER BY id DESC LIMIT 1"
).fetchone()
db.close()
_ok('DB에 010-9999-8888로 저장됨', row is not None and row['phone'] == '010-9999-8888', row)


# ── 6. consume_phone_token 헬퍼 ───────────────────────────────────────────
print('\n[6] consume_phone_token 헬퍼 (회원가입 단계 시뮬레이션)')
db = _patched_get_db()
ok1 = consume_phone_token(db, '010-1234-5678', token)
db.commit()
_ok('첫 사용 → True', ok1)

ok2 = consume_phone_token(db, '010-1234-5678', token)
_ok('재사용 → False (used=1)', ok2 is False)

ok3 = consume_phone_token(db, '010-1234-5678', 'wrong-token')
_ok('잘못된 token → False', ok3 is False)
db.close()


# ── 7. 코드 만료 ─────────────────────────────────────────────────────────
print('\n[7] 만료된 코드 거부')
db = _patched_get_db()
db.execute(
    """INSERT INTO phone_verifications (phone, code, expires_at)
       VALUES ('010-7777-7777', '111111', '2020-01-01T00:00:00')"""
)
db.commit(); db.close()
sc, body = _post('/api/phone/verify-code', {'phone': '010-7777-7777', 'code': '111111'})
_ok('만료 코드 → 400', sc == 400, body)


os.unlink(tmp.name)
print('\n✅ 모든 시나리오 통과')
