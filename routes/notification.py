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
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify, g

from models.database import get_db
from models.push import push_to_users
from routes.auth import require_facility_actor, require_auth, require_super_admin
from services.notification_quota import get_available_quota, quota_summary
from services.notification_review import review_notification
from services.translation_ai import SUPPORTED_LANGS

notification_bp = Blueprint('notification', __name__)

_TARGET_TYPES = {'all_visited', 'specific'}
_TITLE_MAX  = 100
_BODY_MAX   = 2000
_MIN_LEAD_HOURS = 12   # P11 — 신청 후 최소 12시간 이후만 발송 가능


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
    # P11 — 새 컬럼이 없는 구버전 row 도 안전하게 처리.
    keys = set(row.keys())
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
        'ai_review_status': row['ai_review_status']     if 'ai_review_status' in keys else None,
        'ai_review_reason': row['ai_review_reason']     if 'ai_review_reason' in keys else None,
        'approved_by_admin_id': row['approved_by_admin_id'] if 'approved_by_admin_id' in keys else None,
        'approved_at':     row['approved_at']           if 'approved_at' in keys else None,
        'created_at':      row['created_at'],
    }


def _dispatch(db, nid: int, *, force: bool = False) -> tuple[bool, str, str | None]:
    """알림 실제 발송 (P11) — quota 차감 + recipients 등록 + push + status='sent'.

    Parameters
    ----------
    force
        True 면 quota 검증 skip (어드민 강제 발송 시). 기본 False (정상 차감).

    Returns
    -------
    (ok, new_status, error_message)
      - ok=True 면 status='sent'
      - ok=False 면 status 그대로 + error_message 에 사유
    """
    from services.notification_quota import consume_quota   # 순환 import 방지

    notif = db.execute("SELECT * FROM notifications WHERE id=?", (nid,)).fetchone()
    if not notif:
        return False, 'not_found', '알림을 찾을 수 없습니다.'
    if notif['status'] == 'sent':
        return True, 'sent', None
    if notif['status'] == 'canceled':
        return False, 'canceled', '취소된 알림입니다.'

    fac = db.execute(
        "SELECT owner_id FROM facilities WHERE id=?", (notif['facility_id'],)
    ).fetchone()
    if not fac:
        return False, notif['status'], '매장을 찾을 수 없습니다.'
    account_id = fac['owner_id']

    # 수신자 결정 — specific 은 미리 INSERT 된 row 사용, all_visited 는 발송 시점 재계산
    if notif['target_type'] == 'specific':
        rows = db.execute(
            "SELECT user_id FROM notification_recipients WHERE notification_id=?",
            (nid,)
        ).fetchall()
        recipients = [r['user_id'] for r in rows]
    else:
        recipients = _resolve_recipients(db, notif['facility_id'],
                                         notif['target_type'], None)
    total = len(recipients)
    if total == 0:
        return False, notif['status'], '발송 대상자가 없습니다.'

    # quota 차감 (force 면 skip)
    if not force:
        if not consume_quota(db, account_id, amount=total):
            db.execute("UPDATE notifications SET status='unpaid' WHERE id=?", (nid,))
            return False, 'unpaid', f'quota 부족 (필요 {total} 건).'

    # recipients INSERT (all_visited 의 경우)
    for uid in recipients:
        db.execute(
            "INSERT OR IGNORE INTO notification_recipients (notification_id, user_id) VALUES (?,?)",
            (nid, uid)
        )
    db.execute(
        """UPDATE notifications
             SET status='sent', sent_at=datetime('now'), recipient_count=?
           WHERE id=?""",
        (total, nid)
    )
    # 푸시 발송 (P8c) — title 은 시스템 문구(ko 고정), body 는 작성자 lang_hint.
    # 토큰별 lang 으로 자동 번역(P8b push_to_users 통합) + 지원 외 → 영어 fallback.
    push_to_users(db, recipients,
                  title=notif['title'], body=notif['body'],
                  data={'type':         'notification',
                        'notification_id': nid,
                        'facility_id':     notif['facility_id']},
                  title_lang='ko',
                  body_lang=(notif['body_lang'] if 'body_lang' in notif.keys() else None))
    return True, 'sent', None


