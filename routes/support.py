"""고객센터 (Support) API — Phase I.

3 콘솔 공통 도메인. mobile=사용자 문의/신고, provider-web=사장님 문의,
admin-web=inbox/응답/통계/FAQ CRUD.

엔드포인트
---------
공개:
- GET  /api/faqs?kind=&lang=&category=          공개 FAQ 목록
- GET  /api/support/categories?kind=             지원 카테고리 (공개)

사용자/사장님 (require_auth):
- POST /api/support/tickets                      문의 생성 (kind 자동 인식)
- GET  /api/support/tickets/me                   본인 문의 목록
- GET  /api/support/tickets/<tid>                본인 문의 상세 (thread 포함)
- POST /api/support/tickets/<tid>/messages       본인 문의에 메시지 추가
- POST /api/reports                              신고 생성 (mobile)

어드민 (require_super_admin):
- GET   /api/admin/support/tickets?kind=&status= inbox
- GET   /api/admin/support/tickets/<tid>          상세
- POST  /api/admin/support/tickets/<tid>/reply    답변 (status=replied)
- PATCH /api/admin/support/tickets/<tid>          상태/카테고리/우선순위 변경
- GET   /api/admin/support/stats                  응답시간/처리량
- GET   /api/admin/support/categories             목록
- POST  /api/admin/support/categories             생성
- PATCH /api/admin/support/categories/<cid>       수정
- DELETE /api/admin/support/categories/<cid>      삭제
- GET   /api/admin/faqs?kind=&lang=               목록 (active 무시)
- POST  /api/admin/faqs                           생성
- PATCH /api/admin/faqs/<fid>                     수정
- DELETE /api/admin/faqs/<fid>                    삭제
- GET   /api/admin/reports?status=                 신고 목록
- PATCH /api/admin/reports/<rid>                  처리
"""
from __future__ import annotations

from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, g

from models.database import get_db
from models.rate_limit import limiter
from routes.auth import (
    require_auth, require_facility_actor, require_super_admin,
)
import jwt
import os

support_bp = Blueprint('support', __name__)

_VALID_STATUS  = {'open', 'replied', 'closed'}
_VALID_PRIORITY = {'low', 'normal', 'high', 'urgent'}
_VALID_KIND    = {'user', 'provider'}
_VALID_REPORT_TARGET = {'facility', 'user', 'review', 'chat'}
_VALID_REPORT_STATUS = {'pending', 'reviewing', 'resolved', 'rejected'}


# ── 공개: FAQ ────────────────────────────────────────────────────────────────

@support_bp.route('/api/faqs', methods=['GET'])
def list_faqs_public():
    """공개 FAQ. ``?kind=user|provider&lang=ko&category=beacon``."""
    kind     = (request.args.get('kind') or 'user').strip().lower()
    lang     = (request.args.get('lang') or 'ko').strip()
    category = (request.args.get('category') or '').strip()
    if kind not in _VALID_KIND:
        return jsonify({'success': False, 'message': 'kind 는 user|provider'}), 400

    db = get_db()
    sql = ("SELECT id, kind, category, question, answer, lang, sort_order "
           "FROM faqs WHERE kind=? AND lang=? AND active=1")
    args: list = [kind, lang]
    if category:
        sql += " AND category=?"
        args.append(category)
    sql += " ORDER BY sort_order, id"
    rows = db.execute(sql, args).fetchall()
    db.close()
    return jsonify({
        'success': True,
        'kind': kind, 'lang': lang,
        'faqs': [dict(r) for r in rows],
    })


# ── 공개: 카테고리 ──────────────────────────────────────────────────────────

@support_bp.route('/api/support/categories', methods=['GET'])
def list_categories_public():
    kind = (request.args.get('kind') or 'user').strip().lower()
    if kind not in _VALID_KIND:
        return jsonify({'success': False, 'message': 'kind 는 user|provider'}), 400
    db = get_db()
    rows = db.execute(
        """SELECT id, kind, code, label_key, sort_order
           FROM support_categories
           WHERE kind=? AND active=1
           ORDER BY sort_order, id""",
        (kind,)
    ).fetchall()
    db.close()
    return jsonify({'success': True, 'kind': kind,
                    'categories': [dict(r) for r in rows]})


