"""Phase I — 신고 (사용자/사장 → 매장/사용자, 운영자 처리).

기존 ``routes/report.py`` 는 매장 통계 (visitors/stamps/coupons) 용이라 이름 충돌
방지를 위해 ``abuse_report`` 로 분리.

엔드포인트
---------
사용자 / 사장 (sub_type 자동 판별):
- POST /api/abuse-reports                   body {target_kind, target_id, reason_code, reason_detail?}

운영자:
- GET  /api/admin/abuse-reports?status=     inbox
- GET  /api/admin/abuse-reports/<rid>
- PATCH /api/admin/abuse-reports/<rid>      body {status, resolution_note?}
"""
from __future__ import annotations

import json
import os
import uuid

from flask import Blueprint, request, jsonify, g, current_app
from werkzeug.utils import secure_filename

from models.database import get_db
from routes.auth import require_super_admin

abuse_report_bp = Blueprint('abuse_report', __name__)


_ALLOWED_TARGET = {'facility', 'user'}
_ALLOWED_REPORTER = {'user', 'facility'}
_ALLOWED_REASON = {'spam', 'abuse', 'illegal', 'inappropriate', 'other'}
_ALLOWED_STATUS = {'open', 'in_review', 'action_taken', 'dismissed'}

# 첨부 사진 정책 (2026-06-08).
_ATTACH_MAX_COUNT  = 3
_ATTACH_MAX_BYTES  = 5 * 1024 * 1024            # 5MB / 장
_ATTACH_ALLOWED_EXT  = {'jpg', 'jpeg', 'png', 'webp'}
_ATTACH_ALLOWED_MIME = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/webp',
}


def _attach_dir() -> str:
    """``static/abuse_reports/`` 절대 경로. 없으면 생성."""
    base = current_app.static_folder or 'static'
    path = os.path.join(base, 'abuse_reports')
    os.makedirs(path, exist_ok=True)
    return path


def _save_attachment(file_storage) -> str:
    """업로드 파일 저장 → public URL 반환. 검증 실패 시 ValueError."""
    if file_storage is None or not file_storage.filename:
        raise ValueError('파일이 없습니다.')

    orig = secure_filename(file_storage.filename)
    ext = orig.rsplit('.', 1)[-1].lower() if '.' in orig else ''
    if ext not in _ATTACH_ALLOWED_EXT:
        raise ValueError(f'허용되지 않는 확장자: .{ext}')

    mime = (file_storage.mimetype or '').lower()
    if mime and mime not in _ATTACH_ALLOWED_MIME:
        raise ValueError(f'허용되지 않는 MIME: {mime}')

    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > _ATTACH_MAX_BYTES:
        raise ValueError(
            f'파일이 너무 큽니다 ({size // 1024}KB, 최대 5MB).')

    new_name = f'{uuid.uuid4().hex}.{ext}'
    path = os.path.join(_attach_dir(), new_name)
    file_storage.save(path)
    return f'/static/abuse_reports/{new_name}'


def _row_to_report(row) -> dict:
    raw_urls = row['attachment_urls'] if 'attachment_urls' in row.keys() else None
    try:
        urls = json.loads(raw_urls) if raw_urls else []
    except (TypeError, ValueError):
        urls = []
    return {
        'id':            row['id'],
        'target_kind':   row['target_kind'],
        'target_id':     row['target_id'],
        'reporter_kind': row['reporter_kind'],
        'reporter_id':   row['reporter_id'],
        'reason_code':   row['reason_code'],
        'reason_detail': row['reason_detail'],
        'status':        row['status'],
        'resolution_note': row['resolution_note'],
        'resolved_by_admin_id': row['resolved_by_admin_id'],
        'resolved_at':   row['resolved_at'],
        'created_at':    row['created_at'],
        'attachment_urls': urls,
    }


def _detect_reporter():
    """현재 토큰으로 reporter_kind / id 추출."""
    from routes.auth import SECRET_KEY
    import jwt as _jwt
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None, None
    try:
        payload = _jwt.decode(auth.split(' ', 1)[1], SECRET_KEY, algorithms=['HS256'])
    except Exception:
        return None, None
    sub_type = payload.get('sub_type', 'user')
    if sub_type == 'user':
        return 'user', payload.get('user_id')
    if sub_type == 'facility':
        return 'facility', payload.get('user_id')
    return None, None


