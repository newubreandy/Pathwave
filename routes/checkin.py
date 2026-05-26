"""P22-a (2026-05-26): 회원 QR 체크인.

phase1 plan §P22 의 일부 — 점주가 손님을 식별·조회·적립할 다리.
손님이 마이페이지 회원 QR 표시 → 점주가 provider-web 으로 스캔 → 백엔드
검증 → 스탬프 적립 / 쿠폰 사용 (P22-b 이후 별도 PR).

엔드포인트
---------
- POST /api/checkin/member-qr  (사용자) — 본인 회원 QR 토큰 발급 (60초)
- POST /api/checkin/verify     (점주)   — 토큰 검증 + user 기본정보 반환

토큰 구조 (JWT)
---------------
- kind='member_qr', user_id, sub_type='user', exp (60초)
- access_token 과 별개의 kind — replay 방지
- HS256, 기존 SECRET_KEY 재사용

수동 새로고침 정책 (사용자 결정 2026-05-21):
- 결제가 아니므로 단기 자동회전 v1 미적용.
- 사용자가 직접 새로고침 (POST 다시 호출).
- 토큰 발급 시점에 이전 토큰은 60초 후 자연 만료.
- 결제 연계 (Phase 2+) 시 단기 자동회전으로 강화 가능 (구조 유지).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from flask import Blueprint, jsonify, request

from models.database import get_db
from routes.auth import SECRET_KEY, decode_access_token

checkin_bp = Blueprint('checkin', __name__, url_prefix='/api/checkin')

MEMBER_QR_TTL_SEC = 60   # 회원 QR 유효 시간


def _bearer_token() -> str | None:
    h = request.headers.get('Authorization', '')
    if not h.lower().startswith('bearer '):
        return None
    return h.split(None, 1)[1].strip()


# ─── 사용자: 회원 QR 토큰 발급 ────────────────────────────────────────────
@checkin_bp.route('/member-qr', methods=['POST'])
def issue_member_qr():
    """본인 user 의 회원 QR 토큰 발급. 60초 유효.

    Bearer access 토큰 필수.
    응답: {token, expires_in}
    """
    access = _bearer_token()
    if not access:
        return jsonify({'success': False,
                        'message': '로그인이 필요합니다.'}), 401
    try:
        payload = decode_access_token(access, expected_sub_type='user')
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 401

    user_id = payload['user_id']
    exp = datetime.now(timezone.utc) + timedelta(seconds=MEMBER_QR_TTL_SEC)
    qr_payload = {
        'kind':     'member_qr',
        'user_id':  user_id,
        'sub_type': 'user',
        'exp':      int(exp.timestamp()),
    }
    qr_token = jwt.encode(qr_payload, SECRET_KEY, algorithm='HS256')
    return jsonify({
        'success':    True,
        'token':      qr_token,
        'expires_in': MEMBER_QR_TTL_SEC,
    })


# ─── 점주: 회원 QR 토큰 검증 ──────────────────────────────────────────────
@checkin_bp.route('/verify', methods=['POST'])
def verify_member_qr():
    """점주가 스캔한 회원 QR 토큰 검증. user 기본정보 반환.

    Bearer access 토큰 필수 (facility_owner / staff).
    body: {token: '...'}
    응답: {user_id, email, nickname (있으면), is_minor}
    """
    actor_token = _bearer_token()
    if not actor_token:
        return jsonify({'success': False,
                        'message': '로그인이 필요합니다.'}), 401
    try:
        actor = decode_access_token(actor_token, expected_sub_type='facility')
    except ValueError:
        # staff 도 가능
        try:
            actor = decode_access_token(actor_token, expected_sub_type='staff')
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 401

    data = request.get_json(silent=True) or {}
    member_token = (data.get('token') or '').strip()
    if not member_token:
        return jsonify({'success': False,
                        'message': 'token 이 필요합니다.'}), 400

    # 회원 QR 토큰 디코드
    try:
        payload = jwt.decode(member_token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False,
                        'message': '회원 QR 이 만료되었습니다. 손님께 새로고침 요청해 주세요.'}), 400
    except jwt.InvalidTokenError:
        return jsonify({'success': False,
                        'message': '유효하지 않은 회원 QR 입니다.'}), 400

    if payload.get('kind') != 'member_qr':
        return jsonify({'success': False,
                        'message': '회원 QR 토큰이 아닙니다.'}), 400

    user_id = payload.get('user_id')
    if not user_id:
        return jsonify({'success': False,
                        'message': '회원 ID 가 없습니다.'}), 400

    # user 기본정보 조회
    db = get_db()
    try:
        row = db.execute(
            "SELECT id, email, birth_year, status FROM users WHERE id=?",
            (user_id,),
        ).fetchone()
        if not row:
            return jsonify({'success': False,
                            'message': '회원이 존재하지 않습니다.'}), 404
        if (row['status'] or 'active') != 'active':
            return jsonify({'success': False,
                            'message': '비활성 회원입니다.'}), 400

        # 만 18세 이하 여부 (청소년 보호)
        is_minor = False
        try:
            cur_year = datetime.now().year
            byear = int(row['birth_year']) if row['birth_year'] else None
            if byear:
                age = cur_year - byear
                is_minor = age < 19
        except (TypeError, ValueError):
            pass

        return jsonify({
            'success':  True,
            'user_id':  row['id'],
            'email':    row['email'],
            'is_minor': is_minor,
            # actor 메타 (점주 측에서 행동 결정용)
            'actor': {
                'sub_type':    actor.get('sub_type'),
                'facility_id': actor.get('facility_id'),
            },
        })
    finally:
        db.close()
