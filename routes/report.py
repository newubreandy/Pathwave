"""리포트/통계 API. SRS FR-REPORT-001.

기간 필터(``?range=7d|30d|3m|6m|1y``) 지원. 일별 집계는 SQLite의
``strftime('%Y-%m-%d', ...)`` 사용.

엔드포인트
---------
- GET /api/facilities/<fid>/reports/visitors    방문자 추이 + 합계
- GET /api/facilities/<fid>/reports/stamps      스탬프 발급/만료 통계
- GET /api/facilities/<fid>/reports/coupons     쿠폰 발급/사용/만료 비율
- GET /api/facilities/<fid>/reports/summary     대시보드 카드용 합계 (모든 모듈)
"""
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, g

from models.database import get_db
from routes.auth import require_facility_actor

report_bp = Blueprint('report', __name__)

_RANGES = {
    '7d':  7,
    '30d': 30,
    '3m':  90,
    '6m':  180,
    '1y':  365,
}


def _owned_facility(db, fid: int, account_id: int) -> bool:
    return bool(db.execute(
        "SELECT 1 FROM facilities WHERE id=? AND owner_id=? AND active=1",
        (fid, account_id)
    ).fetchone())


def _resolve_range() -> tuple[int, str]:
    raw = (request.args.get('range') or '30d').strip().lower()
    days = _RANGES.get(raw)
    if not days:
        days = _RANGES['30d']
        raw = '30d'
    return days, raw


def _fill_zero_days(rows: list, days: int, key_field: str = 'day') -> list:
    """row가 없는 날짜는 0으로 채워 시계열 빈틈 제거."""
    by_day = {r[key_field]: r for r in rows}
    out = []
    today = datetime.utcnow().date()
    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        if d in by_day:
            out.append(dict(by_day[d]))
        else:
            template = {k: 0 for k in (rows[0].keys() if rows else [])}
            template[key_field] = d
            out.append(template)
    return out


# ── 방문자 추이 ───────────────────────────────────────────────────────────────

@report_bp.route('/api/facilities/<int:fid>/reports/visitors', methods=['GET'])
@require_facility_actor()
def visitors_report(fid):
    """일별 방문자 수 (user_wifi_logs 기준 distinct user)."""
    account_id = g.auth['owner_account_id']
    days, label = _resolve_range()
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    rows = db.execute("""
        SELECT strftime('%Y-%m-%d', connected_at) AS day,
               COUNT(*) AS visits,
               COUNT(DISTINCT user_id) AS unique_users
        FROM user_wifi_logs
        WHERE facility_id=? AND connected_at >= datetime('now', ?)
        GROUP BY day ORDER BY day
    """, (fid, f'-{days} days')).fetchall()
    series = _fill_zero_days([dict(r) for r in rows], days)
    total_unique = db.execute(
        """SELECT COUNT(DISTINCT user_id) AS n FROM user_wifi_logs
           WHERE facility_id=? AND connected_at >= datetime('now', ?)""",
        (fid, f'-{days} days')
    ).fetchone()['n']
    db.close()
    return jsonify({'success': True, 'range': label, 'days': days,
                    'series': series,
                    'totals': {'visits': sum(d['visits'] for d in series),
                               'unique_users': total_unique}})


# ── 스탬프 통계 ───────────────────────────────────────────────────────────────

@report_bp.route('/api/facilities/<int:fid>/reports/stamps', methods=['GET'])
@require_facility_actor()
def stamps_report(fid):
    """스탬프 일별 적립 + 활성/만료 비율 + 보상 도달 사용자 수."""
    account_id = g.auth['owner_account_id']
    days, label = _resolve_range()
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    series_rows = db.execute("""
        SELECT strftime('%Y-%m-%d', created_at) AS day,
               SUM(amount) AS amount,
               COUNT(DISTINCT user_id) AS unique_users
        FROM stamps
        WHERE facility_id=? AND created_at >= datetime('now', ?)
        GROUP BY day ORDER BY day
    """, (fid, f'-{days} days')).fetchall()
    series = _fill_zero_days([dict(r) for r in series_rows], days)

    breakdown = db.execute("""
        SELECT
          SUM(CASE WHEN expires_at IS NULL OR expires_at > datetime('now') THEN amount ELSE 0 END) AS active,
          SUM(CASE WHEN expires_at IS NOT NULL AND expires_at <= datetime('now') THEN amount ELSE 0 END) AS expired
        FROM stamps WHERE facility_id=?""", (fid,)).fetchone()

    policy = db.execute(
        "SELECT reward_threshold FROM stamp_policies WHERE facility_id=? AND active=1",
        (fid,)
    ).fetchone()
    reward_reached = 0
    if policy:
        threshold = policy['reward_threshold']
        rr = db.execute("""
            SELECT COUNT(*) AS n FROM (
              SELECT user_id, SUM(amount) AS total
              FROM stamps
              WHERE facility_id=?
                AND (expires_at IS NULL OR expires_at > datetime('now'))
              GROUP BY user_id
              HAVING total >= ?)
        """, (fid, threshold)).fetchone()
        reward_reached = rr['n']

    db.close()
    return jsonify({'success': True, 'range': label, 'days': days,
                    'series': series,
                    'breakdown': {
                        'active':  breakdown['active']  or 0,
                        'expired': breakdown['expired'] or 0,
                    },
                    'reward_threshold': policy['reward_threshold'] if policy else None,
                    'reward_reached_users': reward_reached})