@abuse_report_bp.route('/api/abuse-reports', methods=['POST'])
def create_report():
    """신고 작성. JSON 또는 multipart/form-data 둘 다 허용.

    multipart 인 경우 ``attachments`` 키로 파일 최대 3장 첨부 가능 (2026-06-08).
    """
    reporter_kind, reporter_id = _detect_reporter()
    if not reporter_kind:
        return jsonify({'success': False, 'message': '사용자 또는 사장 토큰이 필요합니다.'}), 401

    # JSON 또는 form 둘 다 지원.
    is_multipart = request.content_type and request.content_type.startswith('multipart/')
    if is_multipart:
        target_kind = (request.form.get('target_kind') or '').strip()
        target_id_raw = request.form.get('target_id')
        reason_code = (request.form.get('reason_code') or '').strip()
        reason_detail = (request.form.get('reason_detail') or '').strip() or None
    else:
        data = request.get_json(silent=True) or {}
        target_kind = (data.get('target_kind') or '').strip()
        target_id_raw = data.get('target_id')
        reason_code = (data.get('reason_code') or '').strip()
        reason_detail = (data.get('reason_detail') or '').strip() or None

    if target_kind not in _ALLOWED_TARGET:
        return jsonify({'success': False, 'message': f'target_kind 는 {_ALLOWED_TARGET}'}), 400
    try:
        target_id = int(target_id_raw)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'target_id 가 필요합니다.'}), 400
    if reason_code not in _ALLOWED_REASON:
        return jsonify({'success': False, 'message': f'reason_code 는 {_ALLOWED_REASON}'}), 400

    # 첨부 사진 저장 (multipart 인 경우만).
    attachment_urls: list[str] = []
    if is_multipart:
        files = request.files.getlist('attachments')
        if len(files) > _ATTACH_MAX_COUNT:
            return jsonify({'success': False,
                            'message': f'첨부 파일은 최대 {_ATTACH_MAX_COUNT}장입니다.'}), 400
        for f in files:
            if not f or not f.filename:
                continue
            try:
                attachment_urls.append(_save_attachment(f))
            except ValueError as e:
                return jsonify({'success': False, 'message': str(e)}), 400

    db = get_db()
    cur = db.execute(
        """INSERT INTO abuse_reports
             (target_kind, target_id, reporter_kind, reporter_id,
              reason_code, reason_detail, attachment_urls)
           VALUES (?,?,?,?,?,?,?)""",
        (target_kind, target_id, reporter_kind, reporter_id,
         reason_code, reason_detail,
         json.dumps(attachment_urls) if attachment_urls else None)
    )
    rid = cur.lastrowid
    db.commit()
    row = db.execute("SELECT * FROM abuse_reports WHERE id=?", (rid,)).fetchone()
    db.close()
    return jsonify({'success': True, 'report': _row_to_report(row)}), 201


@abuse_report_bp.route('/api/admin/abuse-reports', methods=['GET'])
@require_super_admin()
def admin_list():
    status = (request.args.get('status') or '').strip()
    q = "SELECT * FROM abuse_reports"
    params = []
    if status:
        if status not in _ALLOWED_STATUS:
            return jsonify({'success': False, 'message': f'status 는 {_ALLOWED_STATUS}'}), 400
        q += " WHERE status=?"; params.append(status)
    q += " ORDER BY (status='open') DESC, id DESC"
    db = get_db()
    rows = db.execute(q, params).fetchall()
    db.close()
    return jsonify({'success': True, 'count': len(rows),
                    'reports': [_row_to_report(r) for r in rows]})


@abuse_report_bp.route('/api/admin/abuse-reports/<int:rid>', methods=['GET'])
@require_super_admin()
def admin_get(rid: int):
    db = get_db()
    row = db.execute("SELECT * FROM abuse_reports WHERE id=?", (rid,)).fetchone()
    db.close()
    if not row:
        return jsonify({'success': False, 'message': '신고를 찾을 수 없습니다.'}), 404
    return jsonify({'success': True, 'report': _row_to_report(row)})


@abuse_report_bp.route('/api/admin/abuse-reports/<int:rid>', methods=['PATCH'])
@require_super_admin()
def admin_patch(rid: int):
    admin_id = g.auth['user_id']
    data = request.get_json(silent=True) or {}
    db = get_db()
    if not db.execute("SELECT id FROM abuse_reports WHERE id=?", (rid,)).fetchone():
        db.close()
        return jsonify({'success': False, 'message': '신고를 찾을 수 없습니다.'}), 404
    sets, params = [], []
    if 'status' in data:
        s = data['status']
        if s not in _ALLOWED_STATUS:
            db.close()
            return jsonify({'success': False, 'message': f'status 는 {_ALLOWED_STATUS}'}), 400
        sets.append("status=?"); params.append(s)
        if s in ('action_taken', 'dismissed'):
            sets.append("resolved_at=datetime('now')")
            sets.append("resolved_by_admin_id=?")
            params.append(admin_id)
    if 'resolution_note' in data:
        sets.append("resolution_note=?")
        params.append((data['resolution_note'] or '').strip() or None)
    if not sets:
        db.close()
        return jsonify({'success': False, 'message': '변경할 필드 없음'}), 400
    params.append(rid)
    db.execute(f"UPDATE abuse_reports SET {', '.join(sets)} WHERE id=?", params)
    db.commit(); db.close()
    return jsonify({'success': True})
