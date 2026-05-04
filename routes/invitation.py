"""초대 코드 (Invitation) API — 회원 폐쇄형 가입 흐름.

PR #29 — "와이파이 초대" 기능.
회원/사장/직원이 코드를 발급하고, 받은 사람이 가입 시 그 코드를 사용한다.
가입 완료 시 초대자에게 보상을 부여할 수 있다.

엔드포인트
---------
- POST /api/invitations           — 코드 생성 (user / facility owner / staff)
- GET  /api/invitations           — 내가 발급한 코드 목록
- GET  /api/invitations/<code>    — 코드 검증 (가입 페이지에서 호출)

내부 함수 ``consume_invitation()`` 은 ``routes/auth.py`` 의 register/social_login
에서 가입 완료 직후 호출되어 초대 레코드를 ``accepted`` 상태로 마킹한다.
"""
import os
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify

from models.database import get_db
from routes.auth import decode_access_token

invitation_bp = Blueprint('invitation', __name__, url_prefix='/api/invitations')

INVITATION_REQUIRED = os.environ.get('INVITATION_REQUIRED', '0') == '1'
DEFAULT_EXPIRES_HOURS = int(os.environ.get('INVITATION_EXPIRES_HOURS', '168'))  # 7일


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────
def _generate_code() -> str:
    """대소문자 + 숫자 10자리 short code (URL-safe)."""
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # 헷갈리는 0/O/1/I 제거
    return ''.join(secrets.choice(alphabet) for _ in range(10))


def _resolve_actor(auth_header: str):
    """Authorization 헤더에서 sub_type별로 actor를 식별.

    return: dict {kind: 'user'|'facility'|'staff', id: int, email: str} 또는 None
    """
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ', 1)[1]
    # 시도 순서: user → facility → staff
    for sub_type in ('user', 'facility', 'staff'):
        try:
            payload = decode_access_token(token, expected_sub_type=sub_type)
            return {
                'kind':  sub_type,
                'id':    payload['user_id'],
                'email': payload.get('email', ''),
            }
        except ValueError:
            continue
    return None


def is_invitation_required() -> bool:
    """다른 모듈(auth)에서 폐쇄형 가입 강제 여부 판단."""
    return INVITATION_REQUIRED


def validate_code(db, code: str):
    """코드를 검증하고 invitation row를 반환. 잘못된 경우 (None, 에러메시지)."""
    if not code:
        return None, '초대 코드가 필요합니다.'
    row = db.execute(
        """SELECT * FROM invitations WHERE code=? LIMIT 1""", (code,)
    ).fetchone()
    if not row:
        return None, '존재하지 않는 초대 코드입니다.'
    if row['accepted_user_id']:
        return None, '이미 사용된 초대 코드입니다.'
    if row['expires_at']:
        if datetime.utcnow() > datetime.fromisoformat(row['expires_at']):
            return None, '만료된 초대 코드입니다.'
    return row, None


def consume_invitation(db, code: str, accepted_user_id: int) -> bool:
    """가입 완료 직후 호출. 코드를 accepted 처리하고 보상 트리거.

    호출 측이 db connection을 commit해야 함.
    return: 성공 여부 (이미 사용된 코드면 False)
    """
    if not code:
        return False
    row = db.execute(
        "SELECT id, accepted_user_id FROM invitations WHERE code=?", (code,)
    ).fetchone()
    if not row or row['accepted_user_id']:
        return False
    db.execute(
        """UPDATE invitations
           SET accepted_user_id=?, accepted_at=datetime('now')
           WHERE id=?""",
        (accepted_user_id, row['id'])
    )
    return True


