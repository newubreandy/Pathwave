"""직원 초대/관리 API. SRS FR-STAFF-001/002.

이번 모듈은 **초대 송신/조회/취소/재발송**만 다룬다.
초대 수락(invitee가 받은 토큰을 들고 와서 자기 계정과 매핑)은 권한 모델 결정 후
별도 PR에서 추가한다.

엔드포인트
---------
- ``POST   /api/staff/invite``        새 초대 발송 (email, role)
- ``GET    /api/staff``               내가 보낸 초대 목록 (만료 자동 표시)
- ``POST   /api/staff/<id>/resend``   만료/취소 초대 재발송 (새 토큰 + expires_at)
- ``DELETE /api/staff/<id>``          초대 취소 (status='revoked')
"""
import os
import secrets
from datetime import datetime, timedelta

import bcrypt
from flask import Blueprint, request, jsonify, g

from models.database import get_db
from routes.auth import (
    require_auth, send_email,
    password_complexity_error, issue_token_pair,
)

staff_bp = Blueprint('staff', __name__, url_prefix='/api/staff')

INVITE_TTL_DAY = int(os.environ.get('STAFF_INVITE_TTL_DAY', '7'))   # SRS: 7일
ALLOWED_ROLES  = {'admin', 'staff'}


def _generate_token() -> str:
    """URL-safe 랜덤 토큰 (~43자)."""
    return secrets.token_urlsafe(32)


def _row_status(row) -> str:
    """저장된 status를 만료 시각과 비교해 'expired'를 동적 계산."""
    if row['status'] != 'pending':
        return row['status']
    if datetime.utcnow() > datetime.fromisoformat(row['expires_at']):
        return 'expired'
    return 'pending'


def _row_to_invite(row) -> dict:
    return {
        'id':           row['id'],
        'email':        row['email'],
        'role':         row['role'],
        'status':       _row_status(row),
        'expires_at':   row['expires_at'],
        'accepted_at':  row['accepted_at'],
        'created_at':   row['created_at'],
    }


def _send_invite_email(to_email: str, token: str, role: str) -> bool:
    """초대 메일 — 개발 모드에선 콘솔에 토큰 출력."""
    print('\n' + '=' * 50)
    print(f'[직원 초대] 수신: {to_email} / 역할: {role}')
    print(f'토큰: {token}')
    print('=' * 50 + '\n')
    # 실제 메일은 가입 코드 흐름과 별개. 추후 별도 템플릿 사용 권장.
    # 여기선 dev 우선 → 콘솔 출력 + 이메일 시도 (실패해도 무시)
    try:
        send_email(to_email, token[:8])  # 짧은 표시용
    except Exception:
        pass
    return True


# ── Create ────────────────────────────────────────────────────────────────────

@staff_bp.route('/invite', methods=['POST'])
@require_auth(sub_type='facility')
def create_invite():
    """이메일 + 역할로 새 직원 초대 발송."""
    account_id = g.auth['user_id']
    data       = request.get_json(silent=True) or {}
    email      = (data.get('email') or '').strip().lower()
    role       = (data.get('role')  or '').strip().lower()

    if not email or '@' not in email:
        return jsonify({'success': False, 'message': '유효한 이메일을 입력해 주세요.'}), 400
    if role not in ALLOWED_ROLES:
        return jsonify({'success': False,
                        'message': f"role은 {sorted(ALLOWED_ROLES)} 중 하나여야 합니다."}), 400

    db = get_db()
    # 이 사장님이 이미 같은 이메일로 진행 중인 초대가 있는가?
    existing = db.execute(
        """SELECT id, status, expires_at FROM staff_invitations
           WHERE facility_account_id=? AND email=?
           ORDER BY id DESC LIMIT 1""",
        (account_id, email)
    ).fetchone()
    if existing and existing['status'] == 'pending' and \
       datetime.utcnow() <= datetime.fromisoformat(existing['expires_at']):
        db.close()
        return jsonify({'success': False,
                        'message': '이미 진행 중인 초대가 있습니다.'}), 409

    token   = _generate_token()
    exp     = (datetime.utcnow() + timedelta(days=INVITE_TTL_DAY)).isoformat()
    cur = db.execute(
        """INSERT INTO staff_invitations
           (facility_account_id, email, role, invite_token, expires_at)
           VALUES (?,?,?,?,?)""",
        (account_id, email, role, token, exp),
    )
    invite_id = cur.lastrowid
    row = db.execute("SELECT * FROM staff_invitations WHERE id=?", (invite_id,)).fetchone()
    db.commit()
    db.close()

    _send_invite_email(email, token, role)
    return jsonify({'success': True,
                    'message': '직원 초대를 발송했습니다.',
                    'invitation': _row_to_invite(row)}), 201


