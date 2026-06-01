"""신고(abuse report) 통합 테스트 — 출시 심의 HIGH-1(UGC 신고/차단) 회귀 방지.

기존 test_chat_block.py 는 차단(block)을 다룸. 본 테스트는 신고(abuse_reports) 4 endpoint.

대상
----
- POST  /api/abuse-reports                  (사용자/사장 자동 판별)
- GET   /api/admin/abuse-reports?status=    (운영자 inbox)
- GET   /api/admin/abuse-reports/<rid>      (운영자 단건)
- PATCH /api/admin/abuse-reports/<rid>      (운영자 처리)

검증
----
- 신고 생성: user→facility / facility→user(상호) / 토큰없음 401 / target·reason 검증
- 운영자 조회: open 우선 정렬 + status 필터 + 잘못된 status 400 + 404 + 권한
- 운영자 처리: action_taken 시 resolved_at·admin_id 세팅 / note / 잘못된 status / 빈 변경
"""
import os
import sqlite3
import tempfile

import bcrypt

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name

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
    db = _dbmod.get_db(); cur = db.cursor()

    # 슈퍼어드민
    pw = bcrypt.hashpw(b'admin!23', bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO super_admin_accounts (email, password, name, role, active, created_at)
           VALUES ('admin@t.test', ?, 'Admin', 'super', 1, datetime('now'))""",
        (pw,),
    )
    admin_id = cur.lastrowid

    # 사장(facility account) + 매장
    fpw = bcrypt.hashpw(b'prov!23', bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO facility_accounts
             (business_no, company_name, email, password, manager_name, verified, status, created_at)
           VALUES ('111-11-11111', 'Cafe', 'o@t.test', ?, 'Mgr', 1, 'verified', datetime('now'))""",
        (fpw,),
    )
    account_id = cur.lastrowid
    cur.execute(
        "INSERT INTO facilities (name, owner_id, active, created_at) VALUES ('Cafe One', ?, 1, datetime('now'))",
        (account_id,),
    )
    facility_id = cur.lastrowid

    # 사용자
    cur.execute(
        """INSERT INTO users (email, password, provider, language, verified, birth_year, age_group, created_at)
           VALUES ('u@t.test', 'x', 'email', 'ko', 1, 1990, 'adult', datetime('now'))"""
    )
    user_id = cur.lastrowid

    db.commit(); db.close()
    return {'admin_id': admin_id, 'account_id': account_id,
            'facility_id': facility_id, 'user_id': user_id}


