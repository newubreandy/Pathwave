"""채팅 API. SRS FR-CHAT-001/002.

엔드포인트
---------
- POST /api/facilities/<fid>/chat/rooms       방 생성/조회 (sub_type='user') — 사용자가 매장에 문의 시작
- GET  /api/chat/rooms                         내 방 목록 (user/facility-side 모두)
- GET  /api/chat/rooms/<rid>                   방 상세 (참여자만)
- GET  /api/chat/rooms/<rid>/messages          메시지 목록
- POST /api/chat/rooms/<rid>/messages          메시지 전송
- POST /api/chat/rooms/<rid>/read              내 측 미읽음 일괄 read

권한:
- 앱 사용자 (sub_type='user'): 본인 user_id 방
- facility-side (owner/admin/staff): 본인 owner_account_id 매장 방
- 채팅 응대는 staff도 OK (SRS staff 권한)
"""
from datetime import datetime
import jwt
from flask import Blueprint, request, jsonify, g

from models.database import get_db
from models.push import push_to_users
from routes.auth import require_auth, SECRET_KEY

chat_bp = Blueprint('chat', __name__)

_BODY_MAX = 2000


def _decode_optional(token: str) -> dict | None:
    if not token:
        return None
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except Exception:
        return None


def _resolve_actor():
    """user 또는 facility-side(facility/staff) 토큰 모두 허용. 정규화된 dict 반환:

      - kind: 'user' | 'facility'
      - user_id (kind='user') / owner_account_id, actor_role, actor_id (kind='facility')

    실패 시 None.
    """
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    payload = _decode_optional(auth.split(' ', 1)[1])
    if not payload or payload.get('kind', 'access') != 'access':
        return None
    sub = payload.get('sub_type', 'user')
    if sub == 'user':
        return {'kind': 'user', 'user_id': payload['user_id']}
    if sub == 'facility':
        return {'kind': 'facility',
                'owner_account_id': payload['user_id'],
                'actor_role': 'owner',
                'actor_id':   payload['user_id']}
    if sub == 'staff':
        return {'kind': 'facility',
                'owner_account_id': payload.get('owner_account_id'),
                'actor_role': payload.get('role'),
                'actor_id':   payload['user_id']}
    return None


def _row_to_room(row) -> dict:
    return {
        'id':              row['id'],
        'facility_id':     row['facility_id'],
        'user_id':         row['user_id'],
        'last_message_at': row['last_message_at'],
        'created_at':      row['created_at'],
    }


def _row_to_message(row) -> dict:
    return {
        'id':           row['id'],
        'room_id':      row['room_id'],
        'sender_type':  row['sender_type'],
        'sender_actor_role': row['sender_actor_role'],
        'sender_actor_id':   row['sender_actor_id'],
        'body':         row['body'],
        'read_at':      row['read_at'],
        'created_at':   row['created_at'],
    }


def _can_access_room(db, room, actor) -> bool:
    if not room:
        return False
    if actor['kind'] == 'user':
        return room['user_id'] == actor['user_id']
    # facility-side
    own = db.execute(
        "SELECT 1 FROM facilities WHERE id=? AND owner_id=? AND active=1",
        (room['facility_id'], actor['owner_account_id'])
    ).fetchone()
    return bool(own)


# ── 방 생성 (사용자 측에서 시작) ──────────────────────────────────────────────

@chat_bp.route('/api/facilities/<int:fid>/chat/rooms', methods=['POST'])
@require_auth(sub_type='user')
def create_or_get_room(fid):
    """사용자가 매장에 채팅 시작 — 방이 없으면 생성, 있으면 그대로."""
    user_id = g.auth['user_id']
    db = get_db()
    if not db.execute(
        "SELECT 1 FROM facilities WHERE id=? AND active=1", (fid,)
    ).fetchone():
        db.close()
        return jsonify({'success': False, 'message': '매장을 찾을 수 없습니다.'}), 404
    db.execute(
        "INSERT OR IGNORE INTO chat_rooms (facility_id, user_id) VALUES (?,?)",
        (fid, user_id)
    )
    row = db.execute(
        "SELECT * FROM chat_rooms WHERE facility_id=? AND user_id=?",
        (fid, user_id)
    ).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True, 'room': _row_to_room(row)}), 201


# ── 방 목록 / 상세 ────────────────────────────────────────────────────────────

@chat_bp.route('/api/chat/rooms', methods=['GET'])
def list_rooms():
    """본인 측의 방 목록. user는 본인 user_id, facility는 owner_account_id 매장의 모든 방."""
    actor = _resolve_actor()
    if not actor:
        return jsonify({'success': False, 'message': '인증 토큰이 필요합니다.'}), 401
    db = get_db()
    if actor['kind'] == 'user':
        rows = db.execute("""
            SELECT r.*, f.name AS facility_name,
                   (SELECT COUNT(*) FROM chat_messages m
                     WHERE m.room_id=r.id AND m.sender_type='facility' AND m.read_at IS NULL) AS unread,
                   (SELECT body FROM chat_messages m WHERE m.room_id=r.id ORDER BY id DESC LIMIT 1) AS last_body
            FROM chat_rooms r JOIN facilities f ON r.facility_id=f.id
            WHERE r.user_id=? ORDER BY COALESCE(r.last_message_at, r.created_at) DESC
        """, (actor['user_id'],)).fetchall()
    else:
        rows = db.execute("""
            SELECT r.*, u.email AS user_email, f.name AS facility_name,
                   (SELECT COUNT(*) FROM chat_messages m
                     WHERE m.room_id=r.id AND m.sender_type='user' AND m.read_at IS NULL) AS unread,
                   (SELECT body FROM chat_messages m WHERE m.room_id=r.id ORDER BY id DESC LIMIT 1) AS last_body
            FROM chat_rooms r
            JOIN facilities f ON r.facility_id=f.id
            JOIN users u ON r.user_id=u.id
            WHERE f.owner_id=? AND f.active=1
            ORDER BY COALESCE(r.last_message_at, r.created_at) DESC
        """, (actor['owner_account_id'],)).fetchall()
    db.close()
    out = []
    for r in rows:
        item = _row_to_room(r)
        item['unread']    = r['unread']
        item['last_body'] = r['last_body']
        item['facility_name'] = r['facility_name']
        if actor['kind'] == 'facility':
            item['user_email'] = r['user_email']
        out.append(item)
    return jsonify({'success': True, 'rooms': out})


