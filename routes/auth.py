import os
import random
import re
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from functools import wraps

import bcrypt
import jwt
from flask import Blueprint, request, jsonify, g

from models.database import get_db

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

SECRET_KEY = os.environ.get('SECRET_KEY', 'pathwave-super-secret-key-2024')
SMTP_HOST  = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT  = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER  = os.environ.get('SMTP_USER', '')
SMTP_PASS  = os.environ.get('SMTP_PASS', '')
EMAIL_FROM = os.environ.get('EMAIL_FROM', SMTP_USER)

ACCESS_TTL_MIN  = int(os.environ.get('ACCESS_TTL_MIN', '15'))   # SRS: 15분
REFRESH_TTL_DAY = int(os.environ.get('REFRESH_TTL_DAY', '7'))   # SRS: 7일


# ── Helpers ──────────────────────────────────────────────────────────────────

def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))


def make_jwt(user_id: int, email: str, kind: str = 'access',
             sub_type: str = 'user', extra_claims: dict | None = None) -> str:
    """``kind`` = ``access`` (15m) | ``refresh`` (7d). SRS FR-AUTH-002.

    ``sub_type`` = ``user`` | ``facility`` | ``staff``.
    동일 숫자 ID가 여러 테이블에 존재할 수 있으므로 토큰에 표시한다.
    ``extra_claims``로 role / owner_account_id 등 추가 클레임을 실어 보낼 수 있다.
    """
    ttl = (timedelta(minutes=ACCESS_TTL_MIN)
           if kind == 'access' else timedelta(days=REFRESH_TTL_DAY))
    payload = {
        'user_id': user_id, 'email': email, 'kind': kind,
        'sub_type': sub_type,
        'exp': datetime.utcnow() + ttl,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def issue_token_pair(user_id: int, email: str, sub_type: str = 'user',
                     extra_claims: dict | None = None) -> dict:
    return {
        'token':         make_jwt(user_id, email, 'access',  sub_type, extra_claims),
        'access_token':  make_jwt(user_id, email, 'access',  sub_type, extra_claims),
        'refresh_token': make_jwt(user_id, email, 'refresh', sub_type, extra_claims),
        'expires_in':    ACCESS_TTL_MIN * 60,
    }


def decode_access_token(token: str, expected_sub_type: str = 'user') -> dict:
    """access 토큰 검증 + sub_type 일치 확인. 실패 시 ``ValueError`` (메시지) 발생."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise ValueError('토큰이 만료되었습니다.')
    except jwt.InvalidTokenError:
        raise ValueError('유효하지 않은 토큰입니다.')
    if payload.get('kind', 'access') != 'access':
        raise ValueError('access 토큰이 아닙니다.')
    # sub_type 누락 = 레거시 user 토큰. 신규 발급분부터는 명시.
    if payload.get('sub_type', 'user') != expected_sub_type:
        raise ValueError('이 엔드포인트에 사용할 수 없는 토큰입니다.')
    return payload


def require_super_admin(roles: list[str] | None = None):
    """Super Admin (PathWave 운영자) 라우트 보호 데코레이터.

    토큰 ``sub_type='super_admin'`` 강제. ``roles=['super']``로 제한 가능.
    성공 시 ``g.auth``에 페이로드 + ``actor_role`` 세팅. 실패 시 401/403.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_hdr = request.headers.get('Authorization', '')
            if not auth_hdr.startswith('Bearer '):
                return jsonify({'success': False,
                                'message': '인증 토큰이 없습니다.'}), 401
            token = auth_hdr.split(' ', 1)[1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return jsonify({'success': False, 'message': '토큰이 만료되었습니다.'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'success': False, 'message': '유효하지 않은 토큰입니다.'}), 401
            if payload.get('kind', 'access') != 'access':
                return jsonify({'success': False, 'message': 'access 토큰이 아닙니다.'}), 401
            if payload.get('sub_type') != 'super_admin':
                return jsonify({'success': False,
                                'message': 'Super Admin 토큰이 아닙니다.'}), 401

            actor_role = payload.get('role') or 'admin'
            if roles and actor_role not in roles:
                return jsonify({'success': False,
                                'message': f'권한이 없습니다. 필요: {sorted(roles)}'}), 403

            payload['actor_role'] = actor_role
            g.auth = payload
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_facility_actor(roles: list[str] | None = None):
    """시설 측(owner/admin/staff) 라우트 보호 데코레이터.

    ``sub_type='facility'`` 토큰은 actor_role='owner'로 정규화하고,
    ``sub_type='staff'`` 토큰은 토큰의 ``role``과 ``owner_account_id``를 그대로 사용한다.

    실패 시 401/403, 성공 시 ``flask.g.auth``에 다음 키를 보장:
      - actor_role         'owner' | 'admin' | 'staff'
      - owner_account_id   데이터 범위 결정용 (=facility_accounts.id)
      - user_id, email, sub_type 등 원본 클레임도 그대로
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_hdr = request.headers.get('Authorization', '')
            if not auth_hdr.startswith('Bearer '):
                return jsonify({'success': False,
                                'message': '인증 토큰이 없습니다.'}), 401
            token = auth_hdr.split(' ', 1)[1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return jsonify({'success': False, 'message': '토큰이 만료되었습니다.'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'success': False, 'message': '유효하지 않은 토큰입니다.'}), 401
            if payload.get('kind', 'access') != 'access':
                return jsonify({'success': False, 'message': 'access 토큰이 아닙니다.'}), 401

            sub_type = payload.get('sub_type', 'user')
            if sub_type == 'facility':
                actor_role       = 'owner'
                owner_account_id = payload['user_id']
            elif sub_type == 'staff':
                actor_role       = payload.get('role')
                owner_account_id = payload.get('owner_account_id')
                if actor_role not in {'admin', 'staff'} or not owner_account_id:
                    return jsonify({'success': False,
                                    'message': '토큰 클레임이 누락되었습니다.'}), 401
            else:
                return jsonify({'success': False,
                                'message': '시설 측 토큰이 아닙니다.'}), 401

            if roles and actor_role not in roles:
                return jsonify({'success': False,
                                'message': f'권한이 없습니다. 필요: {sorted(roles)}'}), 403

            payload['actor_role']       = actor_role
            payload['owner_account_id'] = owner_account_id
            g.auth = payload
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_auth(sub_type: str = 'user'):
    """라우트 보호 데코레이터.

    사용:
        @require_auth(sub_type='facility')
        def my_route():
            account_id = g.auth['user_id']  # facility_accounts.id
            ...

    실패 시 401을 반환하고, 성공 시 ``flask.g.auth`` 에 토큰 페이로드를 주입한다.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth = request.headers.get('Authorization', '')
            if not auth.startswith('Bearer '):
                return jsonify({'success': False,
                                'message': '인증 토큰이 없습니다.'}), 401
            try:
                payload = decode_access_token(
                    auth.split(' ', 1)[1], expected_sub_type=sub_type)
            except ValueError as e:
                return jsonify({'success': False, 'message': str(e)}), 401
            g.auth = payload
            return fn(*args, **kwargs)
        return wrapper
    return decorator


_PW_COMPLEX_RE = re.compile(
    r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$'
)


def password_complexity_error(password: str) -> str | None:
    """SRS FR-AUTH-001: 영문+숫자+특수문자 8자 이상."""
    if not password or len(password) < 8:
        return '비밀번호는 최소 8자 이상이어야 합니다.'
    if not _PW_COMPLEX_RE.match(password):
        return '비밀번호는 영문, 숫자, 특수문자를 모두 포함해야 합니다.'
    return None


def firebase_ready() -> bool:
    """firebase_admin이 import 가능하고 default app이 초기화돼 있는지."""
    try:
        import firebase_admin
        return bool(firebase_admin._apps)
    except Exception:
        return False


def send_email(to_email: str, code: str) -> bool:
    if not SMTP_USER or not SMTP_PASS:
        print(f"\n{'='*50}")
        print('[개발 모드] 이메일 인증 코드')
        print(f'수신: {to_email}')
        print(f'코드: {code}')
        print(f"{'='*50}\n")
        return True
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '[PathWave] 이메일 인증 코드'
        msg['From']    = EMAIL_FROM
        msg['To']      = to_email
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px;
                    background:#0f0f1a;border-radius:16px;color:#fff;">
          <h2 style="color:#7c3aed;">PathWave 이메일 인증</h2>
          <p style="color:#a1a1aa;">아래 인증 코드를 입력해 주세요. (5분 내 유효)</p>
          <div style="background:#1e1e2e;border:2px solid #7c3aed;border-radius:12px;
                      padding:24px;text-align:center;">
            <span style="font-size:40px;font-weight:bold;letter-spacing:12px;color:#a78bfa;">
              {code}
            </span>
          </div>
          <p style="color:#71717a;font-size:12px;margin-top:16px;">
            본인이 요청하지 않은 경우 이 메일을 무시하세요.
          </p>
        </div>
        """
        msg.attach(MIMEText(html, 'html'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f'[이메일 발송 오류] {e}')
        return False


# ── 이메일 인증 ───────────────────────────────────────────────────────────────

@auth_bp.route('/send-code', methods=['POST'])
def send_code():
    """Step 1: 이메일 입력 → 인증 코드 발송"""
    data  = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()

    if not email or '@' not in email:
        return jsonify({'success': False, 'message': '유효한 이메일을 입력해 주세요.'}), 400

    db = get_db()
    existing = db.execute(
        "SELECT id FROM users WHERE email=? AND deleted_at IS NULL", (email,)
    ).fetchone()
    if existing:
        db.close()
        return jsonify({'success': False, 'message': '이미 가입된 이메일입니다.'}), 409

    code       = generate_code()
    expires_at = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    db.execute('UPDATE email_codes SET used=1 WHERE email=? AND used=0', (email,))
    db.execute(
        'INSERT INTO email_codes (email, code, expires_at) VALUES (?,?,?)',
        (email, code, expires_at)
    )
    db.commit()
    db.close()

    if not send_email(email, code):
        return jsonify({'success': False, 'message': '이메일 발송에 실패했습니다.'}), 500
    return jsonify({'success': True, 'message': '인증 코드를 발송했습니다.'})


@auth_bp.route('/verify-code', methods=['POST'])
def verify_code():
    """Step 2: 인증 코드 검증"""
    data  = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    code  = (data.get('code')  or '').strip()

    if not email or not code:
        return jsonify({'success': False, 'message': '이메일과 코드를 모두 입력해 주세요.'}), 400

    db  = get_db()
    row = db.execute(
        """SELECT id, expires_at FROM email_codes
           WHERE email=? AND code=? AND used=0
           ORDER BY id DESC LIMIT 1""",
        (email, code)
    ).fetchone()
    db.close()

    if not row:
        return jsonify({'success': False, 'message': '인증 코드가 올바르지 않습니다.'}), 400
    if datetime.utcnow() > datetime.fromisoformat(row['expires_at']):
        return jsonify({'success': False, 'message': '인증 코드가 만료되었습니다.'}), 400
    return jsonify({'success': True, 'message': '이메일 인증이 완료되었습니다.'})


@auth_bp.route('/register', methods=['POST'])
def register():
    """Step 3: 비밀번호 설정 → 최종 회원가입.

    회원 폐쇄형(``INVITATION_REQUIRED=1``) 환경에서는 ``invitation_code`` 필수.
    """
    from routes.invitation import is_invitation_required, validate_code, consume_invitation

    data            = request.get_json(silent=True) or {}
    email           = (data.get('email')           or '').strip().lower()
    code            = (data.get('code')            or '').strip()
    password        = (data.get('password')        or '')
    invitation_code = (data.get('invitation_code') or '').strip() or None

    if not email or not code or not password:
        return jsonify({'success': False, 'message': '모든 필드를 입력해 주세요.'}), 400
    pw_err = password_complexity_error(password)
    if pw_err:
        return jsonify({'success': False, 'message': pw_err}), 400

    db  = get_db()
    row = db.execute(
        """SELECT id, expires_at FROM email_codes
           WHERE email=? AND code=? AND used=0
           ORDER BY id DESC LIMIT 1""",
        (email, code)
    ).fetchone()

    if not row or datetime.utcnow() > datetime.fromisoformat(row['expires_at']):
        db.close()
        return jsonify({'success': False, 'message': '인증이 만료되었습니다. 처음부터 다시 진행해 주세요.'}), 400

    if db.execute("SELECT id FROM users WHERE email=? AND deleted_at IS NULL", (email,)).fetchone():
        db.close()
        return jsonify({'success': False, 'message': '이미 가입된 이메일입니다.'}), 409

    # 폐쇄형 가입: 초대 코드 검증
    if is_invitation_required():
        if not invitation_code:
            db.close()
            return jsonify({'success': False,
                            'message': '회원 가입은 초대 코드가 있어야 진행됩니다.'}), 403
        invite_row, err = validate_code(db, invitation_code)
        if err:
            db.close()
            return jsonify({'success': False, 'message': err}), 400

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    cur = db.execute(
        'INSERT INTO users (email, password, provider, invited_via_code) VALUES (?,?,?,?)',
        (email, hashed, 'email', invitation_code)
    )
    user_id = cur.lastrowid
    db.execute('UPDATE email_codes SET used=1 WHERE email=? AND code=?', (email, code))
    if invitation_code:
        consume_invitation(db, invitation_code, user_id)
    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'message': '회원가입이 완료되었습니다!',
        **issue_token_pair(user_id, email),
        'user': {'id': user_id, 'email': email},
    })


@auth_bp.route('/login', methods=['POST'])
def login():
    """이메일 로그인"""
    data     = request.get_json(silent=True) or {}
    email    = (data.get('email')    or '').strip().lower()
    password = (data.get('password') or '')

    if not email or not password:
        return jsonify({'success': False, 'message': '이메일과 비밀번호를 입력해 주세요.'}), 400

    db  = get_db()
    row = db.execute(
        "SELECT id, password, provider FROM users WHERE email=? AND deleted_at IS NULL",
        (email,)
    ).fetchone()
    db.close()

    if not row:
        return jsonify({'success': False, 'message': '이메일 또는 비밀번호가 올바르지 않습니다.'}), 401
    if row['provider'] != 'email':
        return jsonify({'success': False, 'message': f'{row["provider"]} 소셜 로그인 계정입니다.'}), 401
    if not bcrypt.checkpw(password.encode(), row['password'].encode()):
        return jsonify({'success': False, 'message': '이메일 또는 비밀번호가 올바르지 않습니다.'}), 401

    return jsonify({
        'success': True,
        'message': '로그인 성공!',
        **issue_token_pair(row['id'], email),
        'user': {'id': row['id'], 'email': email},
    })


@auth_bp.route('/social', methods=['POST'])
def social_login():
    """소셜 로그인 (Firebase ID Token 검증)
    Flutter 앱에서 Firebase Auth로 로그인 후 ID Token을 전송.
    서버는 Firebase Admin SDK로 토큰 검증 후 자체 JWT 발급.
    """
    if not firebase_ready():
        return jsonify({'success': False,
                        'message': 'Firebase SDK가 설정되지 않았습니다. 서버 관리자에게 문의해 주세요.'}), 503
    from firebase_admin import auth as firebase_auth

    from routes.invitation import is_invitation_required, validate_code, consume_invitation

    data            = request.get_json(silent=True) or {}
    id_token        = (data.get('id_token') or '').strip()
    provider        = (data.get('provider') or 'social').strip()  # google / apple / kakao / naver
    invitation_code = (data.get('invitation_code') or '').strip() or None

    if not id_token:
        return jsonify({'success': False, 'message': 'ID Token이 필요합니다.'}), 400

    try:
        decoded = firebase_auth.verify_id_token(id_token)
    except Exception as e:
        return jsonify({'success': False, 'message': f'토큰 검증 실패: {str(e)}'}), 401

    firebase_uid = decoded.get('uid')
    email        = (decoded.get('email') or '').lower()
    if not email:
        return jsonify({'success': False, 'message': '이메일 정보를 가져올 수 없습니다.'}), 400

    db = get_db()
    # 기존 소셜 계정 확인 (social_id 기준)
    row = db.execute(
        "SELECT id, email FROM users WHERE social_id=? AND provider=? AND deleted_at IS NULL",
        (firebase_uid, provider)
    ).fetchone()

    if row:
        # 기존 사용자 → 로그인
        user_id    = row['id']
        user_email = row['email']
    else:
        # 이메일로 기존 계정 확인 (다른 방식으로 가입했을 수 있음)
        email_row = db.execute(
            "SELECT id FROM users WHERE email=? AND deleted_at IS NULL", (email,)
        ).fetchone()
        if email_row:
            # 기존 이메일 계정에 소셜 정보 연결
            db.execute(
                "UPDATE users SET social_id=?, provider=? WHERE id=?",
                (firebase_uid, provider, email_row['id'])
            )
            db.commit()
            user_id    = email_row['id']
            user_email = email
        else:
            # 신규 사용자 → 자동 회원가입 (폐쇄형이면 초대 코드 검증)
            if is_invitation_required():
                if not invitation_code:
                    db.close()
                    return jsonify({'success': False,
                                    'message': '회원 가입은 초대 코드가 있어야 진행됩니다.'}), 403
                _, err = validate_code(db, invitation_code)
                if err:
                    db.close()
                    return jsonify({'success': False, 'message': err}), 400
            db.execute(
                "INSERT INTO users (email, provider, social_id, invited_via_code) VALUES (?,?,?,?)",
                (email, provider, firebase_uid, invitation_code)
            )
            user_id = db.execute(
                "SELECT id FROM users WHERE email=?", (email,)
            ).fetchone()['id']
            if invitation_code:
                consume_invitation(db, invitation_code, user_id)
            db.commit()
            user_email = email

    db.close()
    return jsonify({
        'success': True,
        'message': '로그인 성공!',
        **issue_token_pair(user_id, user_email),
        'user': {'id': user_id, 'email': user_email},
    })


@auth_bp.route('/me', methods=['GET'])
def me():
    """토큰으로 현재 유저 정보 조회 (앱 사용자)."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'success': False, 'message': '인증 토큰이 없습니다.'}), 401
    try:
        payload = decode_access_token(auth.split(' ', 1)[1], expected_sub_type='user')
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 401
    return jsonify({'success': True, 'user': {'id': payload['user_id'], 'email': payload['email']}})


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh 토큰으로 새 access 토큰 발급. SRS FR-AUTH-002."""
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

    db  = get_db()
    row = db.execute(
        "SELECT id, email FROM users WHERE id=? AND deleted_at IS NULL",
        (payload['user_id'],)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({'success': False, 'message': '유저를 찾을 수 없습니다.'}), 401

    return jsonify({
        'success': True,
        **issue_token_pair(row['id'], row['email']),
    })


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """비밀번호 찾기: 이메일 인증 코드 발송"""
    data  = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()

    if not email or '@' not in email:
        return jsonify({'success': False, 'message': '유효한 이메일을 입력해 주세요.'}), 400

    db  = get_db()
    row = db.execute(
        "SELECT id, provider FROM users WHERE email=? AND deleted_at IS NULL", (email,)
    ).fetchone()

    # 보안: 존재 여부와 가입 방식 모두 숨긴다 (SRS 4.2 보안 — 계정 열거 방지)
    if not row or row['provider'] != 'email':
        db.close()
        return jsonify({'success': True, 'message': '인증 코드를 발송했습니다. 이메일을 확인해 주세요.'})

    code       = generate_code()
    expires_at = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    db.execute('UPDATE email_codes SET used=1 WHERE email=? AND used=0', (email,))
    db.execute(
        'INSERT INTO email_codes (email, code, expires_at) VALUES (?,?,?)',
        (email, code, expires_at)
    )
    db.commit()
    db.close()

    send_email(email, code)
    return jsonify({'success': True, 'message': '인증 코드를 발송했습니다. 이메일을 확인해 주세요.'})


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """비밀번호 재설정"""
    data     = request.get_json(silent=True) or {}
    email    = (data.get('email')    or '').strip().lower()
    code     = (data.get('code')     or '').strip()
    password = (data.get('password') or '')

    if not email or not code or not password:
        return jsonify({'success': False, 'message': '모든 필드를 입력해 주세요.'}), 400
    pw_err = password_complexity_error(password)
    if pw_err:
        return jsonify({'success': False, 'message': pw_err}), 400

    db  = get_db()
    row = db.execute(
        """SELECT id, expires_at FROM email_codes
           WHERE email=? AND code=? AND used=0
           ORDER BY id DESC LIMIT 1""",
        (email, code)
    ).fetchone()

    if not row or datetime.utcnow() > datetime.fromisoformat(row['expires_at']):
        db.close()
        return jsonify({'success': False, 'message': '인증 코드가 올바르지 않거나 만료되었습니다.'}), 400

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    db.execute('UPDATE users SET password=? WHERE email=?', (hashed, email))
    db.execute('UPDATE email_codes SET used=1 WHERE email=? AND code=?', (email, code))
    db.commit()
    db.close()

    return jsonify({'success': True, 'message': '비밀번호가 재설정되었습니다.'})
