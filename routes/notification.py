"""알림 발송 API. SRS FR-NOTI-001/002.

엔드포인트
---------
- POST   /api/facilities/<fid>/notifications        생성/즉시발송 (owner+admin)
- GET    /api/facilities/<fid>/notifications        이력 (owner+admin)
- GET    /api/facilities/<fid>/notifications/<nid>  상세 (owner+admin)
- DELETE /api/facilities/<fid>/notifications/<nid>  취소 (owner+admin, pending만)
- POST   /api/notifications/<nid>/dispatch          수동 발송 (owner+admin)
                                                    예약 알림을 즉시 발송 (스케줄러 대체)
- GET    /api/users/me/notifications                본인 인박스 (sub_type='user')
- POST   /api/notifications/<nid>/read              읽음 표시 (sub_type='user')

동작
----
- ``target_type='all_visited'`` 시 ``user_wifi_logs``의 distinct user_id를 수신자로 채움
- ``target_type='specific'`` 시 body의 ``user_ids``를 그대로 수신자로
- ``scheduled_at`` 이 NULL이거나 과거면 즉시 발송 (status='sent', sent_at=now)
- 미래면 'pending' — ``/dispatch``로 수동 발송 가능
"""
from datetime import datetime

from flask import Blueprint, request, jsonify, g

from models.database import get_db
from models.push import push_to_users
from routes.auth import require_facility_actor, require_auth

notification_bp = Blueprint('notification', __name__)

_TARGET_TYPES = {'all_visited', 'specific'}
_TITLE_MAX  = 100
_BODY_MAX   = 2000


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _owned_facility(db, fid: int, account_id: int) -> bool:
    return bool(db.execute(
        "SELECT 1 FROM facilities WHERE id=? AND owner_id=? AND active=1",
        (fid, account_id)
    ).fetchone())


def _resolve_recipients(db, fid: int, target_type: str,
                        user_ids: list | None) -> list[int]:
    if target_type == 'specific':
        return list({int(u) for u in (user_ids or []) if int(u) > 0})
    # all_visited
    rows = db.execute(
        "SELECT DISTINCT user_id FROM user_wifi_logs WHERE facility_id=?",
        (fid,)
    ).fetchall()
    return [r['user_id'] for r in rows]


def _row_to_notification(row) -> dict:
    return {
        'id':              row['id'],
        'facility_id':     row['facility_id'],
        'title':           row['title'],
        'body':            row['body'],
        'target_type':     row['target_type'],
        'scheduled_at':    row['scheduled_at'],
        'sent_at':         row['sent_at'],
        'status':          row['status'],
        'recipient_count': row['recipient_count'],
        'issued_by': {
            'role':     row['issued_by_actor_role'],
            'actor_id': row['issued_by_actor_id'],
        },
        'created_at':      row['created_at'],
    }


def _dispatch(db, nid: int) -> tuple[int, str]:
    """수신자 테이블 채움 + status='sent' 갱신.

    이미 수신자가 있으면 다시 채우지 않음 (idempotent).
    반환: (recipient_count, status)
    """
    notif = db.execute("SELECT * FROM notifications WHERE id=?", (nid,)).fetchone()
    if notif['status'] in ('sent', 'canceled'):
        return notif['recipient_count'], notif['status']

    user_ids = _resolve_recipients(
        db, notif['facility_id'], notif['target_type'],
        request.get_json(silent=True).get('user_ids') if request.is_json else None
    )
    # 이미 등록된 수신자 (재발송 가드)
    existing = {r['user_id'] for r in db.execute(
        "SELECT user_id FROM notification_recipients WHERE notification_id=?",
        (nid,)
    ).fetchall()}
    new_users = [u for u in user_ids if u not in existing]
    for uid in new_users:
        db.execute(
            "INSERT INTO notification_recipients (notification_id, user_id) VALUES (?,?)",
            (nid, uid)
        )
    total = len(existing) + len(new_users)
    db.execute(
        """UPDATE notifications
             SET status='sent', sent_at=datetime('now'), recipient_count=?
           WHERE id=?""",
        (total, nid)
    )
    return total, 'sent'


# ── 생성 ──────────────────────────────────────────────────────────────────────