@chat_bp.route('/api/chat/rooms/<int:rid>', methods=['GET'])
def room_detail(rid):
    actor = _resolve_actor()
    if not actor:
        return jsonify({'success': False, 'message': '인증 토큰이 필요합니다.'}), 401
    db = get_db()
    room = db.execute("SELECT * FROM chat_rooms WHERE id=?", (rid,)).fetchone()
    if not _can_access_room(db, room, actor):
        db.close()
        return jsonify({'success': False, 'message': '방을 찾을 수 없거나 권한이 없습니다.'}), 404
    db.close()
    return jsonify({'success': True, 'room': _row_to_room(room)})


# ── 메시지 ────────────────────────────────────────────────────────────────────

@chat_bp.route('/api/chat/rooms/<int:rid>/messages', methods=['GET'])
def list_messages(rid):
    """메시지 목록. ?after_id=N 으로 증분 폴링 지원."""
    actor = _resolve_actor()
    if not actor:
        return jsonify({'success': False, 'message': '인증 토큰이 필요합니다.'}), 401
    after = request.args.get('after_id', type=int)
    db = get_db()
    room = db.execute("SELECT * FROM chat_rooms WHERE id=?", (rid,)).fetchone()
    if not _can_access_room(db, room, actor):
        db.close()
        return jsonify({'success': False, 'message': '방을 찾을 수 없거나 권한이 없습니다.'}), 404
    if after:
        rows = db.execute(
            "SELECT * FROM chat_messages WHERE room_id=? AND id>? ORDER BY id ASC",
            (rid, after)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM chat_messages WHERE room_id=? ORDER BY id ASC",
            (rid,)
        ).fetchall()
    db.close()
    return jsonify({'success': True,
                    'messages': [_row_to_message(r) for r in rows]})


@chat_bp.route('/api/chat/rooms/<int:rid>/messages', methods=['POST'])
def send_message(rid):
    actor = _resolve_actor()
    if not actor:
        return jsonify({'success': False, 'message': '인증 토큰이 필요합니다.'}), 401
    data = request.get_json(silent=True) or {}
    body = (data.get('body') or '').strip()
    if not body or len(body) > _BODY_MAX:
        return jsonify({'success': False,
                        'message': f'body는 1~{_BODY_MAX}자여야 합니다.'}), 400

    db = get_db()
    room = db.execute("SELECT * FROM chat_rooms WHERE id=?", (rid,)).fetchone()
    if not _can_access_room(db, room, actor):
        db.close()
        return jsonify({'success': False, 'message': '방을 찾을 수 없거나 권한이 없습니다.'}), 404

    if actor['kind'] == 'user':
        sender_type = 'user'
        sender_role = None
        sender_id = actor['user_id']
    else:
        sender_type = 'facility'
        sender_role = actor['actor_role']
        sender_id = actor['actor_id']

    cur = db.execute(
        """INSERT INTO chat_messages (room_id, sender_type, sender_actor_role,
                                       sender_actor_id, body)
           VALUES (?,?,?,?,?)""",
        (rid, sender_type, sender_role, sender_id, body)
    )
    db.execute(
        "UPDATE chat_rooms SET last_message_at=datetime('now') WHERE id=?", (rid,)
    )
    new_row = db.execute("SELECT * FROM chat_messages WHERE id=?",
                         (cur.lastrowid,)).fetchone()

    # 상대방에게 푸시 (facility 측 송신 → user에게, user 송신 → facility 직원에게는 추후)
    if sender_type == 'facility':
        push_to_users(
            db, [room['user_id']],
            title=f'새 메시지',
            body=body[:120],
            data={'type': 'chat_message', 'room_id': rid}
        )
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': _row_to_message(new_row)}), 201


@chat_bp.route('/api/chat/rooms/<int:rid>/read', methods=['POST'])
def mark_room_read(rid):
    """내 측의 미읽음 메시지 일괄 read 표시. 멱등."""
    actor = _resolve_actor()
    if not actor:
        return jsonify({'success': False, 'message': '인증 토큰이 필요합니다.'}), 401
    db = get_db()
    room = db.execute("SELECT * FROM chat_rooms WHERE id=?", (rid,)).fetchone()
    if not _can_access_room(db, room, actor):
        db.close()
        return jsonify({'success': False, 'message': '방을 찾을 수 없거나 권한이 없습니다.'}), 404
    # 사용자는 facility 측 보낸 메시지를 read, facility 측은 user 측 메시지를 read
    other_side = 'facility' if actor['kind'] == 'user' else 'user'
    cur = db.execute(
        """UPDATE chat_messages SET read_at=datetime('now')
           WHERE room_id=? AND sender_type=? AND read_at IS NULL""",
        (rid, other_side)
    )
    db.commit()
    affected = cur.rowcount
    db.close()
    return jsonify({'success': True, 'read': affected})
