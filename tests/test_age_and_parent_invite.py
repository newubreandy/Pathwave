"""PR #47 — 연령 분류 + 부모 초대 + 미성년자 시설 제한 통합 테스트."""
import os
import json
import sqlite3
import tempfile
from datetime import datetime

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name
os.environ['EMAIL_PROVIDER'] = 'console'

import models.database as _dbmod  # noqa: E402
def _patched_get_db():
    conn = sqlite3.connect(os.environ['PATHWAVE_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn
_dbmod.get_db = _patched_get_db

from app import app  # noqa: E402

c = app.test_client()
THIS_YEAR = datetime.utcnow().year


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


def _get(path, token=None):
    h = {}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.get(path, headers=h)
    return r.status_code, r.get_json()


def _send_and_get_code(email):
    """rate-limit 우회 — DB 에 직접 코드 인서트 (테스트용)."""
    db = _patched_get_db()
    db.execute(
        """INSERT INTO email_codes (email, code, expires_at, used)
           VALUES (?, '999999', datetime('now', '+5 minutes'), 0)""",
        (email,)
    )
    db.commit(); db.close()
    return '999999'


REQUIRED_USER_CONSENTS = [
    {'kind': 'age14',    'version': 'v', 'accepted': True},
    {'kind': 'terms',    'version': 'v', 'accepted': True},
    {'kind': 'privacy',  'version': 'v', 'accepted': True},
    {'kind': 'location', 'version': 'v', 'accepted': True},
]


# ── [1] 만 14 미만 가입 거부 ────────────────────────────────────────────
print('\n[1] 만 14 미만 (birth_year=2020) → 가입 거부')
code = _send_and_get_code('child@age.test')
s, j = _post('/api/auth/register', {
    'email': 'child@age.test', 'code': code, 'password': 'StrongPw1!',
    'birth_year': 2020,
    'consents': REQUIRED_USER_CONSENTS,
})
_ok(f'400 (got {s})', s == 400, j)
_ok('만 14세 이상 메시지', '14세' in (j.get('message') or ''))


# ── [2] 만 19+ 성인 가입 ─────────────────────────────────────────────────
print('\n[2] 성인(birth_year=1990) 가입 OK + age_group=adult_19_plus')
code = _send_and_get_code('parent@age.test')
s, j = _post('/api/auth/register', {
    'email': 'parent@age.test', 'code': code, 'password': 'StrongPw1!',
    'birth_year': 1990,
    'consents': REQUIRED_USER_CONSENTS,
})
_ok(f'200 (got {s})', s == 200, j)
parent_token = j['access_token']
parent_id = j['user']['id']

db = _patched_get_db()
row = db.execute("SELECT age_group FROM users WHERE id=?", (parent_id,)).fetchone()
db.close()
_ok('age_group=adult_19_plus', row['age_group'] == 'adult_19_plus')


# ── [3] 미성년자 가입 — 부모 초대 없으면 거부 ────────────────────────────
print('\n[3] 미성년자(birth_year=THIS_YEAR-16) → 초대 없으면 403')
minor_year = THIS_YEAR - 16
code = _send_and_get_code('teen@age.test')
s, j = _post('/api/auth/register', {
    'email': 'teen@age.test', 'code': code, 'password': 'StrongPw1!',
    'birth_year': minor_year,
    'consents': REQUIRED_USER_CONSENTS,
})
_ok(f'403 (got {s})', s == 403, j)
_ok('보호자 초대 메시지', '보호자' in (j.get('message') or ''))


# ── [4] 부모가 자녀 초대 발급 (책임 동의 누락) ─────────────────────────
print('\n[4] 부모 자녀 초대 — 책임 동의 누락 시 400')
s, j = _post('/api/invitations/parent', {}, token=parent_token)
_ok(f'400 (got {s})', s == 400, j)


# ── [5] 부모 자녀 초대 — 책임 동의 OK ─────────────────────────────────
print('\n[5] 부모 자녀 초대 — 책임 동의 후 발급 OK')
s, j = _post('/api/invitations/parent', {
    'liability_accepted': True,
    'invitee_email': 'teen@age.test',
}, token=parent_token)
_ok(f'201 (got {s})', s == 201, j)
minor_invite_code = j['invitation']['code']
_ok('is_minor_invite=True', j['invitation']['is_minor_invite'] == True)


# ── [6] 미성년자가 부모 초대 코드로 가입 ─────────────────────────────────
print('\n[6] 미성년자가 부모 초대 코드로 가입 OK')
code = _send_and_get_code('teen2@age.test')   # 새 이메일 (이전엔 코드 소비됨)
s, j = _post('/api/auth/register', {
    'email': 'teen2@age.test', 'code': code, 'password': 'StrongPw1!',
    'birth_year': minor_year,
    'invitation_code': minor_invite_code,
    'consents': REQUIRED_USER_CONSENTS,
})
_ok(f'200 (got {s})', s == 200, j)
minor_token = j['access_token']
minor_id = j['user']['id']

db = _patched_get_db()
row = db.execute(
    "SELECT age_group, parent_invitation_id FROM users WHERE id=?", (minor_id,)
).fetchone()
db.close()
_ok('age_group=minor_14_18', row['age_group'] == 'minor_14_18')
_ok('parent_invitation_id 기록됨', row['parent_invitation_id'] is not None)


# ── [7] 같은 부모 초대 코드 재사용 거부 (단일 사용) ───────────────────────
print('\n[7] 부모 초대 코드 재사용 거부')
code = _send_and_get_code('teen3@age.test')
s, j = _post('/api/auth/register', {
    'email': 'teen3@age.test', 'code': code, 'password': 'StrongPw1!',
    'birth_year': minor_year,
    'invitation_code': minor_invite_code,  # 이미 소비됨
    'consents': REQUIRED_USER_CONSENTS,
})
_ok(f'400 (got {s})', s == 400, j)


# ── [8] 미성년자가 일반 사용자 초대 코드 사용 시 거부 ────────────────────
print('\n[8] 일반 사용자 초대 코드는 미성년자에게 거부')
# 부모가 일반 초대 발급 (is_minor_invite=0)
s, j = _post('/api/invitations', {
    'channel': 'link',
}, token=parent_token)
_ok(f'201 (got {s})', s == 201)
normal_code = j['invitation']['code']

code = _send_and_get_code('teen4@age.test')
s, j = _post('/api/auth/register', {
    'email': 'teen4@age.test', 'code': code, 'password': 'StrongPw1!',
    'birth_year': minor_year,
    'invitation_code': normal_code,
    'consents': REQUIRED_USER_CONSENTS,
})
_ok(f'400 (got {s})', s == 400, j)
_ok('미성년자 초대 아님 메시지', '미성년자 초대용이 아닙니다' in (j.get('message') or ''))


# ── [9] 미성년자가 부모 초대 발급 시도 → 403 ───────────────────────────
print('\n[9] 미성년자는 부모 초대 발급 불가')
s, j = _post('/api/invitations/parent', {
    'liability_accepted': True,
}, token=minor_token)
_ok(f'403 (got {s})', s == 403, j)


# ── [10] adult_only 시설 — 미성년자 핸드셰이크 거부 ───────────────────
print('\n[10] adult_only 시설 핸드셰이크 — 미성년자 차단, 성인 통과')
db = _patched_get_db()
db.execute("""INSERT INTO facilities
              (name, owner_id, active, adult_only, latitude, longitude)
              VALUES ('Adult Bar', ?, 1, 1, 37.5, 127.0)""", (parent_id,))
fid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
db.execute("""INSERT INTO beacons (serial_no, uuid, facility_id, status)
              VALUES ('SN-A','AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',?,'active')""", (fid,))
# WiFi 프로필 필요 (handshake 가 요구)
db.execute("""INSERT INTO wifi_profiles (facility_id, ssid, password, active)
              VALUES (?, 'BarWifi', '', 1)""", (fid,))
db.commit(); db.close()

# 미성년자 핸드셰이크 → 403 + reason
s, j = _post('/api/beacon/handshake', {
    'uuid': 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',
    'rssi': -60,
    'user_id': minor_id,
})
_ok(f'미성년자 → 403 (got {s})', s == 403, j)
_ok('reason=adult_only_minor_blocked', j.get('reason') == 'adult_only_minor_blocked')

# 성인 핸드셰이크 → 200
s, j = _post('/api/beacon/handshake', {
    'uuid': 'AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA',
    'rssi': -60,
    'user_id': parent_id,
})
_ok(f'성인 → 200 (got {s})', s == 200, j)


# ── [11] 검색 — 미성년자 토큰이면 adult_only 자동 필터 ───────────────────
print('\n[11] 검색에서 미성년자에게 adult_only 매장 미노출')
# 일반 매장도 추가 (미성년자에게 보여야 함)
db = _patched_get_db()
db.execute("""INSERT INTO facilities
              (name, owner_id, active, adult_only, latitude, longitude)
              VALUES ('Cafe', ?, 1, 0, 37.5, 127.0)""", (parent_id,))
db.commit(); db.close()

# 미성년자 토큰
s, j = _get('/api/search/facilities', token=minor_token)
_ok('200', s == 200)
names_minor = [r['name'] for r in j['results']]
_ok(f'Adult Bar 미노출 (got {names_minor})', 'Adult Bar' not in names_minor)
_ok(f'Cafe 노출', 'Cafe' in names_minor)

# 성인 토큰
s, j = _get('/api/search/facilities', token=parent_token)
names_adult = [r['name'] for r in j['results']]
_ok(f'성인은 Adult Bar 노출 (got {names_adult})',
    'Adult Bar' in names_adult and 'Cafe' in names_adult)


print('\n✅ 모든 시나리오 통과')
