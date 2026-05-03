"""Super Admin (PathWave 운영자) API.

별도 도메인 (`/api/admin/*`). 사장님(facility) / 직원(staff) / 앱 사용자(user)와
완전히 분리된 인증·권한 체계. 토큰 ``sub_type='super_admin'``.

이번 PR (#24) 스코프: 인증 기반만. 비콘 인벤토리·사장 승인·결제 정산 등은 후속.

엔드포인트
---------
- POST /api/admin/login      이메일/비밀번호 로그인
- GET  /api/admin/me         본인 정보 조회
- POST /api/admin/refresh    refresh 토큰 → access 새로 발급
"""
from datetime import datetime, timedelta

import bcrypt
import jwt
from flask import Blueprint, request, jsonify, g

from models.database import get_db
from routes.auth import (
    SECRET_KEY, ACCESS_TTL_MIN, REFRESH_TTL_DAY,
    make_jwt, issue_token_pair,
    require_super_admin,
)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def _row_to_admin(row) -> dict:
    return {
        'id':            row['id'],
        'email':         row['email'],
        'name':          row['name'],
        'role':          row['role'],
        'active':        bool(row['active']),
        'last_login_at': row['last_login_at'],
        'created_at':    row['created_at'],
    }


@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Super Admin 로그인 — sub_type='super_admin' 토큰 발급."""
    data = request.get_json(silent=True) or {}
    email    = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not email or not password:
        return jsonify({'success': False,
                        'message': '이메일과 비밀번호를 입력해 주세요.'}), 400

    db = get_db()
    row = db.execute(
        "SELECT * FROM super_admin_accounts WHERE email=? AND active=1",
        (email,)
    ).fetchone()
    if not row or not bcrypt.checkpw(password.encode(), row['password'].encode()):
        if db: db.close()
        return jsonify({'success': False,
                        'message': '이메일 또는 비밀번호가 올바르지 않습니다.'}), 401

    db.execute(
        "UPDATE super_admin_accounts SET last_login_at=datetime('now') WHERE id=?",
        (row['id'],)
    )
    db.commit()
    db.close()

    extra = {'role': row['role']}
    return jsonify({
        'success': True,
        'message': '로그인 성공!',
        **issue_token_pair(row['id'], email, sub_type='super_admin', extra_claims=extra),
        'admin': _row_to_admin(row),
    })


@admin_bp.route('/me', methods=['GET'])
@require_super_admin()
def admin_me():
    """본인(super admin) 정보 조회."""
    db = get_db()
    row = db.execute(
        "SELECT * FROM super_admin_accounts WHERE id=?", (g.auth['user_id'],)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({'success': False, 'message': '계정을 찾을 수 없습니다.'}), 404
    return jsonify({'success': True, 'admin': _row_to_admin(row)})


@admin_bp.route('/refresh', methods=['POST'])
def admin_refresh():
    """Super Admin refresh — 다른 sub_type 토큰은 거부."""
    data = request.get_json(silent=True) or {}
    rt   = (data.get('refresh_token') or '').strip()
    if not rt:
        return jsonify({'success': False, 'message': 'refresh_token이 필요합니다.'}), 400
    try:
        payload = jwt.decode(rt, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': '리프레시 토큰이 만료되었습니다.'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': '유효하지 않은 리프레시 토큰입니다.'}), 401
    if payload.get('kind') != 'refresh':
        return jsonify({'success': False, 'message': '리프레시 토큰이 아닙니다.'}), 401
    if payload.get('sub_type') != 'super_admin':
        return jsonify({'success': False,
                        'message': 'Super Admin 토큰이 아닙니다.'}), 401

    db = get_db()
    row = db.execute(
        "SELECT id, email, role FROM super_admin_accounts WHERE id=? AND active=1",
        (payload['user_id'],)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({'success': False,
                        'message': '계정을 찾을 수 없거나 비활성화됨.'}), 401

    extra = {'role': row['role']}
    return jsonify({
        'success': True,
        **issue_token_pair(row['id'], row['email'], sub_type='super_admin',
                           extra_claims=extra),
    })
