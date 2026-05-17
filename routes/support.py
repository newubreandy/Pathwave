"""Phase I — 고객센터 / 1:1 문의 (support tickets + messages + categories).

엔드포인트
---------
사용자 / 사장 (kind 토큰 sub_type 으로 자동 분기):
- POST   /api/support/tickets                 문의 작성
- GET    /api/support/tickets/me              본인 문의 목록
- GET    /api/support/tickets/me/<tid>        본인 문의 상세 (+messages thread)
- POST   /api/support/tickets/me/<tid>/messages  사용자 추가 메시지 (status=open)

운영자 (super admin):
- GET    /api/admin/support/tickets?kind=&status=  inbox
- GET    /api/admin/support/tickets/<tid>          상세 (+messages)
- POST   /api/admin/support/tickets/<tid>/reply    body {body} → support_messages + status=replied
- PATCH  /api/admin/support/tickets/<tid>          body {status, priority} 변경
- GET    /api/admin/support/categories             카테고리 목록
- POST   /api/admin/support/categories             카테고리 추가
- PATCH  /api/admin/support/categories/<cid>       수정
- DELETE /api/admin/support/categories/<cid>       (active=0 으로 soft-delete)
- GET    /api/admin/support/stats                  응답시간 / 처리량 통계

memory ui_legal_compliance: 영업시간(평일 09:00~18:00) + 응답 예상시간(영업일 1~3일)
+ 개인정보 처리 안내는 UI 텍스트에서 표시 (i18n 키).
"""
from __future__ import annotations

from flask import Blueprint, request, jsonify, g

from models.database import get_db
from routes.auth import require_auth, require_facility_actor, require_super_admin

support_bp = Blueprint('support', __name__)


# ── helpers ───────────────────────────────────────────────────────────────────

_ALLOWED_STATUS = {'open', 'replied', 'closed'}
_ALLOWED_PRIORITY = {'low', 'normal', 'high', 'urgent'}
_ALLOWED_KIND = {'user', 'provider'}


def _row_to_ticket(row) -> dict:
    return {
        'id':         row['id'],
        'kind':       row['kind'],
        'user_id':    row['user_id'],
        'facility_account_id': row['facility_account_id'],
        'category':   row['category'],
        'subject':    row['subject'],
        'body':       row['body'],
        'status':     row['status'],
        'priority':   row['priority'],
        'replied_at': row['replied_at'],
        'closed_at':  row['closed_at'],
        'created_at': row['created_at'],
        'updated_at': row['updated_at'],
    }


def _row_to_message(row) -> dict:
    return {
        'id':         row['id'],
        'ticket_id':  row['ticket_id'],
        'sender':     row['sender'],
        'sender_admin_id': row['sender_admin_id'],
        'body':       row['body'],
        'created_at': row['created_at'],
    }


# ── 사용자/사장 — 문의 작성 (sub_type 자동 판별) ─────────────────────────────

def _detect_kind_and_caller_id():
    """현재 요청 토큰에서 kind / caller_id (user_id or facility_account_id) 추출.

    @require_auth(sub_type='user') 데코레이터 또는 @require_facility_actor 둘 다
    지원하려면, 라우트에 별도 어떤 데코로 진입했는지 알 수 없다. 따라서 두 라우트
    경로(`/api/support/tickets`) 를 sub_type 별로 따로 노출하지 않고, 헤더 토큰을
    직접 디코드해서 sub_type 으로 분기한다.
    """
    from routes.auth import SECRET_KEY
    import jwt as _jwt
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None, None
    try:
        payload = _jwt.decode(auth.split(' ', 1)[1], SECRET_KEY, algorithms=['HS256'])
    except Exception:
        return None, None
    sub_type = payload.get('sub_type', 'user')
    if sub_type == 'user':
        return 'user', payload.get('user_id')
    if sub_type == 'facility':
        return 'provider', payload.get('user_id')  # facility_account.id
    return None, None


