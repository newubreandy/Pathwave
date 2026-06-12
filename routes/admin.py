"""Super Admin (PathWave 운영자) API.

별도 도메인 (`/api/admin/*`). 사장님(facility) / 직원(staff) / 앱 사용자(user)와
완전히 분리된 인증·권한 체계. 토큰 ``sub_type='super_admin'``.

이번 PR (#24) 스코프: 인증 기반만. 비콘 인벤토리·사장 승인·결제 정산 등은 후속.

엔드포인트
---------
- POST /api/admin/login      이메일/비밀번호 로그인
- GET  /api/admin/me         본인 정보 조회
- POST /api/admin/refresh    refresh 토큰 → access 새로 발급
"""
from datetime import datetime, timedelta
import os

import bcrypt
import jwt
from flask import Blueprint, request, jsonify, g

from models.database import get_db
from models.payment_provider import get_payment_provider
from models.rate_limit import limiter
from routes.auth import (
    SECRET_KEY, ACCESS_TTL_MIN, REFRESH_TTL_DAY,
    make_jwt, issue_token_pair,
    require_super_admin,
)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def _row_to_admin(row) -> dict:
    return {
        'id':            row['id'],
        'email':         row['email'],
        'name':          row['name'],
        'role':          row['role'],
        'active':        bool(row['active']),
        'last_login_at': row['last_login_at'],
        'created_at':    row['created_at'],
    }


@admin_bp.route('/login', methods=['POST'])
@limiter.limit('10 per minute; 100 per hour')
def admin_login():
    """Super Admin 로그인 — sub_type='super_admin' 토큰 발급."""
    data = request.get_json(silent=True) or {}
    email    = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not email or not password:
        return jsonify({'success': False,
                        'message': '이메일과 비밀번호를 입력해 주세요.'}), 400

    db = get_db()
    row = db.execute(
        "SELECT * FROM super_admin_accounts WHERE email=? AND active=1",
        (email,)
    ).fetchone()
    if not row or not bcrypt.checkpw(password.encode(), row['password'].encode()):
        if db: db.close()
        return jsonify({'success': False,
                        'message': '이메일 또는 비밀번호가 올바르지 않습니다.'}), 401

    db.execute(
        "UPDATE super_admin_accounts SET last_login_at=datetime('now') WHERE id=?",
        (row['id'],)
    )
    db.commit()
    db.close()

    extra = {'role': row['role']}
    return jsonify({
        'success': True,
        'message': '로그인 성공!',
        **issue_token_pair(row['id'], email, sub_type='super_admin', extra_claims=extra),
        'admin': _row_to_admin(row),
    })


@admin_bp.route('/me', methods=['GET'])
@require_super_admin()
def admin_me():
    """본인(super admin) 정보 조회."""
    db = get_db()
    row = db.execute(
        "SELECT * FROM super_admin_accounts WHERE id=?", (g.auth['user_id'],)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({'success': False, 'message': '계정을 찾을 수 없습니다.'}), 404
    return jsonify({'success': True, 'admin': _row_to_admin(row)})


# A-024 — 운영자 본인 비밀번호 변경 (B/D 시리즈)
@admin_bp.route('/change-password', methods=['POST'])
@require_super_admin()
@limiter.limit('5 per minute')
def admin_change_password():
    """슈퍼어드민 본인 비밀번호 변경.

    body: {current_password, new_password}
    - 현재 비번 재확인 → 신규 비번 bcrypt 해시 저장
    - 부트스트랩 초기 비번 사용 중인 경우 운영 환경 진입 전 강제 변경 가능
    """
    from routes.auth import password_complexity_error
    data = request.get_json(silent=True) or {}
    cur  = data.get('current_password') or ''
    new  = data.get('new_password') or ''
    if not cur or not new:
        return jsonify({'success': False,
                        'message': '현재/신규 비밀번호 모두 입력해 주세요.'}), 400
    if cur == new:
        return jsonify({'success': False,
                        'message': '새 비밀번호가 기존과 같습니다.'}), 400
    pw_err = password_complexity_error(new)
    if pw_err:
        return jsonify({'success': False, 'message': pw_err}), 400

    db = get_db()
    row = db.execute(
        "SELECT id, password FROM super_admin_accounts WHERE id=? AND active=1",
        (g.auth['user_id'],)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '계정을 찾을 수 없습니다.'}), 404
    if not bcrypt.checkpw(cur.encode(), row['password'].encode()):
        db.close()
        return jsonify({'success': False,
                        'message': '현재 비밀번호가 일치하지 않습니다.'}), 401
    hashed = bcrypt.hashpw(new.encode(), bcrypt.gensalt()).decode()
    db.execute(
        "UPDATE super_admin_accounts SET password=? WHERE id=?",
        (hashed, row['id'])
    )
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': '비밀번호가 변경되었습니다.'})


# A-023 — 외부 서비스 환경 점검 (외부 키 미설정 경고)
@admin_bp.route('/system/health', methods=['GET'])
@require_super_admin()
def admin_system_health():
    """외부 서비스 (Firebase/DeepL/SendGrid/Toss 등) 키 설정 + 모드 진단.

    각 항목: {key, configured: bool, mode: 'live'|'stub'|'missing', detail}
    - configured: 환경변수에 키가 설정되어 있는가
    - mode: live (실 키) / stub (개발 모드) / missing (미설정)
    - 실제 ping 은 R2/R3 단계에서 추가
    """
    def _check(env_name, *, label, stub_default=False):
        val = os.environ.get(env_name, '').strip()
        if val and val not in ('dummy', 'placeholder', 'stub'):
            return {'key': env_name, 'label': label,
                    'configured': True, 'mode': 'live',
                    'detail': f'설정됨 ({len(val)}자)'}
        if stub_default:
            return {'key': env_name, 'label': label,
                    'configured': False, 'mode': 'stub',
                    'detail': '개발 모드 (stub 동작)'}
        return {'key': env_name, 'label': label,
                'configured': False, 'mode': 'missing',
                'detail': '미설정 — 운영 전 등록 필요'}

    services = [
        _check('FIREBASE_CREDENTIALS_PATH',
               label='Firebase (FCM + 소셜)',  stub_default=True),
        _check('DEEPL_API_KEY',
               label='DeepL (번역)',           stub_default=True),
        _check('ANTHROPIC_API_KEY',
               label='Anthropic (요약/번역 백업)', stub_default=True),
        _check('SENDGRID_API_KEY',
               label='SendGrid (이메일)',      stub_default=True),
        _check('TOSS_API_KEY',
               label='토스페이먼츠 (결제)',     stub_default=True),
        _check('SENTRY_DSN',
               label='Sentry (에러 모니터링)',  stub_default=True),
        _check('GOOGLE_MAPS_API_KEY',
               label='Google Maps (매장 위치)', stub_default=True),
        _check('BOOTSTRAP_SUPER_ADMIN_EMAIL',
               label='부트스트랩 슈퍼어드민',    stub_default=False),
    ]
    summary = {
        'live':    sum(1 for s in services if s['mode'] == 'live'),
        'stub':    sum(1 for s in services if s['mode'] == 'stub'),
        'missing': sum(1 for s in services if s['mode'] == 'missing'),
    }
    return jsonify({'success': True,
                    'services': services,
                    'summary':  summary})