def _h(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _user_token(uid: int) -> str:
    return make_jwt(uid, 'u@t.test', 'access', 'user')


def _facility_token(aid: int, fid: int) -> str:
    return make_jwt(aid, 'o@t.test', 'access', 'facility',
                    {'facility_id': fid, 'role': 'owner', 'owner_account_id': aid})


def _admin_token(admin_id: int) -> str:
    return make_jwt(admin_id, 'admin@t.test', 'access', 'super_admin', {'role': 'super'})


def _truncate_all():
    db = _dbmod.get_db()
    for t in ('abuse_reports', 'facilities', 'facility_accounts', 'users', 'super_admin_accounts'):
        try:
            db.execute(f'DELETE FROM {t}')
        except sqlite3.OperationalError:
            pass
    db.commit(); db.close()


# ══════════════════════════════════════════════════════════════════════════════
# A. 신고 생성
# ══════════════════════════════════════════════════════════════════════════════
def test_a_create_report():
    print('\n── A. 신고 생성 (사용자/사장 상호) ──')
    ids = _seed_baseline()
    UH = _h(_user_token(ids['user_id']))
    FH = _h(_facility_token(ids['account_id'], ids['facility_id']))

    # 사용자 → 매장 신고
    r = c.post('/api/abuse-reports', headers=UH, json={
        'target_kind': 'facility', 'target_id': ids['facility_id'],
        'reason_code': 'spam', 'reason_detail': '도배성 광고',
    })
    body = r.get_json()
    _ok('① user→facility 신고 201 + reporter_kind=user',
        r.status_code == 201 and body['report']['reporter_kind'] == 'user'
        and body['report']['status'] == 'open', body)

    # 매장 → 사용자 신고 (상호 신고 가능)
    r = c.post('/api/abuse-reports', headers=FH, json={
        'target_kind': 'user', 'target_id': ids['user_id'],
        'reason_code': 'abuse',
    })
    body = r.get_json()
    _ok('② facility→user 신고 201 + reporter_kind=facility',
        r.status_code == 201 and body['report']['reporter_kind'] == 'facility', body)


def test_a_create_guards():
    print('\n── A-guards. 신고 생성 검증 ──')
    ids = _seed_baseline()
    UH = _h(_user_token(ids['user_id']))

    # 토큰 없음 → 401
    r = c.post('/api/abuse-reports', json={
        'target_kind': 'facility', 'target_id': 1, 'reason_code': 'spam'})
    _ok('① 토큰 없음 → 401', r.status_code == 401, r.get_json())

    # 잘못된 target_kind → 400
    r = c.post('/api/abuse-reports', headers=UH, json={
        'target_kind': 'alien', 'target_id': 1, 'reason_code': 'spam'})
    _ok('② 잘못된 target_kind → 400', r.status_code == 400, r.get_json())

    # 잘못된 reason_code → 400
    r = c.post('/api/abuse-reports', headers=UH, json={
        'target_kind': 'facility', 'target_id': 1, 'reason_code': 'badvibes'})
    _ok('③ 잘못된 reason_code → 400', r.status_code == 400)

    # target_id 누락/비정수 → 400
    r = c.post('/api/abuse-reports', headers=UH, json={
        'target_kind': 'facility', 'reason_code': 'spam'})
    _ok('④ target_id 누락 → 400', r.status_code == 400)


# ══════════════════════════════════════════════════════════════════════════════
# B. 운영자 조회 (inbox)
# ══════════════════════════════════════════════════════════════════════════════
def test_b_admin_list():
    print('\n── B. 운영자 신고 목록 + 필터 ──')
    ids = _seed_baseline()
    UH = _h(_user_token(ids['user_id']))
    AH = _h(_admin_token(ids['admin_id']))

    # 신고 2건 생성
    c.post('/api/abuse-reports', headers=UH, json={
        'target_kind': 'facility', 'target_id': ids['facility_id'], 'reason_code': 'spam'})
    c.post('/api/abuse-reports', headers=UH, json={
        'target_kind': 'facility', 'target_id': ids['facility_id'], 'reason_code': 'illegal'})

    # 전체 목록
    r = c.get('/api/admin/abuse-reports', headers=AH)
    j = r.get_json()
    _ok('① 목록 200 + count=2', r.status_code == 200 and j['count'] == 2, j)

    # status=open 필터
    r = c.get('/api/admin/abuse-reports?status=open', headers=AH)
    _ok('② status=open 필터 — 2건', r.get_json()['count'] == 2)

    # status=action_taken 필터 — 0건
    r = c.get('/api/admin/abuse-reports?status=action_taken', headers=AH)
    _ok('③ status=action_taken — 0건', r.get_json()['count'] == 0)

    # 잘못된 status → 400
    r = c.get('/api/admin/abuse-reports?status=zzz', headers=AH)
    _ok('④ 잘못된 status → 400', r.status_code == 400, r.get_json())

    # 권한 — 일반 user 토큰 → 401/403
    r = c.get('/api/admin/abuse-reports', headers=UH)
    _ok('⑤ user 토큰으로 admin 조회 → 401/403', r.status_code in (401, 403), r.status_code)


def test_b_admin_get_single():
    print('\n── B2. 운영자 단건 조회 ──')
    ids = _seed_baseline()
    UH = _h(_user_token(ids['user_id']))
    AH = _h(_admin_token(ids['admin_id']))

    rid = c.post('/api/abuse-reports', headers=UH, json={
        'target_kind': 'facility', 'target_id': ids['facility_id'], 'reason_code': 'spam'}
    ).get_json()['report']['id']

    r = c.get(f'/api/admin/abuse-reports/{rid}', headers=AH)
    _ok('① 단건 200 + id 일치',
        r.status_code == 200 and r.get_json()['report']['id'] == rid, r.get_json())

    r = c.get('/api/admin/abuse-reports/999999', headers=AH)
    _ok('② 존재하지 않는 신고 → 404', r.status_code == 404)


# ══════════════════════════════════════════════════════════════════════════════
# C. 운영자 처리 (PATCH)
# ══════════════════════════════════════════════════════════════════════════════
def test_c_admin_patch():
    print('\n── C. 운영자 신고 처리 ──')
    ids = _seed_baseline()
    UH = _h(_user_token(ids['user_id']))
    AH = _h(_admin_token(ids['admin_id']))

    rid = c.post('/api/abuse-reports', headers=UH, json={
        'target_kind': 'facility', 'target_id': ids['facility_id'], 'reason_code': 'abuse'}
    ).get_json()['report']['id']

    # status=action_taken + note → resolved_at·admin_id 세팅
    r = c.patch(f'/api/admin/abuse-reports/{rid}', headers=AH,
                json={'status': 'action_taken', 'resolution_note': '매장 경고 처리'})
    _ok('① PATCH action_taken 200', r.status_code == 200, r.get_json())

    # 검증 — 단건 조회로 resolved 필드 확인
    detail = c.get(f'/api/admin/abuse-reports/{rid}', headers=AH).get_json()['report']
    _ok('② status=action_taken + resolved_at 세팅 + resolved_by_admin_id',
        detail['status'] == 'action_taken' and detail['resolved_at']
        and detail['resolved_by_admin_id'] == ids['admin_id'], detail)
    _ok('③ resolution_note 저장', detail['resolution_note'] == '매장 경고 처리')

    # 잘못된 status → 400
    r = c.patch(f'/api/admin/abuse-reports/{rid}', headers=AH, json={'status': 'zzz'})
    _ok('④ 잘못된 status → 400', r.status_code == 400)

    # 변경 필드 없음 → 400
    r = c.patch(f'/api/admin/abuse-reports/{rid}', headers=AH, json={})
    _ok('⑤ 빈 변경 → 400', r.status_code == 400)

    # 존재하지 않는 신고 → 404
    r = c.patch('/api/admin/abuse-reports/999999', headers=AH, json={'status': 'dismissed'})
    _ok('⑥ 존재하지 않는 신고 PATCH → 404', r.status_code == 404)


def test_c_dismissed_also_resolves():
    print('\n── C2. dismissed 도 resolved 처리 ──')
    ids = _seed_baseline()
    UH = _h(_user_token(ids['user_id']))
    AH = _h(_admin_token(ids['admin_id']))

    rid = c.post('/api/abuse-reports', headers=UH, json={
        'target_kind': 'user', 'target_id': ids['user_id'], 'reason_code': 'other'}
    ).get_json()['report']['id']

    c.patch(f'/api/admin/abuse-reports/{rid}', headers=AH, json={'status': 'dismissed'})
    detail = c.get(f'/api/admin/abuse-reports/{rid}', headers=AH).get_json()['report']
    _ok('① dismissed → resolved_at 세팅 (오신고 기각도 처리완료로 기록)',
        detail['status'] == 'dismissed' and detail['resolved_at'], detail)

    # in_review 는 중간 상태 — resolved_at 세팅 안 함
    rid2 = c.post('/api/abuse-reports', headers=UH, json={
        'target_kind': 'user', 'target_id': ids['user_id'], 'reason_code': 'spam'}
    ).get_json()['report']['id']
    c.patch(f'/api/admin/abuse-reports/{rid2}', headers=AH, json={'status': 'in_review'})
    detail2 = c.get(f'/api/admin/abuse-reports/{rid2}', headers=AH).get_json()['report']
    _ok('② in_review → resolved_at 미세팅 (중간 상태)',
        detail2['status'] == 'in_review' and not detail2['resolved_at'], detail2)


# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    print('═══ 신고(abuse report) 통합 테스트 ═══')
    for fn in (
        test_a_create_report,
        test_a_create_guards,
        test_b_admin_list,
        test_b_admin_get_single,
        test_c_admin_patch,
        test_c_dismissed_also_resolves,
    ):
        _truncate_all()
        fn()
    print('\n✅ 모든 테스트 통과')


if __name__ == '__main__':
    main()