@support_bp.route('/api/support/tickets', methods=['POST'])
def create_ticket():
    kind, caller_id = _detect_kind_and_caller_id()
    if not kind or not caller_id:
        return jsonify({'success': False, 'message': '사용자 또는 사장 토큰이 필요합니다.'}), 401

    data = request.get_json(silent=True) or {}
    subject = (data.get('subject') or '').strip()
    body    = (data.get('body') or '').strip()
    category = (data.get('category') or '').strip() or None
    if not subject or not body:
        return jsonify({'success': False, 'message': 'subject 와 body 는 필수입니다.'}), 400

    db = get_db()
    cur = db.execute(
        """INSERT INTO support_tickets
             (kind, user_id, facility_account_id, category, subject, body)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (kind,
         caller_id if kind == 'user' else None,
         caller_id if kind == 'provider' else None,
         category, subject, body)
    )
    tid = cur.lastrowid
    # 최초 본문은 자동으로 message 1개로 기록 (사용자 thread 첫 줄)
    db.execute(
        """INSERT INTO support_messages (ticket_id, sender, body)
           VALUES (?, 'user', ?)""",
        (tid, body)
    )
    db.commit()
    row = db.execute("SELECT * FROM support_tickets WHERE id=?", (tid,)).fetchone()
    db.close()
    return jsonify({'success': True, 'ticket': _row_to_ticket(row)}), 201


@support_bp.route('/api/support/tickets/me', methods=['GET'])
def list_my_tickets():
    kind, caller_id = _detect_kind_and_caller_id()
    if not kind or not caller_id:
        return jsonify({'success': False, 'message': '인증이 필요합니다.'}), 401

    db = get_db()
    if kind == 'user':
        rows = db.execute(
            """SELECT * FROM support_tickets WHERE kind='user' AND user_id=?
               ORDER BY id DESC""",
            (caller_id,)
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT * FROM support_tickets WHERE kind='provider' AND facility_account_id=?
               ORDER BY id DESC""",
            (caller_id,)
        ).fetchall()
    db.close()
    return jsonify({'success': True,
                    'count': len(rows),
                    'tickets': [_row_to_ticket(r) for r in rows]})


@support_bp.route('/api/support/tickets/me/<int:tid>', methods=['GET'])
def get_my_ticket(tid: int):
    kind, caller_id = _detect_kind_and_caller_id()
    if not kind or not caller_id:
        return jsonify({'success': False, 'message': '인증이 필요합니다.'}), 401

    db = get_db()
    if kind == 'user':
        ticket = db.execute(
            """SELECT * FROM support_tickets
               WHERE id=? AND kind='user' AND user_id=?""",
            (tid, caller_id)
        ).fetchone()
    else:
        ticket = db.execute(
            """SELECT * FROM support_tickets
               WHERE id=? AND kind='provider' AND facility_account_id=?""",
            (tid, caller_id)
        ).fetchone()
    if not ticket:
        db.close()
        return jsonify({'success': False, 'message': '문의를 찾을 수 없습니다.'}), 404

    messages = db.execute(
        "SELECT * FROM support_messages WHERE ticket_id=? ORDER BY id ASC",
        (tid,)
    ).fetchall()
    db.close()
    return jsonify({
        'success': True,
        'ticket': _row_to_ticket(ticket),
        'messages': [_row_to_message(m) for m in messages],
    })


@support_bp.route('/api/support/tickets/me/<int:tid>/messages', methods=['POST'])
def add_my_message(tid: int):
    """사용자가 운영자 답변 이후 추가 메시지를 보내는 경우 — status=open 재오픈."""
    kind, caller_id = _detect_kind_and_caller_id()
    if not kind or not caller_id:
        return jsonify({'success': False, 'message': '인증이 필요합니다.'}), 401

    data = request.get_json(silent=True) or {}
    body = (data.get('body') or '').strip()
    if not body:
        return jsonify({'success': False, 'message': 'body 가 필요합니다.'}), 400

    db = get_db()
    if kind == 'user':
        owned = db.execute(
            "SELECT id FROM support_tickets WHERE id=? AND kind='user' AND user_id=?",
            (tid, caller_id)
        ).fetchone()
    else:
        owned = db.execute(
            "SELECT id FROM support_tickets WHERE id=? AND kind='provider' AND facility_account_id=?",
            (tid, caller_id)
        ).fetchone()
    if not owned:
        db.close()
        return jsonify({'success': False, 'message': '문의를 찾을 수 없습니다.'}), 404

    db.execute(
        """INSERT INTO support_messages (ticket_id, sender, body)
           VALUES (?, 'user', ?)""",
        (tid, body)
    )
    db.execute(
        """UPDATE support_tickets SET status='open',
                   updated_at=datetime('now') WHERE id=?""",
        (tid,)
    )
    db.commit(); db.close()
    return jsonify({'success': True}), 201