@notification_bp.route('/api/facilities/<int:fid>/notifications', methods=['POST'])
@require_facility_actor(roles=['owner', 'admin'])
def create_notification(fid):
    """알림 생성. ``scheduled_at``이 없거나 과거면 즉시 발송.

    body: {title, body, target_type, user_ids?, scheduled_at?}
    """
    account_id = g.auth['owner_account_id']
    actor_role = g.auth['actor_role']
    actor_id   = g.auth['user_id']
    data = request.get_json(silent=True) or {}

    title = (data.get('title') or '').strip()
    body  = (data.get('body')  or '').strip()
    target_type = (data.get('target_type') or '').strip()
    user_ids    = data.get('user_ids')
    scheduled_at_raw = (data.get('scheduled_at') or '').strip() or None

    if not title or len(title) > _TITLE_MAX:
        return jsonify({'success': False,
                        'message': f'title은 1~{_TITLE_MAX}자여야 합니다.'}), 400
    if not body or len(body) > _BODY_MAX:
        return jsonify({'success': False,
                        'message': f'body는 1~{_BODY_MAX}자여야 합니다.'}), 400
    if target_type not in _TARGET_TYPES:
        return jsonify({'success': False,
                        'message': f"target_type은 {sorted(_TARGET_TYPES)} 중 하나여야 합니다."}), 400
    if target_type == 'specific':
        if not isinstance(user_ids, list) or not user_ids \
           or not all(isinstance(u, int) and u > 0 for u in user_ids):
            return jsonify({'success': False,
                            'message': "target_type='specific'일 때 user_ids는 양의 정수 배열이어야 합니다."}), 400
    scheduled_at = None
    if scheduled_at_raw:
        try:
            scheduled_at = datetime.fromisoformat(scheduled_at_raw).isoformat()
        except ValueError:
            return jsonify({'success': False,
                            'message': 'scheduled_at은 ISO 8601 형식이어야 합니다.'}), 400

    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    cur = db.execute(
        """INSERT INTO notifications
             (facility_id, title, body, target_type, scheduled_at,
              issued_by_actor_role, issued_by_actor_id, status)
           VALUES (?,?,?,?,?,?,?,?)""",
        (fid, title, body, target_type, scheduled_at,
         actor_role, actor_id, 'pending')
    )
    nid = cur.lastrowid

    # 즉시 발송 여부 결정
    is_due = scheduled_at is None or scheduled_at <= datetime.utcnow().isoformat()
    if is_due:
        # specific 케이스의 user_ids는 _dispatch가 다시 request.get_json을 보지 않도록 직접 처리
        if target_type == 'specific':
            recipients_list = list(set(user_ids))
        else:
            recipients_list = _resolve_recipients(db, fid, target_type, None)
        for uid in recipients_list:
            db.execute(
                "INSERT OR IGNORE INTO notification_recipients (notification_id, user_id) VALUES (?,?)",
                (nid, uid)
            )
        total = len(recipients_list)
        db.execute(
            """UPDATE notifications
                 SET status='sent', sent_at=datetime('now'), recipient_count=?
               WHERE id=?""",
            (total, nid)
        )
        # 푸시 발송 (best-effort)
        push_to_users(db, recipients_list, title=title, body=body,
                      data={'type': 'notification', 'notification_id': nid,
                            'facility_id': fid})
    row = db.execute("SELECT * FROM notifications WHERE id=?", (nid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '알림이 발송되었습니다.' if is_due else '알림이 예약되었습니다.',
                    'notification': _row_to_notification(row)}), 201


# ── 목록 / 상세 / 취소 ───────────────────────────────────────────────────────

@notification_bp.route('/api/facilities/<int:fid>/notifications', methods=['GET'])
@require_facility_actor(roles=['owner', 'admin'])
def list_notifications(fid):
    """매장 알림 이력 (최신순)."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    rows = db.execute(
        "SELECT * FROM notifications WHERE facility_id=? ORDER BY id DESC",
        (fid,)
    ).fetchall()
    db.close()
    return jsonify({'success': True,
                    'notifications': [_row_to_notification(r) for r in rows]})


@notification_bp.route('/api/facilities/<int:fid>/notifications/<int:nid>', methods=['GET'])
@require_facility_actor(roles=['owner', 'admin'])
def detail_notification(fid, nid):
    account_id = g.auth['owner_account_id']
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    row = db.execute(
        "SELECT * FROM notifications WHERE id=? AND facility_id=?",
        (nid, fid)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({'success': False, 'message': '알림을 찾을 수 없습니다.'}), 404
    return jsonify({'success': True, 'notification': _row_to_notification(row)})


@notification_bp.route('/api/facilities/<int:fid>/notifications/<int:nid>', methods=['DELETE'])
@require_facility_actor(roles=['owner', 'admin'])
def cancel_notification(fid, nid):
    """예약 대기(pending) 알림 취소. 발송 완료(sent)는 취소 불가 (409)."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    row = db.execute(
        "SELECT status FROM notifications WHERE id=? AND facility_id=?",
        (nid, fid)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '알림을 찾을 수 없습니다.'}), 404
    if row['status'] != 'pending':
        db.close()
        return jsonify({'success': False,
                        'message': f"이미 '{row['status']}' 상태인 알림은 취소할 수 없습니다."}), 409
    db.execute("UPDATE notifications SET status='canceled' WHERE id=?", (nid,))
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': '알림이 취소되었습니다.'})


