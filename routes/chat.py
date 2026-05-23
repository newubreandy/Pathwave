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
import json as _json
import time
import jwt
from flask import Blueprint, Response, request, jsonify, g

from models.database import get_db
from models.push import push_to_users
from models.translator import get_translator, TranslatorError
from routes.auth import require_auth, require_super_admin, SECRET_KEY
from routes.block import is_blocked
from services.translation_ai import SUPPORTED_LANGS, normalize_supported_lang

chat_bp = Blueprint('chat', __name__)

_BODY_MAX = 2000
_VIEWER_FALLBACK_LANG = 'en'                       # 지원 외 언어 → 영어 (P8b)
_SUPPORTED_VIEWER_LANGS = frozenset(SUPPORTED_LANGS)


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


# ── viewer 언어 결정 + 번역 캐시 (P8b) ──────────────────────────────────────

def _resolve_viewer_lang(actor, db) -> str:
    """viewer 언어 결정 — ?lang= 쿼리 > users.language > 매장(ko).

    화이트리스트 외 → 'en' (``normalize_supported_lang`` 적용).
    """
    q = (request.args.get('lang') or '').strip()
    if q:
        return normalize_supported_lang(q, fallback=_VIEWER_FALLBACK_LANG)
    if actor['kind'] == 'user':
        row = db.execute("SELECT language FROM users WHERE id=?",
                         (actor['user_id'],)).fetchone()
        if row and row['language']:
            return normalize_supported_lang(row['language'],
                                            fallback=_VIEWER_FALLBACK_LANG)
        return _VIEWER_FALLBACK_LANG
    # facility-side — 한국 사장 가정. 사장님이 외국어 단말이면 ?lang= 로 명시.
    return 'ko'


def _get_or_translate_chat(db, message_id: int, body: str,
                           body_lang: str | None, viewer_lang: str
                           ) -> tuple[str | None, str | None]:
    """채팅 메시지를 ``viewer_lang`` 으로 번역.

    캐시 적중 시 그대로, 미스 시 translator 호출 + cache upsert.
    번역이 불필요/실패 시 ``(None, None)`` — UI 는 원문만 표시.
    """
    if not body or not body_lang:
        return (None, None)
    if body_lang == viewer_lang:
        return (None, None)

    row = db.execute(
        """SELECT translated_text, provider FROM chat_message_translations
           WHERE message_id=? AND lang=?""",
        (message_id, viewer_lang)
    ).fetchone()
    if row:
        return (row['translated_text'], row['provider'])

    translator = get_translator()
    try:
        translated = translator.translate(body, source=body_lang, target=viewer_lang)
    except TranslatorError:
        return (None, None)
    if not translated or translated == body:
        return (None, None)

    db.execute(
        """INSERT OR IGNORE INTO chat_message_translations
             (message_id, lang, translated_text, provider)
           VALUES (?,?,?,?)""",
        (message_id, viewer_lang, translated, translator.name)
    )
    return (translated, translator.name)