# ── 운영자 (super admin) — inbox / 상세 / 답변 / 상태 ──────────────────────────

@support_bp.route('/api/admin/support/tickets', methods=['GET'])
@require_super_admin()
def admin_list_tickets():
    kind   = (request.args.get('kind') or '').strip()
    status = (request.args.get('status') or '').strip()
    q = "SELECT * FROM support_tickets"
    where, params = [], []
    if kind:
        if kind not in _ALLOWED_KIND:
            return jsonify({'success': False, 'message': f'kind 는 {_ALLOWED_KIND}'}), 400
        where.append("kind=?"); params.append(kind)
    if status:
        if status not in _ALLOWED_STATUS:
            return jsonify({'success': False, 'message': f'status 는 {_ALLOWED_STATUS}'}), 400
        where.append("status=?"); params.append(status)
    if where:
        q += " WHERE " + " AND ".join(where)
    q += " ORDER BY (status='open') DESC, priority='urgent' DESC, id DESC"

    db = get_db()
    rows = db.execute(q, params).fetchall()
    db.close()
    return jsonify({'success': True, 'count': len(rows),
                    'tickets': [_row_to_ticket(r) for r in rows]})


@support_bp.route('/api/admin/support/tickets/<int:tid>', methods=['GET'])
@require_super_admin()
def admin_get_ticket(tid: int):
    db = get_db()
    ticket = db.execute("SELECT * FROM support_tickets WHERE id=?", (tid,)).fetchone()
    if not ticket:
        db.close()
        return jsonify({'success': False, 'message': '문의를 찾을 수 없습니다.'}), 404
    messages = db.execute(
        "SELECT * FROM support_messages WHERE ticket_id=? ORDER BY id ASC", (tid,)
    ).fetchall()
    db.close()
    return jsonify({
        'success': True,
        'ticket': _row_to_ticket(ticket),
        'messages': [_row_to_message(m) for m in messages],
    })


@support_bp.route('/api/admin/support/tickets/<int:tid>/reply', methods=['POST'])
@require_super_admin()
def admin_reply(tid: int):
    admin_id = g.auth['user_id']
    data = request.get_json(silent=True) or {}
    body = (data.get('body') or '').strip()
    if not body:
        return jsonify({'success': False, 'message': 'body 가 필요합니다.'}), 400

    db = get_db()
    if not db.execute("SELECT id FROM support_tickets WHERE id=?", (tid,)).fetchone():
        db.close()
        return jsonify({'success': False, 'message': '문의를 찾을 수 없습니다.'}), 404

    db.execute(
        """INSERT INTO support_messages
             (ticket_id, sender, sender_admin_id, body)
           VALUES (?, 'admin', ?, ?)""",
        (tid, admin_id, body)
    )
    db.execute(
        """UPDATE support_tickets
           SET status='replied', replied_at=datetime('now'),
               updated_at=datetime('now')
           WHERE id=?""",
        (tid,)
    )
    db.commit(); db.close()
    return jsonify({'success': True}), 201


@support_bp.route('/api/admin/support/tickets/<int:tid>', methods=['PATCH'])
@require_super_admin()
def admin_patch_ticket(tid: int):
    data = request.get_json(silent=True) or {}
    db = get_db()
    if not db.execute("SELECT id FROM support_tickets WHERE id=?", (tid,)).fetchone():
        db.close()
        return jsonify({'success': False, 'message': '문의를 찾을 수 없습니다.'}), 404

    sets, params = [], []
    if 'status' in data:
        s = data['status']
        if s not in _ALLOWED_STATUS:
            db.close()
            return jsonify({'success': False, 'message': f'status 는 {_ALLOWED_STATUS}'}), 400
        sets.append("status=?"); params.append(s)
        if s == 'closed':
            sets.append("closed_at=datetime('now')")
    if 'priority' in data:
        p = data['priority']
        if p not in _ALLOWED_PRIORITY:
            db.close()
            return jsonify({'success': False, 'message': f'priority 는 {_ALLOWED_PRIORITY}'}), 400
        sets.append("priority=?"); params.append(p)
    if not sets:
        db.close()
        return jsonify({'success': False, 'message': '변경할 필드가 없습니다.'}), 400
    sets.append("updated_at=datetime('now')")
    params.append(tid)
    db.execute(f"UPDATE support_tickets SET {', '.join(sets)} WHERE id=?", params)
    db.commit(); db.close()
    return jsonify({'success': True})