# ── List ──────────────────────────────────────────────────────────────────────

@staff_bp.route('', methods=['GET'])
@require_auth(sub_type='facility')
def list_my_invites():
    """내가 보낸 초대 목록 (최신순)."""
    account_id = g.auth['user_id']
    db = get_db()
    rows = db.execute(
        """SELECT * FROM staff_invitations
           WHERE facility_account_id=?
           ORDER BY id DESC""",
        (account_id,)
    ).fetchall()
    db.close()
    return jsonify({'success': True,
                    'invitations': [_row_to_invite(r) for r in rows]})


# ── Resend ────────────────────────────────────────────────────────────────────

@staff_bp.route('/<int:iid>/resend', methods=['POST'])
@require_auth(sub_type='facility')
def resend_invite(iid):
    """만료/취소된 초대를 새 토큰·만료일로 갱신해 다시 발송."""
    account_id = g.auth['user_id']
    db = get_db()
    row = db.execute(
        """SELECT * FROM staff_invitations
           WHERE id=? AND facility_account_id=?""",
        (iid, account_id)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '초대를 찾을 수 없습니다.'}), 404

    current_status = _row_status(row)
    if current_status == 'accepted':
        db.close()
        return jsonify({'success': False, 'message': '이미 수락된 초대입니다.'}), 409
    if current_status == 'pending':
        db.close()
        return jsonify({'success': False, 'message': '아직 유효한 초대입니다.'}), 409

    token = _generate_token()
    exp   = (datetime.utcnow() + timedelta(days=INVITE_TTL_DAY)).isoformat()
    db.execute(
        """UPDATE staff_invitations
           SET invite_token=?, expires_at=?, status='pending'
           WHERE id=?""",
        (token, exp, iid),
    )
    new_row = db.execute("SELECT * FROM staff_invitations WHERE id=?", (iid,)).fetchone()
    db.commit()
    db.close()

    _send_invite_email(row['email'], token, row['role'])
    return jsonify({'success': True,
                    'message': '초대를 재발송했습니다.',
                    'invitation': _row_to_invite(new_row)})


# ── Revoke ────────────────────────────────────────────────────────────────────

@staff_bp.route('/<int:iid>', methods=['DELETE'])
@require_auth(sub_type='facility')
def revoke_invite(iid):
    """초대 취소 (status='revoked')."""
    account_id = g.auth['user_id']
    db = get_db()
    row = db.execute(
        """SELECT status FROM staff_invitations
           WHERE id=? AND facility_account_id=?""",
        (iid, account_id)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '초대를 찾을 수 없습니다.'}), 404
    if row['status'] == 'accepted':
        db.close()
        return jsonify({'success': False, 'message': '이미 수락된 초대는 취소할 수 없습니다.'}), 409

    db.execute("UPDATE staff_invitations SET status='revoked' WHERE id=?", (iid,))
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': '초대가 취소되었습니다.'})


# ── Accept (invitee) ─────────────────────────────────────────────────────────

def _staff_token_claims(role: str, owner_account_id: int) -> dict:
    return {'role': role, 'owner_account_id': owner_account_id}


def _row_to_staff_account(row) -> dict:
    return {
        'id':                  row['id'],
        'email':               row['email'],
        'role':                row['role'],
        'name':                row['name'],
        'phone':               row['phone'],
        'facility_account_id': row['facility_account_id'],
    }