# A-015 — 쿠폰 통계 (admin)
@admin_bp.route('/coupons', methods=['GET'])
@require_super_admin()
def admin_list_coupons():
    """전체 쿠폰 목록 + 발급/사용/만료 집계.

    ?status=all|active|used|expired (기본 all)
    ?facility_id=N 으로 매장 한정 가능.
    """
    status = (request.args.get('status') or 'all').strip().lower()
    facility_id = request.args.get('facility_id', type=int)
    db = get_db()
    try:
        where, params = [], []
        if facility_id:
            where.append("c.facility_id=?"); params.append(facility_id)
        where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''
        rows = db.execute(
            f"""SELECT c.*, f.name AS facility_name,
                       u.email AS user_email
                FROM coupons c
                LEFT JOIN facilities f ON c.facility_id = f.id
                LEFT JOIN users      u ON c.user_id     = u.id
                {where_sql}
                ORDER BY c.id DESC""",
            params,
        ).fetchall()

        def _status(r):
            if r['used']:
                return 'used'
            if r['expires_at']:
                try:
                    if datetime.fromisoformat(r['expires_at']) < datetime.utcnow():
                        return 'expired'
                except ValueError:
                    pass
            return 'active'

        coupons = []
        for r in rows:
            coupons.append({
                'id':            r['id'],
                'facility_id':   r['facility_id'],
                'facility_name': r['facility_name'],
                'user_id':       r['user_id'],
                'user_email':    r['user_email'],
                'title':         r['title'],
                'benefit':       r['benefit'],
                'expires_at':    r['expires_at'],
                'used':          bool(r['used']),
                'used_at':       r['used_at'],
                'created_at':    r['created_at'],
                'status':        _status(r),
            })
        if status != 'all':
            if status not in ('active', 'used', 'expired'):
                return jsonify({'success': False,
                                'message': "status는 active/used/expired/all 중 하나."}), 400
            coupons = [c for c in coupons if c['status'] == status]

        summary = {
            'issued':  len(coupons),
            'used':    sum(1 for c in coupons if c['status'] == 'used'),
            'active':  sum(1 for c in coupons if c['status'] == 'active'),
            'expired': sum(1 for c in coupons if c['status'] == 'expired'),
        }
        return jsonify({'success': True,
                        'count':   len(coupons),
                        'coupons': coupons,
                        'summary': summary})
    finally:
        db.close()


# A-009 — 직원 모니터링 (admin)
@admin_bp.route('/staff/reports', methods=['GET'])
@require_super_admin()
def admin_staff_reports():
    """전체 staff_accounts + 매장 매핑 + 가입/활동 요약.

    각 row: {id, email, role, name, phone, facility_id, facility_name,
            invitation_status, created_at}
    """
    db = get_db()
    try:
        rows = db.execute(
            """SELECT s.id, s.email, s.role, s.name, s.phone,
                      s.facility_account_id, s.created_at,
                      fa.email AS owner_email,
                      f.id   AS facility_id,
                      f.name AS facility_name,
                      i.status AS invitation_status,
                      i.accepted_at
                 FROM staff_accounts s
                 LEFT JOIN facility_accounts fa ON s.facility_account_id = fa.id
                 LEFT JOIN facilities         f ON f.owner_id = s.facility_account_id
                 LEFT JOIN staff_invitations  i ON s.invitation_id = i.id
                 ORDER BY s.id DESC"""
        ).fetchall()
        reports = [{
            'id':            r['id'],
            'email':         r['email'],
            'role':          r['role'],
            'name':          r['name'],
            'phone':         r['phone'],
            'facility_id':   r['facility_id'],
            'facility_name': r['facility_name'],
            'owner_email':   r['owner_email'],
            'invitation_status': r['invitation_status'],
            'accepted_at':   r['accepted_at'],
            'created_at':    r['created_at'],
        } for r in rows]

        summary = {
            'total':     len(reports),
            'by_role':   {role: sum(1 for x in reports if x['role'] == role)
                          for role in ('owner', 'admin', 'staff')},
        }
        return jsonify({'success': True,
                        'count':    len(reports),
                        'reports':  reports,
                        'summary':  summary})
    finally:
        db.close()


# D-4-pre — 비용 모니터링 + 슈퍼어드민 알림
@admin_bp.route('/cost-monitor', methods=['GET'])
@require_super_admin()
def admin_cost_monitor():
    """외부 AI API 월 비용 + 임계점 + 활성 알림.

    ?year=YYYY · ?month=MM (기본 = 현재 월)
    """
    from models.ai_cost import (
        month_total_usd, threshold_usd, krw_per_usd,
        usd_to_krw, compute_alerts,
    )
    now = datetime.utcnow()
    year  = request.args.get('year',  type=int) or now.year
    month = request.args.get('month', type=int) or now.month
    db = get_db()
    try:
        agg = month_total_usd(db, year, month)
        th_usd = threshold_usd()
        pct = round(agg['total_usd'] / th_usd * 100, 2) if th_usd > 0 else 0.0
        alerts = compute_alerts(agg['total_usd'])
        return jsonify({
            'success':   True,
            'year':      year,
            'month':     month,
            'threshold': {
                'usd':         th_usd,
                'krw':         usd_to_krw(th_usd),
                'krw_per_usd': krw_per_usd(),
            },
            'monthly':   agg,
            'percent':   pct,
            'alerts':    alerts,
            'translation_blocked': agg['total_usd'] >= th_usd,
        })
    finally:
        db.close()


@admin_bp.route('/critical-alerts', methods=['GET'])
@require_super_admin()
def admin_critical_alerts():
    """현재 슈퍼어드민에게 보여줄 활성 알림 (snooze 안 된 것만).

    admin-web 이 매 1분 polling. 활성 알림 = 임계점 도달 + 본인 snooze 만료.
    """
    from models.ai_cost import month_total_usd, compute_alerts
    admin_id = g.auth['user_id']
    now = datetime.utcnow()
    db = get_db()
    try:
        agg = month_total_usd(db, now.year, now.month)
        alerts = compute_alerts(agg['total_usd'])

        # snooze 적용
        snoozes = {
            r['alert_id']: r['snoozed_until']
            for r in db.execute(
                """SELECT alert_id, snoozed_until FROM admin_alert_dismissals
                    WHERE admin_id=? AND snoozed_until > ?""",
                (admin_id, now.isoformat())
            ).fetchall()
        }
        active = []
        for a in alerts:
            if a.get('kind') != 'popup':
                continue  # 배지 only 알림은 critical 응답에 안 포함
            if a['id'] in snoozes:
                continue
            active.append(a)
        return jsonify({'success': True, 'alerts': active})
    finally:
        db.close()


@admin_bp.route('/alerts/<alert_id>/dismiss', methods=['POST'])
@require_super_admin()
def admin_dismiss_alert(alert_id: str):
    """알림 snooze (본인만). body: {hours: int}.

    snooze_hours 는 compute_alerts 에서 정의 — 50%: N/A, 80%: 24h, 100%: 2h.
    클라이언트가 명시한 hours 가 우선 적용.
    """
    if not alert_id or len(alert_id) > 64:
        return jsonify({'success': False, 'message': '알림 ID 가 유효하지 않습니다.'}), 400
    data = request.get_json(silent=True) or {}
    try:
        hours = int(data.get('hours') or 0)
    except (TypeError, ValueError):
        hours = 0
    if hours <= 0 or hours > 168:  # 최대 7일
        return jsonify({'success': False,
                        'message': 'hours 는 1~168 정수.'}), 400

    admin_id = g.auth['user_id']
    until = (datetime.utcnow() + timedelta(hours=hours)).isoformat()
    db = get_db()
    try:
        # 같은 admin_id + alert_id 가 이미 있으면 갱신
        existing = db.execute(
            "SELECT id FROM admin_alert_dismissals WHERE admin_id=? AND alert_id=?",
            (admin_id, alert_id),
        ).fetchone()
        if existing:
            db.execute(
                "UPDATE admin_alert_dismissals SET snoozed_until=? WHERE id=?",
                (until, existing['id']),
            )
        else:
            db.execute(
                """INSERT INTO admin_alert_dismissals (admin_id, alert_id, snoozed_until)
                   VALUES (?,?,?)""",
                (admin_id, alert_id, until),
            )
        db.commit()
        return jsonify({'success': True, 'snoozed_until': until})
    finally:
        db.close()


