"""PR #33 — 시스템 공지 통합 테스트."""
import os
import json
import sqlite3
import tempfile

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name
os.environ['JWT_SECRET']  = 'test-secret-key-32-bytes-long-ok'
os.environ['BOOTSTRAP_SUPER_ADMIN_EMAIL']    = 'admin@pathwave.test'
os.environ['BOOTSTRAP_SUPER_ADMIN_PASSWORD'] = 'AdminPass1!'

import models.database as _dbmod
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

def _del(path, token=None):
    h = {}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.delete(path, headers=h)
    return r.status_code, r.get_json()


# ── 0. super admin 로그인 ───────────────────────────────────────────────────
print('\n[0] 부트스트랩 super admin 로그인')
sc, body = _post('/api/admin/login', {'email': 'admin@pathwave.test', 'password': 'AdminPass1!'})
_ok(f'admin login → 200', sc == 200 and body.get('success'), body)
admin_token = body['access_token']


# ── 1. 일반 회원 가입 (audience=users 검증용) ──────────────────────────────
print('\n[1] 일반 회원 1명 가입')
sc, _ = _post('/api/auth/send-code', {'email': 'u1@test.com'})
_ok(f'send-code → 200', sc == 200)
db = _patched_get_db()
ec = db.execute("SELECT code FROM email_codes WHERE email='u1@test.com' ORDER BY id DESC LIMIT 1").fetchone()['code']
db.close()
sc, body = _post('/api/auth/register', {'email': 'u1@test.com', 'code': ec, 'password': 'User123!'})
_ok(f'register → 200', sc == 200 and body.get('success'), body)
user_token = body['access_token']


# ── 2. 사장 가입 + 자동 verify ──────────────────────────────────────────────
print('\n[2] 사장 1명 가입 + 운영자 승인 + 로그인')
_post('/api/facility/send-code', {'email': 'o1@test.com'})
db = _patched_get_db()
ec = db.execute("SELECT code FROM email_codes WHERE email='o1@test.com' ORDER BY id DESC LIMIT 1").fetchone()['code']
db.close()
_post('/api/facility/register', {
    'email': 'o1@test.com', 'code': ec, 'password': 'Owner123!',
    'company_name': 'TestStore', 'business_no': '111-22-33333',
    'manager_name': '홍사장', 'manager_phone': '010', 'manager_email': 'm@t.com',
})
db = _patched_get_db()
db.execute("UPDATE facility_accounts SET verified=1, status='verified' WHERE email='o1@test.com'")
db.commit(); db.close()
sc, body = _post('/api/facility/login', {'email': 'o1@test.com', 'password': 'Owner123!'})
_ok(f'facility login → 200', sc == 200 and body.get('success'), body)
owner_token = body['access_token']


# ── 3. 운영자가 audience=all 공지 작성 ──────────────────────────────────────
print('\n[3] super_admin이 audience=all 공지 작성')
sc, body = _post('/api/admin/announcements',
                 {'title': '서비스 점검 안내', 'body': '5월 9일 새벽 2시~4시 점검'},
                 token=admin_token)
_ok(f'create announcement (audience=all default) → 201', sc == 201 and body['success'], body)
ann_all_id = body['announcement']['id']


# ── 4. audience=users 공지 작성 ────────────────────────────────────────────
print('\n[4] audience=users 한정 공지 작성')
sc, body = _post('/api/admin/announcements',
                 {'title': '회원 전용 이벤트', 'body': '와이파이 초대 이벤트', 'audience': 'users'},
                 token=admin_token)
_ok(f'create users-only → 201', sc == 201, body)
ann_users_id = body['announcement']['id']


# ── 5. audience=facilities 공지 ─────────────────────────────────────────────
print('\n[5] audience=facilities 한정 공지')
sc, body = _post('/api/admin/announcements',
                 {'title': '사장님 공지', 'body': '리포트 기능 업데이트', 'audience': 'facilities', 'pinned': True},
                 token=admin_token)
_ok(f'create facility-only pinned → 201', sc == 201 and body['announcement']['pinned'], body)


# ── 6. 운영자 토큰 없이 작성 시도 → 401 ────────────────────────────────────
print('\n[6] 인증 없이 공지 작성 시도')
sc, body = _post('/api/admin/announcements', {'title': 'x', 'body': 'x'})
_ok(f'no token → 401', sc == 401, body)


# ── 7. 일반 회원이 공지 조회 → all + users 보임, facilities 미노출 ──────────
print('\n[7] 일반 회원 공지 조회 (all + users 보임)')
sc, body = _get('/api/announcements', token=user_token)
_ok(f'GET → 200', sc == 200, body)
ids = [a['id'] for a in body['announcements']]
_ok(f'audience=all 공지 보임', ann_all_id in ids, ids)
_ok(f'audience=users 공지 보임', ann_users_id in ids, ids)
_ok(f'audience=facilities 공지 미노출', all(a['audience'] != 'facilities' for a in body['announcements']), body)


# ── 8. 사장이 공지 조회 → all + facilities 보임 ────────────────────────────
print('\n[8] 사장 공지 조회 (all + facilities 보임)')
sc, body = _get('/api/announcements', token=owner_token)
_ok(f'GET → 200', sc == 200, body)
audiences = [a['audience'] for a in body['announcements']]
_ok(f'all 보임', 'all' in audiences, audiences)
_ok(f'facilities 보임', 'facilities' in audiences, audiences)
_ok(f'users 미노출', 'users' not in audiences, audiences)


# ── 9. 읽음 처리 ───────────────────────────────────────────────────────────
print('\n[9] 회원이 공지 읽음 처리')
sc, body = _post(f'/api/announcements/{ann_all_id}/read', {}, token=user_token)
_ok(f'mark read → 200', sc == 200 and body['success'], body)

sc, body = _get('/api/announcements', token=user_token)
target = next(a for a in body['announcements'] if a['id'] == ann_all_id)
_ok(f'read=True 반영', target['read'] is True, target)


# ── 10. PATCH 수정 ─────────────────────────────────────────────────────────
print('\n[10] 공지 수정')
sc, body = _patch(f'/api/admin/announcements/{ann_all_id}',
                  {'title': '점검 시간 변경'}, token=admin_token)
_ok(f'patch → 200', sc == 200 and body['announcement']['title'] == '점검 시간 변경', body)


# ── 11. 잘못된 audience ────────────────────────────────────────────────────
print('\n[11] 잘못된 audience 거부')
sc, body = _post('/api/admin/announcements',
                 {'title': 'x', 'body': 'x', 'audience': 'aliens'},
                 token=admin_token)
_ok(f'invalid audience → 400', sc == 400, body)


# ── 12. 삭제 ───────────────────────────────────────────────────────────────
print('\n[12] 공지 삭제')
sc, body = _del(f'/api/admin/announcements/{ann_users_id}', token=admin_token)
_ok(f'delete → 200', sc == 200, body)
sc, body = _get('/api/announcements', token=user_token)
ids = [a['id'] for a in body['announcements']]
_ok(f'삭제된 공지 미노출', ann_users_id not in ids, ids)


os.unlink(tmp.name)
print('\n✅ 모든 시나리오 통과')
