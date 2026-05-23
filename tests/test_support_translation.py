"""P8b — 사용자 문의(support) 자동 번역 회귀 테스트.

검증 범위
---------
1) 사용자 송신 ``lang_hint`` → ``support_messages.body_lang`` 저장
2) 운영자 인박스(viewer_lang='ko') 에 외국어 메시지가 한국어로 번역
3) ``support_message_translations`` 캐시 적중
4) 운영자 답변은 ``body_lang='ko'`` 자동 저장
5) 사용자(en) 측에서 운영자 답변이 영어로 번역
6) 추가 메시지 ``lang_hint`` 동작
7) ``lang_hint`` 누락 → 번역 시도 안 함 (비용 안전장치)

stub translator (``[<target>] <원문>``) 로 검증.
"""
import os
import json
import sqlite3
import tempfile

import bcrypt

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB']          = tmp.name
os.environ['TRANSLATION_PROVIDER'] = 'stub'

import models.database as _dbmod
def _patched_get_db():
    conn = sqlite3.connect(os.environ['PATHWAVE_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn
_dbmod.get_db  = _patched_get_db
_dbmod.DB_PATH = tmp.name

from app import app                                  # noqa: E402
from routes.auth import make_jwt                     # noqa: E402

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


# ── 0. 시드: 사용자(en) + super admin ───────────────────────────────────────
print('\n[0] 시드')
db = _patched_get_db()
hashed = bcrypt.hashpw(b'pw', bcrypt.gensalt()).decode()
cur = db.execute(
    "INSERT INTO users (email, password, language) VALUES (?,?,?)",
    ('tourist@test.com', hashed, 'en')
)
user_id = cur.lastrowid
cur = db.execute(
    """INSERT INTO super_admin_accounts (email, password, role, active)
       VALUES ('admin@test.com', ?, 'super', 1)""",
    (hashed,)
)
admin_id = cur.lastrowid
db.commit(); db.close()

user_token  = make_jwt(user_id,  'tourist@test.com', sub_type='user')
admin_token = make_jwt(admin_id, 'admin@test.com',   sub_type='super_admin')


# ── 1. 외국인(en) 사용자 문의 작성 + lang_hint 저장 ─────────────────────────
print('\n[1] 사용자 lang_hint → body_lang 저장')
status, j = _post('/api/support/tickets',
                  {'subject': 'Wifi not working',
                   'body':    'Hi, the wifi is not connecting.',
                   'lang_hint': 'en'},
                  token=user_token)
_ok('201 응답', status == 201, j)
tid = j['ticket']['id']

db = _patched_get_db()
row = db.execute(
    "SELECT body, body_lang FROM support_messages WHERE ticket_id=?",
    (tid,)
).fetchone()
db.close()
_ok("첫 메시지 body_lang == 'en'", row['body_lang'] == 'en', dict(row))


# ── 2. 운영자(viewer_lang='ko') 인박스 — 영어 메시지를 한국어 번역으로 봄 ───
print('\n[2] 운영자 인박스: 외국어 → 한국어 번역')
status, j = _get(f'/api/admin/support/tickets/{tid}', token=admin_token)
_ok('200 응답',                status == 200, j)
_ok("viewer_lang == 'ko'",     j['viewer_lang'] == 'ko', j)
m1 = j['messages'][0]
_ok('translated_text 머지',
    m1.get('translated_text') == '[ko] Hi, the wifi is not connecting.', m1)
_ok("translated_lang == 'ko'", m1.get('translated_lang') == 'ko', m1)


# ── 3. 캐시 적중 — 재요청 시 row 안 늘어남 ─────────────────────────────────
print('\n[3] 캐시 적중')
db = _patched_get_db()
cache_before = db.execute(
    'SELECT COUNT(*) AS n FROM support_message_translations'
).fetchone()['n']
db.close()
_get(f'/api/admin/support/tickets/{tid}', token=admin_token)
_get(f'/api/admin/support/tickets/{tid}', token=admin_token)
db = _patched_get_db()
cache_after = db.execute(
    'SELECT COUNT(*) AS n FROM support_message_translations'
).fetchone()['n']
db.close()
_ok(f'캐시 row before({cache_before}) == after({cache_after})',
    cache_before == cache_after)


# ── 4. 운영자 한국어 답변 — body_lang='ko' 자동 저장 ──────────────────────
print('\n[4] 운영자 답변 body_lang=ko')
status, j = _post(f'/api/admin/support/tickets/{tid}/reply',
                  {'body': '안녕하세요, 매장에 재접속해보시겠어요?'},
                  token=admin_token)
_ok('201 응답', status == 201, j)
db = _patched_get_db()
row = db.execute(
    "SELECT body_lang FROM support_messages "
    "WHERE ticket_id=? AND sender='admin' ORDER BY id DESC LIMIT 1",
    (tid,)
).fetchone()
db.close()
_ok("운영자 답변 body_lang == 'ko'", row['body_lang'] == 'ko', dict(row))


# ── 5. 사용자(en) 측에서 운영자 답변이 영어로 ──────────────────────────────
print('\n[5] 사용자(en) viewer — 운영자 ko 답변이 영어로 번역')
status, j = _get(f'/api/support/tickets/me/{tid}', token=user_token)
_ok("viewer_lang == 'en' (users.language fallback)",
    j['viewer_lang'] == 'en', j)
admin_msg = next(m for m in j['messages'] if m['sender'] == 'admin')
_ok('운영자 ko 답변이 영어로',
    admin_msg.get('translated_text') == '[en] 안녕하세요, 매장에 재접속해보시겠어요?',
    admin_msg)


# ── 6. 사용자 추가 메시지 + lang_hint ──────────────────────────────────────
print('\n[6] 추가 메시지 lang_hint')
status, j = _post(f'/api/support/tickets/me/{tid}/messages',
                  {'body': 'Still not working', 'lang_hint': 'en'},
                  token=user_token)
_ok('201 응답', status == 201, j)
db = _patched_get_db()
row = db.execute(
    "SELECT body_lang FROM support_messages "
    "WHERE ticket_id=? AND body='Still not working'",
    (tid,)
).fetchone()
db.close()
_ok("추가 메시지 body_lang == 'en'", row['body_lang'] == 'en', dict(row))


# ── 7. lang_hint 누락 → body_lang NULL → 번역 시도 안 함 ───────────────────
print('\n[7] lang_hint 누락 → 번역 안 함')
status, j = _post(f'/api/support/tickets/me/{tid}/messages',
                  {'body': 'lang_hint 없음 메시지'},
                  token=user_token)
_ok('201 응답', status == 201, j)

status, j = _get(f'/api/admin/support/tickets/{tid}', token=admin_token)
last_msg = j['messages'][-1]
_ok("body_lang IS NULL",          last_msg['body_lang'] is None, last_msg)
_ok('translated_text 없음',       'translated_text' not in last_msg, last_msg)


print('\n=== P8b 사용자 문의 자동 번역 — 전체 시나리오 PASS ===')
os.unlink(tmp.name)