# A-022 — 회원(사용자) 관리
@admin_bp.route('/users', methods=['GET'])
@require_super_admin()
def admin_list_users():
    """사용자 목록. 검색/필터/페이지네이션.

    ?q=email_prefix · ?status=active|deleted|all · ?provider=email|google|kakao|...
    ?age_group=adult|minor · ?limit=50 (기본, 최대 500) · ?offset=0
    """
    q          = (request.args.get('q') or '').strip()
    status     = (request.args.get('status') or 'active').strip().lower()
    provider   = (request.args.get('provider') or '').strip().lower()
    age_group  = (request.args.get('age_group') or '').strip().lower()
    limit      = min(max(request.args.get('limit', type=int) or 50, 1), 500)
    offset     = max(request.args.get('offset', type=int) or 0, 0)

    if status not in ('active', 'deleted', 'all'):
        return jsonify({'success': False,
                        'message': "status는 active/deleted/all 중 하나."}), 400

    db = get_db()
    try:
        where, params = [], []
        if status == 'active':
            where.append('u.deleted_at IS NULL')
        elif status == 'deleted':
            where.append('u.deleted_at IS NOT NULL')
        if provider:
            where.append('u.provider=?'); params.append(provider)
        if age_group:
            where.append('u.age_group=?'); params.append(age_group)
        if q:
            where.append('u.email LIKE ?'); params.append(f'%{q}%')
        where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''

        total = db.execute(
            f'SELECT COUNT(*) AS n FROM users u {where_sql}',
            params,
        ).fetchone()['n']

        rows = db.execute(
            f"""SELECT u.id, u.email, u.provider, u.language,
                       u.birth_year, u.age_group,
                       u.deleted_at, u.created_at,
                       u.invited_via_code,
                       (SELECT COUNT(*) FROM abuse_reports
                          WHERE target_kind='user' AND target_id=u.id) AS reported_count,
                       (SELECT COUNT(*) FROM chat_rooms
                          WHERE user_id=u.id) AS chat_rooms_count
                  FROM users u
                  {where_sql}
                  ORDER BY u.id DESC
                  LIMIT ? OFFSET ?""",
            [*params, limit, offset],
        ).fetchall()
        users = [{
            'id':               r['id'],
            'email':            r['email'],
            'provider':         r['provider'],
            'language':         r['language'],
            'birth_year':       r['birth_year'],
            'age_group':        r['age_group'],
            'deleted_at':       r['deleted_at'],
            'created_at':       r['created_at'],
            'invited_via_code': r['invited_via_code'],
            'reported_count':   r['reported_count'],
            'chat_rooms_count': r['chat_rooms_count'],
        } for r in rows]
        return jsonify({'success': True,
                        'total':  total,
                        'limit':  limit,
                        'offset': offset,
                        'users':  users})
    finally:
        db.close()


@admin_bp.route('/users/<int:uid>/force-delete', methods=['POST'])
@require_super_admin()
def admin_force_delete_user(uid: int):
    """운영자 강제 탈퇴 (예: 신고 누적 / 부정 이용 확정).

    DELETE /api/auth/me 와 동일한 soft-delete + 이메일 anonymize 적용.
    body: {reason?: str} — 감사 로그용.
    """
    data = request.get_json(silent=True) or {}
    reason = (data.get('reason') or '').strip() or 'admin force-delete'

    db = get_db()
    try:
        row = db.execute(
            'SELECT id, email, deleted_at FROM users WHERE id=?', (uid,)
        ).fetchone()
        if not row:
            return jsonify({'success': False, 'message': '사용자를 찾을 수 없습니다.'}), 404
        if row['deleted_at']:
            return jsonify({'success': False, 'message': '이미 탈퇴된 사용자입니다.'}), 409
        # soft delete + 이메일 익명화 (재가입 시 UNIQUE 충돌 방지)
        anonymized = f'{uid}+deleted@deleted.local'
        db.execute(
            "UPDATE users SET deleted_at=datetime('now'), email=? WHERE id=?",
            (anonymized, uid),
        )
        # 즉시 알림 차단
        db.execute('DELETE FROM push_tokens WHERE user_id=?', (uid,))
        db.commit()
        return jsonify({'success': True,
                        'message': '강제 탈퇴 처리되었습니다.',
                        'reason':  reason})
    finally:
        db.close()


# A-010 — 채팅 모니터링 (admin)
@admin_bp.route('/chat/rooms', methods=['GET'])
@require_super_admin()
def admin_chat_rooms():
    """전체 chat_rooms + 매장명/사용자 이메일 + 메시지 수 + 마지막 메시지 시각.

    ?limit=N (기본 100, 최대 500)
    """
    limit = min(max(request.args.get('limit', type=int) or 100, 1), 500)
    db = get_db()
    try:
        rows = db.execute(
            """SELECT cr.id, cr.facility_id, cr.user_id, cr.last_message_at,
                      cr.created_at,
                      f.name  AS facility_name,
                      u.email AS user_email,
                      (SELECT COUNT(*) FROM chat_messages WHERE room_id=cr.id)
                          AS message_count
                 FROM chat_rooms cr
                 LEFT JOIN facilities f ON cr.facility_id = f.id
                 LEFT JOIN users      u ON cr.user_id     = u.id
                 ORDER BY COALESCE(cr.last_message_at, cr.created_at) DESC
                 LIMIT ?""",
            (limit,)
        ).fetchall()
        rooms = [{
            'id':              r['id'],
            'facility_id':     r['facility_id'],
            'facility_name':   r['facility_name'],
            'user_id':         r['user_id'],
            'user_email':      r['user_email'],
            'message_count':   r['message_count'],
            'last_message_at': r['last_message_at'],
            'created_at':      r['created_at'],
        } for r in rows]
        return jsonify({'success': True,
                        'count': len(rooms),
                        'rooms': rooms})
    finally:
        db.close()


