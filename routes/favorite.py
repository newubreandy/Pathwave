"""사용자 즐겨찾기 매장 (Phase C — 매장 도메인 보강).

엔드포인트
---------
- GET    /api/users/me/favorites           목록 (간단한 매장 카드 데이터 포함)
- POST   /api/users/me/favorites           {facility_id} 즐겨찾기 추가
- DELETE /api/users/me/favorites/<fid>     즐겨찾기 해제

모두 ``sub_type='user'`` 토큰 필수.
"""
from flask import Blueprint, request, jsonify, g

from models.database import get_db
from routes.auth import require_auth

favorite_bp = Blueprint('favorite', __name__, url_prefix='/api/users/me/favorites')


def _row_to_card(row) -> dict:
    return {
        'id':           row['id'],
        'name':         row['name'],
        'address':      row['address'],
        'description':  row['description'],
        'image_url':    row['image_url'],
        'latitude':     row['latitude'],
        'longitude':    row['longitude'],
        'favorited_at': row['favorited_at'] if 'favorited_at' in row.keys() else None,
    }


@favorite_bp.route('', methods=['GET'])
@require_auth(sub_type='user')
def list_favorites():
    user_id = g.auth['user_id']
    db = get_db()
    rows = db.execute(
        """SELECT f.id, f.name, f.address, f.description, f.image_url,
                  f.latitude, f.longitude, uf.created_at AS favorited_at
             FROM user_favorites uf
             JOIN facilities f ON uf.facility_id = f.id
            WHERE uf.user_id = ? AND f.active = 1
            ORDER BY uf.created_at DESC""",
        (user_id,)
    ).fetchall()
    db.close()
    return jsonify({'success': True,
                    'count': len(rows),
                    'favorites': [_row_to_card(r) for r in rows]})


@favorite_bp.route('', methods=['POST'])
@require_auth(sub_type='user')
def add_favorite():
    user_id = g.auth['user_id']
    data = request.get_json(silent=True) or {}
    fid = data.get('facility_id')
    try:
        fid = int(fid) if fid is not None else None
    except (TypeError, ValueError):
        fid = None
    if not fid:
        return jsonify({'success': False, 'message': 'facility_id 가 필요합니다.'}), 400

    db = get_db()
    fac = db.execute(
        "SELECT id FROM facilities WHERE id=? AND active=1", (fid,)
    ).fetchone()
    if not fac:
        db.close()
        return jsonify({'success': False, 'message': '매장을 찾을 수 없습니다.'}), 404

    # 중복 추가는 멱등 — 이미 있으면 success
    try:
        db.execute(
            "INSERT INTO user_favorites (user_id, facility_id) VALUES (?,?)",
            (user_id, fid)
        )
        db.commit()
    except Exception:
        pass  # UNIQUE 충돌 → 이미 즐겨찾기

    db.close()
    return jsonify({'success': True, 'message': '즐겨찾기에 추가되었습니다.',
                    'facility_id': fid}), 201


@favorite_bp.route('/<int:fid>', methods=['DELETE'])
@require_auth(sub_type='user')
def remove_favorite(fid: int):
    user_id = g.auth['user_id']
    db = get_db()
    db.execute(
        "DELETE FROM user_favorites WHERE user_id=? AND facility_id=?",
        (user_id, fid)
    )
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': '즐겨찾기가 해제되었습니다.',
                    'facility_id': fid})