# ── 쿠폰 통계 ─────────────────────────────────────────────────────────────────

@report_bp.route('/api/facilities/<int:fid>/reports/coupons', methods=['GET'])
@require_facility_actor()
def coupons_report(fid):
    """쿠폰 일별 발급 + 발급/사용/만료 도넛."""
    account_id = g.auth['owner_account_id']
    days, label = _resolve_range()
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    series_rows = db.execute("""
        SELECT strftime('%Y-%m-%d', created_at) AS day,
               COUNT(*) AS issued,
               SUM(CASE WHEN used=1 THEN 1 ELSE 0 END) AS used
        FROM coupons
        WHERE facility_id=? AND created_at >= datetime('now', ?)
        GROUP BY day ORDER BY day
    """, (fid, f'-{days} days')).fetchall()
    series = _fill_zero_days([dict(r) for r in series_rows], days)

    breakdown = db.execute("""
        SELECT
          COUNT(*) AS total,
          SUM(CASE WHEN used=1 THEN 1 ELSE 0 END) AS used,
          SUM(CASE WHEN used=0 AND expires_at IS NOT NULL AND expires_at <= datetime('now') THEN 1 ELSE 0 END) AS expired,
          SUM(CASE WHEN used=0 AND (expires_at IS NULL OR expires_at > datetime('now')) THEN 1 ELSE 0 END) AS active
        FROM coupons WHERE facility_id=?""", (fid,)).fetchone()
    db.close()
    return jsonify({'success': True, 'range': label, 'days': days,
                    'series': series,
                    'breakdown': {
                        'total':   breakdown['total']   or 0,
                        'active':  breakdown['active']  or 0,
                        'used':    breakdown['used']    or 0,
                        'expired': breakdown['expired'] or 0,
                    }})


# ── 요약 카드 (대시보드) ─────────────────────────────────────────────────────

@report_bp.route('/api/facilities/<int:fid>/reports/summary', methods=['GET'])
@require_facility_actor()
def summary_report(fid):
    """대시보드 카드: 활성 비콘, 이번 달 방문자/접속, 이번 달 발급 쿠폰, 전월 대비 증감."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    active_beacons = db.execute(
        "SELECT COUNT(*) n FROM beacons WHERE facility_id=? AND status='active'", (fid,)
    ).fetchone()['n']

    def visits_in(start_clause: str) -> int:
        return db.execute(
            f"""SELECT COUNT(DISTINCT user_id) n FROM user_wifi_logs
                WHERE facility_id=? AND {start_clause}""",
            (fid,)
        ).fetchone()['n']
    visitors_this = visits_in("connected_at >= date('now','start of month')")
    visitors_prev = visits_in("connected_at >= date('now','start of month','-1 month') "
                              "AND connected_at < date('now','start of month')")

    def coupons_in(start_clause: str) -> int:
        return db.execute(
            f"""SELECT COUNT(*) n FROM coupons
                WHERE facility_id=? AND {start_clause}""",
            (fid,)
        ).fetchone()['n']
    coupons_this = coupons_in("created_at >= date('now','start of month')")
    coupons_prev = coupons_in("created_at >= date('now','start of month','-1 month') "
                               "AND created_at < date('now','start of month')")

    def trend(curr: int, prev: int) -> float | None:
        if prev == 0:
            return None
        return round((curr - prev) / prev * 100, 1)

    db.close()
    return jsonify({'success': True,
                    'cards': {
                        'active_beacons':    active_beacons,
                        'visitors_this_month': visitors_this,
                        'visitors_trend_pct': trend(visitors_this, visitors_prev),
                        'coupons_issued_this_month': coupons_this,
                        'coupons_trend_pct': trend(coupons_this, coupons_prev),
                    }})
