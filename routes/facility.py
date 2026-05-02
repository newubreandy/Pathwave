"""시설(매장) 계정 회원가입 / 로그인 API. SRS FR-AUTH-001/002.

엔드포인트
---------
- ``POST /api/facility/send-code``    이메일 인증 코드 발송
- ``POST /api/facility/verify-code``  인증 코드 검증
- ``POST /api/facility/register``     8필드 회원가입 완료 (토큰 발급)
- ``POST /api/facility/login``        이메일/비밀번호 로그인
- ``GET  /api/facility/me``           현재 시설 계정 조회
"""
import re
from datetime import datetime, timedelta

import bcrypt
from flask import Blueprint, request, jsonify

from models.database import get_db
from routes.auth import (
    generate_code, send_email,
    password_complexity_error, issue_token_pair, decode_access_token,
)

facility_bp = Blueprint('facility', __name__, url_prefix='/api/facility')

_BUSINESS_NO_RE = re.compile(r'^\d{3}-\d{2}-\d{5}$')


def _business_no_error(no: str) -> str | None:
    if not _BUSINESS_NO_RE.match(no or ''):
        return '사업자등록번호 형식이 올바르지 않습니다 (예: 123-45-67890).'
    return None


# ── 이메일 인증 ───────────────────────────────────────────────────────────────

@facility_bp.route('/send-code', methods=['POST'])
def send_code():
    """시설 회원가입용 이메일 인증 코드 발송."""
    data  = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    if not email or '@' not in email:
        return jsonify({'success': False, 'message': '유효한 이메일을 입력해 주세요.'}), 400

    db = get_db()
    if db.execute("SELECT 1 FROM facility_accounts WHERE email=?", (email,)).fetchone():
        db.close()
        return jsonify({'success': False, 'message': '이미 가입된 이메일입니다.'}), 409

    code = generate_code()
    exp  = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    db.execute('UPDATE email_codes SET used=1 WHERE email=? AND used=0', (email,))
    db.execute('INSERT INTO email_codes (email, code, expires_at) VALUES (?,?,?)',
               (email, code, exp))
    db.commit(); db.close()

    if not send_email(email, code):
        return jsonify({'success': False, 'message': '이메일 발송에 실패했습니다.'}), 500
    return jsonify({'success': True, 'message': '인증 코드를 발송했습니다.'})


@facility_bp.route('/verify-code', methods=['POST'])
def verify_code():
    """이메일 인증 코드 검증 (실제 used=1 처리는 register에서)."""
    data  = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    code  = (data.get('code')  or '').strip()
    if not email or not code:
        return jsonify({'success': False, 'message': '이메일과 코드를 모두 입력해 주세요.'}), 400

    db  = get_db()
    row = db.execute(
        """SELECT expires_at FROM email_codes
           WHERE email=? AND code=? AND used=0
           ORDER BY id DESC LIMIT 1""", (email, code)
    ).fetchone()
    db.close()

    if not row:
        return jsonify({'success': False, 'message': '인증 코드가 올바르지 않습니다.'}), 400
    if datetime.utcnow() > datetime.fromisoformat(row['expires_at']):
        return jsonify({'success': False, 'message': '인증 코드가 만료되었습니다.'}), 400
    return jsonify({'success': True, 'message': '이메일 인증이 완료되었습니다.'})


# ── 회원가입 ──────────────────────────────────────────────────────────────────

