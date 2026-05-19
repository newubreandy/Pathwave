"""앱 버전 강제 업데이트 — mobile 앱 부팅 시 호출.

엔드포인트
---------
공개:
  GET  /api/version/check?platform=ios|android&current=1.0.0
       → {force_update, recommend_update, min_supported, latest, store_url, force_message}

운영자 (super_admin):
  GET  /api/admin/app-versions
  PUT  /api/admin/app-versions/<platform>
       body: {min_supported, latest, store_url?, force_message?}

비교 규칙
--------
- semver 'X.Y.Z' 를 (X, Y, Z) 튜플로 비교
- current < min_supported  → force_update=True  (사용 불가, 강제 업데이트)
- current < latest         → recommend_update=True (선택 업데이트)
- 그 외                    → 둘 다 False
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from models.database import get_db
from routes.auth import require_super_admin

version_bp = Blueprint('version', __name__)

_ALLOWED_PLATFORMS = {'ios', 'android'}


def _parse_semver(v: str) -> tuple[int, int, int]:
    """'1.2.3' → (1, 2, 3). 비정상 입력 시 (0,0,0)."""
    try:
        parts = (v or '').strip().split('.')
        nums = [int(p) for p in parts[:3]]
        while len(nums) < 3:
            nums.append(0)
        return tuple(nums)  # type: ignore[return-value]
    except (ValueError, AttributeError):
        return (0, 0, 0)


def _row_to_dict(row) -> dict:
    return {
        'platform':      row['platform'],
        'min_supported': row['min_supported'],
        'latest':        row['latest'],
        'store_url':     row['store_url'],
        'force_message': row['force_message'],
        'updated_at':    row['updated_at'],
    }


# ════════════════════════════════════════════════════════════════════════════
#                                 공개
# ════════════════════════════════════════════════════════════════════════════

@version_bp.route('/api/version/check', methods=['GET'])
def check_version():
    platform = (request.args.get('platform') or '').strip().lower()
    current  = (request.args.get('current') or '').strip()
    if platform not in _ALLOWED_PLATFORMS:
        return jsonify({'success': False,
                        'message': "platform 은 'ios' 또는 'android' 여야 합니다."}), 400
    if not current:
        return jsonify({'success': False,
                        'message': 'current 버전이 필요합니다.'}), 400

    db = get_db()
    try:
        row = db.execute(
            "SELECT * FROM app_versions WHERE platform=?", (platform,)
        ).fetchone()
        if not row:
            return jsonify({
                'success': True,
                'platform': platform,
                'force_update': False,
                'recommend_update': False,
                'min_supported': None,
                'latest': None,
                'store_url': None,
                'force_message': None,
            })

        cur_v = _parse_semver(current)
        min_v = _parse_semver(row['min_supported'])
        lat_v = _parse_semver(row['latest'])
        force     = cur_v < min_v
        recommend = (not force) and cur_v < lat_v
        return jsonify({
            'success': True,
            'platform': platform,
            'current': current,
            'force_update': force,
            'recommend_update': recommend,
            **_row_to_dict(row),
        })
    finally:
        db.close()


# ════════════════════════════════════════════════════════════════════════════
#                          운영자 (super_admin)
# ════════════════════════════════════════════════════════════════════════════

@version_bp.route('/api/admin/app-versions', methods=['GET'])
@require_super_admin()
def admin_list():
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM app_versions ORDER BY platform"
        ).fetchall()
        return jsonify({'success': True,
                        'versions': [_row_to_dict(r) for r in rows]})
    finally:
        db.close()


@version_bp.route('/api/admin/app-versions/<platform>', methods=['PUT'])
@require_super_admin()
def admin_upsert(platform: str):
    platform = (platform or '').strip().lower()
    if platform not in _ALLOWED_PLATFORMS:
        return jsonify({'success': False,
                        'message': "platform 은 'ios' 또는 'android' 여야 합니다."}), 400
    data = request.get_json(silent=True) or {}
    min_supported = (data.get('min_supported') or '').strip()
    latest        = (data.get('latest') or '').strip()
    store_url     = (data.get('store_url') or '').strip() or None
    force_message = (data.get('force_message') or '').strip() or None

    if not min_supported or not latest:
        return jsonify({'success': False,
                        'message': 'min_supported 와 latest 는 필수입니다.'}), 400
    if _parse_semver(min_supported) > _parse_semver(latest):
        return jsonify({'success': False,
                        'message': 'min_supported 는 latest 보다 클 수 없습니다.'}), 400

    db = get_db()
    try:
        existing = db.execute(
            "SELECT platform FROM app_versions WHERE platform=?", (platform,)
        ).fetchone()
        if existing:
            db.execute(
                """UPDATE app_versions
                     SET min_supported=?, latest=?, store_url=?, force_message=?,
                         updated_at=datetime('now')
                   WHERE platform=?""",
                (min_supported, latest, store_url, force_message, platform)
            )
        else:
            db.execute(
                """INSERT INTO app_versions
                     (platform, min_supported, latest, store_url, force_message)
                   VALUES (?,?,?,?,?)""",
                (platform, min_supported, latest, store_url, force_message)
            )
        db.commit()
        row = db.execute(
            "SELECT * FROM app_versions WHERE platform=?", (platform,)
        ).fetchone()
        return jsonify({'success': True, 'version': _row_to_dict(row)})
    finally:
        db.close()