@admin_bp.route('/refresh', methods=['POST'])
def admin_refresh():
    """Super Admin refresh — 다른 sub_type 토큰은 거부."""
    data = request.get_json(silent=True) or {}
    rt   = (data.get('refresh_token') or '').strip()
    if not rt:
        return jsonify({'success': False, 'message': 'refresh_token이 필요합니다.'}), 400
    try:
        payload = jwt.decode(rt, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': '리프레시 토큰이 만료되었습니다.'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': '유효하지 않은 리프레시 토큰입니다.'}), 401
    if payload.get('kind') != 'refresh':
        return jsonify({'success': False, 'message': '리프레시 토큰이 아닙니다.'}), 401
    if payload.get('sub_type') != 'super_admin':
        return jsonify({'success': False,
                        'message': 'Super Admin 토큰이 아닙니다.'}), 401

    db = get_db()
    row = db.execute(
        "SELECT id, email, role FROM super_admin_accounts WHERE id=? AND active=1",
        (payload['user_id'],)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({'success': False,
                        'message': '계정을 찾을 수 없거나 비활성화됨.'}), 401

    extra = {'role': row['role']}
    return jsonify({
        'success': True,
        **issue_token_pair(row['id'], row['email'], sub_type='super_admin',
                           extra_claims=extra),
    })


# ════ 비콘 인벤토리 관리 (FSC-BP108B 등 하드웨어 입고/할당) ════════════════

import re as _re

# 8-4-4-4-12 대시 포맷, 또는 32자리 대시 없는 포맷 둘 다 허용 (FSC-BP108B 펌웨어 케이스 대비).
_UUID_RE = _re.compile(
    r'^([0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'
    r'|[0-9A-Fa-f]{32})$'
)
_BEACON_STATUSES = {'inventory', 'active', 'inactive', 'lost'}


def _row_to_beacon(row) -> dict:
    keys = row.keys()
    return {
        'id':           row['id'],
        'serial_no':    row['serial_no'],
        'uuid':         row['uuid'],
        'major':        row['major'] if 'major' in keys else None,
        'minor':        row['minor'] if 'minor' in keys else None,
        'facility_id':  row['facility_id'],
        'facility_name': row['facility_name'] if 'facility_name' in keys else None,
        'status':       row['status'],
        'battery_pct':  row['battery_pct'],
        'firmware_ver': row['firmware_ver'],
        # P15 — 비콘 role (wifi 핸드오프 | cashier 계산대 트리거).
        'role':         row['role'] if 'role' in keys else 'wifi',
        'created_at':   row['created_at'],        # 비콘 입고일
        # P22 후속 (2026-05-27): 매장 서비스 시작일 + 설치위치 + 신청인 이메일.
        'assigned_at':    row['assigned_at']    if 'assigned_at'    in keys else None,
        'location_label': row['location_label'] if 'location_label' in keys else None,
        'owner_email':    row['owner_email']    if 'owner_email'    in keys else None,
    }


@admin_bp.route('/beacons/import', methods=['POST'])
@require_super_admin()
def import_beacons():
    """비콘 bulk 입고. body: {beacons: [{serial_no, uuid, firmware_ver?}]}.

    각 row는 ``status='inventory'``로 들어감. SN/UUID 중복은 422의 errors[]에
    상세 보고하고 나머지는 정상 처리(부분 성공).
    """
    data = request.get_json(silent=True) or {}
    items = data.get('beacons') or []
    if not isinstance(items, list) or not items:
        return jsonify({'success': False,
                        'message': 'beacons 배열이 필요합니다.'}), 400
    if len(items) > 1000:
        return jsonify({'success': False,
                        'message': '한 번에 최대 1000개까지.'}), 400

    db = get_db()
    imported, errors = [], []
    for idx, item in enumerate(items):
        sn   = (item.get('serial_no') or '').strip()
        uuid = (item.get('uuid') or '').strip().upper()
        fw   = (item.get('firmware_ver') or '').strip() or None
        major = item.get('major')
        minor = item.get('minor')
        # Phase C — Major/Minor 는 0~65535 정수 (iBeacon 표준). 인벤토리 단계에서는 선택.
        for nm, val in (('major', major), ('minor', minor)):
            if val is None or val == '':
                continue
            try:
                v = int(val)
            except (TypeError, ValueError):
                errors.append({'index': idx, 'serial_no': sn, 'uuid': uuid,
                               'error': f'invalid_{nm}'})
                val = -1
            else:
                if not 0 <= v <= 65535:
                    errors.append({'index': idx, 'serial_no': sn, 'uuid': uuid,
                                   'error': f'{nm}_out_of_range'})
                    val = -1
                else:
                    if nm == 'major': major = v
                    else: minor = v
        if isinstance(major, str): major = None
        if isinstance(minor, str): minor = None
        if not sn or not _UUID_RE.match(uuid):
            errors.append({'index': idx, 'serial_no': sn, 'uuid': uuid,
                           'error': 'invalid_format'})
            continue
        try:
            cur = db.execute(
                """INSERT INTO beacons
                     (serial_no, uuid, major, minor, firmware_ver, status)
                   VALUES (?,?,?,?,?,'inventory')""",
                (sn, uuid, major if isinstance(major, int) else None,
                 minor if isinstance(minor, int) else None, fw)
            )
            imported.append({'id': cur.lastrowid, 'serial_no': sn, 'uuid': uuid,
                             'major': major if isinstance(major, int) else None,
                             'minor': minor if isinstance(minor, int) else None})
        except Exception as e:
            errors.append({'index': idx, 'serial_no': sn, 'uuid': uuid,
                           'error': str(e)})
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'imported_count': len(imported),
                    'imported': imported,
                    'errors': errors}), 201


@admin_bp.route('/beacons', methods=['GET'])
@require_super_admin()
def list_beacons():
    """전체 비콘. 필터: ``?status``, ``?facility_id``, ``?q`` (serial 부분 일치)."""
    status = (request.args.get('status') or '').strip()
    facility_id = request.args.get('facility_id', type=int)
    q = (request.args.get('q') or '').strip()

    db = get_db()
    # P22 후속 (2026-05-27): owner_email + location_label 응답 포함.
    sql = """SELECT b.*, f.name AS facility_name, fa.email AS owner_email
             FROM beacons b
             LEFT JOIN facilities f ON b.facility_id = f.id
             LEFT JOIN facility_accounts fa ON f.owner_id = fa.id"""
    where, params = [], []
    if status:
        if status not in _BEACON_STATUSES:
            db.close()
            return jsonify({'success': False,
                            'message': f"status는 {sorted(_BEACON_STATUSES)} 중 하나여야 합니다."}), 400
        where.append("b.status=?"); params.append(status)
    if facility_id:
        where.append("b.facility_id=?"); params.append(facility_id)
    if q:
        # P22 후속: 시리얼 / 매장명 / 신청인 이메일 통합 검색 (UUID 제외 — 사용자 정책)
        where.append("(b.serial_no LIKE ? OR f.name LIKE ? OR fa.email LIKE ?)")
        params.extend([f'%{q}%', f'%{q}%', f'%{q}%'])
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY b.id DESC"
    rows = db.execute(sql, params).fetchall()
    db.close()
    return jsonify({'success': True,
                    'count': len(rows),
                    'beacons': [_row_to_beacon(r) for r in rows]})


