"""Kakao 로그인 토큰 교환 (Phase A 백엔드 골격).

운영
----
ENV KAKAO_REST_API_KEY 와 KAKAO_CLIENT_SECRET (선택) 가 설정되면 실 Kakao
``/oauth/token`` + ``/v2/user/me`` 호출. 없으면 console stub — 입력 받은 가짜
authorization_code 로 가짜 사용자 정보 반환하여 mobile/web 통합 흐름은 그대로 검증.

엔드포인트
---------
- POST /api/social/kakao/exchange  body {authorization_code, redirect_uri?}

mobile (kakao_flutter_sdk_user) 또는 web 이 authorization_code 를 받아 이 백엔드에
넘기면 백엔드가 access_token 교환 + 사용자 프로필 조회 + PathWave 사용자
회원가입/로그인 매핑까지 처리한다 (실 구현은 keys 받은 뒤).
"""
from __future__ import annotations

import os
import json
import urllib.parse
import urllib.request

from flask import Blueprint, request, jsonify

from models.log import logger
from models.rate_limit import limiter

social_kakao_bp = Blueprint('social_kakao', __name__, url_prefix='/api/social/kakao')


def _configured() -> bool:
    return bool(os.environ.get('KAKAO_REST_API_KEY', '').strip())


@social_kakao_bp.route('/exchange', methods=['POST'])
@limiter.limit('30 per minute')
def exchange():
    data = request.get_json(silent=True) or {}
    code = (data.get('authorization_code') or '').strip()
    redirect_uri = (data.get('redirect_uri') or '').strip()
    if not code:
        return jsonify({'success': False, 'message': 'authorization_code 가 필요합니다.'}), 400

    if not _configured():
        # ── Stub: 키 없으면 console mock — UI/통합 흐름 검증용 ─────────────
        logger.info('[social/kakao] stub exchange (KAKAO_REST_API_KEY 미설정). code=%s', code[:8])
        return jsonify({
            'success': True,
            'stub': True,
            'social_id': f'kakao-stub-{abs(hash(code)) % 100000}',
            'email': f'kakao-stub-{abs(hash(code)) % 100000}@kakao.test',
            'nickname': 'Kakao Tester',
            'provider': 'kakao',
        })

    # ── 실 Kakao API ──────────────────────────────────────────────────────
    rest_api_key = os.environ['KAKAO_REST_API_KEY'].strip()
    secret = os.environ.get('KAKAO_CLIENT_SECRET', '').strip()
    token_url = 'https://kauth.kakao.com/oauth/token'
    body_params = {
        'grant_type': 'authorization_code',
        'client_id': rest_api_key,
        'code': code,
    }
    if redirect_uri:
        body_params['redirect_uri'] = redirect_uri
    if secret:
        body_params['client_secret'] = secret

    try:
        req = urllib.request.Request(
            token_url,
            data=urllib.parse.urlencode(body_params).encode(),
            headers={'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            tok = json.loads(resp.read().decode())
        access_token = tok.get('access_token')
        if not access_token:
            return jsonify({'success': False, 'message': 'Kakao access_token 발급 실패'}), 502

        # 사용자 정보 조회
        me_req = urllib.request.Request(
            'https://kapi.kakao.com/v2/user/me',
            headers={'Authorization': f'Bearer {access_token}'},
        )
        with urllib.request.urlopen(me_req, timeout=8) as resp:
            me = json.loads(resp.read().decode())
        kakao_id = me.get('id')
        account = me.get('kakao_account') or {}
        email = account.get('email')
        nickname = (account.get('profile') or {}).get('nickname')
        return jsonify({
            'success': True,
            'stub': False,
            'social_id': str(kakao_id) if kakao_id else None,
            'email': email,
            'nickname': nickname,
            'provider': 'kakao',
        })
    except Exception as e:
        logger.error('[social/kakao] exchange 실패: %s', e, exc_info=True)
        return jsonify({'success': False, 'message': f'Kakao 인증 실패: {e}'}), 502
