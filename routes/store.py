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
    """매장 비활성화 (soft delete; 데이터 보존, 조회에서 제외).

    cascade — 매장이 비활성화되면 그 매장에 묶인 비콘/WiFi도 운영 중단:
      * beacons.status='inactive'
      * wifi_profiles.active=0
    """
    account_id = g.auth['user_id']
    db = get_db()
    cur = db.execute(
        """UPDATE facilities SET active=0
           WHERE id=? AND owner_id=? AND active=1""",
        (fid, account_id)
    )
    affected = cur.rowcount
    if affected == 0:
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    # cascade
    db.execute("UPDATE beacons       SET status='inactive' WHERE facility_id=?", (fid,))
    db.execute("UPDATE wifi_profiles SET active=0          WHERE facility_id=?", (fid,))
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': '매장이 비활성화되었습니다.'})


# ── 매장 이미지 헬퍼 ──────────────────────────────────────────────────────────

def _owned_facility(db, fid: int, account_id: int) -> bool:
    return bool(db.execute(
        "SELECT 1 FROM facilities WHERE id=? AND owner_id=? AND active=1",
        (fid, account_id)
    ).fetchone())


def _sync_primary_to_facility(db, fid: int) -> None:
    """현재 대표 이미지의 URL을 ``facilities.image_url``에 미러링한다.
    대표가 없으면 NULL로 비운다."""
    row = db.execute(
        "SELECT image_url FROM facility_images WHERE facility_id=? AND is_primary=1 LIMIT 1",
        (fid,)
    ).fetchone()
    db.execute("UPDATE facilities SET image_url=? WHERE id=?",
               (row['image_url'] if row else None, fid))


def _row_to_image(row) -> dict:
    return {
        'id':         row['id'],
        'image_url':  row['image_url'],
        'is_primary': bool(row['is_primary']),
        'sort_order': row['sort_order'],
        'created_at': row['created_at'],
    }


# ── 매장 이미지 CRUD ──────────────────────────────────────────────────────────

@store_bp.route('/<int:fid>/images', methods=['POST'])
@require_auth(sub_type='facility')
def add_image(fid):
    """매장 이미지 추가. 첫 이미지면 자동으로 대표 지정."""
    account_id = g.auth['user_id']
    data       = request.get_json(silent=True) or {}
    image_url  = (data.get('image_url') or '').strip()
    if not image_url:
        return jsonify({'success': False, 'message': 'image_url은 필수입니다.'}), 400

    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    has_any = db.execute(
        "SELECT 1 FROM facility_images WHERE facility_id=? LIMIT 1", (fid,)
    ).fetchone() is not None
    auto_primary = not has_any
    requested_primary = bool(data.get('is_primary'))
    is_primary = 1 if (auto_primary or requested_primary) else 0

    sort_order = data.get('sort_order')
    if sort_order is None:
        max_row = db.execute(
            "SELECT COALESCE(MAX(sort_order), -1) AS m FROM facility_images WHERE facility_id=?",
            (fid,)
        ).fetchone()
        sort_order = max_row['m'] + 1

    if is_primary:
        db.execute("UPDATE facility_images SET is_primary=0 WHERE facility_id=?", (fid,))

    cur = db.execute(
        """INSERT INTO facility_images (facility_id, image_url, is_primary, sort_order)
           VALUES (?,?,?,?)""",
        (fid, image_url, is_primary, sort_order),
    )
    iid = cur.lastrowid
    if is_primary:
        _sync_primary_to_facility(db, fid)

    row = db.execute("SELECT * FROM facility_images WHERE id=?", (iid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '이미지가 추가되었습니다.',
                    'image': _row_to_image(row)}), 201


@store_bp.route('/<int:fid>/images', methods=['GET'])
@require_auth(sub_type='facility')
def list_images(fid):
    """매장 이미지 목록 (sort_order ASC, id ASC)."""
    account_id = g.auth['user_id']
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    rows = db.execute(
        """SELECT * FROM facility_images WHERE facility_id=?
           ORDER BY sort_order ASC, id ASC""",
        (fid,)
    ).fetchall()
    db.close()
    return jsonify({'success': True,
                    'facility_id': fid,
                    'images': [_row_to_image(r) for r in rows]})


