"""Phase L — 알림 카테고리별 on/off 테스트.

사용자 + 시설(사장) 각각:
- GET: 카탈로그 전체 (저장 안 된 항목도 기본 enabled=True 로 노출)
- PUT: enabled true/false 토글
- 잘못된 카테고리 / 잘못된 body → 400
- 인증 없음 → 401
- 사용자 카테고리는 시설 엔드포인트에서 거부 (반대도) → 400
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


# ── 0. 사용자 1명 DB 직접 시드 + 토큰 발급 ─────────────────────────────────
print('\n[0] 사용자 / 시설 계정 DB 직접 시드')
db = _patched_get_db()
hashed = bcrypt.hashpw(b'pw', bcrypt.gensalt()).decode()
cur = db.execute(
    "INSERT INTO users (email, password) VALUES (?,?)",
    ('u1@test.com', hashed)
)
user_id = cur.lastrowid
cur = db.execute(
    """INSERT INTO facility_accounts
         (business_no, company_name, email, password,
          manager_name, manager_phone, manager_email,
          verified, status)
       VALUES ('111-22-33333','Test Store','owner@test.com', ?,
               'Owner','010-0000-0000','owner@test.com', 1, 'verified')""",
    (hashed,)
)
facility_id = cur.lastrowid
db.commit(); db.close()
user_token     = make_jwt(user_id,     'u1@test.com',    sub_type='user')
facility_token = make_jwt(facility_id, 'owner@test.com', sub_type='facility')
_ok('user_id 발급', user_id > 0)
_ok('facility_id 발급', facility_id > 0)


# ── 1. 사용자 GET — 카탈로그 4개 모두 기본 enabled=True ─────────────────────
print('\n[1] 사용자 GET — 기본값 (모두 켜짐)')
sc, body = _get('/api/users/me/notification-preferences', token=user_token)
_ok('GET → 200', sc == 200 and body.get('success'), body)
prefs = body['preferences']
_ok('카탈로그 4개 (beacon/coupon/marketing/system)',
    len(prefs) == 4 and {p['category'] for p in prefs} ==
    {'beacon', 'coupon', 'marketing', 'system'}, prefs)
_ok('모두 enabled=True (기본값)',
    all(p['enabled'] is True for p in prefs), prefs)


# ── 2. 사용자 PUT — marketing 끄기 ──────────────────────────────────────────
print('\n[2] 사용자 PUT — marketing off')
sc, body = _put('/api/users/me/notification-preferences/marketing',
                {'enabled': False}, token=user_token)
_ok('PUT marketing=false → 200', sc == 200 and body['enabled'] is False, body)

sc, body = _get('/api/users/me/notification-preferences', token=user_token)
mkt = next(p for p in body['preferences'] if p['category'] == 'marketing')
_ok('GET 후 marketing 만 enabled=False', mkt['enabled'] is False, body)
others = [p for p in body['preferences'] if p['category'] != 'marketing']
_ok('나머지는 그대로 True', all(p['enabled'] for p in others), others)


# ── 3. 사용자 PUT — 다시 켜기 (멱등) ────────────────────────────────────────
print('\n[3] 사용자 PUT — marketing 재활성 (멱등)')
sc, body = _put('/api/users/me/notification-preferences/marketing',
                {'enabled': True}, token=user_token)
_ok('PUT marketing=true → 200', sc == 200 and body['enabled'] is True, body)
sc, body = _get('/api/users/me/notification-preferences', token=user_token)
mkt = next(p for p in body['preferences'] if p['category'] == 'marketing')
_ok('marketing 다시 True', mkt['enabled'] is True, body)


# ── 4. 잘못된 카테고리 / 입력 → 400 ─────────────────────────────────────────
print('\n[4] 잘못된 카테고리 / 입력')
sc, _ = _put('/api/users/me/notification-preferences/unknown',
             {'enabled': True}, token=user_token)
_ok('unknown category → 400', sc == 400)
sc, _ = _put('/api/users/me/notification-preferences/beacon',
             {}, token=user_token)
_ok('enabled 누락 → 400', sc == 400)
sc, _ = _put('/api/users/me/notification-preferences/beacon',
             {'enabled': 'maybe'}, token=user_token)
_ok('enabled 비-boolean → 400', sc == 400)


# ── 5. 인증 가드 ────────────────────────────────────────────────────────────
print('\n[5] 인증 가드')
sc, _ = _get('/api/users/me/notification-preferences')
_ok('GET 비인증 → 401', sc == 401)
sc, _ = _put('/api/users/me/notification-preferences/beacon',
             {'enabled': True})
_ok('PUT 비인증 → 401', sc == 401)


# ── 6. 시설(사장) GET / PUT ────────────────────────────────────────────────
print('\n[6] 시설(사장) GET / PUT')
sc, body = _get('/api/facility/me/notification-preferences', token=facility_token)
_ok('facility GET → 200', sc == 200 and body.get('success'), body)
fac_prefs = body['preferences']
_ok('facility 카탈로그 5개',
    len(fac_prefs) == 5 and
    {p['category'] for p in fac_prefs} ==
    {'customer_visit', 'coupon_used', 'sales_report', 'system', 'billing'},
    fac_prefs)
_ok('facility 모두 기본 True',
    all(p['enabled'] is True for p in fac_prefs), fac_prefs)

sc, body = _put('/api/facility/me/notification-preferences/billing',
                {'enabled': False}, token=facility_token)
_ok('facility billing=false → 200',
    sc == 200 and body['enabled'] is False, body)
sc, body = _get('/api/facility/me/notification-preferences', token=facility_token)
billing = next(p for p in body['preferences'] if p['category'] == 'billing')
_ok('billing 저장 후 False', billing['enabled'] is False, body)


# ── 7. 카테고리 격리 검증 (사용자/시설 카탈로그 분리) ──────────────────────
print('\n[7] 카테고리 격리')
sc, _ = _put('/api/facility/me/notification-preferences/beacon',
             {'enabled': True}, token=facility_token)
_ok('사용자 카테고리는 시설 엔드포인트에서 거부 → 400', sc == 400)
sc, _ = _put('/api/users/me/notification-preferences/billing',
             {'enabled': True}, token=user_token)
_ok('시설 카테고리는 사용자 엔드포인트에서 거부 → 400', sc == 400)


# ── 8. 토큰 종류 가드 (user 토큰으로 facility 엔드포인트 호출 금지) ───────
print('\n[8] 토큰 종류 가드')
sc, _ = _get('/api/facility/me/notification-preferences', token=user_token)
_ok('user 토큰으로 facility GET → 401/403',
    sc in (401, 403))
sc, _ = _get('/api/users/me/notification-preferences', token=facility_token)
_ok('facility 토큰으로 user GET → 401/403',
    sc in (401, 403))


print('\n✅ 알림 카테고리별 on/off 테스트 통과')