def _row_to_message(row, *, viewer_lang: str | None = None, db=None) -> dict:
    """메시지 row → JSON. ``viewer_lang`` 지정 시 번역 머지(lazy + 캐시).

    응답 필드:
      - ``body``           : 원문
      - ``body_lang``      : 원문 언어 (lang_hint)
      - ``translated_text``: viewer_lang 으로 번역된 텍스트 (있을 때만)
      - ``translated_lang``: viewer_lang
    """
    body_lang = row['body_lang'] if 'body_lang' in row.keys() else None
    m = {
        'id':           row['id'],
        'room_id':      row['room_id'],
        'sender_type':  row['sender_type'],
        'sender_actor_role': row['sender_actor_role'],
        'sender_actor_id':   row['sender_actor_id'],
        'body':         row['body'],
        'body_lang':    body_lang,
        'read_at':      row['read_at'],
        'created_at':   row['created_at'],
    }
    if viewer_lang and db is not None:
        translated, provider = _get_or_translate_chat(
            db, row['id'], row['body'], body_lang, viewer_lang
        )
        if translated:
            m['translated_text']     = translated
            m['translated_lang']     = viewer_lang
            m['translated_provider'] = provider
    return m


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
            WHERE r.user_id=?
              AND NOT EXISTS (SELECT 1 FROM chat_blocks b
                               WHERE b.user_id=r.user_id AND b.facility_id=r.facility_id)
            ORDER BY COALESCE(r.last_message_at, r.created_at) DESC
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
              AND NOT EXISTS (SELECT 1 FROM chat_blocks b
                               WHERE b.user_id=r.user_id AND b.facility_id=r.facility_id)
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
    viewer_lang = _resolve_viewer_lang(actor, db)
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
    # 번역 캐시 미스 시 _row_to_message 가 upsert — commit 으로 반영.
    messages = [_row_to_message(r, viewer_lang=viewer_lang, db=db) for r in rows]
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'messages':    messages,
                    'viewer_lang': viewer_lang})


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

    # P8b — 클라이언트가 본인 단말 언어를 lang_hint 로 같이 보낸다.
    # 화이트리스트 외/누락 → NULL 저장 (수신 시 viewer 측에서 번역 시도 안 함).
    lang_hint = (data.get('lang_hint') or '').strip()
    body_lang = lang_hint if lang_hint in _SUPPORTED_VIEWER_LANGS else None

    db = get_db()
    room = db.execute("SELECT * FROM chat_rooms WHERE id=?", (rid,)).fetchone()
    if not _can_access_room(db, room, actor):
        db.close()
        return jsonify({'success': False, 'message': '방을 찾을 수 없거나 권한이 없습니다.'}), 404

    # 차단된 상대와는 양쪽 모두 메시지 전송 불가 (UGC 모더레이션).
    if is_blocked(db, room['user_id'], room['facility_id']):
        db.close()
        return jsonify({'success': False,
                        'message': '차단된 대화에는 메시지를 보낼 수 없습니다.'}), 403

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
                                       sender_actor_id, body, body_lang)
           VALUES (?,?,?,?,?,?)""",
        (rid, sender_type, sender_role, sender_id, body, body_lang)
    )
    db.execute(
        "UPDATE chat_rooms SET last_message_at=datetime('now') WHERE id=?", (rid,)
    )
    new_row = db.execute("SELECT * FROM chat_messages WHERE id=?",
                         (cur.lastrowid,)).fetchone()

    # 응답: sender 측 viewer_lang 으로 머지 (대부분 sender 본인 언어 = body_lang → 번역 없음).
    viewer_lang = _resolve_viewer_lang(actor, db)
    message_payload = _row_to_message(new_row, viewer_lang=viewer_lang, db=db)

    # 상대방에게 푸시 (facility 측 송신 → user에게, user 송신 → facility 직원에게는 추후)
    # P8b — title 은 시스템 문구(ko 고정), body 는 sender 의 lang_hint(body_lang).
    #       수신자 push_tokens.language 가 다르면 자동 번역, 지원 외 → 영어 fallback.
    if sender_type == 'facility':
        push_to_users(
            db, [room['user_id']],
            title='새 메시지',
            body=body[:120],
            data={'type': 'chat_message', 'room_id': rid},
            title_lang='ko',
            body_lang=body_lang,
        )
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': message_payload}), 201


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


# ── SSE 실시간 스트림 ────────────────────────────────────────────────────────

# 토큰을 URL 쿼리(?token=)로도 받음 — EventSource는 헤더 커스터마이징이 표준이 아니므로.
def _resolve_actor_with_query() -> dict | None:
    actor = _resolve_actor()
    if actor:
        return actor
    qtoken = (request.args.get('token') or '').strip()
    if not qtoken:
        return None
    payload = _decode_optional(qtoken)
    if not payload or payload.get('kind', 'access') != 'access':
        return None
    sub = payload.get('sub_type', 'user')
    if sub == 'user':
        return {'kind': 'user', 'user_id': payload['user_id']}
    if sub == 'facility':
        return {'kind': 'facility',
                'owner_account_id': payload['user_id'],
                'actor_role': 'owner', 'actor_id': payload['user_id']}
    if sub == 'staff':
        return {'kind': 'facility',
                'owner_account_id': payload.get('owner_account_id'),
                'actor_role': payload.get('role'), 'actor_id': payload['user_id']}
    return None


@chat_bp.route('/api/chat/rooms/<int:rid>/stream', methods=['GET'])
def stream_room(rid):
    """SSE 스트림 — 새 메시지가 들어오면 ``message`` 이벤트로 푸시.

    클라이언트:
        const es = new EventSource(`/api/chat/rooms/${rid}/stream?token=${access}`);
        es.addEventListener('message', e => { const m = JSON.parse(e.data); ... });

    헤더 토큰도 가능하지만 EventSource가 헤더 커스터마이징 미지원이라
    쿼리 파라미터(?token=...) 우선 지원.

    구현: 폴링 기반 (DB 2초 간격 체크). 운영 부하 시 Redis pub/sub 으로 진화.
    """
    actor = _resolve_actor_with_query()
    if not actor:
        return jsonify({'success': False, 'message': '인증 토큰이 필요합니다.'}), 401
    after_id = request.args.get('after_id', type=int) or 0

    db = get_db()
    room = db.execute("SELECT * FROM chat_rooms WHERE id=?", (rid,)).fetchone()
    if not _can_access_room(db, room, actor):
        db.close()
        return jsonify({'success': False,
                        'message': '방을 찾을 수 없거나 권한이 없습니다.'}), 404
    # SSE 연결 시작 시 한 번만 결정 (?lang= 쿼리 또는 users.language).
    viewer_lang = _resolve_viewer_lang(actor, db)
    db.close()

    poll_interval = 2.0           # 초
    keepalive_interval = 15       # 초마다 ping
    max_total_seconds = 60 * 5    # 5분 후 클라이언트 재연결 유도

    def gen():
        last_id = after_id
        last_keepalive = time.time()
        started = time.time()
        # 즉시 연결 확인용 retry 권장값
        yield 'retry: 5000\n\n'
        while True:
            # 새 메시지 가져오기 + viewer_lang 으로 번역 머지(필요 시 캐시 upsert)
            local_db = get_db()
            rows = local_db.execute(
                "SELECT * FROM chat_messages WHERE room_id=? AND id>? ORDER BY id ASC",
                (rid, last_id)
            ).fetchall()
            payloads = []
            for r in rows:
                payloads.append(
                    _row_to_message(r, viewer_lang=viewer_lang, db=local_db)
                )
                last_id = r['id']
            local_db.commit()  # 번역 캐시 upsert 반영
            local_db.close()
            for m in payloads:
                yield f'event: message\ndata: {_json.dumps(m, ensure_ascii=False)}\n\n'

            now = time.time()
            if now - last_keepalive >= keepalive_interval:
                yield ': keepalive\n\n'
                last_keepalive = now
            if now - started >= max_total_seconds:
                # 의도적 끊김 → 클라이언트 자동 재연결 (retry: 5000)
                return
            time.sleep(poll_interval)

    headers = {
        'Content-Type':         'text/event-stream',
        'Cache-Control':        'no-cache',
        'X-Accel-Buffering':    'no',
        'Connection':           'keep-alive',
    }
    return Response(gen(), headers=headers)
