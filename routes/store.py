"""시설(매장) CRUD API. SRS FR-STORE-001.

facility_accounts(사장님 계정) 1 : N facilities(매장) 관계.
모든 라우트는 시설 토큰(``sub_type='facility'``)을 요구하며,
본인 ``owner_id`` 매장만 조회/수정/삭제할 수 있다.

엔드포인트
---------
- ``POST   /api/facilities``        새 매장 등록
- ``GET    /api/facilities``        내 매장 목록 (활성)
- ``GET    /api/facilities/<id>``   매장 상세
- ``PATCH  /api/facilities/<id>``   매장 정보 부분 수정
- ``DELETE /api/facilities/<id>``   매장 비활성화 (soft delete)
"""
from flask import Blueprint, request, jsonify, g

from models.database import get_db
from routes.auth import require_auth

store_bp = Blueprint('store', __name__, url_prefix='/api/facilities')

_UPDATABLE_FIELDS = {
    'name', 'address', 'latitude', 'longitude', 'description', 'image_url',
}


def _row_to_facility(row) -> dict:
    return {
        'id':          row['id'],
        'name':        row['name'],
        'address':     row['address'],
        'latitude':    row['latitude'],
        'longitude':   row['longitude'],
        'description': row['description'],
        'image_url':   row['image_url'],
        'active':      bool(row['active']),
        'created_at':  row['created_at'],
    }


def _normalize_text(value, *, allow_empty=False) -> str | None:
    s = (value or '').strip() if isinstance(value, str) else value
    if isinstance(s, str):
        if not s:
            return None if not allow_empty else ''
        return s
    return value


# ── Create ────────────────────────────────────────────────────────────────────

@store_bp.route('', methods=['POST'])
@require_auth(sub_type='facility')
def create_facility():
    """매장 등록."""
    account_id = g.auth['user_id']
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': '매장명은 필수입니다.'}), 400

    db = get_db()
    cur = db.execute(
        """INSERT INTO facilities
           (name, address, latitude, longitude, description, image_url,
            owner_id, active)
           VALUES (?,?,?,?,?,?,?,1)""",
        (name,
         _normalize_text(data.get('address')),
         data.get('latitude'),
         data.get('longitude'),
         _normalize_text(data.get('description')),
         _normalize_text(data.get('image_url')),
         account_id),
    )
    row = db.execute("SELECT * FROM facilities WHERE id=?",
                     (cur.lastrowid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '매장이 등록되었습니다.',
                    'facility': _row_to_facility(row)}), 201


# ── Read ──────────────────────────────────────────────────────────────────────

@store_bp.route('', methods=['GET'])
@require_auth(sub_type='facility')
def list_my_facilities():
    """내 매장 목록 (활성만)."""
    account_id = g.auth['user_id']
    db = get_db()
    rows = db.execute(
        """SELECT * FROM facilities
           WHERE owner_id=? AND active=1
           ORDER BY id DESC""",
        (account_id,)
    ).fetchall()
    db.close()
    return jsonify({'success': True,
                    'facilities': [_row_to_facility(r) for r in rows]})


@store_bp.route('/<int:fid>', methods=['GET'])
@require_auth(sub_type='facility')
def get_facility(fid):
    """매장 상세 (소유)."""
    account_id = g.auth['user_id']
    db = get_db()
    row = db.execute(
        """SELECT * FROM facilities
           WHERE id=? AND owner_id=? AND active=1""",
        (fid, account_id)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    return jsonify({'success': True, 'facility': _row_to_facility(row)})


# ── Update ────────────────────────────────────────────────────────────────────

@store_bp.route('/<int:fid>', methods=['PATCH'])
@require_auth(sub_type='facility')
def update_facility(fid):
    """매장 정보 부분 수정 (소유). 보낸 필드만 갱신."""
    account_id = g.auth['user_id']
    data = request.get_json(silent=True) or {}

    db = get_db()
    owned = db.execute(
        """SELECT 1 FROM facilities
           WHERE id=? AND owner_id=? AND active=1""",
        (fid, account_id)
    ).fetchone()
    if not owned:
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    sets, vals = [], []
    for key, raw in data.items():
        if key not in _UPDATABLE_FIELDS:
            continue
        if key == 'name':
            v = (raw or '').strip()
            if not v:
                db.close()
                return jsonify({'success': False,
                                'message': '매장명은 비울 수 없습니다.'}), 400
            vals.append(v)
        elif key in ('address', 'description', 'image_url'):
            vals.append(_normalize_text(raw))
        else:  # latitude, longitude
            vals.append(raw)
        sets.append(f'{key}=?')

    if not sets:
        db.close()
        return jsonify({'success': False,
                        'message': '수정할 필드가 없습니다.'}), 400

    vals.append(fid)
    db.execute(f"UPDATE facilities SET {', '.join(sets)} WHERE id=?", vals)
    row = db.execute("SELECT * FROM facilities WHERE id=?", (fid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '매장 정보가 수정되었습니다.',
                    'facility': _row_to_facility(row)})


# ── Delete (soft) ─────────────────────────────────────────────────────────────

@store_bp.route('/<int:fid>', methods=['DELETE'])
@require_auth(sub_type='facility')
def delete_facility(fid):
    """매장 비활성화 (soft delete; 데이터는 보존, 조회에서 제외)."""
    account_id = g.auth['user_id']
    db = get_db()
    cur = db.execute(
        """UPDATE facilities SET active=0
           WHERE id=? AND owner_id=? AND active=1""",
        (fid, account_id)
    )
    db.commit()
    affected = cur.rowcount
    db.close()
    if affected == 0:
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    return jsonify({'success': True, 'message': '매장이 비활성화되었습니다.'})
