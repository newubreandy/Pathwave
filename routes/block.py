"""채팅 차단 (block) — 손님(user)이 매장(facility)을 차단.

출시 심사 대비 (Apple App Store Guideline 1.2 — UGC 모더레이션):
손님이 불쾌한 매장과의 대화를 차단할 수 있어야 한다. 차단되면
채팅방이 양쪽 목록에서 숨겨지고 메시지 전송이 막힌다. 해지(unblock) 가능.

엔드포인트
---------
손님 (sub_type='user'):
- POST   /api/blocks               body {facility_id}   매장 차단
- DELETE /api/blocks/<fid>                               차단 해지
- GET    /api/blocks                                     내 차단 목록

신고(abuse-reports)와 달리 차단은 본인만의 설정이므로 운영자 처리 없음.
"""
from __future__ import annotations

from flask import Blueprint, request, jsonify, g

from models.database import get_db
from routes.auth import require_auth

block_bp = Blueprint('block', __name__)


def is_blocked(db, user_id: int, facility_id: int) -> bool:
    """손님이 해당 매장을 차단했는지 여부. chat.py 에서 import 해서 사용."""
    row = db.execute(
        "SELECT 1 FROM chat_blocks WHERE user_id=? AND facility_id=?",
        (user_id, facility_id),
    ).fetchone()
    return row is not None


@block_bp.route('/api/blocks', methods=['POST'])
@require_auth(sub_type='user')
def create_block():
    """매장 차단. 이미 차단돼 있으면 멱등 (success)."""
    user_id = g.auth['user_id']
    data = request.get_json(silent=True) or {}
    facility_id = data.get('facility_id')
    if not isinstance(facility_id, int):
        try:
            facility_id = int(facility_id)
        except (TypeError, ValueError):
            return jsonify({'success': False,
                            'message': 'facility_id 가 필요합니다.'}), 400

    db = get_db()
    if not db.execute(
        "SELECT 1 FROM facilities WHERE id=?", (facility_id,)
    ).fetchone():
        db.close()
        return jsonify({'success': False, 'message': '매장을 찾을 수 없습니다.'}), 404

    db.execute(
        "INSERT OR IGNORE INTO chat_blocks (user_id, facility_id) VALUES (?,?)",
        (user_id, facility_id),
    )
    db.commit()
    db.close()
    return jsonify({'success': True}), 201


@block_bp.route('/api/blocks/<int:fid>', methods=['DELETE'])
@require_auth(sub_type='user')
def delete_block(fid: int):
    """차단 해지. 차단돼 있지 않아도 멱등 (success)."""
    user_id = g.auth['user_id']
    db = get_db()
    db.execute(
        "DELETE FROM chat_blocks WHERE user_id=? AND facility_id=?",
        (user_id, fid),
    )
    db.commit()
    db.close()
    return jsonify({'success': True})


@block_bp.route('/api/blocks', methods=['GET'])
@require_auth(sub_type='user')
def list_blocks():
    """내가 차단한 매장 목록 (차단 해지 화면용)."""
    user_id = g.auth['user_id']
    db = get_db()
    rows = db.execute(
        """SELECT b.facility_id, b.created_at, f.name AS facility_name
             FROM chat_blocks b
             JOIN facilities f ON b.facility_id = f.id
            WHERE b.user_id = ?
            ORDER BY b.id DESC""",
        (user_id,),
    ).fetchall()
    db.close()
    return jsonify({
        'success': True,
        'blocks': [
            {
                'facility_id':   r['facility_id'],
                'facility_name': r['facility_name'],
                'created_at':    r['created_at'],
            }
            for r in rows
        ],
    })
