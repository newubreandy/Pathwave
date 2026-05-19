"""알림 카테고리별 on/off 설정 — 사용자 / 시설(사장님) 별도.

엔드포인트
---------
사용자 (sub_type='user'):
  GET  /api/users/me/notification-preferences
  PUT  /api/users/me/notification-preferences/<category>   body: {enabled: bool}

시설 (owner+admin, staff 는 읽기만 가능하도록 staff 도 허용):
  GET  /api/facility/me/notification-preferences
  PUT  /api/facility/me/notification-preferences/<category> body: {enabled: bool}

기본값
------
notification_preferences 행이 없으면 ``enabled=true`` (기본 수신).
PUT 으로 false 또는 true 를 명시할 때만 row 가 생성/갱신된다.
"""
from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from models.database import get_db
from routes.auth import require_auth, require_facility_actor

notification_preferences_bp = Blueprint('notification_preferences', __name__)

# ── 카테고리 메타 ─────────────────────────────────────────────────────────────
USER_CATEGORIES: dict[str, str] = {
    'beacon':    '비콘 진입 알림',
    'coupon':    '쿠폰 / 스탬프 알림',
    'marketing': '마케팅 / 이벤트 알림',
    'system':    '시스템 공지',
}

FACILITY_CATEGORIES: dict[str, str] = {
    'customer_visit': '손님 입장 알림',
    'coupon_used':    '쿠폰 사용 알림',
    'sales_report':   '매출 일보',
    'system':         '시스템 공지',
    'billing':        '결제 / 구독 알림',
}


# ── 공통 헬퍼 ─────────────────────────────────────────────────────────────────

def _load_prefs(db, sub_type: str, subject_id: int,
                catalog: dict[str, str]) -> list[dict]:
    """카탈로그의 모든 카테고리 + 현재 enabled 상태 (없으면 True) 반환."""
    rows = db.execute(
        """SELECT category, enabled
             FROM notification_preferences
            WHERE sub_type=? AND subject_id=?""",
        (sub_type, subject_id)
    ).fetchall()
    saved = {r['category']: bool(r['enabled']) for r in rows}
    return [{
        'category': code,
        'label':    label,
        'enabled':  saved.get(code, True),
    } for code, label in catalog.items()]


def _upsert_pref(db, sub_type: str, subject_id: int,
                 category: str, enabled: bool) -> None:
    row = db.execute(
        """SELECT id FROM notification_preferences
            WHERE sub_type=? AND subject_id=? AND category=?""",
        (sub_type, subject_id, category)
    ).fetchone()
    if row:
        db.execute(
            """UPDATE notification_preferences
                  SET enabled=?, updated_at=datetime('now')
                WHERE id=?""",
            (1 if enabled else 0, row['id'])
        )
    else:
        db.execute(
            """INSERT INTO notification_preferences
                  (sub_type, subject_id, category, enabled)
               VALUES (?,?,?,?)""",
            (sub_type, subject_id, category, 1 if enabled else 0)
        )


def _parse_enabled(data: dict) -> bool | None:
    if 'enabled' not in data:
        return None
    val = data['enabled']
    if isinstance(val, bool):
        return val
    if isinstance(val, int):
        return val != 0
    if isinstance(val, str):
        s = val.strip().lower()
        if s in ('true', '1', 'yes', 'on'):  return True
        if s in ('false', '0', 'no', 'off'): return False
    return None


# ════════════════════════════════════════════════════════════════════════════
#                                  사용자
# ════════════════════════════════════════════════════════════════════════════

@notification_preferences_bp.route(
    '/api/users/me/notification-preferences', methods=['GET'])
@require_auth(sub_type='user')
def user_list():
    uid = g.auth['user_id']
    db = get_db()
    try:
        return jsonify({'success': True, 'sub_type': 'user',
                        'preferences': _load_prefs(db, 'user', uid,
                                                   USER_CATEGORIES)})
    finally:
        db.close()


@notification_preferences_bp.route(
    '/api/users/me/notification-preferences/<category>', methods=['PUT'])
@require_auth(sub_type='user')
def user_upsert(category: str):
    if category not in USER_CATEGORIES:
        return jsonify({'success': False,
                        'message': f'알 수 없는 카테고리: {category}'}), 400
    data = request.get_json(silent=True) or {}
    enabled = _parse_enabled(data)
    if enabled is None:
        return jsonify({'success': False,
                        'message': 'enabled 는 boolean 이어야 합니다.'}), 400
    uid = g.auth['user_id']
    db = get_db()
    try:
        _upsert_pref(db, 'user', uid, category, enabled)
        db.commit()
        return jsonify({'success': True, 'category': category, 'enabled': enabled})
    finally:
        db.close()


# ════════════════════════════════════════════════════════════════════════════
#                                  시설
# ════════════════════════════════════════════════════════════════════════════

@notification_preferences_bp.route(
    '/api/facility/me/notification-preferences', methods=['GET'])
@require_facility_actor(roles=['owner', 'admin', 'staff'])
def facility_list():
    account_id = g.auth['owner_account_id']
    db = get_db()
    try:
        return jsonify({'success': True, 'sub_type': 'facility',
                        'preferences': _load_prefs(db, 'facility', account_id,
                                                   FACILITY_CATEGORIES)})
    finally:
        db.close()


@notification_preferences_bp.route(
    '/api/facility/me/notification-preferences/<category>', methods=['PUT'])
@require_facility_actor(roles=['owner', 'admin'])
def facility_upsert(category: str):
    """staff 는 PUT 불가 — 사장님/매장관리자만 설정 변경."""
    if category not in FACILITY_CATEGORIES:
        return jsonify({'success': False,
                        'message': f'알 수 없는 카테고리: {category}'}), 400
    data = request.get_json(silent=True) or {}
    enabled = _parse_enabled(data)
    if enabled is None:
        return jsonify({'success': False,
                        'message': 'enabled 는 boolean 이어야 합니다.'}), 400
    account_id = g.auth['owner_account_id']
    db = get_db()
    try:
        _upsert_pref(db, 'facility', account_id, category, enabled)
        db.commit()
        return jsonify({'success': True, 'category': category, 'enabled': enabled})
    finally:
        db.close()