@admin_bp.route('/beacons/<int:bid>', methods=['PATCH'])
@require_super_admin()
def update_beacon(bid):
    """펌웨어/배터리/상태/UUID 갱신."""
    data = request.get_json(silent=True) or {}
    db = get_db()
    row = db.execute("SELECT * FROM beacons WHERE id=?", (bid,)).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '비콘을 찾을 수 없습니다.'}), 404

    sets, vals = [], []
    if 'firmware_ver' in data:
        sets.append('firmware_ver=?')
        vals.append((data['firmware_ver'] or '').strip() or None)
    if 'battery_pct' in data:
        bp = data['battery_pct']
        if not isinstance(bp, int) or not 0 <= bp <= 100:
            db.close()
            return jsonify({'success': False,
                            'message': 'battery_pct는 0~100 정수여야 합니다.'}), 400
        sets.append('battery_pct=?'); vals.append(bp)
    if 'status' in data:
        s = data['status']
        if s not in _BEACON_STATUSES:
            db.close()
            return jsonify({'success': False,
                            'message': f"status는 {sorted(_BEACON_STATUSES)} 중 하나여야 합니다."}), 400
        sets.append('status=?'); vals.append(s)
    if 'uuid' in data:
        uu = (data['uuid'] or '').strip().upper()
        if not _UUID_RE.match(uu):
            db.close()
            return jsonify({'success': False,
                            'message': 'uuid 형식이 올바르지 않습니다.'}), 400
        sets.append('uuid=?'); vals.append(uu)
    # P15b — 비콘 role (wifi 핸드오프 | cashier 계산대 트리거)
    if 'role' in data:
        rv = (data['role'] or '').strip().lower()
        if rv not in ('wifi', 'cashier'):
            db.close()
            return jsonify({'success': False,
                            'message': "role 은 'wifi' 또는 'cashier'."}), 400
        sets.append('role=?'); vals.append(rv)
    # P22 후속 (2026-05-27): 설치위치 라벨 (예: "입구", "객실 101", "스파").
    if 'location_label' in data:
        ll = (data['location_label'] or '').strip()
        # 64자 제한, 빈 문자열은 NULL 처리
        ll = ll[:64] if ll else None
        sets.append('location_label=?'); vals.append(ll)
    if not sets:
        db.close()
        return jsonify({'success': False, 'message': '수정할 필드가 없습니다.'}), 400

    vals.append(bid)
    db.execute(f"UPDATE beacons SET {', '.join(sets)} WHERE id=?", vals)
    new_row = db.execute(
        """SELECT b.*, f.name AS facility_name, fa.email AS owner_email
           FROM beacons b
           LEFT JOIN facilities f ON b.facility_id=f.id
           LEFT JOIN facility_accounts fa ON f.owner_id=fa.id
           WHERE b.id=?""", (bid,)
    ).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True, 'beacon': _row_to_beacon(new_row)})


@admin_bp.route('/beacons/<int:bid>/assign', methods=['POST'])
@require_super_admin()
def assign_beacon(bid):
    """매장에 비콘 직접 할당. body: {facility_id}.

    inventory 또는 inactive 상태에서 active로 전환 + facility_id 설정.
    """
    data = request.get_json(silent=True) or {}
    facility_id = data.get('facility_id')
    if not isinstance(facility_id, int) or facility_id < 1:
        return jsonify({'success': False, 'message': 'facility_id가 필요합니다.'}), 400

    db = get_db()
    beacon = db.execute("SELECT * FROM beacons WHERE id=?", (bid,)).fetchone()
    if not beacon:
        db.close()
        return jsonify({'success': False, 'message': '비콘을 찾을 수 없습니다.'}), 404
    if beacon['status'] == 'active' and beacon['facility_id'] == facility_id:
        db.close()
        return jsonify({'success': False, 'message': '이미 해당 매장에 할당된 비콘입니다.'}), 409
    if beacon['status'] == 'lost':
        db.close()
        return jsonify({'success': False,
                        'message': "분실 상태 비콘은 먼저 PATCH로 status='inventory'로 복구해 주세요."}), 409
    fac = db.execute(
        "SELECT id FROM facilities WHERE id=? AND active=1", (facility_id,)
    ).fetchone()
    if not fac:
        db.close()
        return jsonify({'success': False, 'message': '매장을 찾을 수 없거나 비활성입니다.'}), 404

    # P22 후속 (2026-05-27): 매장 서비스 시작일 (assigned_at) 자동 기록.
    db.execute(
        """UPDATE beacons
              SET facility_id=?, status='active',
                  assigned_at=COALESCE(assigned_at, datetime('now'))
            WHERE id=?""",
        (facility_id, bid)
    )
    db.commit()
    new_row = db.execute(
        """SELECT b.*, f.name AS facility_name, fa.email AS owner_email
           FROM beacons b
           LEFT JOIN facilities f ON b.facility_id=f.id
           LEFT JOIN facility_accounts fa ON f.owner_id=fa.id
           WHERE b.id=?""", (bid,)
    ).fetchone()
    db.close()
    return jsonify({'success': True, 'beacon': _row_to_beacon(new_row)})


# ════ 사장 가입 승인 / 정지 ═══════════════════════════════════════════════

def _row_to_facility_account(row) -> dict:
    return {
        'id':                   row['id'],
        'business_no':          row['business_no'],
        'company_name':         row['company_name'],
        'email':                row['email'],
        'phone':                row['phone'],
        'manager_name':         row['manager_name'],
        'manager_phone':        row['manager_phone'],
        'manager_email':        row['manager_email'],
        'status':               row['status'] or 'pending',
        'business_doc_url':     row['business_doc_url'],
        'approved_at':          row['approved_at'],
        'approved_by_admin_id': row['approved_by_admin_id'],
        'suspended_at':         row['suspended_at'],
        'suspended_reason':     row['suspended_reason'],
        'created_at':           row['created_at'],
    }


@admin_bp.route('/facility-accounts', methods=['GET'])
@require_super_admin()
def list_facility_accounts():
    """사장 계정 목록. ?status=pending|verified|suspended|all (기본 all)."""
    status = (request.args.get('status') or 'all').strip()
    q = (request.args.get('q') or '').strip()
    db = get_db()
    sql = "SELECT * FROM facility_accounts"
    where, params = [], []
    if status != 'all':
        where.append("(status=? OR (status IS NULL AND ?='pending'))")
        params.extend([status, status])
    if q:
        where.append("(email LIKE ? OR company_name LIKE ? OR business_no LIKE ?)")
        like = f'%{q}%'
        params.extend([like, like, like])
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC"
    rows = db.execute(sql, params).fetchall()
    db.close()
    return jsonify({'success': True,
                    'count': len(rows),
                    'accounts': [_row_to_facility_account(r) for r in rows]})


@admin_bp.route('/facility-accounts/<int:aid>', methods=['GET'])
@require_super_admin()
def get_facility_account(aid):
    db = get_db()
    row = db.execute("SELECT * FROM facility_accounts WHERE id=?", (aid,)).fetchone()
    db.close()
    if not row:
        return jsonify({'success': False, 'message': '계정을 찾을 수 없습니다.'}), 404
    return jsonify({'success': True, 'account': _row_to_facility_account(row)})


@admin_bp.route('/facility-accounts/<int:aid>/verify', methods=['POST'])
@require_super_admin()
def verify_facility_account(aid):
    """가입 승인 — pending → verified."""
    admin_id = g.auth['user_id']
    db = get_db()
    row = db.execute(
        "SELECT id, status FROM facility_accounts WHERE id=?", (aid,)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '계정을 찾을 수 없습니다.'}), 404
    if row['status'] == 'verified':
        db.close()
        return jsonify({'success': False, 'message': '이미 승인된 계정입니다.'}), 409

    db.execute(
        """UPDATE facility_accounts
             SET status='verified', verified=1,
                 approved_at=datetime('now'),
                 approved_by_admin_id=?,
                 suspended_at=NULL, suspended_reason=NULL
           WHERE id=?""",
        (admin_id, aid)
    )
    new_row = db.execute("SELECT * FROM facility_accounts WHERE id=?", (aid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '계정이 승인되었습니다.',
                    'account': _row_to_facility_account(new_row)})


