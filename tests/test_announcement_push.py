"""PR #38 — 시스템 공지 작성 시 send_push=true 통합 테스트.

audience='all' / 'users' 일 때 실제 push_to_users 가 호출되어 stub provider 가
누적 로그에 기록하는지 + audience='facilities' 시 skipped 가 보고되는지 확인.
"""
import os
import json
import sqlite3
import tempfile

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name
os.environ['BOOTSTRAP_SUPER_ADMIN_EMAIL']    = 'admin@push.test'
os.environ['BOOTSTRAP_SUPER_ADMIN_PASSWORD'] = 'AdminPass1!'
os.environ['PUSH_PROVIDER'] = 'stub'

import models.database as _dbmod  # noqa: E402
def _patched_get_db():
    conn = sqlite3.connect(os.environ['PATHWAVE_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn
_dbmod.get_db = _patched_get_db

from app import app  # noqa: E402
import models.push as _push_mod  # noqa: E402

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


# ── [1] super admin 로그인 ───────────────────────────────────────────────
print('\n[1] super admin 로그인')
s, j = _post('/api/admin/login',
             {'email': 'admin@push.test', 'password': 'AdminPass1!'})
_ok('login → 200', s == 200, j)
admin_token = j['access_token']


# ── [2] 사용자 2명 + 토큰 등록 (push 대상) ────────────────────────────────
print('\n[2] 사용자 2명 생성 + 푸시 토큰 등록')
db = _patched_get_db()
db.execute("INSERT INTO users (email, password) VALUES (?,?)",
           ('u1@push.test', 'irrelevant'))
db.execute("INSERT INTO users (email, password) VALUES (?,?)",
           ('u2@push.test', 'irrelevant'))
uids = [r['id'] for r in db.execute("SELECT id FROM users").fetchall()]
db.execute("INSERT INTO push_tokens (user_id, token, platform) VALUES (?,?,?)",
           (uids[0], 'tok-u1-aaaaaa', 'fcm'))
db.execute("INSERT INTO push_tokens (user_id, token, platform) VALUES (?,?,?)",
           (uids[1], 'tok-u2-bbbbbb', 'fcm'))
db.commit(); db.close()
_ok(f'사용자 {len(uids)}명 + 토큰 2개', len(uids) == 2)


# ── [3] audience='users' + send_push=true → push 발송 확인 ─────────────────
print("\n[3] audience='users' + send_push=true → push_to_users 호출")
_push_mod.StubPushProvider.sent_log.clear()
s, j = _post('/api/admin/announcements', {
    'title':     '🔔 점검 공지',
    'body':      '오늘 23시 점검입니다.',
    'audience':  'users',
    'send_push': True,
}, token=admin_token)
_ok('create → 201', s == 201, j)
pr = j.get('push_result') or {}
_ok(f"push_result.sent == 2 (실제 stub 호출 건수)", pr.get('sent') == 2, pr)
_ok(f"stub log에 2건 누적 (총 {len(_push_mod.StubPushProvider.sent_log)})",
    len(_push_mod.StubPushProvider.sent_log) == 2)
first = _push_mod.StubPushProvider.sent_log[0]
_ok(f"stub log[0].title == '🔔 점검 공지'",
    first['title'] == '🔔 점검 공지', first)


# ── [4] audience='all' + send_push=true → 동일하게 발송 ───────────────────
print("\n[4] audience='all' + send_push=true → users 전수 발송")
_push_mod.StubPushProvider.sent_log.clear()
s, j = _post('/api/admin/announcements', {
    'title':     '⏰ 정기 안내',
    'body':      '주요 변경사항 안내드립니다.',
    'audience':  'all',
    'send_push': True,
}, token=admin_token)
_ok('create → 201', s == 201, j)
pr = j.get('push_result') or {}
_ok(f"push_result.sent == 2", pr.get('sent') == 2, pr)


# ── [5] audience='facilities' + send_push=true → skipped 보고 ─────────────
print("\n[5] audience='facilities' + send_push=true → skipped (token table 없음)")
_push_mod.StubPushProvider.sent_log.clear()
s, j = _post('/api/admin/announcements', {
    'title':     '사장님 공지',
    'body':      '사장 대상 안내',
    'audience':  'facilities',
    'send_push': True,
}, token=admin_token)
_ok('create → 201', s == 201, j)
pr = j.get('push_result') or {}
_ok(f"push_result.skipped 표시 (audience=facilities_no_token_table)",
    'skipped' in pr, pr)
_ok('실 stub 호출 0건', len(_push_mod.StubPushProvider.sent_log) == 0)


# ── [6] send_push=false → push_result 없음 ────────────────────────────────
print('\n[6] send_push 미설정 시 push_result 미포함')
s, j = _post('/api/admin/announcements', {
    'title':     '조용한 공지',
    'body':      '푸시 없이 인박스만',
    'audience':  'users',
}, token=admin_token)
_ok('create → 201', s == 201, j)
_ok('push_result 키 없음', 'push_result' not in j, j)


# ── [7] 작성된 공지 4개 모두 목록에 ─────────────────────────────────────────
print('\n[7] 공지 목록 조회')
r = c.get('/api/admin/announcements',
          headers={'Authorization': f'Bearer {admin_token}'})
js = r.get_json()
_ok(f"총 4개 (생성한 만큼)", js['count'] == 4, js)


print('\n✅ 모든 시나리오 통과')
