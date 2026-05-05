"""휴대폰 인증 (Phone Verification) — PR #37.

회원가입·사장 가입 시 휴대폰 본인 확인을 위한 SMS 코드 발송/검증.

엔드포인트
---------
- POST /api/phone/send-code      — 인증 코드 발송 (Stub 또는 실 SMS)
- POST /api/phone/verify-code    — 코드 검증 → 1회용 token 발급

SMS Provider
-----------
환경변수 ``SMS_PROVIDER``로 선택:
  - ``stub`` (기본): 콘솔에 코드 출력, 비용 0, 개발/테스트 용
  - ``aligo`` 등: 추후 ``_send_via_real()`` 구현 시 활성화

검증 후 발급되는 ``token``은 ``register`` 등 이후 단계에서 함께 제출하여
사장 가입 흐름의 휴대폰 본인 확인 증빙으로 사용된다.
"""
import os
import re
import secrets
import string
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify

from models.database import get_db

phone_bp = Blueprint('phone', __name__, url_prefix='/api/phone')

CODE_TTL_MIN = int(os.environ.get('PHONE_CODE_TTL_MIN', '5'))
TOKEN_TTL_MIN = int(os.environ.get('PHONE_TOKEN_TTL_MIN', '30'))
SMS_PROVIDER = os.environ.get('SMS_PROVIDER', 'stub').strip().lower()

_PHONE_RE = re.compile(r'^01[016789]-?\d{3,4}-?\d{4}$')


# ── 유틸 ──────────────────────────────────────────────────────────────────────
def _normalize_phone(s: str) -> str:
    """공백·하이픈 제거 후 010-XXXX-XXXX 형식으로."""
    s = re.sub(r'[\s\-]', '', s or '')
    if len(s) == 11 and s.startswith('01'):
        return f'{s[:3]}-{s[3:7]}-{s[7:]}'
    if len(s) == 10 and s.startswith('01'):
        return f'{s[:3]}-{s[3:6]}-{s[6:]}'
    return s


def _gen_code() -> str:
    return ''.join(secrets.choice(string.digits) for _ in range(6))


def _gen_token() -> str:
    return secrets.token_urlsafe(24)


def _send_via_stub(phone: str, code: str) -> bool:
    print('=' * 50)
    print(f'[SMS:stub] 휴대폰 인증 코드')
    print(f'  수신: {phone}')
    print(f'  코드: {code}')
    print('=' * 50)
    return True


def _send_via_real(phone: str, code: str) -> bool:
    """실 SMS 연동 hook. 추후 통신사 API(Aligo, NHN SENS 등) 호출."""
    raise NotImplementedError('Real SMS provider not configured. Set SMS_PROVIDER=stub for dev.')


def _send_sms(phone: str, code: str) -> bool:
    if SMS_PROVIDER == 'stub':
        return _send_via_stub(phone, code)
    return _send_via_real(phone, code)


# ── 엔드포인트 ───────────────────────────────────────────────────────────────
@phone_bp.route('/send-code', methods=['POST'])
def send_code():
    """휴대폰 인증 코드 발송.

    body: {phone: '010-...', purpose?: 'register'|'login'|'reset'}
    """
    data    = request.get_json(silent=True) or {}
    phone   = _normalize_phone(data.get('phone') or '')
    purpose = (data.get('purpose') or 'register').strip().lower()

    if not _PHONE_RE.match(phone):
        return jsonify({'success': False,
                        'message': '올바른 휴대폰 번호 형식이 아닙니다 (예: 010-1234-5678).'}), 400

    code = _gen_code()
    expires = (datetime.utcnow() + timedelta(minutes=CODE_TTL_MIN)).isoformat()

    db = get_db()
    # 기존 미사용 코드는 폐기
    db.execute("UPDATE phone_verifications SET used=1 WHERE phone=? AND used=0", (phone,))
    db.execute(
        """INSERT INTO phone_verifications (phone, code, purpose, expires_at)
           VALUES (?,?,?,?)""",
        (phone, code, purpose, expires)
    )
    db.commit(); db.close()

    if not _send_sms(phone, code):
        return jsonify({'success': False, 'message': 'SMS 발송에 실패했습니다.'}), 500

    return jsonify({
        'success': True,
        'message': '인증 코드를 발송했습니다.',
        'expires_in_seconds': CODE_TTL_MIN * 60,
        'provider': SMS_PROVIDER,
    })


@phone_bp.route('/verify-code', methods=['POST'])
def verify_code():
    """인증 코드 검증 + 1회용 token 발급."""
    data  = request.get_json(silent=True) or {}
    phone = _normalize_phone(data.get('phone') or '')
    code  = (data.get('code') or '').strip()

    if not phone or not code:
        return jsonify({'success': False, 'message': '휴대폰 번호와 코드를 입력해 주세요.'}), 400

    db  = get_db()
    row = db.execute(
        """SELECT id, expires_at FROM phone_verifications
           WHERE phone=? AND code=? AND used=0
           ORDER BY id DESC LIMIT 1""",
        (phone, code)
    ).fetchone()

    if not row:
        db.close()
        return jsonify({'success': False, 'message': '인증 코드가 올바르지 않습니다.'}), 400
    if datetime.utcnow() > datetime.fromisoformat(row['expires_at']):
        db.close()
        return jsonify({'success': False, 'message': '인증 코드가 만료되었습니다.'}), 400

    token = _gen_token()
    token_expires = (datetime.utcnow() + timedelta(minutes=TOKEN_TTL_MIN)).isoformat()

    db.execute(
        """UPDATE phone_verifications
           SET verified=1, verified_at=datetime('now'), token=?, expires_at=?
           WHERE id=?""",
        (token, token_expires, row['id'])
    )
    db.commit(); db.close()

    return jsonify({
        'success': True,
        'message': '휴대폰 인증이 완료되었습니다.',
        'token': token,
        'token_expires_in_seconds': TOKEN_TTL_MIN * 60,
    })


# ── 헬퍼 (다른 모듈에서 token 검증) ───────────────────────────────────────────
def consume_phone_token(db, phone: str, token: str) -> bool:
    """phone+token 매칭이 유효하고 미사용·미만료면 used=1로 마킹하고 True.

    회원가입 등 후속 단계에서 본인 확인 증빙으로 사용.
    """
    if not phone or not token:
        return False
    phone = _normalize_phone(phone)
    row = db.execute(
        """SELECT id, expires_at, used, verified
             FROM phone_verifications
            WHERE phone=? AND token=?
            LIMIT 1""",
        (phone, token)
    ).fetchone()
    if not row or row['used'] or not row['verified']:
        return False
    if datetime.utcnow() > datetime.fromisoformat(row['expires_at']):
        return False
    db.execute("UPDATE phone_verifications SET used=1 WHERE id=?", (row['id'],))
    return True