@admin_bp.route('/facility-accounts/<int:aid>/suspend', methods=['POST'])
@require_super_admin()
def suspend_facility_account(aid):
    """계정 정지 — verified|pending → suspended. body: {reason?}."""
    data = request.get_json(silent=True) or {}
    reason = (data.get('reason') or '').strip() or None
    db = get_db()
    row = db.execute("SELECT id, status FROM facility_accounts WHERE id=?", (aid,)).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '계정을 찾을 수 없습니다.'}), 404
    if row['status'] == 'suspended':
        db.close()
        return jsonify({'success': False, 'message': '이미 정지된 계정입니다.'}), 409
    db.execute(
        """UPDATE facility_accounts
             SET status='suspended', verified=0,
                 suspended_at=datetime('now'),
                 suspended_reason=?
           WHERE id=?""",
        (reason, aid)
    )
    new_row = db.execute("SELECT * FROM facility_accounts WHERE id=?", (aid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '계정이 정지되었습니다.',
                    'account': _row_to_facility_account(new_row)})


@admin_bp.route('/facility-accounts/<int:aid>/reactivate', methods=['POST'])
@require_super_admin()
def reactivate_facility_account(aid):
    """정지 해제 — suspended → verified."""
    db = get_db()
    row = db.execute("SELECT id, status FROM facility_accounts WHERE id=?", (aid,)).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '계정을 찾을 수 없습니다.'}), 404
    if row['status'] != 'suspended':
        db.close()
        return jsonify({'success': False,
                        'message': "정지 상태가 아닙니다."}), 409
    db.execute(
        """UPDATE facility_accounts
             SET status='verified', verified=1,
                 suspended_at=NULL, suspended_reason=NULL
           WHERE id=?""", (aid,)
    )
    new_row = db.execute("SELECT * FROM facility_accounts WHERE id=?", (aid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True, 'account': _row_to_facility_account(new_row)})


# ════ 대시보드 통계 ═════════════════════════════════════════════════════════

@admin_bp.route('/stats/overview', methods=['GET'])
@require_super_admin()
def stats_overview():
    """전사 KPI 한 번에. 대시보드 카드용."""
    db = get_db()
    cards = {
        'total_facility_accounts': db.execute(
            "SELECT COUNT(*) AS n FROM facility_accounts").fetchone()['n'],
        'pending_facility_accounts': db.execute(
            "SELECT COUNT(*) AS n FROM facility_accounts WHERE status='pending'").fetchone()['n'],
        'verified_facility_accounts': db.execute(
            "SELECT COUNT(*) AS n FROM facility_accounts WHERE status='verified'").fetchone()['n'],
        'suspended_facility_accounts': db.execute(
            "SELECT COUNT(*) AS n FROM facility_accounts WHERE status='suspended'").fetchone()['n'],
        'total_facilities': db.execute(
            "SELECT COUNT(*) AS n FROM facilities WHERE active=1").fetchone()['n'],
        'total_users': db.execute(
            "SELECT COUNT(*) AS n FROM users WHERE deleted_at IS NULL").fetchone()['n'],
        'total_beacons': db.execute(
            "SELECT COUNT(*) AS n FROM beacons").fetchone()['n'],
        'inventory_beacons': db.execute(
            "SELECT COUNT(*) AS n FROM beacons WHERE status='inventory'").fetchone()['n'],
        'active_beacons': db.execute(
            "SELECT COUNT(*) AS n FROM beacons WHERE status='active'").fetchone()['n'],
        'mtd_paid_total_krw': db.execute(
            """SELECT COALESCE(SUM(total),0) AS n FROM payments
               WHERE status='paid' AND created_at >= date('now','start of month')""").fetchone()['n'],
        'mtd_payment_count': db.execute(
            """SELECT COUNT(*) AS n FROM payments
               WHERE status='paid' AND created_at >= date('now','start of month')""").fetchone()['n'],
        'active_subscriptions': db.execute(
            "SELECT COUNT(*) AS n FROM service_subscriptions WHERE status='active'").fetchone()['n'],
    }
    db.close()
    return jsonify({'success': True, 'cards': cards})


@admin_bp.route('/stats/pending', methods=['GET'])
@require_super_admin()
def stats_pending():
    """처리 필요(액션) 현황 — 대시보드 액션 보드용 (2026-06-12).

    운영관리자가 대응해야 하는 건수만 모음. 각 키는 admin-web 의
    해당 관리 화면과 1:1 (클릭 이동).
    """
    db = get_db()
    counts = {
        # 계정 승인 대기 → /dashboard/approvals
        'owners_pending': db.execute(
            "SELECT COUNT(*) AS n FROM facility_accounts WHERE status='pending'"
        ).fetchone()['n'],
        # 고객 문의 미답변 → /dashboard/support
        'support_open': db.execute(
            "SELECT COUNT(*) AS n FROM support_tickets WHERE status='open'"
        ).fetchone()['n'],
        # 서비스 신청 대기 → /dashboard/service-requests
        'service_requests_pending': db.execute(
            "SELECT COUNT(*) AS n FROM service_requests WHERE status='pending'"
        ).fetchone()['n'],
        # 신고 미처리 → /dashboard/abuse-reports
        'abuse_open': db.execute(
            "SELECT COUNT(*) AS n FROM abuse_reports WHERE status='open'"
        ).fetchone()['n'],
        # 알림 처리 대기 (수동 승인 review + 결제 대기 unpaid) → /dashboard/notifications
        'notifications_pending': db.execute(
            "SELECT COUNT(*) AS n FROM notifications WHERE status IN ('review','unpaid')"
        ).fetchone()['n'],
        # 비콘 분실/이상 → /dashboard/beacons?status=lost
        'beacons_lost': db.execute(
            "SELECT COUNT(*) AS n FROM beacons WHERE status='lost'"
        ).fetchone()['n'],
    }
    db.close()
    return jsonify({'success': True, 'counts': counts})


@admin_bp.route('/stats/payments', methods=['GET'])
@require_super_admin()
def stats_payments():
    """일별 매출 시계열 (?range=7d|30d|3m|6m|1y, 기본 30d)."""
    raw = (request.args.get('range') or '30d').strip().lower()
    days_map = {'7d': 7, '30d': 30, '3m': 90, '6m': 180, '1y': 365}
    days = days_map.get(raw, 30)
    db = get_db()
    rows = db.execute("""
        SELECT strftime('%Y-%m-%d', created_at) AS day,
               COUNT(*) AS count,
               COALESCE(SUM(total), 0) AS total
        FROM payments
        WHERE status='paid' AND created_at >= datetime('now', ?)
        GROUP BY day ORDER BY day
    """, (f'-{days} days',)).fetchall()
    db.close()
    return jsonify({'success': True, 'range': raw, 'days': days,
                    'series': [dict(r) for r in rows]})


# ════ 전체 결제 / 구독 관리 ═════════════════════════════════════════════════

def _row_to_payment(row) -> dict:
    return {
        'id':                row['id'],
        'facility_account_id': row['facility_account_id'],
        'subscription_id':   row['subscription_id'],
        'order_no':          row['order_no'],
        'amount':            row['amount'],
        'vat':               row['vat'],
        'total':             row['total'],
        'pg_tid':            row['pg_tid'],
        'status':            row['status'],
        'receipt_email':     row['receipt_email'],
        'paid_at':           row['paid_at'],
        'created_at':        row['created_at'],
    }