# ── 인증 헬퍼: 토큰에서 kind 와 requester_id 추출 ────────────────────────────

def _resolve_requester() -> tuple[str, int] | None:
    """Authorization Bearer 토큰을 보고 (kind, requester_id) 반환.

    user 토큰  → ('user', users.id)
    facility/staff 토큰 → ('provider', facility_accounts.id)
    super_admin → 사용자 측 라우트에서는 None
    """
    auth_hdr = request.headers.get('Authorization', '')
    if not auth_hdr.startswith('Bearer '):
        return None
    try:
        secret = os.environ.get('SECRET_KEY', 'pathwave-super-secret-key-2024')
        payload = jwt.decode(auth_hdr.split(' ', 1)[1], secret, algorithms=['HS256'])
    except Exception:
        return None
    if payload.get('kind', 'access') != 'access':
        return None
    sub = payload.get('sub_type', 'user')
    if sub == 'user':
        return 'user', int(payload['user_id'])
    if sub == 'facility':
        return 'provider', int(payload['user_id'])
    if sub == 'staff':
        owner = payload.get('owner_account_id')
        if not owner:
            return None
        return 'provider', int(owner)
    return None


# ── 사용자/사장님: 문의 생성 ────────────────────────────────────────────────

@support_bp.route('/api/support/tickets', methods=['POST'])
@limiter.limit('20 per hour')
def create_ticket():
    who = _resolve_requester()
    if not who:
        return jsonify({'success': False, 'message': '인증이 필요합니다.'}), 401
    kind, requester_id = who

    data = request.get_json(silent=True) or {}
    category = (data.get('category') or '').strip()
    subject  = (data.get('subject')  or '').strip()
    body     = (data.get('body')     or '').strip()
    priority = (data.get('priority') or 'normal').strip().lower()
    if not category or not subject or not body:
        return jsonify({'success': False,
                        'message': 'category / subject / body 필수'}), 400
    if priority not in _VALID_PRIORITY:
        priority = 'normal'

    db = get_db()
    cur = db.execute(
        """INSERT INTO support_tickets
              (kind, requester_id, category, subject, body, status, priority)
           VALUES (?,?,?,?,?,?,?)""",
        (kind, requester_id, category, subject, body, 'open', priority)
    )
    tid = cur.lastrowid
    db.execute(
        """INSERT INTO support_messages (ticket_id, sender, sender_id, body)
           VALUES (?,?,?,?)""",
        (tid, kind, requester_id, body)
    )
    db.commit(); db.close()
    return jsonify({'success': True, 'ticket_id': tid,
                    'status': 'open', 'kind': kind}), 201


# ── 본인 문의 목록 ──────────────────────────────────────────────────────────

@support_bp.route('/api/support/tickets/me', methods=['GET'])
def my_tickets():
    who = _resolve_requester()
    if not who:
        return jsonify({'success': False, 'message': '인증이 필요합니다.'}), 401
    kind, requester_id = who

    db = get_db()
    rows = db.execute(
        """SELECT id, category, subject, status, priority,
                  created_at, updated_at, last_reply_at
           FROM support_tickets
           WHERE kind=? AND requester_id=?
           ORDER BY created_at DESC
           LIMIT 100""",
        (kind, requester_id)
    ).fetchall()
    db.close()
    return jsonify({'success': True, 'kind': kind,
                    'tickets': [dict(r) for r in rows]})


# ── 본인 문의 상세 (thread 포함) ────────────────────────────────────────────

@support_bp.route('/api/support/tickets/<int:tid>', methods=['GET'])
def my_ticket_detail(tid):
    who = _resolve_requester()
    if not who:
        return jsonify({'success': False, 'message': '인증이 필요합니다.'}), 401
    kind, requester_id = who

    db = get_db()
    ticket = db.execute(
        """SELECT * FROM support_tickets
           WHERE id=? AND kind=? AND requester_id=?""",
        (tid, kind, requester_id)
    ).fetchone()
    if not ticket:
        db.close()
        return jsonify({'success': False, 'message': '문의를 찾을 수 없습니다.'}), 404
    messages = db.execute(
        """SELECT id, sender, sender_id, body, created_at
           FROM support_messages WHERE ticket_id=? ORDER BY created_at""",
        (tid,)
    ).fetchall()
    db.close()
    return jsonify({'success': True,
                    'ticket': dict(ticket),
                    'messages': [dict(m) for m in messages]})


