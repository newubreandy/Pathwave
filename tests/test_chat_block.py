"""출시 심사 HIGH #1 — 채팅 차단(block) 테스트.

Apple App Store Guideline 1.2 (UGC 모더레이션):
손님이 매장을 차단하면 양쪽 채팅방 목록에서 숨겨지고 메시지 전송이 막힌다.
차단 해지(unblock) 시 원복.

검증:
- POST /api/blocks            차단 생성 (멱등)
- GET  /api/blocks            내 차단 목록
- DELETE /api/blocks/<fid>    차단 해지 (멱등)
- 차단 시 방 목록에서 양쪽 숨김 / 메시지 전송 403
- 인증 가드 (비인증 401, facility 토큰 거부)
- 없는 매장 차단 → 404
"""
import os
import json
import sqlite3
import tempfile

import bcrypt

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name

import models.database as _dbmod
def _patched_get_db():
    conn = sqlite3.connect(os.environ['PATHWAVE_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn
_dbmod.get_db = _patched_get_db

from app import app  # noqa: E402
from routes.auth import make_jwt  # noqa: E402

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
    r = c.post(path, data=json.dumps(data or {}), headers=h)
    return r.status_code, r.get_json()


def _get(path, token=None):
    h = {}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.get(path, headers=h)
    return r.status_code, r.get_json()


def _delete(path, token=None):
    h = {}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.delete(path, headers=h)
    return r.status_code, r.get_json()


# ── 0. 시드: 사용자 + 매장(facility_account + facility) ──────────────────────
print('\n[0] 사용자 / 매장 시드')
db = _patched_get_db()
hashed = bcrypt.hashpw(b'pw', bcrypt.gensalt()).decode()
cur = db.execute("INSERT INTO users (email, password) VALUES (?,?)",
                 ('blocker@test.com', hashed))
user_id = cur.lastrowid
cur = db.execute(
    """INSERT INTO facility_accounts
         (business_no, company_name, email, password,
          manager_name, manager_phone, manager_email, verified, status)
       VALUES ('111-22-33333','Test Store','owner@test.com', ?,
               'Owner','010-0000-0000','owner@test.com', 1, 'verified')""",
    (hashed,))
owner_account_id = cur.lastrowid
cur = db.execute(
    "INSERT INTO facilities (name, owner_id, active) VALUES ('테스트 매장', ?, 1)",
    (owner_account_id,))
facility_id = cur.lastrowid
db.commit(); db.close()

user_token     = make_jwt(user_id,          'blocker@test.com', sub_type='user')
facility_token = make_jwt(owner_account_id, 'owner@test.com',   sub_type='facility')
_ok('user_id 발급', user_id > 0)
_ok('facility_id 발급', facility_id > 0)


# ── 1. 채팅방 생성 + 메시지 전송 정상 ────────────────────────────────────────
print('\n[1] 채팅방 개설 + 메시지 전송 (차단 전)')
sc, body = _post(f'/api/facilities/{facility_id}/chat/rooms', token=user_token)
_ok('openRoom → 201', sc == 201 and body.get('success'), body)
room_id = body['room']['id']

sc, body = _post(f'/api/chat/rooms/{room_id}/messages',
                 {'body': '안녕하세요'}, token=user_token)
_ok('user 메시지 전송 → 201', sc == 201, body)

sc, body = _get('/api/chat/rooms', token=user_token)
_ok('user 방 목록에 방 보임', sc == 200 and len(body['rooms']) == 1, body)
sc, body = _get('/api/chat/rooms', token=facility_token)
_ok('facility 방 목록에 방 보임', sc == 200 and len(body['rooms']) == 1, body)


# ── 2. 차단 생성 ─────────────────────────────────────────────────────────────
print('\n[2] 매장 차단')
sc, body = _post('/api/blocks', {'facility_id': facility_id}, token=user_token)
_ok('POST /api/blocks → 201', sc == 201 and body.get('success'), body)

# 멱등 — 두 번 차단해도 OK
sc, body = _post('/api/blocks', {'facility_id': facility_id}, token=user_token)
_ok('중복 차단 멱등 → 201', sc == 201 and body.get('success'), body)


# ── 3. 차단 후 방 목록에서 양쪽 숨김 ─────────────────────────────────────────
print('\n[3] 차단 후 방 숨김 (양쪽)')
sc, body = _get('/api/chat/rooms', token=user_token)
_ok('user 방 목록에서 숨김', sc == 200 and len(body['rooms']) == 0, body)
sc, body = _get('/api/chat/rooms', token=facility_token)
_ok('facility 방 목록에서 숨김', sc == 200 and len(body['rooms']) == 0, body)


# ── 4. 차단 후 메시지 전송 차단 (양쪽 403) ──────────────────────────────────
print('\n[4] 차단 후 메시지 전송 차단')
sc, body = _post(f'/api/chat/rooms/{room_id}/messages',
                 {'body': '보내기 시도'}, token=user_token)
_ok('user 메시지 전송 → 403', sc == 403, body)
sc, body = _post(f'/api/chat/rooms/{room_id}/messages',
                 {'body': '매장 응답 시도'}, token=facility_token)
_ok('facility 메시지 전송 → 403', sc == 403, body)


# ── 5. 차단 목록 조회 ────────────────────────────────────────────────────────
print('\n[5] 차단 목록 조회')
sc, body = _get('/api/blocks', token=user_token)
_ok('GET /api/blocks → 200, 1건', sc == 200 and len(body['blocks']) == 1, body)
_ok('차단 항목에 매장명 포함',
    body['blocks'][0]['facility_name'] == '테스트 매장', body)
_ok('차단 항목에 facility_id 포함',
    body['blocks'][0]['facility_id'] == facility_id, body)


# ── 6. 차단 해지 + 원복 ──────────────────────────────────────────────────────
print('\n[6] 차단 해지 후 원복')
sc, body = _delete(f'/api/blocks/{facility_id}', token=user_token)
_ok('DELETE /api/blocks/<fid> → 200', sc == 200 and body.get('success'), body)

sc, body = _get('/api/chat/rooms', token=user_token)
_ok('해지 후 user 방 다시 보임', sc == 200 and len(body['rooms']) == 1, body)
sc, body = _post(f'/api/chat/rooms/{room_id}/messages',
                 {'body': '해지 후 전송'}, token=user_token)
_ok('해지 후 메시지 전송 → 201', sc == 201, body)

# 멱등 — 차단 안 된 상태에서 해지해도 OK
sc, body = _delete(f'/api/blocks/{facility_id}', token=user_token)
_ok('미차단 상태 해지 멱등 → 200', sc == 200 and body.get('success'), body)


# ── 7. 인증 가드 ─────────────────────────────────────────────────────────────
print('\n[7] 인증 가드')
sc, _ = _post('/api/blocks', {'facility_id': facility_id})
_ok('비인증 POST → 401', sc == 401)
sc, _ = _get('/api/blocks')
_ok('비인증 GET → 401', sc == 401)
sc, _ = _post('/api/blocks', {'facility_id': facility_id}, token=facility_token)
_ok('facility 토큰 POST 거부 → 401', sc == 401)


# ── 8. 잘못된 입력 ───────────────────────────────────────────────────────────
print('\n[8] 잘못된 입력')
sc, _ = _post('/api/blocks', {}, token=user_token)
_ok('facility_id 누락 → 400', sc == 400)
sc, _ = _post('/api/blocks', {'facility_id': 999999}, token=user_token)
_ok('없는 매장 차단 → 404', sc == 404)


print('\n✅ 채팅 차단(block) 테스트 통과')