@admin_bp.route('/payments', methods=['GET'])
@require_super_admin()
def admin_list_payments():
    """전체 결제 내역. ?status, ?facility_account_id, ?date_from/to (YYYY-MM-DD)."""
    status = (request.args.get('status') or '').strip()
    fac_id = request.args.get('facility_account_id', type=int)
    df = (request.args.get('date_from') or '').strip()
    dt = (request.args.get('date_to') or '').strip()
    db = get_db()
    sql = "SELECT * FROM payments"
    where, params = [], []
    if status:
        where.append("status=?"); params.append(status)
    if fac_id:
        where.append("facility_account_id=?"); params.append(fac_id)
    if df:
        where.append("date(created_at) >= ?"); params.append(df)
    if dt:
        where.append("date(created_at) <= ?"); params.append(dt)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT 1000"
    rows = db.execute(sql, params).fetchall()
    db.close()
    return jsonify({'success': True,
                    'count': len(rows),
                    'payments': [_row_to_payment(r) for r in rows]})


@admin_bp.route('/payments/<int:pid>/refund', methods=['POST'])
@require_super_admin()
def admin_refund_payment(pid):
    """결제 환불 (현재 시뮬 — 실 PG 연동 시 webhook 호출).

    body: ``{reason?}``. 결제 status='paid' → 'refunded'로 전이.
    """
    data = request.get_json(silent=True) or {}
    reason = (data.get('reason') or '').strip() or None
    db = get_db()
    row = db.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '결제를 찾을 수 없습니다.'}), 404
    if row['status'] != 'paid':
        db.close()
        return jsonify({'success': False,
                        'message': f"환불 가능한 상태가 아닙니다 (현재 '{row['status']}')."}), 409

    # PG provider 환불 호출. sim 모드면 항상 성공, toss 모드면 실 호출.
    provider = get_payment_provider()
    refund_res = provider.refund(
        payment_key=row['pg_tid'] or '',
        amount=row['total'],
        reason=reason,
    )
    if not refund_res.get('success'):
        db.close()
        return jsonify({
            'success': False,
            'message': refund_res.get('message', 'PG 환불 호출에 실패했습니다.'),
            'pg_error': refund_res.get('error'),
            'provider': refund_res.get('provider'),
        }), 502

    db.execute(
        "UPDATE payments SET status='refunded' WHERE id=?", (pid,)
    )
    new_row = db.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': f"환불 처리되었습니다 (provider={refund_res.get('provider')}).",
                    'refund_reason': reason,
                    'payment': _row_to_payment(new_row)})


def _row_to_subscription(row) -> dict:
    return {
        'id':                  row['id'],
        'facility_account_id': row['facility_account_id'],
        'service_type':        row['service_type'],
        'quantity':            row['quantity'],
        'period_months':       row['period_months'],
        'unit_price':          row['unit_price'],
        'total_price':         row['total_price'],
        'started_at':          row['started_at'],
        'ends_at':             row['ends_at'],
        'status':              row['status'],
        'created_at':          row['created_at'],
    }


@admin_bp.route('/subscriptions', methods=['GET'])
@require_super_admin()
def admin_list_subscriptions():
    """전체 구독. ?status, ?facility_account_id."""
    status = (request.args.get('status') or '').strip()
    fac_id = request.args.get('facility_account_id', type=int)
    db = get_db()
    sql = "SELECT * FROM service_subscriptions"
    where, params = [], []
    if status:
        where.append("status=?"); params.append(status)
    if fac_id:
        where.append("facility_account_id=?"); params.append(fac_id)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT 1000"
    rows = db.execute(sql, params).fetchall()
    db.close()
    return jsonify({'success': True,
                    'count': len(rows),
                    'subscriptions': [_row_to_subscription(r) for r in rows]})


@admin_bp.route('/beacons/<int:bid>/unassign', methods=['POST'])
@require_super_admin()
def unassign_beacon(bid):
    """매장에서 회수 → inventory 복귀."""
    db = get_db()
    # P22 후속 (2026-05-27): 회수 시 assigned_at 도 NULL (다음 할당 시 새 시작일).
    cur = db.execute(
        """UPDATE beacons
              SET facility_id=NULL, status='inventory', assigned_at=NULL
            WHERE id=? AND facility_id IS NOT NULL""",
        (bid,)
    )
    db.commit()
    affected = cur.rowcount
    db.close()
    if affected == 0:
        return jsonify({'success': False,
                        'message': '비콘을 찾을 수 없거나 이미 인벤토리 상태입니다.'}), 404
    return jsonify({'success': True})


# ── 서비스 신청 ↔ 비콘 매칭 (P-B, 2026-05-29) ────────────────────────────────
# 점주 신청(설치위치+WiFi)에 인벤토리 비콘을 매칭 → 할당·활성·WiFi 연결.
# 설계: docs/pathwave_beacon_provisioning_design_2026-05-29.md

@admin_bp.route('/service-requests', methods=['GET'])
@require_super_admin()
def list_service_requests():
    """서비스 신청 목록 (유닛 포함). ?status= 로 필터 (기본 전체)."""
    status = (request.args.get('status') or '').strip()
    db = get_db()
    where, params = [], []
    if status:
        where.append('r.status=?'); params.append(status)
    sql = """SELECT r.*, f.name AS facility_name, fa.email AS owner_email
             FROM service_requests r
             LEFT JOIN facilities f ON r.facility_id = f.id
             LEFT JOIN facility_accounts fa ON r.facility_account_id = fa.id"""
    if where:
        sql += ' WHERE ' + ' AND '.join(where)
    sql += ' ORDER BY r.id DESC'
    rows = db.execute(sql, params).fetchall()
    out = []
    for r in rows:
        units = db.execute(
            """SELECT u.id, u.location_label, u.ssid, u.period_start, u.period_end,
                      u.beacon_id, u.status, b.serial_no AS beacon_serial
               FROM service_request_units u
               LEFT JOIN beacons b ON u.beacon_id = b.id
               WHERE u.request_id=? ORDER BY u.id""",
            (r['id'],)
        ).fetchall()
        # 보안: wifi_password_enc 는 노출하지 않는다 (매칭 시 서버 내부에서만 사용).
        out.append({
            'id':            r['id'],
            'facility_id':   r['facility_id'],
            'facility_name': r['facility_name'],
            'owner_email':   r['owner_email'],
            'service_type':  r['service_type'],
            'status':        r['status'],
            'note':          r['note'],
            'created_at':    r['created_at'],
            'units':         [dict(u) for u in units],
        })
    db.close()
    return jsonify({'success': True, 'requests': out})