# ── 수동 발송 ─────────────────────────────────────────────────────────────────

@notification_bp.route('/api/notifications/<int:nid>/dispatch', methods=['POST'])
@require_facility_actor(roles=['owner', 'admin'])
def dispatch_notification(nid):
    """예약 대기 알림을 즉시 발송 (스케줄러 대체용).

    이미 sent/canceled 인 경우 409.
    """
    account_id = g.auth['owner_account_id']
    db = get_db()
    row = db.execute(
        """SELECT n.* FROM notifications n
           JOIN facilities f ON n.facility_id=f.id
           WHERE n.id=? AND f.owner_id=?""",
        (nid, account_id)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '알림을 찾을 수 없습니다.'}), 404
    if row['status'] != 'pending':
        db.close()
        return jsonify({'success': False,
                        'message': f"이미 '{row['status']}' 상태입니다."}), 409

    recipients = _resolve_recipients(db, row['facility_id'], row['target_type'], None)
    for uid in recipients:
        db.execute(
            "INSERT OR IGNORE INTO notification_recipients (notification_id, user_id) VALUES (?,?)",
            (nid, uid)
        )
    db.execute(
        """UPDATE notifications
             SET status='sent', sent_at=datetime('now'), recipient_count=?
           WHERE id=?""",
        (len(recipients), nid)
    )
    push_to_users(db, recipients, title=row['title'], body=row['body'],
                  data={'type': 'notification', 'notification_id': nid,
                        'facility_id': row['facility_id']})
    new_row = db.execute("SELECT * FROM notifications WHERE id=?", (nid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '알림이 발송되었습니다.',
                    'notification': _row_to_notification(new_row)})


# ── 사용자 인박스 ────────────────────────────────────────────────────────────

@notification_bp.route('/api/users/me/notifications', methods=['GET'])
@require_auth(sub_type='user')
def my_notifications():
    """본인 인박스. ``?unread=1`` 으로 미읽음만 필터."""
    user_id = g.auth['user_id']
    only_unread = request.args.get('unread', '').strip() in ('1', 'true', 'yes')
    db = get_db()
    sql = """
        SELECT n.id, n.title, n.body, n.facility_id, f.name AS facility_name,
               n.sent_at, r.read_at, r.id AS recipient_id
        FROM notification_recipients r
        JOIN notifications n ON r.notification_id = n.id
        JOIN facilities    f ON n.facility_id = f.id
        WHERE r.user_id=? AND n.status='sent'
    """
    if only_unread:
        sql += " AND r.read_at IS NULL"
    sql += " ORDER BY n.sent_at DESC"
    rows = db.execute(sql, (user_id,)).fetchall()
    db.close()
    return jsonify({'success': True,
                    'notifications': [{
                        'id':            r['id'],
                        'title':         r['title'],
                        'body':          r['body'],
                        'facility_id':   r['facility_id'],
                        'facility_name': r['facility_name'],
                        'sent_at':       r['sent_at'],
                        'read':          r['read_at'] is not None,
                        'read_at':       r['read_at'],
                    } for r in rows]})


@notification_bp.route('/api/notifications/<int:nid>/read', methods=['POST'])
@require_auth(sub_type='user')
def mark_read(nid):
    """본인의 해당 알림 수신 row를 읽음으로 표시. 멱등 (이미 읽음이어도 200)."""
    user_id = g.auth['user_id']
    db = get_db()
    row = db.execute(
        """SELECT id FROM notification_recipients
           WHERE notification_id=? AND user_id=?""",
        (nid, user_id)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False,
                        'message': '받은 알림이 아닙니다.'}), 404
    db.execute(
        "UPDATE notification_recipients SET read_at=datetime('now') WHERE id=? AND read_at IS NULL",
        (row['id'],)
    )
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': '읽음으로 표시했습니다.'})
