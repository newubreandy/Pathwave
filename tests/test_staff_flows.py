"""직원(staff) 흐름 통합 테스트 — 기존 페르소나 테스트가 안 다룬 영역 보강.

이미 test_persona_p4p5_staff.py 가 invite·list·accept·login 4개를 다룸.
본 테스트는 미커버 4개 + 가드 케이스에 집중.

대상
----
- POST /api/staff/<iid>/resend (만료/취소 invite 재발송)
- DELETE /api/staff/<iid>       (revoke)
- GET  /api/staff/me/today      (오늘 활동 집계)
- GET  /api/staff/me            (본인 정보 + 소유주 매장)

검증
----
- resend: pending 상태 → 409, revoked → 200 + new token, accepted → 409, 404
- revoke: pending → 200, accepted → 409, 다른 매장 → 404
- /me/today: 본인 적립만 보임 + amount 합산 정확
- /me: 200 + staff_account + owner.company_name
"""
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta

import bcrypt

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
from models.rate_limit import limiter  # noqa: E402
from routes.auth import make_jwt  # noqa: E402

limiter.enabled = False
c = app.test_client()


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


# ── 픽스처 ──────────────────────────────────────────────────────────────────
def _seed_baseline() -> dict:
    """점주 + 매장. 직원 invite·accept 는 각 시나리오에서 명시 실행."""
    db = _dbmod.get_db(); cur = db.cursor()
    pw = bcrypt.hashpw(b'Owner!2345', bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO facility_accounts
             (business_no, company_name, email, password, manager_name,
              verified, status, created_at)
           VALUES ('111-11-11111', 'Cafe', 'o@t.test', ?, 'Mgr', 1, 'verified',
                   datetime('now'))""",
        (pw,),
    )
    aid = cur.lastrowid
    cur.execute(
        """INSERT INTO facilities (name, owner_id, active, created_at)
           VALUES ('Cafe One', ?, 1, datetime('now'))""",
        (aid,),
    )
    fid = cur.lastrowid

    # 다른 점주 (소유권 가드 검증용)
    pw2 = bcrypt.hashpw(b'Other!2345', bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO facility_accounts
             (business_no, company_name, email, password, manager_name,
              verified, status, created_at)
           VALUES ('999-99-99999', 'Other', 'x@t.test', ?, 'Mgr', 1, 'verified',
                   datetime('now'))""",
        (pw2,),
    )
    aid2 = cur.lastrowid

    db.commit(); db.close()
    return {'aid': aid, 'fid': fid, 'aid_other': aid2}


