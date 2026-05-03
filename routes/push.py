"""푸시 토큰 등록/해제 (sub_type='user').

엔드포인트
---------
- POST   /api/users/me/push-tokens             등록 (upsert by token)
- DELETE /api/users/me/push-tokens             token 지정 해제
- GET    /api/users/me/push-tokens             내 등록 목록
"""
from flask import Blueprint, request, jsonify, g

from models.database import get_db
from routes.auth import require_auth

push_bp = Blueprint('push', __name__, url_prefix='/api/users/me/push-tokens')

_ALLOWED_PLATFORMS = {'fcm', 'apns'}


@push_bp.route('', methods=['POST'])
@require_auth(sub_type='user')
def register_token():
    user_id = g.auth['user_id']
    data = request.get_json(silent=True) or {}
    token    = (data.get('token') or '').strip()
    platform = (data.get('platform') or '').strip().lower()
    language = (data.get('language') or '').strip() or None
    if not token:
        return jsonify({'success': False, 'message': 'token은 필수입니다.'}), 400
    if platform not in _ALLOWED_PLATFORMS:
        return jsonify({'success': False,
                        'message': f"platform은 {sorted(_ALLOWED_PLATFORMS)} 중 하나여야 합니다."}), 400

    db = get_db()
    db.execute(
        """INSERT INTO push_tokens (user_id, token, platform, language)
           VALUES (?,?,?,?)
           ON CONFLICT (token, platform) DO UPDATE SET
             user_id  = excluded.user_id,
             language = excluded.language,
             updated_at = datetime('now')""",
        (user_id, token, platform, language)
    )
    row = db.execute(
        "SELECT * FROM push_tokens WHERE token=? AND platform=?", (token, platform)
    ).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True, 'token': dict(row)}), 201


@push_bp.route('', methods=['GET'])
@require_auth(sub_type='user')
def list_tokens():
    user_id = g.auth['user_id']
    db = get_db()
    rows = db.execute(
        "SELECT id, platform, language, created_at, updated_at FROM push_tokens WHERE user_id=?",
        (user_id,)
    ).fetchall()
    db.close()
    return jsonify({'success': True, 'tokens': [dict(r) for r in rows]})


@push_bp.route('', methods=['DELETE'])
@require_auth(sub_type='user')
def remove_token():
    user_id = g.auth['user_id']
    data = request.get_json(silent=True) or {}
    token    = (data.get('token') or '').strip()
    platform = (data.get('platform') or '').strip().lower()
    if not token or platform not in _ALLOWED_PLATFORMS:
        return jsonify({'success': False,
                        'message': 'token + platform 필수.'}), 400
    db = get_db()
    cur = db.execute(
        "DELETE FROM push_tokens WHERE user_id=? AND token=? AND platform=?",
        (user_id, token, platform)
    )
    db.commit()
    affected = cur.rowcount
    db.close()
    return jsonify({'success': True, 'removed': affected})
