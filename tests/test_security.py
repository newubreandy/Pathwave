"""PR #35 — 보안 블로커 (SECRET_KEY/AES_KEY ENV 강제 + CORS + rate-limit) 통합 테스트."""
import os
import json
import sys
import sqlite3
import tempfile
import importlib

# 임시 DB
tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name

import models.database as _dbmod  # noqa: E402
def _patched_get_db():
    conn = sqlite3.connect(os.environ['PATHWAVE_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn
_dbmod.get_db = _patched_get_db


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


# ── [1] 운영 ENV 검증 ────────────────────────────────────────────────────────
print('\n[1] PATHWAVE_ENV=production 일 때 SECRET_KEY 누락 → RuntimeError')
os.environ['PATHWAVE_ENV'] = 'production'
os.environ.pop('SECRET_KEY', None)
os.environ.pop('PATHWAVE_AES_KEY', None)
os.environ.pop('CORS_ORIGINS', None)

# app 모듈을 새로 로드해서 _validate_production_env 가 발동하도록
sys.modules.pop('app', None)
err = None
try:
    import app  # noqa: F401
except RuntimeError as e:
    err = str(e)
_ok('SECRET_KEY 누락 → RuntimeError 발생', err and 'SECRET_KEY' in err, err)

print('\n[2] SECRET_KEY 만 주고 AES_KEY 누락 → RuntimeError')
os.environ['SECRET_KEY'] = 'real-strong-secret-32bytes-AAAAA'
sys.modules.pop('app', None)
err = None
try:
    import app  # noqa: F401
except RuntimeError as e:
    err = str(e)
_ok('PATHWAVE_AES_KEY 누락 → RuntimeError 발생', err and 'PATHWAVE_AES_KEY' in err, err)

print('\n[3] AES_KEY 까지 주고 CORS_ORIGINS 누락 → RuntimeError')
os.environ['PATHWAVE_AES_KEY'] = 'YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU='  # 32B base64
sys.modules.pop('app', None)
err = None
try:
    import app  # noqa: F401
except RuntimeError as e:
    err = str(e)
_ok('CORS_ORIGINS 누락 → RuntimeError 발생', err and 'CORS_ORIGINS' in err, err)

print('\n[4] dev 기본 SECRET_KEY 사용 → RuntimeError')
os.environ['SECRET_KEY'] = 'pathwave-super-secret-key-2024'
os.environ['CORS_ORIGINS'] = 'https://app.pathwave.kr'
sys.modules.pop('app', None)
err = None
try:
    import app  # noqa: F401
except RuntimeError as e:
    err = str(e)
_ok('dev 기본 SECRET_KEY 사용 → RuntimeError', err and 'SECRET_KEY' in err, err)

print('\n[5] 모든 ENV 정상 + production → 부팅 성공')
os.environ['SECRET_KEY'] = 'real-strong-secret-32bytes-AAAAA'
os.environ['CORS_ORIGINS'] = 'https://app.pathwave.kr,https://admin.pathwave.kr'
sys.modules.pop('app', None)
import app as _app_prod  # noqa: F401
_ok('production 정상 부팅', True)

# dev 모드로 돌려서 rate-limit 테스트
print('\n[6] PATHWAVE_ENV=development → 부팅 통과 (ENV 검증 스킵)')
os.environ['PATHWAVE_ENV'] = 'development'
os.environ.pop('SECRET_KEY', None)
os.environ.pop('PATHWAVE_AES_KEY', None)
os.environ.pop('CORS_ORIGINS', None)
sys.modules.pop('app', None)
import app as _app_dev  # noqa: F401
_ok('development 정상 부팅 (ENV 없어도 통과)', True)


# ── [7] Rate-limit 동작 확인 ─────────────────────────────────────────────────
print('\n[7] /api/auth/send-code rate-limit (5/분)')
c = _app_dev.app.test_client()
codes = []
for i in range(7):
    r = c.post('/api/auth/send-code',
               data=json.dumps({'email': f'x{i}@test.kr'}),
               headers={'Content-Type': 'application/json'})
    codes.append(r.status_code)
# 처음 5번은 200/400 등 정상 처리, 6번째부터는 429
n429 = sum(1 for s in codes if s == 429)
_ok(f'5 요청 초과 시 429 발생 (총 {len(codes)}회 중 429={n429}회)', n429 >= 1, codes)


# ── [8] CORS 화이트리스트 모드 ───────────────────────────────────────────────
print('\n[8] CORS_ORIGINS 설정 시 화이트리스트 적용')
os.environ['CORS_ORIGINS'] = 'https://allowed.pathwave.kr'
sys.modules.pop('app', None)
import app as _app_cors  # noqa: F401
c2 = _app_cors.app.test_client()
# preflight: allowed origin
r_ok = c2.options('/api/auth/login',
                   headers={'Origin': 'https://allowed.pathwave.kr',
                            'Access-Control-Request-Method': 'POST'})
allow_hdr_ok = r_ok.headers.get('Access-Control-Allow-Origin', '')
_ok(f'화이트리스트 origin 허용 (header={allow_hdr_ok!r})',
    allow_hdr_ok == 'https://allowed.pathwave.kr', dict(r_ok.headers))

# preflight: not in whitelist
r_ng = c2.options('/api/auth/login',
                   headers={'Origin': 'https://evil.example.com',
                            'Access-Control-Request-Method': 'POST'})
allow_hdr_ng = r_ng.headers.get('Access-Control-Allow-Origin', '')
_ok(f'미허용 origin 차단 (header={allow_hdr_ng!r})',
    allow_hdr_ng == '', dict(r_ng.headers))


print('\n✅ 모든 시나리오 통과')
