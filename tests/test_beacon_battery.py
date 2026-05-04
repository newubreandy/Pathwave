"""PR #34 — 비콘 배터리 모니터링 통합 테스트."""
import os, json, sqlite3, tempfile

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name
os.environ['JWT_SECRET']  = 'test-secret-key-32-bytes-long-ok'
os.environ['BOOTSTRAP_SUPER_ADMIN_EMAIL']    = 'admin@pw.test'
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
    print(f"  {'✓' if cond else '✗'} {label}")
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


def _post(p, d, t=None):
    h = {'Content-Type': 'application/json'}
    if t: h['Authorization'] = f'Bearer {t}'
    r = c.post(p, data=json.dumps(d), headers=h)
    return r.status_code, r.get_json()

def _get(p, t=None):
    h = {'Authorization': f'Bearer {t}'} if t else {}
    r = c.get(p, headers=h)
    return r.status_code, r.get_json()


# ── 0. super admin 로그인 ──────────────────────────────────────────────────
print('\n[0] super admin 로그인')
sc, body = _post('/api/admin/login', {'email': 'admin@pw.test', 'password': 'AdminPass1!'})
_ok(f'login → 200', sc == 200, body)
admin_t = body['access_token']


# ── 1. 비콘 3개 입고 ───────────────────────────────────────────────────────
print('\n[1] 비콘 3개 일괄 입고')
sc, body = _post('/api/admin/beacons/import', {
    'beacons': [
        {'serial_no': 'SN-A', 'uuid': 'AAAA0001-AAAA-AAAA-AAAA-AAAAAAAAAAAA'},
        {'serial_no': 'SN-B', 'uuid': 'AAAA0002-AAAA-AAAA-AAAA-AAAAAAAAAAAA'},
        {'serial_no': 'SN-C', 'uuid': 'AAAA0003-AAAA-AAAA-AAAA-AAAAAAAAAAAA'},
    ]
}, admin_t)
_ok(f'import 성공', sc in (200, 201) and body.get('imported_count') == 3, body)


# ── 2. 비콘 배터리 보고 (각각 다른 잔량) ────────────────────────────────────
print('\n[2] 비콘 배터리 보고')
db = _patched_get_db()
ids = [r['id'] for r in db.execute("SELECT id FROM beacons ORDER BY id").fetchall()]
db.close()

# 3개 비콘 — 80%, 15%, 5% (저전력 임계 20%)
for bid, pct in zip(ids, [80, 15, 5]):
    sc, body = _post(f'/api/beacon/{bid}/battery', {'battery_pct': pct, 'voltage_mv': 2900})
    _ok(f'beacon#{bid} pct={pct} → 200', sc == 200, body)


# ── 3. 잘못된 입력 거부 ────────────────────────────────────────────────────
print('\n[3] 입력 검증')
sc, _ = _post(f'/api/beacon/{ids[0]}/battery', {})
_ok('battery_pct 누락 → 400', sc == 400)
sc, _ = _post(f'/api/beacon/{ids[0]}/battery', {'battery_pct': 150})
_ok('범위 초과 → 400', sc == 400)
sc, _ = _post(f'/api/beacon/9999/battery', {'battery_pct': 50})
_ok('존재하지 않는 비콘 → 404', sc == 404)


# ── 4. 운영자 전체 배터리 현황 ─────────────────────────────────────────────
print('\n[4] 운영자 전체 현황 조회')
sc, body = _get('/api/admin/beacons/battery-status?low_threshold=20', admin_t)
_ok(f'battery-status → 200', sc == 200, body)
_ok(f"total=3", body['summary']['total'] == 3, body)
_ok(f"low_battery=2 (15%, 5%)", body['summary']['low_battery'] == 2, body)
_ok(f"avg_pct ≈ 33.3", abs(body['summary']['avg_pct'] - 33.3) < 0.1, body)
_ok(f"low_battery_beacons 정렬 (낮은 순)", body['low_battery_beacons'][0]['battery_pct'] == 5, body)


# ── 5. 임계치 변경 ─────────────────────────────────────────────────────────
print('\n[5] 임계치 50으로 변경')
sc, body = _get('/api/admin/beacons/battery-status?low_threshold=50', admin_t)
_ok(f"low_battery=2 (여전히 15, 5만 ≤50)", body['summary']['low_battery'] == 2, body)


# ── 6. 시계열 조회 ────────────────────────────────────────────────────────
print('\n[6] 비콘 배터리 시계열')
sc, body = _get(f'/api/admin/beacons/{ids[0]}/battery-history', admin_t)
_ok(f'history → 200', sc == 200, body)
_ok(f'count=1', body['count'] == 1, body)


# ── 7. 같은 비콘 두 번 더 보고 → 시계열 누적 ────────────────────────────────
print('\n[7] 추가 보고로 시계열 누적')
_post(f'/api/beacon/{ids[0]}/battery', {'battery_pct': 75})
_post(f'/api/beacon/{ids[0]}/battery', {'battery_pct': 70})
sc, body = _get(f'/api/admin/beacons/{ids[0]}/battery-history', admin_t)
_ok(f'count=3', body['count'] == 3, body)
_ok(f'최신순 정렬 (DESC)', body['history'][0]['battery_pct'] == 70, body)


# ── 8. 인증 없이 운영자 엔드포인트 → 401 ───────────────────────────────────
print('\n[8] 인증 없이 운영자 조회')
sc, _ = _get('/api/admin/beacons/battery-status')
_ok('no token → 401', sc == 401)


os.unlink(tmp.name)
print('\n✅ 모든 시나리오 통과')