# ── 엔드포인트 ───────────────────────────────────────────────────────────────
@invitation_bp.route('', methods=['POST'])
def create_invitation():
    """초대 코드 생성. 회원/사장/직원 인증 토큰 필요."""
    actor = _resolve_actor(request.headers.get('Authorization', ''))
    if not actor:
        return jsonify({'success': False, 'message': '인증이 필요합니다.'}), 401

    data           = request.get_json(silent=True) or {}
    invitee_email  = (data.get('invitee_email') or '').strip().lower() or None
    invitee_phone  = (data.get('invitee_phone') or '').strip() or None
    channel        = (data.get('channel') or 'link').strip().lower()
    facility_id    = data.get('facility_id')   # owner/staff 발급 시 매장 지정 가능

    if channel not in ('link', 'kakao', 'sms', 'qr'):
        return jsonify({'success': False, 'message': '지원하지 않는 채널입니다.'}), 400

    code = _generate_code()
    expires_at = (datetime.utcnow() + timedelta(hours=DEFAULT_EXPIRES_HOURS)).isoformat()

    # actor 종류별 inviter 컬럼 매핑
    inviter_user_id             = actor['id'] if actor['kind'] == 'user'     else None
    inviter_facility_id         = facility_id if actor['kind'] == 'facility' else None
    inviter_facility_account_id = actor['id'] if actor['kind'] == 'facility' else None
    inviter_staff_id            = actor['id'] if actor['kind'] == 'staff'    else None

    db  = get_db()
    cur = db.execute(
        """INSERT INTO invitations
           (code, inviter_user_id, inviter_facility_id, inviter_facility_account_id,
            inviter_staff_id, invitee_email, invitee_phone, channel, expires_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (code, inviter_user_id, inviter_facility_id, inviter_facility_account_id,
         inviter_staff_id, invitee_email, invitee_phone, channel, expires_at)
    )
    invitation_id = cur.lastrowid
    db.commit(); db.close()

    base_url = os.environ.get('SIGNUP_BASE_URL', 'https://pathwave.io/signup')
    share_url = f'{base_url}?invite={code}'

    return jsonify({
        'success': True,
        'invitation': {
            'id': invitation_id,
            'code': code,
            'channel': channel,
            'share_url': share_url,
            'expires_at': expires_at,
            'inviter_kind': actor['kind'],
        },
    }), 201


@invitation_bp.route('', methods=['GET'])
def list_invitations():
    """내가 발급한 초대 목록 (회원/사장/직원 모두 자신 기준)."""
    actor = _resolve_actor(request.headers.get('Authorization', ''))
    if not actor:
        return jsonify({'success': False, 'message': '인증이 필요합니다.'}), 401

    if actor['kind'] == 'user':
        sql = "SELECT * FROM invitations WHERE inviter_user_id=? ORDER BY id DESC LIMIT 100"
    elif actor['kind'] == 'facility':
        # facility actor의 경우 user_id가 facility_account_id를 의미할 수 있음 → 모든 매장 발급분
        sql = "SELECT * FROM invitations WHERE inviter_facility_id IS NOT NULL ORDER BY id DESC LIMIT 100"
    else:  # staff
        sql = "SELECT * FROM invitations WHERE inviter_staff_id=? ORDER BY id DESC LIMIT 100"

    db = get_db()
    if actor['kind'] == 'facility':
        rows = db.execute(sql).fetchall()
    else:
        rows = db.execute(sql, (actor['id'],)).fetchall()
    db.close()

    items = []
    for r in rows:
        items.append({
            'id': r['id'],
            'code': r['code'],
            'channel': r['channel'],
            'invitee_email': r['invitee_email'],
            'invitee_phone': r['invitee_phone'],
            'accepted_user_id': r['accepted_user_id'],
            'accepted_at': r['accepted_at'],
            'rewarded': bool(r['rewarded']),
            'expires_at': r['expires_at'],
            'created_at': r['created_at'],
        })
    return jsonify({'success': True, 'invitations': items, 'count': len(items)})


@invitation_bp.route('/<code>', methods=['GET'])
def verify_code(code: str):
    """가입 페이지에서 코드 유효성 사전 검증 (인증 불필요).

    초대자 정보(닉네임/매장명)를 노출해 신규 사용자에게 신뢰를 줄 수 있다.
    """
    db = get_db()
    row, err = validate_code(db, code)
    if err:
        db.close()
        return jsonify({'success': False, 'message': err}), 400

    inviter_label = '익명'
    if row['inviter_user_id']:
        u = db.execute(
            "SELECT email FROM users WHERE id=?", (row['inviter_user_id'],)
        ).fetchone()
        if u:
            inviter_label = u['email'].split('@')[0]
    elif row['inviter_facility_id']:
        f = db.execute(
            "SELECT name FROM facilities WHERE id=?", (row['inviter_facility_id'],)
        ).fetchone()
        if f:
            inviter_label = f['name']
    elif row['inviter_facility_account_id']:
        fa = db.execute(
            "SELECT company_name FROM facility_accounts WHERE id=?",
            (row['inviter_facility_account_id'],)
        ).fetchone()
        if fa:
            inviter_label = fa['company_name']
    db.close()

    return jsonify({
        'success': True,
        'invitation': {
            'code': row['code'],
            'channel': row['channel'],
            'inviter_label': inviter_label,
            'expires_at': row['expires_at'],
        },
    })