@facility_bp.route('/register', methods=['POST'])
def register():
    """시설 계정 회원가입 (SRS FR-AUTH-001).

    필수 필드 (8개):
      - company_name   업체명(상호)
      - business_no    사업자등록번호 (000-00-00000)
      - email          로그인 이메일
      - password       비밀번호 (영+숫+특 8자+)
      - code           이메일 인증 코드
      - manager_name   담당자 성함
      - manager_phone  담당자 연락처
      - manager_email  담당자 이메일
    """
    data          = request.get_json(silent=True) or {}
    email         = (data.get('email')         or '').strip().lower()
    code          = (data.get('code')          or '').strip()
    password      = (data.get('password')      or '')
    company_name  = (data.get('company_name')  or '').strip()
    business_no   = (data.get('business_no')   or '').strip()
    manager_name  = (data.get('manager_name')  or '').strip()
    manager_phone = (data.get('manager_phone') or '').strip()
    manager_email = (data.get('manager_email') or '').strip().lower()

    if not all([email, code, password, company_name, business_no,
                manager_name, manager_phone, manager_email]):
        return jsonify({'success': False, 'message': '모든 필드를 입력해 주세요.'}), 400

    if (err := _business_no_error(business_no)):
        return jsonify({'success': False, 'message': err}), 400
    if (err := password_complexity_error(password)):
        return jsonify({'success': False, 'message': err}), 400

    db  = get_db()
    row = db.execute(
        """SELECT expires_at FROM email_codes
           WHERE email=? AND code=? AND used=0
           ORDER BY id DESC LIMIT 1""", (email, code)
    ).fetchone()
    if not row or datetime.utcnow() > datetime.fromisoformat(row['expires_at']):
        db.close()
        return jsonify({'success': False, 'message': '인증이 만료되었습니다. 처음부터 다시 진행해 주세요.'}), 400

    if db.execute(
        "SELECT 1 FROM facility_accounts WHERE email=? OR business_no=?",
        (email, business_no)
    ).fetchone():
        db.close()
        return jsonify({'success': False,
                        'message': '이미 가입된 이메일 또는 사업자번호입니다.'}), 409

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    cur = db.execute(
        """INSERT INTO facility_accounts
           (business_no, company_name, email, password,
            manager_name, manager_phone, manager_email, verified)
           VALUES (?,?,?,?,?,?,?,1)""",
        (business_no, company_name, email, hashed,
         manager_name, manager_phone, manager_email)
    )
    facility_account_id = cur.lastrowid
    db.execute('UPDATE email_codes SET used=1 WHERE email=? AND code=?', (email, code))
    db.commit(); db.close()

    return jsonify({
        'success': True,
        'message': '시설 회원가입이 완료되었습니다!',
        **issue_token_pair(facility_account_id, email, sub_type='facility'),
        'facility_account': {
            'id': facility_account_id,
            'company_name': company_name,
            'email': email,
        },
    })


# ── 로그인 ────────────────────────────────────────────────────────────────────

@facility_bp.route('/login', methods=['POST'])
def login():
    """시설 계정 로그인."""
    data     = request.get_json(silent=True) or {}
    email    = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '')
    if not email or not password:
        return jsonify({'success': False, 'message': '이메일과 비밀번호를 입력해 주세요.'}), 400

    db  = get_db()
    row = db.execute(
        "SELECT id, password, company_name FROM facility_accounts WHERE email=?",
        (email,)
    ).fetchone()
    db.close()

    if not row or not bcrypt.checkpw(password.encode(), row['password'].encode()):
        return jsonify({'success': False,
                        'message': '이메일 또는 비밀번호가 올바르지 않습니다.'}), 401

    return jsonify({
        'success': True,
        'message': '로그인 성공!',
        **issue_token_pair(row['id'], email, sub_type='facility'),
        'facility_account': {
            'id': row['id'],
            'company_name': row['company_name'],
            'email': email,
        },
    })


@facility_bp.route('/me', methods=['GET'])
def me():
    """토큰으로 현재 시설 계정 정보 조회."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'success': False, 'message': '인증 토큰이 없습니다.'}), 401
    try:
        payload = decode_access_token(auth.split(' ', 1)[1], expected_sub_type='facility')
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 401

    db  = get_db()
    row = db.execute(
        """SELECT id, company_name, email, business_no,
                  manager_name, manager_phone, manager_email
           FROM facility_accounts WHERE id=?""",
        (payload['user_id'],)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({'success': False, 'message': '계정을 찾을 수 없습니다.'}), 404
    return jsonify({'success': True, 'facility_account': dict(row)})