# ── 본인 문의에 메시지 추가 ─────────────────────────────────────────────────

@support_bp.route('/api/support/tickets/<int:tid>/messages', methods=['POST'])
@limiter.limit('30 per hour')
def my_ticket_reply(tid):
    who = _resolve_requester()
    if not who:
        return jsonify({'success': False, 'message': '인증이 필요합니다.'}), 401
    kind, requester_id = who

    data = request.get_json(silent=True) or {}
    body = (data.get('body') or '').strip()
    if not body:
        return jsonify({'success': False, 'message': 'body 필수'}), 400

    db = get_db()
    t = db.execute(
        "SELECT id, status FROM support_tickets WHERE id=? AND kind=? AND requester_id=?",
        (tid, kind, requester_id)
    ).fetchone()
    if not t:
        db.close()
        return jsonify({'success': False, 'message': '문의를 찾을 수 없습니다.'}), 404
    if t['status'] == 'closed':
        db.close()
        return jsonify({'success': False, 'message': '종결된 문의에는 메시지를 추가할 수 없습니다.'}), 409

    db.execute(
        """INSERT INTO support_messages (ticket_id, sender, sender_id, body)
           VALUES (?,?,?,?)""",
        (tid, kind, requester_id, body)
    )
    # 사용자가 메시지를 보내면 status='open' 으로 되돌려 운영자 응답 대기로 표시
    db.execute(
        "UPDATE support_tickets SET status='open', updated_at=datetime('now') WHERE id=?",
        (tid,)
    )
    db.commit(); db.close()
    return jsonify({'success': True})


# ── 신고 생성 (mobile/provider) ─────────────────────────────────────────────

@support_bp.route('/api/reports', methods=['POST'])
@limiter.limit('10 per hour')
def create_report():
    who = _resolve_requester()
    if not who:
        return jsonify({'success': False, 'message': '인증이 필요합니다.'}), 401
    kind, reporter_id = who

    data = request.get_json(silent=True) or {}
    target_kind = (data.get('target_kind') or '').strip().lower()
    target_id   = data.get('target_id')
    reason_code = (data.get('reason_code') or 'etc').strip().lower()
    reason_text = (data.get('reason_text') or '').strip()
    if target_kind not in _VALID_REPORT_TARGET or not target_id:
        return jsonify({'success': False,
                        'message': 'target_kind / target_id 필수'}), 400

    db = get_db()
    cur = db.execute(
        """INSERT INTO reports
             (target_kind, target_id, reporter_id, reporter_kind,
              reason_code, reason_text, status)
           VALUES (?,?,?,?,?,?, 'pending')""",
        (target_kind, int(target_id), reporter_id, kind, reason_code, reason_text)
    )
    rid = cur.lastrowid
    db.commit(); db.close()
    return jsonify({'success': True, 'report_id': rid, 'status': 'pending'}), 201


# ── ADMIN: inbox 목록 ───────────────────────────────────────────────────────

@support_bp.route('/api/admin/support/tickets', methods=['GET'])
@require_super_admin()
def admin_list_tickets():
    kind   = (request.args.get('kind')   or '').strip().lower()
    status = (request.args.get('status') or '').strip().lower()
    limit  = min(int(request.args.get('limit') or 100), 500)
    db = get_db()
    sql = "SELECT * FROM support_tickets WHERE 1=1"
    args: list = []
    if kind in _VALID_KIND:
        sql += " AND kind=?"; args.append(kind)
    if status in _VALID_STATUS:
        sql += " AND status=?"; args.append(status)
    sql += " ORDER BY (status='open') DESC, created_at DESC LIMIT ?"
    args.append(limit)
    rows = db.execute(sql, args).fetchall()
    db.close()
    return jsonify({'success': True, 'tickets': [dict(r) for r in rows]})


# ── ADMIN: 상세 ─────────────────────────────────────────────────────────────

