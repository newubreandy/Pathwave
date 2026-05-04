"""PR #29 — 초대 코드 통합 테스트.

시나리오:
1. 회원가입 (사장님) → 매장 발급 초대 코드 생성
2. 신규 회원이 그 코드로 가입 (이메일 인증 + 초대 코드)
3. 가입 완료 시 초대 코드 accepted 마킹 확인
4. 같은 코드 재사용 → 거부
5. 회원-회원 초대 흐름 (회원이 다른 사람 초대)
6. INVITATION_REQUIRED=1 환경에서 코드 없이 가입 → 403

실행:
    cd /Users/m5pro16/Desktop/pathwave
    ./venv/bin/python tests/test_invitations.py
"""
import os
import sys
import json
import sqlite3
import tempfile
import pathlib

# 임시 DB로 격리 실행
tmp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
tmp_db.close()
os.environ['PATHWAVE_DB']         = tmp_db.name
os.environ['INVITATION_REQUIRED'] = '1'   # 이번 테스트는 폐쇄형 강제
os.environ['JWT_SECRET']          = 'test-secret'

# DB path 환경변수가 있으면 그쪽 쓰도록 database.py를 살짝 우회
import models.database as _db_mod
_orig_get_db = _db_mod.get_db
def _patched_get_db():
    conn = sqlite3.connect(os.environ['PATHWAVE_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn
_db_mod.get_db = _patched_get_db

from app import app   # noqa: E402

client = app.test_client()


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


def _post(path, data, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    resp = client.post(path, data=json.dumps(data), headers=headers)
    return resp.status_code, resp.get_json()


def _get(path, token=None):
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    resp = client.get(path, headers=headers)
    return resp.status_code, resp.get_json()


# ── 시나리오 1: 사장 가입 (참고용 — 매장 발급 코드 시연) ─────────────────────
print('\n[1] 사장 회원가입 + 승인 (운영자가 1명 부트스트랩되어 있다고 가정)')

# 이메일 인증
sc, body = _post('/api/facility/send-code', {'email': 'owner@test.com'})
_ok(f'/api/facility/send-code → {sc}', sc == 200)

# 코드 가져오기 (DB 직접)
db = _patched_get_db()
code = db.execute(
    "SELECT code FROM email_codes WHERE email='owner@test.com' ORDER BY id DESC LIMIT 1"
).fetchone()['code']
db.close()

sc, body = _post('/api/facility/register', {
    'email': 'owner@test.com',
    'code': code,
    'password': 'Owner123!',
    'company_name': '테스트마켓',
    'business_no': '111-22-33333',
    'manager_name': '홍사장',
    'manager_phone': '010-0000-0000',
    'manager_email': 'manager@test.com',
})
_ok(f'/api/facility/register → 201 (pending)', sc == 201, body)

# 운영자가 승인 (DB 직접)
db = _patched_get_db()
db.execute("UPDATE facility_accounts SET verified=1, status='verified' WHERE email='owner@test.com'")
db.commit(); db.close()

sc, body = _post('/api/facility/login', {'email': 'owner@test.com', 'password': 'Owner123!'})
_ok(f'/api/facility/login → 200', sc == 200 and body.get('success'), body)
owner_token = body['access_token']


# ── 시나리오 2: 사장이 매장 발급 초대 코드 만들기 ─────────────────────────
print('\n[2] 사장이 매장 명의로 초대 코드 발급')
sc, body = _post('/api/invitations',
                 {'channel': 'link', 'invitee_email': 'newuser@test.com'},
                 token=owner_token)
_ok(f'POST /api/invitations → 201', sc == 201 and body.get('success'), body)
shop_invite = body['invitation']['code']
print(f'      발급된 코드: {shop_invite}')


# ── 시나리오 3: 코드 없이 가입 시도 → 403 (INVITATION_REQUIRED=1) ──────────
print('\n[3] 회원 가입 — 초대 코드 없이 시도 → 거부')
_post('/api/auth/send-code', {'email': 'newuser@test.com'})
db = _patched_get_db()
ec = db.execute(
    "SELECT code FROM email_codes WHERE email='newuser@test.com' ORDER BY id DESC LIMIT 1"
).fetchone()['code']
db.close()

sc, body = _post('/api/auth/register', {
    'email': 'newuser@test.com',
    'code': ec,
    'password': 'Newuser1!',
})
_ok(f'코드 없이 register → 403', sc == 403, body)


# ── 시나리오 4: 코드 검증 (가입 페이지에서 사전 호출) ─────────────────────
print('\n[4] 코드 사전 검증')
sc, body = _get(f'/api/invitations/{shop_invite}')
_ok(f'GET /api/invitations/<code> → 200', sc == 200 and body.get('success'), body)
_ok('inviter_label에 매장명 노출', body['invitation']['inviter_label'] == '테스트마켓', body)


# ── 시나리오 5: 코드와 함께 가입 → 성공 ───────────────────────────────────
print('\n[5] 초대 코드와 함께 회원 가입 → 성공')
sc, body = _post('/api/auth/register', {
    'email': 'newuser@test.com',
    'code': ec,
    'password': 'Newuser1!',
    'invitation_code': shop_invite,
})
_ok(f'register with code → 200', sc == 200 and body.get('success'), body)
new_user_token = body['access_token']
new_user_id    = body['user']['id']


# ── 시나리오 6: 같은 코드 재사용 → 거부 ───────────────────────────────────
print('\n[6] 같은 초대 코드로 재가입 시도 → 거부')
_post('/api/auth/send-code', {'email': 'another@test.com'})
db = _patched_get_db()
ec2 = db.execute(
    "SELECT code FROM email_codes WHERE email='another@test.com' ORDER BY id DESC LIMIT 1"
).fetchone()['code']
db.close()

sc, body = _post('/api/auth/register', {
    'email': 'another@test.com',
    'code': ec2,
    'password': 'Another1!',
    'invitation_code': shop_invite,
})
_ok(f'재사용 → 400', sc == 400, body)


# ── 시나리오 7: 가입한 회원이 다른 사람 초대 ───────────────────────────────
print('\n[7] 회원이 본인 명의로 초대 코드 발급')
sc, body = _post('/api/invitations',
                 {'channel': 'kakao', 'invitee_email': 'friend@test.com'},
                 token=new_user_token)
_ok(f'회원 발급 invitation → 201', sc == 201 and body['invitation']['inviter_kind'] == 'user', body)


# ── 시나리오 8: 내 초대 목록 ───────────────────────────────────────────────
print('\n[8] 내 초대 목록 조회')
sc, body = _get('/api/invitations', token=new_user_token)
_ok(f'GET /api/invitations → 200, count=1', sc == 200 and body['count'] == 1, body)


# ── DB 검증 ────────────────────────────────────────────────────────────────
print('\n[9] DB 정합성 확인')
db = _patched_get_db()
row = db.execute("SELECT * FROM invitations WHERE code=?", (shop_invite,)).fetchone()
_ok(f'사용된 코드의 accepted_user_id={new_user_id}', row['accepted_user_id'] == new_user_id, dict(row))
_ok(f'accepted_at NOT NULL', row['accepted_at'] is not None, dict(row))

user_row = db.execute("SELECT invited_via_code FROM users WHERE id=?", (new_user_id,)).fetchone()
_ok(f'users.invited_via_code 기록됨', user_row['invited_via_code'] == shop_invite, dict(user_row))
db.close()


# 정리
os.unlink(tmp_db.name)
print('\n✅ 모든 시나리오 통과')
