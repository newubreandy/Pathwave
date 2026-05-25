"""매장 업종 카테고리 — 공개 GET + admin CRUD.

사장 가입 시 매장 정보의 category 필드는 본 API 응답 안에서만 선택 가능.
자유 입력 금지 (DB 파편화 방지).

엔드포인트
---------
- GET    /api/categories                    (공개) — active 카테고리 + group 분류
- GET    /api/admin/categories              (admin) — 전체 (active 무관)
- POST   /api/admin/categories              (admin) — 신규
- PATCH  /api/admin/categories/<int:cid>    (admin) — 수정
- DELETE /api/admin/categories/<int:cid>    (admin) — 비활성화 (실삭제 아님)
"""
from __future__ import annotations

from flask import Blueprint, request, jsonify, g

from models.database import get_db
from routes.auth import require_super_admin

categories_bp = Blueprint('categories', __name__)


def _row_to_category(r) -> dict:
    return {
        'id':         r['id'],
        'name':       r['name'],
        'group':      r['group_name'],
        'sort_order': r['sort_order'],
        'active':     bool(r['active']),
        'updated_at': r['updated_at'],
    }


# ─── 공개 GET ─────────────────────────────────────────────────────────────
@categories_bp.route('/api/categories', methods=['GET'])
def list_public_categories():
    """active 카테고리 + group 분류. provider/mobile 가입 시 드롭다운에 사용.

    응답: {
      categories: [{id, name, group, ...}, ...],
      groups: {group_name: [name, ...]},     # 빠른 그룹 매핑
    }
    """
    db = get_db()
    try:
        rows = db.execute(
            """SELECT * FROM store_categories WHERE active=1
                ORDER BY group_name ASC, sort_order ASC, id ASC"""
        ).fetchall()
        cats = [_row_to_category(r) for r in rows]
        groups = {}
        for c in cats:
            groups.setdefault(c['group'] or '기타', []).append(c['name'])
        return jsonify({'success': True,
                        'count':      len(cats),
                        'categories': cats,
                        'groups':     groups})
    finally:
        db.close()


# ─── admin 전체 조회 (active 무관) ────────────────────────────────────────
@categories_bp.route('/api/admin/categories', methods=['GET'])
@require_super_admin()
def list_admin_categories():
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM store_categories ORDER BY group_name ASC, sort_order ASC"
        ).fetchall()
        return jsonify({'success':    True,
                        'count':      len(rows),
                        'categories': [_row_to_category(r) for r in rows]})
    finally:
        db.close()


# ─── admin 신규 ───────────────────────────────────────────────────────────
@categories_bp.route('/api/admin/categories', methods=['POST'])
@require_super_admin()
def create_category():
    """body: {name, group?, sort_order?}"""
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    group = (data.get('group') or '기타').strip()
    sort_order = int(data.get('sort_order') or 0)
    if not name:
        return jsonify({'success': False, 'message': 'name 필수.'}), 400
    if len(name) > 60:
        return jsonify({'success': False, 'message': 'name 60자 이내.'}), 400
    db = get_db()
    try:
        # 중복 (active 무관) 거부
        if db.execute(
            "SELECT 1 FROM store_categories WHERE name=?", (name,)
        ).fetchone():
            return jsonify({'success': False,
                            'message': '이미 존재하는 카테고리.'}), 409
        cur = db.execute(
            """INSERT INTO store_categories (name, group_name, sort_order, active)
               VALUES (?, ?, ?, 1)""",
            (name, group, sort_order),
        )
        row = db.execute(
            "SELECT * FROM store_categories WHERE id=?", (cur.lastrowid,)
        ).fetchone()
        db.commit()
        return jsonify({'success':  True,
                        'category': _row_to_category(row)}), 201
    finally:
        db.close()


# ─── admin 수정 ───────────────────────────────────────────────────────────
@categories_bp.route('/api/admin/categories/<int:cid>', methods=['PATCH'])
@require_super_admin()
def update_category(cid: int):
    """body: 변경할 필드만 (name, group, sort_order, active)"""
    data = request.get_json(silent=True) or {}
    db = get_db()
    try:
        row = db.execute(
            "SELECT * FROM store_categories WHERE id=?", (cid,)
        ).fetchone()
        if not row:
            return jsonify({'success': False, 'message': '카테고리 없음.'}), 404

        fields, params = [], []
        if 'name' in data:
            nm = (data.get('name') or '').strip()
            if not nm:
                return jsonify({'success': False, 'message': 'name 비울 수 없음.'}), 400
            # 다른 row 와 중복 거부
            dup = db.execute(
                "SELECT id FROM store_categories WHERE name=? AND id<>?",
                (nm, cid),
            ).fetchone()
            if dup:
                return jsonify({'success': False,
                                'message': '같은 이름의 카테고리 존재.'}), 409
            fields.append('name=?'); params.append(nm)
        if 'group' in data:
            fields.append('group_name=?'); params.append((data.get('group') or '').strip() or None)
        if 'sort_order' in data:
            fields.append('sort_order=?'); params.append(int(data.get('sort_order') or 0))
        if 'active' in data:
            fields.append('active=?'); params.append(1 if data.get('active') else 0)
        if not fields:
            return jsonify({'success': False, 'message': '변경할 필드 없음.'}), 400
        fields.append("updated_at=datetime('now')")
        db.execute(
            f"UPDATE store_categories SET {', '.join(fields)} WHERE id=?",
            (*params, cid),
        )
        new_row = db.execute(
            "SELECT * FROM store_categories WHERE id=?", (cid,)
        ).fetchone()
        db.commit()
        return jsonify({'success': True, 'category': _row_to_category(new_row)})
    finally:
        db.close()


# ─── admin 삭제 (비활성화) ────────────────────────────────────────────────
@categories_bp.route('/api/admin/categories/<int:cid>', methods=['DELETE'])
@require_super_admin()
def deactivate_category(cid: int):
    """실삭제 대신 active=0 (가입 흐름 안전). 완전 삭제 필요 시 ?hard=1."""
    hard = (request.args.get('hard') or '') in ('1', 'true', 'yes')
    db = get_db()
    try:
        row = db.execute(
            "SELECT id FROM store_categories WHERE id=?", (cid,)
        ).fetchone()
        if not row:
            return jsonify({'success': False, 'message': '카테고리 없음.'}), 404
        if hard:
            db.execute("DELETE FROM store_categories WHERE id=?", (cid,))
        else:
            db.execute(
                "UPDATE store_categories SET active=0, updated_at=datetime('now') WHERE id=?",
                (cid,),
            )
        db.commit()
        return jsonify({'success': True,
                        'mode': 'hard_delete' if hard else 'deactivated'})
    finally:
        db.close()
