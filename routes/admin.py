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

_UUID_RE = _re.compile(r'^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$')
_BEACON_STATUSES = {'inventory', 'active', 'inactive', 'lost'}


def _row_to_beacon(row) -> dict:
    return {
        'id':           row['id'],
        'serial_no':    row['serial_no'],
        'uuid':         row['uuid'],
        'facility_id':  row['facility_id'],
        'facility_name': row['facility_name'] if 'facility_name' in row.keys() else None,
        'status':       row['status'],
        'battery_pct':  row['battery_pct'],
        'firmware_ver': row['firmware_ver'],
        'created_at':   row['created_at'],
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
        if not sn or not _UUID_RE.match(uuid):
            errors.append({'index': idx, 'serial_no': sn, 'uuid': uuid,
                           'error': 'invalid_format'})
            continue
        try:
            cur = db.execute(
                """INSERT INTO beacons (serial_no, uuid, firmware_ver, status)
                   VALUES (?,?,?,'inventory')""",
                (sn, uuid, fw)
            )
            imported.append({'id': cur.lastrowid, 'serial_no': sn, 'uuid': uuid})
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
    sql = """SELECT b.*, f.name AS facility_name
             FROM beacons b
             LEFT JOIN facilities f ON b.facility_id = f.id"""
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
        where.append("b.serial_no LIKE ?"); params.append(f'%{q}%')
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
    if not sets:
        db.close()
        return jsonify({'success': False, 'message': '수정할 필드가 없습니다.'}), 400

    vals.append(bid)
    db.execute(f"UPDATE beacons SET {', '.join(sets)} WHERE id=?", vals)
    new_row = db.execute(
        """SELECT b.*, f.name AS facility_name
           FROM beacons b LEFT JOIN facilities f ON b.facility_id=f.id
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

    db.execute(
        "UPDATE beacons SET facility_id=?, status='active' WHERE id=?",
        (facility_id, bid)
    )
    db.commit()
    new_row = db.execute(
        """SELECT b.*, f.name AS facility_name
           FROM beacons b LEFT JOIN facilities f ON b.facility_id=f.id
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
    cur = db.execute(
        """UPDATE beacons SET facility_id=NULL, status='inventory'
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