def _h(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _owner_token(account_id: int, facility_id: int) -> str:
    return make_jwt(account_id, 'o@t.test', 'access', 'facility',
                    {'facility_id': facility_id, 'role': 'owner',
                     'owner_account_id': account_id})


def _create_invite(account_id: int, facility_id: int, email='s@t.test',
                   role='staff') -> int:
    """초대 1건 생성 → invitation_id 반환."""
    OH = _h(_owner_token(account_id, facility_id))
    r = c.post('/api/staff/invite', headers=OH,
               json={'email': email, 'role': role})
    return r.get_json()['invitation']['id']


def _accept_invite(token: str, password='Staff!2345',
                   name='Staff', phone='010-0000-0000') -> dict:
    """초대 토큰으로 accept → {access_token, staff_account, ...} 반환."""
    r = c.post('/api/staff/accept',
               json={'invite_token': token, 'password': password,
                     'name': name, 'phone': phone})
    return r.get_json()


def _staff_token_for(email='s@t.test', password='Staff!2345') -> str:
    """staff_login 거쳐 토큰 발급."""
    r = c.post('/api/staff/login', json={'email': email, 'password': password})
    return r.get_json()['access_token']


def _truncate_all():
    db = _dbmod.get_db()
    for t in (
        'coupons', 'stamps', 'chat_messages', 'chat_rooms',
        'staff_accounts', 'staff_invitations',
        'facilities', 'facility_accounts', 'users',
    ):
        try:
            db.execute(f'DELETE FROM {t}')
        except sqlite3.OperationalError:
            pass
    db.commit(); db.close()


# ══════════════════════════════════════════════════════════════════════════════
# A. 초대 재발송 (resend)
# ══════════════════════════════════════════════════════════════════════════════
def test_a_resend_guards():
    print('\n── A. 초대 resend 가드 ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['aid'], ids['fid']))
    iid = _create_invite(ids['aid'], ids['fid'])

    # pending 상태에서 resend → 409 (아직 유효)
    r = c.post(f'/api/staff/{iid}/resend', headers=OH)
    _ok('① pending invite resend → 409', r.status_code == 409, r.get_json())

    # 존재하지 않는 invite → 404
    r = c.post('/api/staff/999999/resend', headers=OH)
    _ok('② 존재하지 않는 invite → 404', r.status_code == 404)

    # revoked → 200 + 새 토큰 (status='pending' 으로 복원)
    c.delete(f'/api/staff/{iid}', headers=OH)
    r = c.post(f'/api/staff/{iid}/resend', headers=OH)
    body = r.get_json()
    _ok('③ revoked invite resend → 200 + status pending',
        r.status_code == 200 and body['invitation']['status'] == 'pending', body)

    # accepted invite resend → 409 (token 은 응답 미포함이라 DB 직접 조회)
    db = _dbmod.get_db()
    new_token = db.execute("SELECT invite_token FROM staff_invitations WHERE id=?",
                           (iid,)).fetchone()['invite_token']
    db.close()
    _accept_invite(new_token)
    r = c.post(f'/api/staff/{iid}/resend', headers=OH)
    _ok('④ accepted invite resend → 409', r.status_code == 409, r.get_json())


# ══════════════════════════════════════════════════════════════════════════════
# B. 초대 취소 (revoke / DELETE)
# ══════════════════════════════════════════════════════════════════════════════
def test_b_revoke_guards():
    print('\n── B. 초대 revoke 가드 ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['aid'], ids['fid']))
    iid = _create_invite(ids['aid'], ids['fid'])

    # pending → 200 + status='revoked'
    r = c.delete(f'/api/staff/{iid}', headers=OH)
    _ok('① pending revoke → 200', r.status_code == 200, r.get_json())
    db = _dbmod.get_db()
    st = db.execute("SELECT status FROM staff_invitations WHERE id=?", (iid,)).fetchone()['status']
    db.close()
    _ok('② DB status=revoked', st == 'revoked')

    # accepted → 409
    iid2 = _create_invite(ids['aid'], ids['fid'], email='s2@t.test')
    db = _dbmod.get_db()
    tok2 = db.execute("SELECT invite_token FROM staff_invitations WHERE id=?", (iid2,)).fetchone()['invite_token']
    db.close()
    _accept_invite(tok2)
    r = c.delete(f'/api/staff/{iid2}', headers=OH)
    _ok('③ accepted invite revoke → 409', r.status_code == 409, r.get_json())

    # 다른 매장 invite (account_id 불일치) → 404
    iid3 = _create_invite(ids['aid_other'], 999, email='s3@t.test')
    r = c.delete(f'/api/staff/{iid3}', headers=OH)
    _ok('④ 다른 매장 invite revoke → 404', r.status_code == 404)


# ══════════════════════════════════════════════════════════════════════════════
# C. /api/staff/me + /me/today
# ══════════════════════════════════════════════════════════════════════════════
def test_c_staff_me_and_today():
    print('\n── C. staff /me + /me/today ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['aid'], ids['fid']))

    # 직원 1명 초대·수락
    iid = _create_invite(ids['aid'], ids['fid'])
    db = _dbmod.get_db()
    tok = db.execute("SELECT invite_token FROM staff_invitations WHERE id=?", (iid,)).fetchone()['invite_token']
    db.close()
    _accept_invite(tok, name='홍길동', phone='010-1111-2222')

    SH = _h(_staff_token_for())

    # /me
    r = c.get('/api/staff/me', headers=SH)
    body = r.get_json()
    _ok('① /me 200 + staff_account.name=홍길동',
        r.status_code == 200 and body['staff_account']['name'] == '홍길동', body)
    _ok('② /me owner.company_name 노출',
        body['owner']['company_name'] == 'Cafe', body['owner'])

    # 사용자 시드 (스탬프 대상)
    db = _dbmod.get_db()
    db.execute(
        """INSERT INTO users (email, password, provider, language, verified, birth_year, age_group, created_at)
           VALUES ('u1@t.test', 'x', 'email', 'ko', 1, 1990, 'adult', datetime('now'))"""
    )
    uid = db.execute("SELECT id FROM users WHERE email='u1@t.test'").fetchone()['id']
    db.commit(); db.close()

    # 직원이 스탬프 적립 (오늘)
    r = c.post(f"/api/facilities/{ids['fid']}/stamps", headers=SH,
               json={'user_id': uid, 'amount': 3})
    _ok('③ 직원 스탬프 적립 201', r.status_code in (200, 201), r.get_json())

    # 점주가 별도 적립 (다른 actor — 직원 me/today 에 안 보여야 함)
    c.post(f"/api/facilities/{ids['fid']}/stamps", headers=OH,
           json={'user_id': uid, 'amount': 5})

    # /me/today — 본인이 적립한 것만, amount 합 = 3
    r = c.get('/api/staff/me/today', headers=SH)
    body = r.get_json()
    _ok('④ /me/today 200', r.status_code == 200, body)
    _ok('⑤ 본인 적립 스탬프 1건 + 합계 3',
        len(body['today']['stamps_granted']) == 1
        and body['totals']['stamps_count'] == 3, body['totals'])


# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    print('═══ 직원(staff) 흐름 보강 테스트 ═══')
    for fn in (
        test_a_resend_guards,
        test_b_revoke_guards,
        test_c_staff_me_and_today,
    ):
        _truncate_all()
        fn()
    print('\n✅ 모든 테스트 통과')


if __name__ == '__main__':
    main()