@support_bp.route('/api/admin/support/tickets/<int:tid>', methods=['GET'])
@require_super_admin()
def admin_ticket_detail(tid):
    db = get_db()
    ticket = db.execute("SELECT * FROM support_tickets WHERE id=?", (tid,)).fetchone()
    if not ticket:
        db.close()
        return jsonify({'success': False, 'message': '문의를 찾을 수 없습니다.'}), 404
    messages = db.execute(
        "SELECT id, sender, sender_id, body, created_at FROM support_messages "
        "WHERE ticket_id=? ORDER BY created_at",
        (tid,)
    ).fetchall()
    # 요청자 정보 (이름/이메일) 표시용
    requester = None
    if ticket['kind'] == 'user':
        u = db.execute(
            "SELECT id, email FROM users WHERE id=?", (ticket['requester_id'],)
        ).fetchone()
        if u: requester = {'id': u['id'], 'email': u['email'], 'kind': 'user'}
    else:
        u = db.execute(
            "SELECT id, email, company_name FROM facility_accounts WHERE id=?",
            (ticket['requester_id'],)
        ).fetchone()
        if u:
            requester = {'id': u['id'], 'email': u['email'],
                         'company_name': u['company_name'], 'kind': 'provider'}
    db.close()
    return jsonify({'success': True,
                    'ticket': dict(ticket),
                    'requester': requester,
                    'messages': [dict(m) for m in messages]})


# ── ADMIN: 답변 ─────────────────────────────────────────────────────────────

@support_bp.route('/api/admin/support/tickets/<int:tid>/reply', methods=['POST'])
@require_super_admin()
def admin_reply(tid):
    data = request.get_json(silent=True) or {}
    body = (data.get('body') or '').strip()
    close = bool(data.get('close'))
    if not body:
        return jsonify({'success': False, 'message': 'body 필수'}), 400

    admin_id = int(g.auth['user_id'])
    db = get_db()
    t = db.execute("SELECT id, status FROM support_tickets WHERE id=?", (tid,)).fetchone()
    if not t:
        db.close()
        return jsonify({'success': False, 'message': '문의를 찾을 수 없습니다.'}), 404

    db.execute(
        """INSERT INTO support_messages (ticket_id, sender, sender_id, body)
           VALUES (?,?,?,?)""",
        (tid, 'admin', admin_id, body)
    )
    new_status = 'closed' if close else 'replied'
    closed_at  = "datetime('now')" if close else 'NULL'
    db.execute(
        f"""UPDATE support_tickets
            SET status=?, last_reply_at=datetime('now'),
                assigned_admin_id=?, updated_at=datetime('now'),
                closed_at=CASE WHEN ?=1 THEN datetime('now') ELSE closed_at END
            WHERE id=?""",
        (new_status, admin_id, 1 if close else 0, tid)
    )
    db.commit(); db.close()
    return jsonify({'success': True, 'status': new_status})


# ── ADMIN: PATCH (상태/카테고리/우선순위) ──────────────────────────────────

@support_bp.route('/api/admin/support/tickets/<int:tid>', methods=['PATCH'])
@require_super_admin()
def admin_patch_ticket(tid):
    data = request.get_json(silent=True) or {}
    fields: list[str] = []
    args:   list = []
    if 'status' in data:
        s = (data['status'] or '').strip().lower()
        if s not in _VALID_STATUS:
            return jsonify({'success': False, 'message': 'status 값 오류'}), 400
        fields.append('status=?'); args.append(s)
        if s == 'closed':
            fields.append("closed_at=datetime('now')")
    if 'priority' in data:
        p = (data['priority'] or '').strip().lower()
        if p not in _VALID_PRIORITY:
            return jsonify({'success': False, 'message': 'priority 값 오류'}), 400
        fields.append('priority=?'); args.append(p)
    if 'category' in data:
        c = (data['category'] or '').strip()
        if c:
            fields.append('category=?'); args.append(c)

    if not fields:
        return jsonify({'success': False, 'message': '수정할 필드가 없습니다.'}), 400

    fields.append("updated_at=datetime('now')")
    args.append(tid)
    db = get_db()
    db.execute(f"UPDATE support_tickets SET {', '.join(fields)} WHERE id=?", args)
    db.commit(); db.close()
    return jsonify({'success': True})


# ── ADMIN: stats (응답시간/처리량) ─────────────────────────────────────────

