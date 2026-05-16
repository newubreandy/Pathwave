"""Naver 로그인 토큰 교환 (Phase A 백엔드 골격).

운영
----
ENV NAVER_CLIENT_ID + NAVER_CLIENT_SECRET 가 설정되면 실 Naver ``/oauth2.0/token``
+ ``/v1/nid/me`` 호출. 없으면 console stub.

엔드포인트
---------
- POST /api/social/naver/exchange  body {authorization_code, state, redirect_uri?}
"""
from __future__ import annotations

import os
import json
import urllib.parse
import urllib.request

from flask import Blueprint, request, jsonify

from models.log import logger
from models.rate_limit import limiter

social_naver_bp = Blueprint('social_naver', __name__, url_prefix='/api/social/naver')


def _configured() -> bool:
    return (
        bool(os.environ.get('NAVER_CLIENT_ID', '').strip())
        and bool(os.environ.get('NAVER_CLIENT_SECRET', '').strip())
    )


@social_naver_bp.route('/exchange', methods=['POST'])
@limiter.limit('30 per minute')
def exchange():
    data = request.get_json(silent=True) or {}
    code = (data.get('authorization_code') or '').strip()
    state = (data.get('state') or '').strip()
    redirect_uri = (data.get('redirect_uri') or '').strip()
    if not code or not state:
        return jsonify({'success': False, 'message': 'authorization_code + state 가 필요합니다.'}), 400

    if not _configured():
        logger.info('[social/naver] stub exchange (NAVER_CLIENT_* 미설정). code=%s', code[:8])
        return jsonify({
            'success': True,
            'stub': True,
            'social_id': f'naver-stub-{abs(hash(code)) % 100000}',
            'email': f'naver-stub-{abs(hash(code)) % 100000}@naver.test',
            'nickname': 'Naver Tester',
            'provider': 'naver',
        })

    client_id     = os.environ['NAVER_CLIENT_ID'].strip()
    client_secret = os.environ['NAVER_CLIENT_SECRET'].strip()
    token_url = 'https://nid.naver.com/oauth2.0/token'
    body_params = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'state': state,
    }
    if redirect_uri:
        body_params['redirect_uri'] = redirect_uri

    try:
        req = urllib.request.Request(
            f'{token_url}?{urllib.parse.urlencode(body_params)}',
            method='GET',
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            tok = json.loads(resp.read().decode())
        access_token = tok.get('access_token')
        if not access_token:
            return jsonify({'success': False, 'message': 'Naver access_token 발급 실패'}), 502

        me_req = urllib.request.Request(
            'https://openapi.naver.com/v1/nid/me',
            headers={'Authorization': f'Bearer {access_token}'},
        )
        with urllib.request.urlopen(me_req, timeout=8) as resp:
            me = json.loads(resp.read().decode())
        response = me.get('response') or {}
        return jsonify({
            'success': True,
            'stub': False,
            'social_id': response.get('id'),
            'email': response.get('email'),
            'nickname': response.get('nickname') or response.get('name'),
            'provider': 'naver',
        })
    except Exception as e:
        logger.error('[social/naver] exchange 실패: %s', e, exc_info=True)
        return jsonify({'success': False, 'message': f'Naver 인증 실패: {e}'}), 502