# ── 카테고리 마스터 (어드민) ─────────────────────────────────────────────────

@support_bp.route('/api/admin/support/categories', methods=['GET'])
@require_super_admin()
def admin_list_categories():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM support_categories ORDER BY kind, sort_order, id"
    ).fetchall()
    db.close()
    return jsonify({'success': True,
                    'categories': [dict(r) for r in rows]})


@support_bp.route('/api/admin/support/categories', methods=['POST'])
@require_super_admin()
def admin_add_category():
    data = request.get_json(silent=True) or {}
    kind = (data.get('kind') or '').strip()
    code = (data.get('code') or '').strip()
    label_key = (data.get('label_key') or '').strip()
    sort_order = data.get('sort_order') or 0
    if kind not in _ALLOWED_KIND or not code or not label_key:
        return jsonify({'success': False, 'message': 'kind/code/label_key 필수'}), 400
    db = get_db()
    try:
        cur = db.execute(
            """INSERT INTO support_categories (kind, code, label_key, sort_order)
               VALUES (?,?,?,?)""",
            (kind, code, label_key, int(sort_order))
        )
        db.commit()
        cid = cur.lastrowid
    except Exception as e:
        db.close()
        return jsonify({'success': False, 'message': f'중복 또는 오류: {e}'}), 409
    db.close()
    return jsonify({'success': True, 'id': cid}), 201


@support_bp.route('/api/admin/support/categories/<int:cid>', methods=['PATCH'])
@require_super_admin()
def admin_patch_category(cid: int):
    data = request.get_json(silent=True) or {}
    db = get_db()
    if not db.execute("SELECT id FROM support_categories WHERE id=?", (cid,)).fetchone():
        db.close()
        return jsonify({'success': False, 'message': '카테고리를 찾을 수 없습니다.'}), 404
    sets, params = [], []
    for f in ('label_key', 'sort_order', 'active'):
        if f in data:
            sets.append(f"{f}=?")
            params.append(data[f])
    if not sets:
        db.close()
        return jsonify({'success': False, 'message': '변경할 필드 없음'}), 400
    params.append(cid)
    db.execute(f"UPDATE support_categories SET {', '.join(sets)} WHERE id=?", params)
    db.commit(); db.close()
    return jsonify({'success': True})


@support_bp.route('/api/admin/support/categories/<int:cid>', methods=['DELETE'])
@require_super_admin()
def admin_delete_category(cid: int):
    db = get_db()
    db.execute("UPDATE support_categories SET active=0 WHERE id=?", (cid,))
    db.commit(); db.close()
    return jsonify({'success': True})


# ── 운영자 통계 ─────────────────────────────────────────────────────────────

@support_bp.route('/api/admin/support/stats', methods=['GET'])
@require_super_admin()
def admin_stats():
    db = get_db()
    total      = db.execute("SELECT COUNT(*) AS n FROM support_tickets").fetchone()['n']
    open_cnt   = db.execute("SELECT COUNT(*) AS n FROM support_tickets WHERE status='open'").fetchone()['n']
    replied    = db.execute("SELECT COUNT(*) AS n FROM support_tickets WHERE status='replied'").fetchone()['n']
    closed     = db.execute("SELECT COUNT(*) AS n FROM support_tickets WHERE status='closed'").fetchone()['n']
    by_kind    = db.execute(
        "SELECT kind, COUNT(*) AS n FROM support_tickets GROUP BY kind"
    ).fetchall()
    # 평균 응답시간 (분) — replied_at - created_at, SQLite julianday
    avg_resp = db.execute(
        """SELECT AVG((julianday(replied_at) - julianday(created_at)) * 1440.0) AS avg_min
           FROM support_tickets WHERE replied_at IS NOT NULL"""
    ).fetchone()['avg_min']
    db.close()
    return jsonify({
        'success': True,
        'total': total,
        'open': open_cnt,
        'replied': replied,
        'closed': closed,
        'by_kind': {r['kind']: r['n'] for r in by_kind},
        'avg_response_minutes': round(avg_resp, 1) if avg_resp else None,
    })
