"""P17 — iOS .mobileconfig 다건 설치 회귀 테스트.

검증 범위
---------
1) 비로그인 → 401
2) 사용자 토큰 + 매장 정상 → 200 + Content-Type 'application/x-apple-aspen-config'
   + Content-Disposition attachment
3) XML plist 안에 SSID/Password/EncryptionType 포함
4) 다건 wifi → PayloadContent N개
5) 없는 매장 → 404
6) WiFi 없는 매장 → 404
7) 미성년자 + adult_only → 403
8) 평문 password 가 응답에 (HTTPS 가정으로 통신 보안)
"""
import os
import sqlite3
import tempfile
import plistlib

import bcrypt

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name

import models.database as _dbmod
_dbmod.DB_PATH = tmp.name
_dbmod.init_db()

from app import app                                    # noqa: E402
from routes.auth import make_jwt                       # noqa: E402
from models.crypto import encrypt_secret               # noqa: E402

c = app.test_client()


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


# ── 0. 시드 ──────────────────────────────────────────────────────────────
print('\n[0] 시드 — 사용자 + 매장 + WiFi 3개 (2 with password / 1 open)')
db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
hashed = bcrypt.hashpw(b'pw', bcrypt.gensalt()).decode()
db.execute("INSERT INTO users (email, password, language) VALUES ('u1@x.com', ?, 'ko')", (hashed,))
db.execute("INSERT INTO users (email, password, language, age_group) VALUES ('minor@x.com', ?, 'ko', 'minor_14_18')", (hashed,))
db.execute("INSERT INTO facilities (name, owner_id, active) VALUES ('Cafe Seoul', 1, 1)")
db.execute("INSERT INTO facilities (name, owner_id, active) VALUES ('Bar Adult', 1, 1)")
db.execute("UPDATE facilities SET adult_only=1 WHERE id=2")
# Cafe Seoul (1) 의 WiFi 3개. password 는 암호화 저장.
for i, (ssid, pw) in enumerate([('CAFE-AP1', 'pw1'), ('CAFE-AP2', 'pw2'), ('CAFE-OPEN', '')], start=1):
    enc = encrypt_secret(pw) if pw else encrypt_secret('')
    db.execute(
        "INSERT INTO wifi_profiles (facility_id, ssid, password, scope, credential_mode, country, active) VALUES (1, ?, ?, 'public', 'static', 'KR', 1)",
        (ssid, enc)
    )
# 빈 매장 — facility 3 (WiFi 없음)
db.execute("INSERT INTO facilities (name, owner_id, active) VALUES ('Empty Cafe', 1, 1)")
db.commit(); db.close()

user_token  = make_jwt(1, 'u1@x.com',    sub_type='user')
minor_token = make_jwt(2, 'minor@x.com', sub_type='user')


# ── 1. 비로그인 → 401 ──────────────────────────────────────────────────
print('\n[1] 비로그인 → 401')
r = c.get('/api/beacon/wifi/venue/1.mobileconfig')
_ok('401 응답', r.status_code == 401, r.get_data(as_text=True))


# ── 2. 정상 다운로드 → 200 + Content-Type + Content-Disposition ────────
print('\n[2] 정상 다운로드')
r = c.get('/api/beacon/wifi/venue/1.mobileconfig',
          headers={'Authorization': f'Bearer {user_token}'})
_ok('200 응답',                  r.status_code == 200, r.status_code)
_ok("Content-Type 'application/x-apple-aspen-config'",
    r.content_type == 'application/x-apple-aspen-config', r.content_type)
_ok('Content-Disposition attachment',
    'attachment' in (r.headers.get('Content-Disposition') or ''),
    r.headers.get('Content-Disposition'))
_ok('filename 에 facility id 포함',
    'pathwave-1' in (r.headers.get('Content-Disposition') or ''),
    r.headers.get('Content-Disposition'))


