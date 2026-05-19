"""앱 버전 강제 업데이트 테스트."""
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


def _put(path, data, token=None):
    h = {'Content-Type': 'application/json'}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.put(path, data=json.dumps(data), headers=h)
    return r.status_code, r.get_json()


def _get(path, token=None):
    h = {}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.get(path, headers=h)
    return r.status_code, r.get_json()


# ── 0. 슈퍼어드민 로그인 ────────────────────────────────────────────────────
print('\n[0] 슈퍼어드민 로그인')
sc, body = _post('/api/admin/login',
                 {'email': 'admin@pathwave.test', 'password': 'AdminPass1!'})
_ok('admin login → 200', sc == 200 and body.get('success'), body)
admin_token = body['access_token']


# ── 1. 미등록 platform — 영향 없음 ─────────────────────────────────────────
print('\n[1] 미등록 platform = force/recommend 둘 다 False')
sc, body = _get('/api/version/check?platform=ios&current=1.0.0')
_ok('check ios → 200', sc == 200)
_ok('미등록 시 force_update=False', body['force_update'] is False, body)
_ok('미등록 시 recommend_update=False', body['recommend_update'] is False, body)


# ── 2. 슈퍼어드민이 ios 버전 등록 ──────────────────────────────────────────
print('\n[2] 슈퍼어드민이 ios 버전 등록')
sc, body = _put('/api/admin/app-versions/ios', {
    'min_supported': '1.0.0',
    'latest':        '1.2.0',
    'store_url':     'https://apps.apple.com/app/id000',
    'force_message': '보안 패치 적용을 위해 업데이트가 필요합니다.',
}, token=admin_token)
_ok('PUT ios → 200', sc == 200 and body.get('success'), body)


# ── 3. 케이스별 분류 ───────────────────────────────────────────────────────
print('\n[3] 버전별 응답 분류')
cases = [
    ('0.9.0', True,  False, '구버전 = 강제 업데이트'),
    ('1.0.0', False, True,  'min 과 동일 = 강제 X, 권장 O'),
    ('1.1.0', False, True,  'latest 미만 = 권장 업데이트'),
    ('1.2.0', False, False, 'latest 와 동일 = 안내 없음'),
    ('2.0.0', False, False, '최신보다 신버전 = 안내 없음'),
]
for current, expect_force, expect_rec, label in cases:
    sc, body = _get(f'/api/version/check?platform=ios&current={current}')
    cond = (sc == 200
            and body['force_update'] is expect_force
            and body['recommend_update'] is expect_rec)
    _ok(f'current={current} → {label}', cond, body)


# ── 4. 잘못된 입력 ─────────────────────────────────────────────────────────
print('\n[4] 잘못된 입력은 400')
sc, _ = _get('/api/version/check?platform=windows&current=1.0.0')
_ok('platform=windows → 400', sc == 400)
sc, _ = _get('/api/version/check?platform=ios')
_ok('current 누락 → 400', sc == 400)


# ── 5. min > latest 거부 ───────────────────────────────────────────────────
print('\n[5] min_supported > latest 는 400')
sc, _ = _put('/api/admin/app-versions/android', {
    'min_supported': '2.0.0',
    'latest':        '1.0.0',
}, token=admin_token)
_ok('min > latest → 400', sc == 400)


# ── 6. 권한 가드 ───────────────────────────────────────────────────────────
print('\n[6] 인증 없이 admin 엔드포인트는 401')
sc, _ = _put('/api/admin/app-versions/ios',
             {'min_supported': '1.0.0', 'latest': '1.0.0'})
_ok('PUT 비인증 → 401', sc == 401)
sc, _ = _get('/api/admin/app-versions')
_ok('GET 비인증 → 401', sc == 401)


# ── 7. 어드민 list ─────────────────────────────────────────────────────────
print('\n[7] 어드민 list')
sc, body = _get('/api/admin/app-versions', token=admin_token)
_ok('GET list → 200', sc == 200 and body.get('success'))
_ok('ios 1건 존재', any(v['platform'] == 'ios' for v in body['versions']), body)


print('\n✅ 앱 버전 강제 업데이트 테스트 통과')