@support_bp.route('/api/admin/support/stats', methods=['GET'])
@require_super_admin()
def admin_stats():
    days = int(request.args.get('days') or 30)
    db = get_db()

    counts = db.execute(
        """SELECT kind, status, COUNT(*) AS n
           FROM support_tickets
           WHERE created_at >= datetime('now', ?)
           GROUP BY kind, status""",
        (f'-{days} days',)
    ).fetchall()

    # 평균 응답시간 (created_at → last_reply_at, replied/closed 만)
    avg_rows = db.execute(
        """SELECT kind,
                  AVG(CAST((julianday(last_reply_at) - julianday(created_at)) * 24 AS REAL))
                    AS avg_hours,
                  COUNT(*) AS replied_count
           FROM support_tickets
           WHERE last_reply_at IS NOT NULL
             AND created_at >= datetime('now', ?)
           GROUP BY kind""",
        (f'-{days} days',)
    ).fetchall()

    daily = db.execute(
        """SELECT strftime('%Y-%m-%d', created_at) AS day,
                  COUNT(*) AS created
           FROM support_tickets
           WHERE created_at >= datetime('now', ?)
           GROUP BY day ORDER BY day""",
        (f'-{days} days',)
    ).fetchall()

    open_now = db.execute(
        "SELECT kind, COUNT(*) AS n FROM support_tickets WHERE status='open' GROUP BY kind"
    ).fetchall()

    db.close()
    return jsonify({
        'success': True,
        'days': days,
        'counts': [dict(r) for r in counts],
        'avg_response': [dict(r) for r in avg_rows],
        'daily': [dict(r) for r in daily],
        'open_now': [dict(r) for r in open_now],
    })


# ── ADMIN: 카테고리 CRUD ───────────────────────────────────────────────────

@support_bp.route('/api/admin/support/categories', methods=['GET'])
@require_super_admin()
def admin_list_categories():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM support_categories ORDER BY kind, sort_order, id"
    ).fetchall()
    db.close()
    return jsonify({'success': True, 'categories': [dict(r) for r in rows]})


@support_bp.route('/api/admin/support/categories', methods=['POST'])
@require_super_admin()
def admin_create_category():
    data = request.get_json(silent=True) or {}
    kind = (data.get('kind') or '').strip().lower()
    code = (data.get('code') or '').strip()
    label_key = (data.get('label_key') or '').strip()
    sort_order = int(data.get('sort_order') or 0)
    if kind not in _VALID_KIND or not code or not label_key:
        return jsonify({'success': False, 'message': 'kind/code/label_key 필수'}), 400
    db = get_db()
    try:
        cur = db.execute(
            """INSERT INTO support_categories (kind, code, label_key, sort_order, active)
               VALUES (?,?,?,?,1)""",
            (kind, code, label_key, sort_order)
        )
        db.commit()
        cid = cur.lastrowid
    except Exception as e:
        db.close()
        return jsonify({'success': False, 'message': str(e)}), 400
    db.close()
    return jsonify({'success': True, 'id': cid}), 201


@support_bp.route('/api/admin/support/categories/<int:cid>', methods=['PATCH'])
@require_super_admin()
def admin_update_category(cid):
    data = request.get_json(silent=True) or {}
    fields: list[str] = []
    args:   list = []
    for k in ('label_key', 'code'):
        if k in data:
            fields.append(f'{k}=?'); args.append((data[k] or '').strip())
    if 'sort_order' in data:
        fields.append('sort_order=?'); args.append(int(data['sort_order'] or 0))
    if 'active' in data:
        fields.append('active=?'); args.append(1 if data['active'] else 0)
    if not fields:
        return jsonify({'success': False, 'message': '수정할 필드가 없습니다.'}), 400
    args.append(cid)
    db = get_db()
    db.execute(f"UPDATE support_categories SET {', '.join(fields)} WHERE id=?", args)
    db.commit(); db.close()
    return jsonify({'success': True})


@support_bp.route('/api/admin/support/categories/<int:cid>', methods=['DELETE'])
@require_super_admin()
def admin_delete_category(cid):
    db = get_db()
    db.execute("DELETE FROM support_categories WHERE id=?", (cid,))
    db.commit(); db.close()
    return jsonify({'success': True})


# ── ADMIN: FAQ CRUD ─────────────────────────────────────────────────────────