# ── 생성 ──────────────────────────────────────────────────────────────────────

@notification_bp.route('/api/facilities/<int:fid>/notifications', methods=['POST'])
@require_facility_actor(roles=['owner', 'admin'])
def create_notification(fid):
    """알림(부가서비스 푸시) 신청 — P11 워크플로.

    body: ``{title, body, target_type, user_ids?, scheduled_at}``
    - ``scheduled_at`` 필수 (now + 12h 이상)
    - quota 부족 → ``status='unpaid'`` (row 생성하되 발송 X, 결제 후 어드민이 활성화)
    - AI 자동 검토:
      * ``auto_pass`` → ``status='pending'`` (스케줄러가 시각 도래 시 dispatch)
      * ``flagged``  → ``status='review'``  (어드민 수동 승인 대기)
      * ``blocked``  → ``status='review'``  (사유 명시, 어드민이 reject 권장)

    즉시 발송 흐름은 제거됨 — 모든 알림은 12시간 후 스케줄러를 통해 발송.
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
    # P8c — 작성자(사장) 단말 언어. 발송 시 토큰 lang 으로 자동 번역.
    lang_hint = (data.get('lang_hint') or '').strip()
    body_lang = lang_hint if lang_hint in SUPPORTED_LANGS else None

    # ── 입력 검증 ─────────────────────────────────────────────────────────
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

    # ── P11: 12시간 리드타임 필수 ─────────────────────────────────────────
    if not scheduled_at_raw:
        return jsonify({'success': False,
                        'message': f'scheduled_at은 필수입니다 (최소 {_MIN_LEAD_HOURS}시간 이후).'}), 400
    try:
        # 2026-06-11 — JS toISOString() 의 'Z' 접미 대응 (theme.py 와 동일 패턴).
        # aware datetime 은 UTC naive 로 변환 — naive utcnow() 비교 시 TypeError(500) 방지.
        scheduled_dt = datetime.fromisoformat(scheduled_at_raw.replace('Z', '+00:00'))
        if scheduled_dt.tzinfo is not None:
            scheduled_dt = scheduled_dt.astimezone(timezone.utc).replace(tzinfo=None)
    except ValueError:
        return jsonify({'success': False,
                        'message': 'scheduled_at은 ISO 8601 형식이어야 합니다.'}), 400
    min_dt = datetime.utcnow() + timedelta(hours=_MIN_LEAD_HOURS)
    if scheduled_dt < min_dt:
        return jsonify({'success': False,
                        'message': f'발송 시각은 신청 시각으로부터 최소 {_MIN_LEAD_HOURS}시간 이후여야 합니다.'}), 400
    scheduled_at = scheduled_dt.isoformat()

    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    # ── 수신자 추정 (quota 검증용) ───────────────────────────────────────
    recipients_list = _resolve_recipients(
        db, fid, target_type,
        user_ids if target_type == 'specific' else None
    )
    needed = len(recipients_list)
    if needed == 0:
        db.close()
        return jsonify({'success': False,
                        'message': '발송 대상자가 없습니다.'}), 400

    # ── P11: quota 검증 ─────────────────────────────────────────────────
    available = get_available_quota(db, account_id)
    is_paid   = available >= needed

    # ── P11: AI 자동 검토 ───────────────────────────────────────────────
    ai_status, ai_reason = review_notification(db, title, body)

    # ── 상태 결정 ────────────────────────────────────────────────────────
    if not is_paid:
        status = 'unpaid'
    elif ai_status == 'auto_pass':
        status = 'pending'
    else:
        # flagged / blocked → 어드민 수동 검토 큐
        status = 'review'

    # ── INSERT ──────────────────────────────────────────────────────────
    cur = db.execute(
        """INSERT INTO notifications
             (facility_id, title, body, body_lang, target_type, scheduled_at,
              issued_by_actor_role, issued_by_actor_id, status,
              ai_review_status, ai_review_reason, recipient_count)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (fid, title, body, body_lang, target_type, scheduled_at,
         actor_role, actor_id, status,
         ai_status, ai_reason, needed)
    )
    nid = cur.lastrowid

    # specific 케이스는 수신자 목록을 미리 보존 (스케줄러가 발송 시 user_ids 가 사라지면 안 됨)
    if target_type == 'specific':
        for uid in recipients_list:
            db.execute(
                "INSERT OR IGNORE INTO notification_recipients (notification_id, user_id) VALUES (?,?)",
                (nid, uid)
            )

    row = db.execute("SELECT * FROM notifications WHERE id=?", (nid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({
        'success':         True,
        'message':         {
            'unpaid':  '결제 수량이 부족합니다. 푸시 수량을 충전 후 활성화됩니다.',
            'review':  '발송 전 운영팀 검토가 진행됩니다.',
            'pending': '알림이 예약되었습니다. 예약 시각에 발송됩니다.',
        }.get(status, '알림이 신청되었습니다.'),
        'notification':    _row_to_notification(row),
        'recipient_count': needed,
        'available_quota': available,
        'is_paid':         is_paid,
    }), 201


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
    # P11 — 발송 전 상태(pending/review/unpaid) 모두 취소 가능. sent/canceled 만 차단.
    if row['status'] in ('sent', 'canceled'):
        db.close()
        return jsonify({'success': False,
                        'message': f"이미 '{row['status']}' 상태인 알림은 취소할 수 없습니다."}), 409
    db.execute("UPDATE notifications SET status='canceled' WHERE id=?", (nid,))
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': '알림이 취소되었습니다.'})


# ── 사장 수동 발송 라우트 제거 (P11 정책: 발송은 어드민 서버 only) ─────────
# 기존 `POST /api/notifications/<nid>/dispatch` 는 제거. 어드민용은
# `POST /api/admin/notifications/<nid>/dispatch` 로 대체.


# ── 사장 quota 조회 (P11) ────────────────────────────────────────────────
@notification_bp.route('/api/facilities/<int:fid>/notifications/quota', methods=['GET'])
@require_facility_actor(roles=['owner', 'admin'])
def get_my_notification_quota(fid):
    """사장 본인의 푸시 quota 잔량 + 사용 통계.

    응답: ``{purchased, used, available, expired}``
    """
    account_id = g.auth['owner_account_id']
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    summary = quota_summary(db, account_id)
    db.close()
    return jsonify({'success': True, 'quota': summary})


# ── 사용자 인박스 ────────────────────────────────────────────────────────────

@notification_bp.route('/api/users/me/notifications/unread-count', methods=['GET'])
@require_auth(sub_type='user')
def my_notifications_unread_count():
    """본인 미읽음 알림 개수 (2026-06-08).

    탭/AppBar 뱃지용. body = ``{ success: true, count: int }``.
    """
    user_id = g.auth['user_id']
    db = get_db()
    row = db.execute(
        """SELECT COUNT(*) AS c
             FROM notification_recipients r
             JOIN notifications n ON r.notification_id = n.id
            WHERE r.user_id=? AND n.status='sent' AND r.read_at IS NULL""",
        (user_id,)
    ).fetchone()
    db.close()
    return jsonify({'success': True, 'count': int(row['c'] or 0)})


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


# ── 슈퍼어드민 라우트 (P11) ──────────────────────────────────────────────────
#
# 사장이 신청한 알림을 어드민이 검토·승인·발송하는 워크플로.
# 모든 라우트는 ``@require_super_admin`` 으로 보호.

_ADMIN_FILTER_STATUS = {'unpaid', 'review', 'pending', 'sent', 'canceled'}


@notification_bp.route('/api/admin/notifications', methods=['GET'])
@require_super_admin()
def admin_list_notifications():
    """전체 매장 알림 큐 — 어드민 인박스.

    필터: ?status=, ?facility_id=, ?ai_review_status=
    """
    status      = (request.args.get('status') or '').strip()
    fid_raw     = (request.args.get('facility_id') or '').strip()
    ai_status   = (request.args.get('ai_review_status') or '').strip()

    where, params = [], []
    if status:
        if status not in _ADMIN_FILTER_STATUS:
            return jsonify({'success': False,
                            'message': f'status 는 {sorted(_ADMIN_FILTER_STATUS)} 중 하나'}), 400
        where.append('n.status=?');           params.append(status)
    if fid_raw:
        try:
            where.append('n.facility_id=?'); params.append(int(fid_raw))
        except ValueError:
            return jsonify({'success': False, 'message': 'facility_id 는 정수.'}), 400
    if ai_status:
        where.append('n.ai_review_status=?'); params.append(ai_status)

    q = ("SELECT n.*, f.name AS facility_name "
         "FROM notifications n JOIN facilities f ON n.facility_id=f.id")
    if where:
        q += ' WHERE ' + ' AND '.join(where)
    # 검토 대기 우선 → 예약 시각 오름차순 → id 내림차순
    q += (" ORDER BY (n.status='review') DESC, "
          "(n.status='pending') DESC, "
          "n.scheduled_at ASC, n.id DESC LIMIT 200")

    db = get_db()
    rows = db.execute(q, params).fetchall()
    db.close()
    out = []
    for r in rows:
        item = _row_to_notification(r)
        item['facility_name'] = r['facility_name']
        out.append(item)
    return jsonify({'success': True, 'count': len(out), 'notifications': out})


@notification_bp.route('/api/admin/notifications/<int:nid>', methods=['GET'])
@require_super_admin()
def admin_get_notification(nid):
    """알림 상세 + 수신자 미리보기 (최대 20명)."""
    db = get_db()
    row = db.execute(
        """SELECT n.*, f.name AS facility_name
           FROM notifications n JOIN facilities f ON n.facility_id=f.id
           WHERE n.id=?""",
        (nid,)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '알림을 찾을 수 없습니다.'}), 404
    rcps_rows = db.execute(
        "SELECT user_id FROM notification_recipients WHERE notification_id=? LIMIT 20",
        (nid,)
    ).fetchall()
    db.close()
    item = _row_to_notification(row)
    item['facility_name']         = row['facility_name']
    item['recipients_preview']    = [r['user_id'] for r in rcps_rows]
    return jsonify({'success': True, 'notification': item})


@notification_bp.route('/api/admin/notifications/<int:nid>/approve', methods=['POST'])
@require_super_admin()
def admin_approve_notification(nid):
    """review 큐 승인 — status='pending' 으로 전환 + 검토 흔적 기록.

    스케줄러가 ``scheduled_at`` 도래 시 자동 발송 (또는 어드민이 즉시 dispatch).
    """
    admin_id = g.auth['user_id']
    db = get_db()
    row = db.execute("SELECT status FROM notifications WHERE id=?", (nid,)).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '알림을 찾을 수 없습니다.'}), 404
    if row['status'] not in ('review', 'unpaid'):
        db.close()
        return jsonify({'success': False,
                        'message': f"'{row['status']}' 상태에서는 승인할 수 없습니다."}), 409
    db.execute(
        """UPDATE notifications
             SET status='pending',
                 approved_by_admin_id=?,
                 approved_at=datetime('now')
           WHERE id=?""",
        (admin_id, nid)
    )
    new_row = db.execute("SELECT * FROM notifications WHERE id=?", (nid,)).fetchone()
    db.commit(); db.close()
    return jsonify({'success': True,
                    'message': '승인되었습니다. 예약 시각에 발송됩니다.',
                    'notification': _row_to_notification(new_row)})