# ── 3. XML plist 파싱 + 구조 검증 ──────────────────────────────────────
print('\n[3] XML plist 파싱 + 구조')
profile = plistlib.loads(r.data)
_ok("PayloadType == 'Configuration'",
    profile['PayloadType'] == 'Configuration', profile.get('PayloadType'))
_ok('PayloadVersion == 1',       profile['PayloadVersion'] == 1)
_ok('PayloadIdentifier 매장 id 포함',
    f'venue.1' in profile['PayloadIdentifier'], profile['PayloadIdentifier'])
_ok('PayloadDisplayName 에 매장명',
    'Cafe Seoul' in profile['PayloadDisplayName'], profile['PayloadDisplayName'])


# ── 4. PayloadContent — wifi 3개 ───────────────────────────────────────
print('\n[4] PayloadContent — wifi 다건 (3개)')
contents = profile['PayloadContent']
_ok(f'wifi 3개 (실제 {len(contents)})', len(contents) == 3, len(contents))
ssids = sorted(w['SSID_STR'] for w in contents)
_ok('SSID 목록 정확',
    ssids == ['CAFE-AP1', 'CAFE-AP2', 'CAFE-OPEN'], ssids)

# password 있는 것은 WPA, 없는 것은 None
for w in contents:
    if w['SSID_STR'] == 'CAFE-OPEN':
        _ok("CAFE-OPEN EncryptionType == 'None'",
            w['EncryptionType'] == 'None', w)
        _ok('CAFE-OPEN Password 없음', 'Password' not in w, w)
    else:
        _ok(f"{w['SSID_STR']} EncryptionType == 'WPA'",
            w['EncryptionType'] == 'WPA', w)
        _ok(f"{w['SSID_STR']} Password 평문 포함",
            w.get('Password', '').startswith('pw'), w)


# ── 5. 모든 wifi entry 가 PayloadType == 'com.apple.wifi.managed' ─────
print('\n[5] PayloadType per wifi')
for w in contents:
    _ok(f"{w['SSID_STR']} PayloadType com.apple.wifi.managed",
        w['PayloadType'] == 'com.apple.wifi.managed', w)


# ── 6. AutoJoin true + HIDDEN_NETWORK false ────────────────────────────
print('\n[6] AutoJoin + HIDDEN')
for w in contents:
    _ok(f"{w['SSID_STR']} AutoJoin true",
        w['AutoJoin'] is True, w)
    _ok(f"{w['SSID_STR']} HIDDEN_NETWORK false",
        w['HIDDEN_NETWORK'] is False, w)


# ── 7. 없는 매장 → 404 ─────────────────────────────────────────────────
print('\n[7] 없는 매장 → 404')
r = c.get('/api/beacon/wifi/venue/9999.mobileconfig',
          headers={'Authorization': f'Bearer {user_token}'})
_ok('404 응답', r.status_code == 404, r.status_code)


# ── 8. WiFi 없는 매장 → 404 ────────────────────────────────────────────
print('\n[8] WiFi 없는 매장(facility 3) → 404')
r = c.get('/api/beacon/wifi/venue/3.mobileconfig',
          headers={'Authorization': f'Bearer {user_token}'})
_ok('404 응답', r.status_code == 404, r.status_code)


# ── 9. 미성년자 + adult_only → 403 ─────────────────────────────────────
print('\n[9] 미성년자 + adult_only → 403')
# 매장 2 (adult_only) 에 WiFi 추가
db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
db.execute("INSERT INTO wifi_profiles (facility_id, ssid, password, active) VALUES (2, 'BAR-AP', ?, 1)", (encrypt_secret('pw'),))
db.commit(); db.close()
r = c.get('/api/beacon/wifi/venue/2.mobileconfig',
          headers={'Authorization': f'Bearer {minor_token}'})
_ok('403 응답', r.status_code == 403, r.status_code)


print('\n=== P17 (.mobileconfig 다건 설치) PASS ===')
os.unlink(tmp.name)