@support_bp.route('/api/admin/faqs', methods=['GET'])
@require_super_admin()
def admin_list_faqs():
    kind = (request.args.get('kind') or '').strip().lower()
    lang = (request.args.get('lang') or '').strip()
    db = get_db()
    sql = "SELECT * FROM faqs WHERE 1=1"
    args: list = []
    if kind in _VALID_KIND:
        sql += " AND kind=?"; args.append(kind)
    if lang:
        sql += " AND lang=?"; args.append(lang)
    sql += " ORDER BY kind, lang, sort_order, id"
    rows = db.execute(sql, args).fetchall()
    db.close()
    return jsonify({'success': True, 'faqs': [dict(r) for r in rows]})


@support_bp.route('/api/admin/faqs', methods=['POST'])
@require_super_admin()
def admin_create_faq():
    data = request.get_json(silent=True) or {}
    kind = (data.get('kind') or '').strip().lower()
    category = (data.get('category') or '').strip()
    question = (data.get('question') or '').strip()
    answer   = (data.get('answer') or '').strip()
    lang     = (data.get('lang') or 'ko').strip()
    sort_order = int(data.get('sort_order') or 0)
    active   = 1 if data.get('active', True) else 0
    if kind not in _VALID_KIND or not category or not question or not answer:
        return jsonify({'success': False,
                        'message': 'kind/category/question/answer 필수'}), 400
    db = get_db()
    cur = db.execute(
        """INSERT INTO faqs (kind, category, question, answer, lang, sort_order, active)
           VALUES (?,?,?,?,?,?,?)""",
        (kind, category, question, answer, lang, sort_order, active)
    )
    db.commit()
    fid = cur.lastrowid
    db.close()
    return jsonify({'success': True, 'id': fid}), 201


@support_bp.route('/api/admin/faqs/<int:fid>', methods=['PATCH'])
@require_super_admin()
def admin_update_faq(fid):
    data = request.get_json(silent=True) or {}
    fields: list[str] = []
    args:   list = []
    for k in ('category', 'question', 'answer', 'lang'):
        if k in data:
            fields.append(f'{k}=?'); args.append((data[k] or '').strip())
    if 'sort_order' in data:
        fields.append('sort_order=?'); args.append(int(data['sort_order'] or 0))
    if 'active' in data:
        fields.append('active=?'); args.append(1 if data['active'] else 0)
    if not fields:
        return jsonify({'success': False, 'message': '수정할 필드가 없습니다.'}), 400
    fields.append("updated_at=datetime('now')")
    args.append(fid)
    db = get_db()
    db.execute(f"UPDATE faqs SET {', '.join(fields)} WHERE id=?", args)
    db.commit(); db.close()
    return jsonify({'success': True})


@support_bp.route('/api/admin/faqs/<int:fid>', methods=['DELETE'])
@require_super_admin()
def admin_delete_faq(fid):
    db = get_db()
    db.execute("DELETE FROM faqs WHERE id=?", (fid,))
    db.commit(); db.close()
    return jsonify({'success': True})


# ── ADMIN: 신고 처리 ───────────────────────────────────────────────────────

@support_bp.route('/api/admin/reports', methods=['GET'])
@require_super_admin()
def admin_list_reports():
    status = (request.args.get('status') or '').strip().lower()
    db = get_db()
    sql = "SELECT * FROM reports WHERE 1=1"
    args: list = []
    if status in _VALID_REPORT_STATUS:
        sql += " AND status=?"; args.append(status)
    sql += " ORDER BY (status='pending') DESC, created_at DESC LIMIT 200"
    rows = db.execute(sql, args).fetchall()
    db.close()
    return jsonify({'success': True, 'reports': [dict(r) for r in rows]})


@support_bp.route('/api/admin/reports/<int:rid>', methods=['PATCH'])
@require_super_admin()
def admin_patch_report(rid):
    data = request.get_json(silent=True) or {}
    new_status = (data.get('status') or '').strip().lower()
    note = (data.get('handled_note') or '').strip()
    if new_status not in _VALID_REPORT_STATUS:
        return jsonify({'success': False, 'message': 'status 값 오류'}), 400
    admin_id = int(g.auth['user_id'])
    db = get_db()
    db.execute(
        """UPDATE reports
           SET status=?, handled_admin_id=?, handled_at=datetime('now'),
               handled_note=?
           WHERE id=?""",
        (new_status, admin_id, note or None, rid)
    )
    db.commit(); db.close()
    return jsonify({'success': True})