@notification_bp.route('/api/admin/notifications/<int:nid>/reject', methods=['POST'])
@require_super_admin()
def admin_reject_notification(nid):
    """review 큐 거부 — status='canceled' + 검토 흔적 기록."""
    admin_id = g.auth['user_id']
    db = get_db()
    row = db.execute("SELECT status FROM notifications WHERE id=?", (nid,)).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '알림을 찾을 수 없습니다.'}), 404
    if row['status'] in ('sent', 'canceled'):
        db.close()
        return jsonify({'success': False,
                        'message': f"'{row['status']}' 상태에서는 거부할 수 없습니다."}), 409
    db.execute(
        """UPDATE notifications
             SET status='canceled',
                 approved_by_admin_id=?,
                 approved_at=datetime('now')
           WHERE id=?""",
        (admin_id, nid)
    )
    db.commit(); db.close()
    return jsonify({'success': True, 'message': '거부되었습니다.'})


@notification_bp.route('/api/admin/notifications/<int:nid>/dispatch', methods=['POST'])
@require_super_admin()
def admin_dispatch_notification(nid):
    """어드민 즉시 발송. quota 차감 + push. 12시간 정책 무시 (어드민 권한)."""
    db = get_db()
    ok, new_status, err = _dispatch(db, nid)
    if not ok:
        db.close()
        return jsonify({'success': False, 'status': new_status,
                        'message': err or '발송 실패'}), 409
    new_row = db.execute("SELECT * FROM notifications WHERE id=?", (nid,)).fetchone()
    db.commit(); db.close()
    return jsonify({'success': True,
                    'message': '알림이 발송되었습니다.',
                    'notification': _row_to_notification(new_row)})


