"""NICE 본인인증 wrapper (Phase A 백엔드 골격).

운영
----
ENV NICE_CLIENT_ID + NICE_CLIENT_SECRET + NICE_RETURN_URL 이 설정되면 실 NICE
``CheckPlus`` 표준창 호출. 없으면 console stub — 가짜 본인인증 토큰을 반환해
회원가입 흐름은 그대로 검증.

PathWave 가 본인인증을 쓰는 시나리오:
- 미성년자 본인인증 (만 14세 이상)
- 자녀 초대 보호자 본인인증
- 결제 카드 명의자 확인

실 키 발급: NICE평가정보 (https://www.niceid.co.kr/) 사업자 가입 → CheckPlus
계약. mock 발급은 PathWave 법인 등록 후 가능.
"""
from __future__ import annotations

import os
import uuid
import hashlib
import datetime as _dt

from models.log import logger


def _configured() -> bool:
    return all(os.environ.get(k, '').strip() for k in (
        'NICE_CLIENT_ID', 'NICE_CLIENT_SECRET', 'NICE_RETURN_URL'
    ))


def request_token(*, purpose: str = 'register') -> dict:
    """본인인증 요청 토큰 생성.

    응답: {success, stub, request_no, redirect_url}
    클라이언트(web/mobile)는 redirect_url 을 띄워 사용자가 NICE 표준창에서
    본인인증 완료하면 NICE 가 NICE_RETURN_URL 로 콜백 → verify_callback() 처리.
    """
    request_no = uuid.uuid4().hex[:20]
    if not _configured():
        logger.info('[nice] stub request_token (NICE_CLIENT_* 미설정). purpose=%s', purpose)
        return {
            'success': True,
            'stub': True,
            'request_no': request_no,
            # stub 단계에서는 가짜 redirect_url. mobile/web 은 stub 응답을 받고
            # 가짜 사용자 정보로 회원가입 흐름을 검증.
            'redirect_url': f'about:blank#nice-stub-{request_no}',
        }
    # 실 NICE 표준창 URL 빌딩은 실 키 받은 뒤 구현. 현재는 placeholder.
    return {
        'success': True,
        'stub': False,
        'request_no': request_no,
        'redirect_url': os.environ.get('NICE_RETURN_URL', '').strip(),
    }


def verify_callback(payload: dict) -> dict:
    """NICE 콜백 처리 — 응답 토큰 검증 + 본인 정보 추출.

    실 NICE 응답은 암호화된 EncodeData 를 복호화해야 함. 키 받기 전에는 stub 으로
    가짜 본인 정보 반환.

    응답: {success, stub, name?, birthdate?, gender?, phone?, ci?, di?, age?}
    """
    if not _configured():
        logger.info('[nice] stub verify_callback')
        return {
            'success': True,
            'stub': True,
            'name': '홍길동',
            'birthdate': '1995-03-15',
            'gender': 'M',
            'phone': '01012345678',
            # CI/DI 는 NICE 가 생성하는 본인 고유 ID — stub 은 hash 흉내.
            'ci': hashlib.sha256(b'stub-ci').hexdigest()[:88],
            'di': hashlib.sha256(b'stub-di').hexdigest()[:64],
            'age': _dt.datetime.now().year - 1995,
        }
    # 실 NICE 응답 복호화 로직은 키 받은 뒤 구현. (NICE 가 제공하는 모듈 또는
    # 자체 AES-128 복호화 — 계약 시 받는 SDK 문서대로.)
    return {
        'success': False,
        'stub': False,
        'error': 'NICE 실 응답 복호화 로직 미구현 (실 키 받은 뒤 추가)',
    }