@staff_bp.route('/accept', methods=['POST'])
def accept_invite():
    """초대 토큰 + 비밀번호로 staff_accounts 생성 + 토큰 발급.

    - invite_token: pending 상태이고 만료되지 않아야 함
    - password: 영문+숫자+특수 8자+
    - 동일 이메일이 staff_accounts에 이미 있으면 거부
    """
    data     = request.get_json(silent=True) or {}
    token    = (data.get('invite_token') or '').strip()
    password = data.get('password') or ''
    name     = (data.get('name')  or '').strip() or None
    phone    = (data.get('phone') or '').strip() or None

    if not token or not password:
        return jsonify({'success': False,
                        'message': 'invite_token, password는 필수입니다.'}), 400
    pw_err = password_complexity_error(password)
    if pw_err:
        return jsonify({'success': False, 'message': pw_err}), 400

    db = get_db()
    invite = db.execute(
        "SELECT * FROM staff_invitations WHERE invite_token=?",
        (token,)
    ).fetchone()
    if not invite:
        db.close()
        return jsonify({'success': False, 'message': '초대를 찾을 수 없습니다.'}), 404
    if invite['status'] == 'accepted':
        db.close()
        return jsonify({'success': False, 'message': '이미 수락된 초대입니다.'}), 409
    if invite['status'] == 'revoked':
        db.close()
        return jsonify({'success': False, 'message': '취소된 초대입니다.'}), 410
    if datetime.utcnow() > datetime.fromisoformat(invite['expires_at']):
        db.close()
        return jsonify({'success': False, 'message': '만료된 초대입니다.'}), 410

    if db.execute(
        "SELECT 1 FROM staff_accounts WHERE email=?", (invite['email'],)
    ).fetchone():
        db.close()
        return jsonify({'success': False,
                        'message': '이미 가입된 이메일입니다.'}), 409

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    cur = db.execute(
        """INSERT INTO staff_accounts
           (facility_account_id, email, password, role, name, phone, invitation_id)
           VALUES (?,?,?,?,?,?,?)""",
        (invite['facility_account_id'], invite['email'], hashed,
         invite['role'], name, phone, invite['id']),
    )
    staff_id = cur.lastrowid
    db.execute(
        "UPDATE staff_invitations SET status='accepted', accepted_at=datetime('now') WHERE id=?",
        (invite['id'],)
    )
    row = db.execute("SELECT * FROM staff_accounts WHERE id=?", (staff_id,)).fetchone()
    db.commit()
    db.close()

    claims = _staff_token_claims(row['role'], row['facility_account_id'])
    return jsonify({
        'success': True,
        'message': '직원 가입이 완료되었습니다.',
        **issue_token_pair(staff_id, row['email'], sub_type='staff', extra_claims=claims),
        'staff_account': _row_to_staff_account(row),
    }), 201


# ── Login / Me ────────────────────────────────────────────────────────────────

@staff_bp.route('/login', methods=['POST'])
def staff_login():
    """직원/관리자 로그인. 토큰에 role + owner_account_id 포함."""
    data     = request.get_json(silent=True) or {}
    email    = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not email or not password:
        return jsonify({'success': False,
                        'message': '이메일과 비밀번호를 입력해 주세요.'}), 400

    db = get_db()
    row = db.execute(
        "SELECT * FROM staff_accounts WHERE email=?", (email,)
    ).fetchone()
    db.close()
    if not row or not bcrypt.checkpw(password.encode(), row['password'].encode()):
        return jsonify({'success': False,
                        'message': '이메일 또는 비밀번호가 올바르지 않습니다.'}), 401

    claims = _staff_token_claims(row['role'], row['facility_account_id'])
    return jsonify({
        'success': True,
        'message': '로그인 성공!',
        **issue_token_pair(row['id'], email, sub_type='staff', extra_claims=claims),
        'staff_account': _row_to_staff_account(row),
    })


@staff_bp.route('/me', methods=['GET'])
@require_auth(sub_type='staff')
def staff_me():
    """본인 정보 + 소속 사장님(매장 그룹) 정보 간략 반환."""
    db = get_db()
    row = db.execute(
        "SELECT * FROM staff_accounts WHERE id=?", (g.auth['user_id'],)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '계정을 찾을 수 없습니다.'}), 404
    owner = db.execute(
        "SELECT id, company_name FROM facility_accounts WHERE id=?",
        (row['facility_account_id'],)
    ).fetchone()
    db.close()
    return jsonify({
        'success': True,
        'staff_account': _row_to_staff_account(row),
        'owner': dict(owner) if owner else None,
    })
