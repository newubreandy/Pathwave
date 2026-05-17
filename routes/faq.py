"""Phase I — FAQ (사용자/사장 분리, 언어별, 어드민 CRUD).

엔드포인트
---------
- GET    /api/faqs?kind=&lang=    공개 (인증 불필요)
- GET    /api/admin/faqs          어드민 전체 (active 포함)
- POST   /api/admin/faqs
- PATCH  /api/admin/faqs/<fid>
- DELETE /api/admin/faqs/<fid>    (active=0 soft-delete)
"""
from __future__ import annotations

from flask import Blueprint, request, jsonify

from models.database import get_db
from routes.auth import require_super_admin

faq_bp = Blueprint('faq', __name__)


_ALLOWED_KIND = {'user', 'provider'}


def _row_to_faq(row) -> dict:
    return {
        'id':         row['id'],
        'kind':       row['kind'],
        'category':   row['category'],
        'question':   row['question'],
        'answer':     row['answer'],
        'lang':       row['lang'],
        'sort_order': row['sort_order'],
        'active':     bool(row['active']),
        'created_at': row['created_at'],
        'updated_at': row['updated_at'],
    }


@faq_bp.route('/api/faqs', methods=['GET'])
def list_public():
    kind = (request.args.get('kind') or 'user').strip()
    lang = (request.args.get('lang') or 'ko').strip()
    db = get_db()
    rows = db.execute(
        """SELECT * FROM faqs
           WHERE kind=? AND lang=? AND active=1
           ORDER BY category, sort_order, id""",
        (kind, lang)
    ).fetchall()
    db.close()
    return jsonify({'success': True,
                    'count': len(rows),
                    'faqs': [_row_to_faq(r) for r in rows]})


@faq_bp.route('/api/admin/faqs', methods=['GET'])
@require_super_admin()
def admin_list():
    kind = (request.args.get('kind') or '').strip()
    lang = (request.args.get('lang') or '').strip()
    q = "SELECT * FROM faqs"
    where, params = [], []
    if kind:
        where.append("kind=?"); params.append(kind)
    if lang:
        where.append("lang=?"); params.append(lang)
    if where:
        q += " WHERE " + " AND ".join(where)
    q += " ORDER BY kind, category, sort_order, id"
    db = get_db()
    rows = db.execute(q, params).fetchall()
    db.close()
    return jsonify({'success': True, 'count': len(rows),
                    'faqs': [_row_to_faq(r) for r in rows]})


@faq_bp.route('/api/admin/faqs', methods=['POST'])
@require_super_admin()
def admin_add():
    data = request.get_json(silent=True) or {}
    kind     = (data.get('kind') or '').strip()
    question = (data.get('question') or '').strip()
    answer   = (data.get('answer') or '').strip()
    category = (data.get('category') or '').strip() or None
    lang     = (data.get('lang') or 'ko').strip()
    sort_order = int(data.get('sort_order') or 0)
    if kind not in _ALLOWED_KIND or not question or not answer:
        return jsonify({'success': False, 'message': 'kind / question / answer 필수'}), 400
    db = get_db()
    cur = db.execute(
        """INSERT INTO faqs (kind, category, question, answer, lang, sort_order)
           VALUES (?,?,?,?,?,?)""",
        (kind, category, question, answer, lang, sort_order)
    )
    db.commit()
    fid = cur.lastrowid
    row = db.execute("SELECT * FROM faqs WHERE id=?", (fid,)).fetchone()
    db.close()
    return jsonify({'success': True, 'faq': _row_to_faq(row)}), 201


@faq_bp.route('/api/admin/faqs/<int:fid>', methods=['PATCH'])
@require_super_admin()
def admin_patch(fid: int):
    data = request.get_json(silent=True) or {}
    db = get_db()
    if not db.execute("SELECT id FROM faqs WHERE id=?", (fid,)).fetchone():
        db.close()
        return jsonify({'success': False, 'message': 'FAQ 를 찾을 수 없습니다.'}), 404
    sets, params = [], []
    for f in ('category', 'question', 'answer', 'lang', 'sort_order', 'active'):
        if f in data:
            sets.append(f"{f}=?")
            params.append(data[f])
    if not sets:
        db.close()
        return jsonify({'success': False, 'message': '변경할 필드 없음'}), 400
    sets.append("updated_at=datetime('now')")
    params.append(fid)
    db.execute(f"UPDATE faqs SET {', '.join(sets)} WHERE id=?", params)
    db.commit(); db.close()
    return jsonify({'success': True})


@faq_bp.route('/api/admin/faqs/<int:fid>', methods=['DELETE'])
@require_super_admin()
def admin_delete(fid: int):
    db = get_db()
    db.execute("UPDATE faqs SET active=0, updated_at=datetime('now') WHERE id=?", (fid,))
    db.commit(); db.close()
    return jsonify({'success': True})