@admin_bp.route('/service-request-units/<int:uid>/match', methods=['POST'])
@require_super_admin()
def match_request_unit(uid):
    """신청 유닛에 인벤토리 비콘을 매칭. body: {beacon_id}.

    - 비콘: facility_id 할당 + status='active' + major(=facility_id)/minor(자동) + location_label.
    - WiFi: 유닛 SSID 가 있으면 wifi_profiles 생성(암호화 비번 그대로 복사) + beacon_wifi 연결.
    - 유닛 status='matched'. 신청의 모든 유닛이 matched 면 신청도 'matched'.
    """
    data = request.get_json(silent=True) or {}
    beacon_id = data.get('beacon_id')
    if not isinstance(beacon_id, int):
        return jsonify({'success': False, 'message': 'beacon_id 가 필요합니다.'}), 400

    db = get_db()
    unit = db.execute(
        """SELECT u.*, r.facility_id AS req_facility_id, r.id AS req_id
           FROM service_request_units u
           JOIN service_requests r ON u.request_id = r.id
           WHERE u.id=?""",
        (uid,)
    ).fetchone()
    if not unit:
        db.close()
        return jsonify({'success': False, 'message': '신청 유닛을 찾을 수 없습니다.'}), 404
    if unit['beacon_id']:
        db.close()
        return jsonify({'success': False, 'message': '이미 비콘이 매칭된 유닛입니다.'}), 409
    fac_id = unit['req_facility_id']
    if not fac_id:
        db.close()
        return jsonify({'success': False,
                        'message': '신청에 매장이 연결되어 있지 않습니다.'}), 400

    beacon = db.execute("SELECT * FROM beacons WHERE id=?", (beacon_id,)).fetchone()
    if not beacon:
        db.close()
        return jsonify({'success': False, 'message': '비콘을 찾을 수 없습니다.'}), 404
    if beacon['status'] != 'inventory':
        db.close()
        return jsonify({'success': False,
                        'message': "인벤토리(할당 대기) 상태 비콘만 매칭할 수 있습니다."}), 409

    # 매장 내 다음 minor 자동 할당
    nxt = db.execute(
        "SELECT COALESCE(MAX(minor), 0) + 1 AS m FROM beacons WHERE facility_id=?",
        (fac_id,)
    ).fetchone()['m']

    # 비콘 할당 + 설치위치(점주 신청값)
    db.execute(
        """UPDATE beacons
              SET facility_id=?, status='active', major=?, minor=?, location_label=?,
                  assigned_at=datetime('now')
            WHERE id=?""",
        (fac_id, fac_id, nxt, unit['location_label'], beacon_id)
    )

    # WiFi 연결 (유닛에 SSID 있으면). wifi_profiles.password 는 AES 암호값 그대로 저장.
    if unit['ssid']:
        cur = db.execute(
            "INSERT INTO wifi_profiles (facility_id, ssid, password, active) VALUES (?,?,?,1)",
            (fac_id, unit['ssid'], unit['wifi_password_enc'] or '')
        )
        wpid = cur.lastrowid
        db.execute(
            "INSERT OR IGNORE INTO beacon_wifi (beacon_id, wifi_profile_id, priority) VALUES (?,?,0)",
            (beacon_id, wpid)
        )

    db.execute(
        "UPDATE service_request_units SET beacon_id=?, status='matched' WHERE id=?",
        (beacon_id, uid)
    )
    # 모든 유닛 matched 면 신청도 matched
    remaining = db.execute(
        "SELECT COUNT(*) AS c FROM service_request_units WHERE request_id=? AND status!='matched'",
        (unit['req_id'],)
    ).fetchone()['c']
    if remaining == 0:
        db.execute("UPDATE service_requests SET status='matched' WHERE id=?", (unit['req_id'],))
    db.commit()
    db.close()
    return jsonify({'success': True, 'unit_id': uid, 'beacon_id': beacon_id,
                    'major': fac_id, 'minor': nxt,
                    'request_done': remaining == 0,
                    'message': '비콘이 매칭·할당되었습니다.'})


@admin_bp.route('/service-requests/<int:rid>/ship', methods=['POST'])
@require_super_admin()
def ship_service_request(rid):
    """매칭완료된 신청을 발송 처리 (matched → shipped). 라벨 부착 후 택배 발송."""
    db = get_db()
    row = db.execute("SELECT status FROM service_requests WHERE id=?", (rid,)).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '신청을 찾을 수 없습니다.'}), 404
    if row['status'] != 'matched':
        db.close()
        return jsonify({'success': False,
                        'message': "비콘 매칭이 완료된(matched) 신청만 발송할 수 있습니다."}), 409
    db.execute("UPDATE service_requests SET status='shipped' WHERE id=?", (rid,))
    db.commit()
    db.close()
    return jsonify({'success': True, 'status': 'shipped', 'message': '발송 처리되었습니다.'})


# ── 비콘 배터리 모니터링 (PR #34) ────────────────────────────────────────────
@admin_bp.route('/beacons/battery-status', methods=['GET'])
@require_super_admin()
def beacons_battery_status():
    """전체 비콘 배터리 현황 요약 + 저전력 리스트.

    query: ?low_threshold=N (기본 20)
    """
    try:
        low = int(request.args.get('low_threshold', 20))
    except ValueError:
        low = 20
    low = max(0, min(100, low))

    db = get_db()
    summary = db.execute(
        """SELECT
             COUNT(*)                                               AS total,
             SUM(CASE WHEN status='active'   THEN 1 ELSE 0 END)     AS active_cnt,
             SUM(CASE WHEN status='inventory' THEN 1 ELSE 0 END)    AS inventory_cnt,
             SUM(CASE WHEN battery_pct IS NULL THEN 1 ELSE 0 END)   AS unknown_cnt,
             SUM(CASE WHEN battery_pct <= ? THEN 1 ELSE 0 END)      AS low_cnt,
             AVG(battery_pct)                                       AS avg_pct
           FROM beacons""",
        (low,)
    ).fetchone()

    low_rows = db.execute(
        """SELECT b.id, b.serial_no, b.facility_id, b.status,
                  b.battery_pct, b.battery_updated_at, b.last_seen_at,
                  f.name AS facility_name
             FROM beacons b
        LEFT JOIN facilities f ON f.id=b.facility_id
            WHERE b.battery_pct IS NOT NULL AND b.battery_pct <= ?
         ORDER BY b.battery_pct ASC LIMIT 200""",
        (low,)
    ).fetchall()
    db.close()

    return jsonify({
        'success': True,
        'low_threshold': low,
        'summary': {
            'total':         summary['total'] or 0,
            'active':        summary['active_cnt'] or 0,
            'inventory':     summary['inventory_cnt'] or 0,
            'unknown':       summary['unknown_cnt'] or 0,
            'low_battery':   summary['low_cnt'] or 0,
            'avg_pct':       round(summary['avg_pct'], 1) if summary['avg_pct'] is not None else None,
        },
        'low_battery_beacons': [
            {
                'id':                 r['id'],
                'serial_no':          r['serial_no'],
                'status':             r['status'],
                'facility_id':        r['facility_id'],
                'facility_name':      r['facility_name'],
                'battery_pct':        r['battery_pct'],
                'battery_updated_at': r['battery_updated_at'],
                'last_seen_at':       r['last_seen_at'],
            }
            for r in low_rows
        ],
    })


@admin_bp.route('/beacons/<int:bid>/battery-history', methods=['GET'])
@require_super_admin()
def beacon_battery_history(bid: int):
    """특정 비콘의 배터리 시계열 (최근 N건). query: ?limit=100"""
    try:
        limit = int(request.args.get('limit', 100))
    except ValueError:
        limit = 100
    limit = max(1, min(1000, limit))

    db = get_db()
    if not db.execute("SELECT id FROM beacons WHERE id=?", (bid,)).fetchone():
        db.close()
        return jsonify({'success': False, 'message': '비콘을 찾을 수 없습니다.'}), 404

    rows = db.execute(
        """SELECT id, battery_pct, voltage_mv, reported_at
             FROM beacon_battery_history
            WHERE beacon_id=?
         ORDER BY id DESC LIMIT ?""",
        (bid, limit)
    ).fetchall()
    db.close()

    return jsonify({
        'success': True,
        'beacon_id': bid,
        'count': len(rows),
        'history': [
            {
                'id':          r['id'],
                'battery_pct': r['battery_pct'],
                'voltage_mv':  r['voltage_mv'],
                'reported_at': r['reported_at'],
            }
            for r in rows
        ],
    })
