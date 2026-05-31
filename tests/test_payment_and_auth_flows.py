"""결제 + 인증 + 회원 QR 흐름 통합 테스트.

대상 PR / 흐름
--------------
A. 점주 비밀번호 재설정 (#230)
   - POST /api/facility/forgot-password  (계정 열거 방지)
   - POST /api/facility/reset-password
B. pg_key AES-256-GCM 암호화 (#230)
   - POST /api/billing/cards    (등록 시 암호화 저장)
   - POST /api/billing/subscriptions  (결제 시 복호화)
   - 레거시 평문 fallback
C. 회원 QR + 제로페이 결제 (#226, #227)
   - POST /api/checkin/member-qr   (사용자 본인 토큰 발급)
   - POST /api/checkin/verify       (점주, deleted_at 컬럼 기반 — status 컬럼 미사용 #227 확인)
   - POST /api/checkin/zeropay-charge

회귀 방지 + 신규 DB 부팅 안전 검증 목적.
"""
import os
import sqlite3
import tempfile
import time

import bcrypt
import jwt as pyjwt

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB']  = tmp.name
os.environ['PG_PROVIDER']  = 'sim'   # billing.py — sim provider 사용

import models.database as _dbmod  # noqa: E402


def _patched_get_db():
    conn = sqlite3.connect(os.environ['PATHWAVE_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


_dbmod.get_db = _patched_get_db

from app import app  # noqa: E402
from models.crypto import decrypt_secret, encrypt_secret  # noqa: E402
from models.rate_limit import limiter  # noqa: E402
from routes.auth import SECRET_KEY, make_jwt  # noqa: E402

# 테스트는 단일 IP(127.0.0.1)에서 forgot-password 등을 빠르게 반복 호출하므로
# 운영 rate-limit (3/min 등) 에 차단된다. 테스트 격리를 위해 비활성.
limiter.enabled = False

c = app.test_client()


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


# ── 픽스처 ──────────────────────────────────────────────────────────────────
def _seed_provider(email='p@t.test', password='Test!23456', verified=True) -> int:
    db = _dbmod.get_db(); cur = db.cursor()
    pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO facility_accounts
             (business_no, company_name, email, password, manager_name,
              verified, status, created_at)
           VALUES ('111-22-33333', 'Test Co', ?, ?, 'Mgr', 1,
                   ?, datetime('now'))""",
        (email, pw, 'verified' if verified else 'pending'),
    )
    aid = cur.lastrowid
    db.commit(); db.close()
    return aid


def _seed_user(email='u@t.test', password='User!2345', deleted=False) -> int:
    db = _dbmod.get_db(); cur = db.cursor()
    pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO users
             (email, password, provider, language, verified, birth_year, age_group, created_at, deleted_at)
           VALUES (?, ?, 'email', 'ko', 1, 1990, 'adult', datetime('now'), ?)""",
        (email, pw, 'datetime("now")' if deleted else None),
    )
    if deleted:
        # SQLite literal datetime not handled by '?' parameter binding for deleted_at flag
        # → 명시적으로 UPDATE 한 번 더.
        db.execute("UPDATE users SET deleted_at=datetime('now') WHERE id=?", (cur.lastrowid,))
    uid = cur.lastrowid
    db.commit(); db.close()
    return uid


def _h(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _truncate_all():
    db = _dbmod.get_db()
    for t in (
        'billing_keys', 'payments', 'service_subscriptions',
        'email_codes', 'users', 'facility_accounts', 'facilities',
        'beacons', 'wifi_profiles', 'beacon_wifi',
    ):
        try:
            db.execute(f'DELETE FROM {t}')
        except sqlite3.OperationalError:
            pass
    db.commit(); db.close()


# ══════════════════════════════════════════════════════════════════════════════
# A. 점주 비밀번호 재설정 (#230)
# ══════════════════════════════════════════════════════════════════════════════
def test_facility_forgot_reset_happy_path():
    print('\n── A1. 점주 forgot → reset 정상 흐름 ──')
    _seed_provider('p@t.test', 'OldPass!23')

    # forgot — 가입 이메일
    r = c.post('/api/facility/forgot-password', json={'email': 'p@t.test'})
    _ok('① forgot 가입자 → 200 success', r.status_code == 200 and r.get_json()['success'] is True)

    db = _dbmod.get_db()
    row = db.execute("SELECT code FROM email_codes WHERE email=? AND used=0 ORDER BY id DESC LIMIT 1",
                     ('p@t.test',)).fetchone()
    db.close()
    _ok('② email_codes 에 코드 생성', row is not None)
    code = row['code'] if row else None

    # reset
    r = c.post('/api/facility/reset-password',
               json={'email': 'p@t.test', 'code': code, 'password': 'NewPass!23'})
    _ok('③ reset 200 + success', r.status_code == 200 and r.get_json()['success'] is True,
        r.get_json())

    # 새 비번 로그인
    r = c.post('/api/facility/login', json={'email': 'p@t.test', 'password': 'NewPass!23'})
    _ok('④ 새 비번 로그인 200 + token', r.status_code == 200 and 'access_token' in r.get_json(),
        r.get_json())

    # 옛 비번 거부
    r = c.post('/api/facility/login', json={'email': 'p@t.test', 'password': 'OldPass!23'})
    _ok('⑤ 옛 비번 401', r.status_code == 401)


def test_facility_forgot_enumeration_protection():
    print('\n── A2. forgot 계정 열거 방지 ──')
    _seed_provider('p@t.test', 'X!23456789')

    r1 = c.post('/api/facility/forgot-password', json={'email': 'p@t.test'})
    r2 = c.post('/api/facility/forgot-password', json={'email': 'nobody@nowhere.kr'})
    _ok('① 가입자 200', r1.status_code == 200)
    _ok('② 미가입자도 200 (응답 동일)', r2.status_code == 200)
    _ok('③ 응답 message 동일 (열거 단서 차단)',
        r1.get_json()['message'] == r2.get_json()['message'],
        f"가입={r1.get_json()['message'][:30]} / 미가입={r2.get_json()['message'][:30]}")

    # 미가입자엔 코드 생성 X
    db = _dbmod.get_db()
    n = db.execute("SELECT COUNT(*) c FROM email_codes WHERE email=?",
                   ('nobody@nowhere.kr',)).fetchone()['c']
    db.close()
    _ok('④ 미가입자 코드 미생성', n == 0)


def test_facility_reset_validation():
    print('\n── A3. reset 입력 검증 ──')
    _seed_provider('p@t.test', 'X!23456789')
    c.post('/api/facility/forgot-password', json={'email': 'p@t.test'})
    db = _dbmod.get_db()
    code = db.execute(
        "SELECT code FROM email_codes WHERE email=? ORDER BY id DESC LIMIT 1",
        ('p@t.test',)
    ).fetchone()['code']
    db.close()

    # 틀린 코드
    r = c.post('/api/facility/reset-password',
               json={'email': 'p@t.test', 'code': '000000', 'password': 'NewPass!23'})
    _ok('① 틀린 코드 → 400', r.status_code == 400)

    # 약한 비밀번호
    r = c.post('/api/facility/reset-password',
               json={'email': 'p@t.test', 'code': code, 'password': 'weak'})
    _ok('② 약한 비번 → 400 + 메시지 포함',
        r.status_code == 400 and 'password' in str(r.get_json()).lower() or '비밀번호' in str(r.get_json()),
        r.get_json())

    # 필수 필드 누락
    r = c.post('/api/facility/reset-password',
               json={'email': 'p@t.test'})
    _ok('③ 필수 필드 누락 → 400', r.status_code == 400)


# ══════════════════════════════════════════════════════════════════════════════
# B. pg_key AES-256-GCM 암호화 (#230)
# ══════════════════════════════════════════════════════════════════════════════
def test_pgkey_encrypt_round_trip():
    print('\n── B1. pg_key 등록 시 암호화 + 복호화 round-trip ──')
    aid = _seed_provider('o@t.test', 'Owner!2345')
    db = _dbmod.get_db()
    db.execute(
        "INSERT INTO facilities (name, owner_id, active, created_at) "
        "VALUES ('S', ?, 1, datetime('now'))",
        (aid,),
    )
    fid = db.execute("SELECT id FROM facilities WHERE owner_id=?", (aid,)).fetchone()['id']
    db.commit(); db.close()

    H = _h(make_jwt(aid, 'o@t.test', 'access', 'facility',
                    {'facility_id': fid, 'role': 'owner', 'owner_account_id': aid}))

    # 카드 등록
    r = c.post('/api/billing/cards', headers=H, json={'card_brand': 'KB', 'last4': '4242'})
    _ok('① 카드 등록 201', r.status_code == 201, r.get_json())

    # DB pg_key 평문 아님
    db = _dbmod.get_db()
    row = db.execute("SELECT pg_key FROM billing_keys WHERE facility_account_id=? AND active=1",
                     (aid,)).fetchone()
    db.close()
    enc = row['pg_key']
    _ok('② DB pg_key 평문 sim- 아님 (암호화 저장)', not enc.startswith('sim-'),
        f"enc[:20]={enc[:20]}")
    _ok('③ 복호화 → sim- 시작 (원본 복원)',
        decrypt_secret(enc).startswith('sim-'),
        f"dec[:20]={decrypt_secret(enc)[:20]}")

    # 구독 결제 — 암호화 키 통과한 채로 PG sim 호출 성공
    r = c.post('/api/billing/subscriptions', headers=H,
               json={'service_type': 'wifi', 'quantity': 1, 'period_months': 1})
    body = r.get_json()
    _ok('④ 구독+결제 201 + payment paid',
        r.status_code == 201 and body['payment']['status'] == 'paid', body)


def test_pgkey_legacy_plaintext_fallback():
    print('\n── B2. 레거시 평문 pg_key fallback (decrypt 가 평문이면 그대로 반환) ──')
    aid = _seed_provider('o@t.test', 'Owner!2345')
    db = _dbmod.get_db()
    db.execute("INSERT INTO facilities (name, owner_id, active, created_at) "
               "VALUES ('S', ?, 1, datetime('now'))", (aid,))
    fid = db.execute("SELECT id FROM facilities WHERE owner_id=?", (aid,)).fetchone()['id']

    # 평문 pg_key 직접 삽입 (레거시 데이터 시뮬레이션)
    db.execute(
        "INSERT INTO billing_keys (facility_account_id, pg_key, card_brand, masked_card, active)"
        " VALUES (?, 'sim-legacyplain', 'KB', '****-****-****-9999', 1)",
        (aid,),
    )
    db.commit(); db.close()

    H = _h(make_jwt(aid, 'o@t.test', 'access', 'facility',
                    {'facility_id': fid, 'role': 'owner', 'owner_account_id': aid}))

    # 결제 — decrypt_secret 이 평문이면 그대로 반환 → 정상 진행
    r = c.post('/api/billing/subscriptions', headers=H,
               json={'service_type': 'wifi', 'quantity': 1, 'period_months': 1})
    body = r.get_json()
    _ok('① 평문 pg_key 도 결제 성공 (decrypt_secret 의 레거시 fallback)',
        r.status_code == 201 and body['payment']['status'] == 'paid', body)


# ══════════════════════════════════════════════════════════════════════════════
# C. 회원 QR + 제로페이 결제 (#226, #227)
# ══════════════════════════════════════════════════════════════════════════════
def _mint_user_token(user_id: int, email: str = 'u@t.test') -> str:
    return make_jwt(user_id, email, 'access', 'user')


def _mint_facility_token(account_id: int, facility_id: int) -> str:
    return make_jwt(account_id, 'p@t.test', 'access', 'facility',
                    {'facility_id': facility_id, 'role': 'owner', 'owner_account_id': account_id})


def test_member_qr_issue_and_verify():
    print('\n── C1. 회원 QR 발급 + 점주 verify (#227 deleted_at 기반 확인) ──')
    uid = _seed_user('u@t.test')
    aid = _seed_provider('p@t.test', 'X!23456789')
    db = _dbmod.get_db()
    db.execute(
        "INSERT INTO facilities (name, owner_id, active, created_at) "
        "VALUES ('S', ?, 1, datetime('now'))",
        (aid,),
    )
    fid = db.execute("SELECT id FROM facilities WHERE owner_id=?", (aid,)).fetchone()['id']
    db.commit(); db.close()

    UH = _h(_mint_user_token(uid))
    FH = _h(_mint_facility_token(aid, fid))

    # 사용자: 회원 QR 발급
    r = c.post('/api/checkin/member-qr', headers=UH)
    body = r.get_json()
    _ok('① member-qr 200 + token + expires_in 60',
        r.status_code == 200 and 'token' in body and body['expires_in'] == 60, body)
    member_token = body['token']

    # 점주: verify (위치: #227 의 status 컬럼 버그 수정 확인 — deleted_at 기반)
    r = c.post('/api/checkin/verify', headers=FH, json={'token': member_token})
    body = r.get_json()
    _ok('② verify 200 + email + is_minor=False (status 컬럼 미사용 — #227 fix)',
        r.status_code == 200 and body.get('email') == 'u@t.test' and body.get('is_minor') is False,
        body)


def test_member_qr_verify_for_deleted_user():
    print('\n── C2. 탈퇴한 회원 QR verify → 400 (deleted_at 기반) ──')
    uid = _seed_user('u@t.test', deleted=True)
    aid = _seed_provider('p@t.test', 'X!23456789')
    db = _dbmod.get_db()
    db.execute(
        "INSERT INTO facilities (name, owner_id, active, created_at) "
        "VALUES ('S', ?, 1, datetime('now'))",
        (aid,),
    )
    fid = db.execute("SELECT id FROM facilities WHERE owner_id=?", (aid,)).fetchone()['id']
    db.commit(); db.close()

    UH = _h(_mint_user_token(uid))
    FH = _h(_mint_facility_token(aid, fid))

    member_token = c.post('/api/checkin/member-qr', headers=UH).get_json()['token']
    r = c.post('/api/checkin/verify', headers=FH, json={'token': member_token})
    _ok('① 탈퇴 회원 → 400 + 탈퇴 메시지',
        r.status_code == 400 and '탈퇴' in r.get_json().get('message', ''),
        r.get_json())


def test_member_qr_verify_expired_token():
    print('\n── C3. 만료 토큰 verify → 400 ──')
    uid = _seed_user('u@t.test')
    aid = _seed_provider('p@t.test', 'X!23456789')
    db = _dbmod.get_db()
    db.execute("INSERT INTO facilities (name, owner_id, active, created_at) "
               "VALUES ('S', ?, 1, datetime('now'))", (aid,))
    fid = db.execute("SELECT id FROM facilities WHERE owner_id=?", (aid,)).fetchone()['id']
    db.commit(); db.close()

    # 만료된 member_qr 토큰을 직접 mint (exp=과거)
    expired = pyjwt.encode(
        {'kind': 'member_qr', 'user_id': uid, 'sub_type': 'user', 'exp': int(time.time()) - 10},
        SECRET_KEY, algorithm='HS256',
    )
    FH = _h(_mint_facility_token(aid, fid))
    r = c.post('/api/checkin/verify', headers=FH, json={'token': expired})
    _ok('① 만료 토큰 → 400',
        r.status_code == 400 and '만료' in r.get_json().get('message', ''),
        r.get_json())


def test_zeropay_charge_happy_path_and_guards():
    print('\n── C4. 제로페이 결제 (mock) + 가드 ──')
    uid = _seed_user('u@t.test')
    aid = _seed_provider('p@t.test', 'X!23456789')
    db = _dbmod.get_db()
    db.execute("INSERT INTO facilities (name, owner_id, active, created_at) "
               "VALUES ('S', ?, 1, datetime('now'))", (aid,))
    fid = db.execute("SELECT id FROM facilities WHERE owner_id=?", (aid,)).fetchone()['id']
    db.commit(); db.close()

    UH = _h(_mint_user_token(uid))
    FH = _h(_mint_facility_token(aid, fid))
    member_token = c.post('/api/checkin/member-qr', headers=UH).get_json()['token']

    # 정상 결제
    r = c.post('/api/checkin/zeropay-charge', headers=FH,
               json={'token': member_token, 'amount': 12000})
    body = r.get_json()
    _ok('① 결제 200 + amount + method=zeropay + mock=True',
        r.status_code == 200 and body['amount'] == 12000 and body['method'] == 'zeropay'
        and body.get('mock') is True, body)
    _ok('② order_no = ZP-<user_id>-<ts>',
        body['order_no'].startswith(f'ZP-{uid}-'), body['order_no'])

    # 가드: amount <= 0
    r = c.post('/api/checkin/zeropay-charge', headers=FH,
               json={'token': member_token, 'amount': 0})
    _ok('③ amount=0 → 400', r.status_code == 400, r.get_json())

    # 가드: token 누락
    r = c.post('/api/checkin/zeropay-charge', headers=FH,
               json={'amount': 1000})
    _ok('④ token 누락 → 400', r.status_code == 400)

    # 가드: 만료된 토큰
    expired = pyjwt.encode(
        {'kind': 'member_qr', 'user_id': uid, 'sub_type': 'user', 'exp': int(time.time()) - 10},
        SECRET_KEY, algorithm='HS256',
    )
    r = c.post('/api/checkin/zeropay-charge', headers=FH,
               json={'token': expired, 'amount': 1000})
    _ok('⑤ 만료 토큰 → 400', r.status_code == 400)


# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    print('═══ 결제 + 인증 + 회원 QR 통합 테스트 ═══')
    for fn in (
        test_facility_forgot_reset_happy_path,
        test_facility_forgot_enumeration_protection,
        test_facility_reset_validation,
        test_pgkey_encrypt_round_trip,
        test_pgkey_legacy_plaintext_fallback,
        test_member_qr_issue_and_verify,
        test_member_qr_verify_for_deleted_user,
        test_member_qr_verify_expired_token,
        test_zeropay_charge_happy_path_and_guards,
    ):
        _truncate_all()
        fn()
    print('\n✅ 모든 테스트 통과')


if __name__ == '__main__':
    main()