@store_bp.route('/<int:fid>/images/<int:iid>', methods=['PATCH'])
@require_auth(sub_type='facility')
def update_image(fid, iid):
    """이미지 메타 수정 (is_primary / sort_order / image_url)."""
    account_id = g.auth['user_id']
    data       = request.get_json(silent=True) or {}

    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    img = db.execute(
        "SELECT * FROM facility_images WHERE id=? AND facility_id=?",
        (iid, fid)
    ).fetchone()
    if not img:
        db.close()
        return jsonify({'success': False, 'message': '이미지를 찾을 수 없습니다.'}), 404

    sets, vals = [], []
    if 'image_url' in data:
        v = (data.get('image_url') or '').strip()
        if not v:
            db.close()
            return jsonify({'success': False,
                            'message': 'image_url은 비울 수 없습니다.'}), 400
        sets.append('image_url=?'); vals.append(v)
    if 'sort_order' in data:
        sets.append('sort_order=?'); vals.append(data.get('sort_order'))

    set_primary = bool(data.get('is_primary')) if 'is_primary' in data else None
    if set_primary is True:
        # 다른 모든 이미지 대표 해제 후 본인을 대표로
        db.execute("UPDATE facility_images SET is_primary=0 WHERE facility_id=?", (fid,))
        sets.append('is_primary=?'); vals.append(1)
    elif set_primary is False and img['is_primary']:
        # 본인을 대표 해제 (수동으로 해제)
        sets.append('is_primary=?'); vals.append(0)

    if not sets:
        db.close()
        return jsonify({'success': False, 'message': '수정할 필드가 없습니다.'}), 400

    vals.append(iid)
    db.execute(f"UPDATE facility_images SET {', '.join(sets)} WHERE id=?", vals)
    _sync_primary_to_facility(db, fid)
    row = db.execute("SELECT * FROM facility_images WHERE id=?", (iid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '이미지가 수정되었습니다.',
                    'image': _row_to_image(row)})


@store_bp.route('/<int:fid>/images/<int:iid>', methods=['DELETE'])
@require_auth(sub_type='facility')
def delete_image(fid, iid):
    """이미지 삭제. 대표를 지우면 남은 첫 이미지로 대표 승계."""
    account_id = g.auth['user_id']
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    img = db.execute(
        "SELECT is_primary FROM facility_images WHERE id=? AND facility_id=?",
        (iid, fid)
    ).fetchone()
    if not img:
        db.close()
        return jsonify({'success': False, 'message': '이미지를 찾을 수 없습니다.'}), 404

    db.execute("DELETE FROM facility_images WHERE id=?", (iid,))

    if img['is_primary']:
        successor = db.execute(
            """SELECT id FROM facility_images WHERE facility_id=?
               ORDER BY sort_order ASC, id ASC LIMIT 1""",
            (fid,)
        ).fetchone()
        if successor:
            db.execute("UPDATE facility_images SET is_primary=1 WHERE id=?",
                       (successor['id'],))

    _sync_primary_to_facility(db, fid)
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': '이미지가 삭제되었습니다.'})


# ── 매장별 비콘 목록 ──────────────────────────────────────────────────────────

@store_bp.route('/<int:fid>/beacons', methods=['GET'])
@require_auth(sub_type='facility')
def list_facility_beacons(fid):
    """특정 매장의 비콘 목록 (소유 매장만)."""
    account_id = g.auth['user_id']
    db = get_db()
    owned = db.execute(
        "SELECT 1 FROM facilities WHERE id=? AND owner_id=? AND active=1",
        (fid, account_id)
    ).fetchone()
    if not owned:
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    rows = db.execute(
        """SELECT id, serial_no, uuid, status, battery_pct, firmware_ver, created_at
           FROM beacons WHERE facility_id=?
           ORDER BY id DESC""",
        (fid,)
    ).fetchall()
    db.close()
    return jsonify({
        'success': True,
        'facility_id': fid,
        'beacons': [dict(r) for r in rows],
    })
