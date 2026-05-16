"""SolAPI (CoolSMS) SMS / 카카오 알림톡 발송 wrapper (Phase A 백엔드 골격).

운영
----
ENV SOLAPI_API_KEY + SOLAPI_API_SECRET + SOLAPI_SENDER_PHONE 이 설정되면 실 발송.
없으면 console stub — 발송 내용을 로그에 출력해 통합 흐름 검증.

PathWave 가 사용할 시나리오:
- 비콘 인증코드 SMS (회원가입)
- 미성년 자녀 가입 초대 SMS
- 스탬프/쿠폰 카카오 알림톡 (Bizfee 등록 후)
- 결제 영수증/환불 알림 SMS

PathWave 가 실 키 받는 위치: SolAPI 콘솔 (https://console.solapi.com/) 가입 후
API Key + Secret + 발신번호 등록.
"""
from __future__ import annotations

import os
import hmac
import hashlib
import json
import uuid
import datetime as _dt
import urllib.request
import urllib.parse

from models.log import logger


def _configured() -> bool:
    return all(os.environ.get(k, '').strip() for k in (
        'SOLAPI_API_KEY', 'SOLAPI_API_SECRET', 'SOLAPI_SENDER_PHONE'
    ))


def _signed_headers() -> dict:
    """SolAPI HMAC 시그니처 — 실 키 있을 때만 호출."""
    api_key = os.environ['SOLAPI_API_KEY'].strip()
    api_secret = os.environ['SOLAPI_API_SECRET'].strip()
    date = _dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    salt = uuid.uuid4().hex
    msg = (date + salt).encode()
    signature = hmac.new(api_secret.encode(), msg, hashlib.sha256).hexdigest()
    return {
        'Authorization': f'HMAC-SHA256 apiKey={api_key}, date={date}, salt={salt}, signature={signature}',
        'Content-Type': 'application/json; charset=utf-8',
    }


def send_sms(to_phone: str, body: str, *, sender: str | None = None) -> dict:
    """SMS 발송. (실 키 없으면 console stub).

    return: {success, stub, message_id?}
    """
    if not _configured():
        logger.info('[solapi] stub SMS — to=%s body=%s', to_phone, body[:80])
        return {'success': True, 'stub': True, 'message_id': f'sim-{uuid.uuid4().hex[:8]}'}

    sender = sender or os.environ['SOLAPI_SENDER_PHONE'].strip()
    payload = {
        'message': {
            'to': to_phone,
            'from': sender,
            'text': body,
        }
    }
    try:
        req = urllib.request.Request(
            'https://api.solapi.com/messages/v4/send',
            data=json.dumps(payload).encode(),
            headers=_signed_headers(),
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        return {
            'success': True,
            'stub': False,
            'message_id': data.get('messageId') or data.get('groupId'),
        }
    except Exception as e:
        logger.error('[solapi] SMS 발송 실패: %s', e, exc_info=True)
        return {'success': False, 'stub': False, 'error': str(e)}


def send_alimtalk(to_phone: str, template_id: str, variables: dict) -> dict:
    """카카오 알림톡 발송. 발신 프로필 + 템플릿 ID 가 SolAPI 콘솔에 등록되어
    있어야 한다 (PathWave 입주 후 별도 절차).

    실 키 없으면 console stub.
    """
    if not _configured():
        logger.info('[solapi] stub Alimtalk — to=%s template=%s vars=%s',
                    to_phone, template_id, variables)
        return {'success': True, 'stub': True, 'message_id': f'sim-{uuid.uuid4().hex[:8]}'}

    pfId = os.environ.get('SOLAPI_KAKAO_PFID', '').strip()
    if not pfId:
        return {'success': False, 'stub': False,
                'error': 'SOLAPI_KAKAO_PFID 미설정 (카카오 발신 프로필 ID)'}

    sender = os.environ['SOLAPI_SENDER_PHONE'].strip()
    payload = {
        'message': {
            'to': to_phone,
            'from': sender,
            'kakaoOptions': {
                'pfId': pfId,
                'templateId': template_id,
                'variables': variables,
            },
        }
    }
    try:
        req = urllib.request.Request(
            'https://api.solapi.com/messages/v4/send',
            data=json.dumps(payload).encode(),
            headers=_signed_headers(),
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        return {
            'success': True,
            'stub': False,
            'message_id': data.get('messageId') or data.get('groupId'),
        }
    except Exception as e:
        logger.error('[solapi] Alimtalk 발송 실패: %s', e, exc_info=True)
        return {'success': False, 'stub': False, 'error': str(e)}
