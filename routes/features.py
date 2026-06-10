"""Feature Flag 라우트 (2026-06-08).

- GET  /api/me/features                — 활성 모듈 목록 (인증 불요)
- GET  /api/admin/features             — 전체 모듈 + 활성 여부 (슈퍼어드민)
- PATCH /api/admin/features/<key>      — 모듈 ON/OFF (슈퍼어드민)
"""
from __future__ import annotations

from flask import Blueprint, request, jsonify, g

from routes.auth import require_super_admin
from services.feature_flags import (
    list_features, set_feature, DEFAULT_FLAGS,
)


features_bp = Blueprint('features', __name__)


@features_bp.route('/api/me/features', methods=['GET'])
def my_features():
    """클라이언트가 자기 환경에서 활성된 모듈 키 목록 받음."""
    return jsonify({'success': True, 'features': list_features()})


@features_bp.route('/api/admin/features', methods=['GET'])
@require_super_admin()
def admin_list_features():
    """슈퍼어드민 — 전체 모듈 + DEFAULT 여부 + 현재 활성."""
    current = list_features()
    items = []
    for key, default_enabled in DEFAULT_FLAGS.items():
        items.append({
            'key':              key,
            'default_enabled':  default_enabled,
            'current_enabled':  current.get(key, default_enabled),
        })
    return jsonify({'success': True, 'items': items})


@features_bp.route('/api/admin/features/<key>', methods=['PATCH'])
@require_super_admin()
def admin_set_feature(key: str):
    """슈퍼어드민 — 모듈 ON/OFF."""
    if key not in DEFAULT_FLAGS:
        return jsonify({'success': False,
                        'message': f'알 수 없는 모듈 키: {key}'}), 404
    data = request.get_json(silent=True) or {}
    enabled = bool(data.get('enabled'))
    set_feature(key, enabled, updated_by=g.auth.get('user_id'))
    return jsonify({'success': True, 'key': key, 'enabled': enabled})