# ── 어드민 금칙어 관리 ──────────────────────────────────────────────────────

_BLOCKLIST_SEVERITY = {'block', 'flag'}


@notification_bp.route('/api/admin/notifications/blocklist', methods=['GET'])
@require_super_admin()
def admin_list_blocklist():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM notification_blocklist ORDER BY (severity='block') DESC, id DESC"
    ).fetchall()
    db.close()
    return jsonify({'success': True,
                    'count': len(rows),
                    'blocklist': [dict(r) for r in rows]})


@notification_bp.route('/api/admin/notifications/blocklist', methods=['POST'])
@require_super_admin()
def admin_add_blocklist():
    admin_id = g.auth['user_id']
    data = request.get_json(silent=True) or {}
    term     = (data.get('term') or '').strip()
    severity = (data.get('severity') or 'flag').strip().lower()
    note     = (data.get('note') or '').strip() or None
    if not term:
        return jsonify({'success': False, 'message': 'term 은 필수.'}), 400
    if severity not in _BLOCKLIST_SEVERITY:
        return jsonify({'success': False,
                        'message': f'severity 는 {sorted(_BLOCKLIST_SEVERITY)} 중 하나.'}), 400
    db = get_db()
    try:
        cur = db.execute(
            """INSERT INTO notification_blocklist (term, severity, note, created_by_admin_id)
               VALUES (?,?,?,?)""",
            (term, severity, note, admin_id)
        )
        db.commit()
    except Exception:
        db.close()
        return jsonify({'success': False, 'message': '이미 등록된 단어입니다.'}), 409
    bid = cur.lastrowid
    row = db.execute("SELECT * FROM notification_blocklist WHERE id=?", (bid,)).fetchone()
    db.close()
    return jsonify({'success': True, 'blocklist': dict(row)}), 201


@notification_bp.route('/api/admin/notifications/blocklist/<int:bid>', methods=['DELETE'])
@require_super_admin()
def admin_delete_blocklist(bid):
    db = get_db()
    cur = db.execute("DELETE FROM notification_blocklist WHERE id=?", (bid,))
    db.commit()
    affected = cur.rowcount
    db.close()
    if affected == 0:
        return jsonify({'success': False, 'message': '단어를 찾을 수 없습니다.'}), 404
    return jsonify({'success': True})
