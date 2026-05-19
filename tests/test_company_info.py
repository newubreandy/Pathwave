"""Phase M — 법인 정보 (footer 자동 동기) 테스트."""
import os
import json
import sqlite3
import tempfile

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name
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
    return c.post(path, data=json.dumps(data), headers=h)


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
r = _post('/api/admin/login',
          {'email': 'admin@pathwave.test', 'password': 'AdminPass1!'})
body = r.get_json()
_ok('admin login → 200', r.status_code == 200 and body.get('success'), body)
admin_token = body['access_token']


# ── 1. 최초 GET — 모든 필드 null ───────────────────────────────────────────
print('\n[1] 최초 GET — 모든 필드 null')
sc, body = _get('/api/company-info')
_ok('GET → 200', sc == 200 and body.get('success'), body)
ci = body['company_info']
_EXPECTED_FIELDS = {'company_name', 'ceo', 'biz_number', 'commerce_number',
                    'address', 'phone', 'email', 'hosting', 'updated_at'}
_ok('카탈로그 9 필드 (8 + updated_at)',
    set(ci.keys()) == _EXPECTED_FIELDS, ci)
_ok('값 모두 null', all(ci[k] is None for k in _EXPECTED_FIELDS), ci)


# ── 2. PUT 으로 일부 필드 입력 ─────────────────────────────────────────────
print('\n[2] PUT 으로 일부 필드 입력 (INSERT)')
sc, body = _put('/api/admin/company-info', {
    'company_name':    '주식회사 트리거소프트',
    'ceo':             '홍길동',
    'biz_number':      '123-45-67890',
    'commerce_number': '제2026-서울강남-0001호',
    'address':         '서울특별시 강남구 테헤란로 1',
    'phone':           '02-1234-5678',
    'hosting':         'AWS Korea',
}, token=admin_token)
_ok('PUT → 200', sc == 200 and body.get('success'), body)
ci = body['company_info']
_ok('company_name 저장', ci['company_name'] == '주식회사 트리거소프트', ci)
_ok('biz_number 저장', ci['biz_number'] == '123-45-67890', ci)
_ok('hosting 저장', ci['hosting'] == 'AWS Korea', ci)
_ok('email 미지정 → null', ci['email'] is None, ci)


# ── 3. GET 으로 영속 확인 ──────────────────────────────────────────────────
print('\n[3] GET 으로 영속 확인')
sc, body = _get('/api/company-info')
ci = body['company_info']
_ok('GET 후 ceo=홍길동', ci['ceo'] == '홍길동', ci)


# ── 4. 부분 PUT — UPDATE (덮어쓰기) ────────────────────────────────────────
print('\n[4] 부분 PUT — ceo 만 변경 (UPDATE)')
sc, body = _put('/api/admin/company-info',
                {'ceo': '이몽룡'}, token=admin_token)
_ok('PUT → 200', sc == 200 and body.get('success'), body)
ci = body['company_info']
_ok('ceo 갱신됨', ci['ceo'] == '이몽룡', ci)
_ok('company_name 유지', ci['company_name'] == '주식회사 트리거소프트', ci)
_ok('biz_number 유지', ci['biz_number'] == '123-45-67890', ci)


# ── 5. 빈 문자열 → null 처리 (지움) ─────────────────────────────────────────
print('\n[5] 빈 문자열 → null 처리')
sc, body = _put('/api/admin/company-info',
                {'hosting': ''}, token=admin_token)
_ok('PUT hosting="" → 200', sc == 200)
_ok('hosting → null', body['company_info']['hosting'] is None, body)


# ── 6. 잘못된 입력 ──────────────────────────────────────────────────────────
print('\n[6] 잘못된 입력')
sc, _ = _put('/api/admin/company-info', {}, token=admin_token)
_ok('빈 body → 400', sc == 400)
sc, _ = _put('/api/admin/company-info',
             {'phone': 12345}, token=admin_token)
_ok('phone 정수 → 400', sc == 400)
sc, _ = _put('/api/admin/company-info',
             {'unknown_field': 'x'}, token=admin_token)
_ok('알 수 없는 필드만 있을 때 → 400 (필터링 후 비어짐)', sc == 400)


# ── 7. 인증 가드 ───────────────────────────────────────────────────────────
print('\n[7] 인증 가드')
sc, _ = _put('/api/admin/company-info', {'phone': '01-1234-5678'})
_ok('비인증 PUT → 401', sc == 401)


# ── 8. 단일 행 보장 — 두 번째 INSERT 시도해도 UPDATE 로 처리 ────────────────
print('\n[8] 단일 행 (id=1) 보장')
db = _patched_get_db()
rows = db.execute("SELECT COUNT(*) AS n FROM company_info").fetchone()
db.close()
_ok('row 1건만 존재', rows['n'] == 1, rows)


print('\n✅ 법인 정보 (Phase M) 테스트 통과')
