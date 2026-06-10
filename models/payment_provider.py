"""PG (Payment Gateway) provider abstraction.

환경변수
-------
- ``PG_PROVIDER`` = ``sim`` (기본, 시뮬) | ``toss``
- ``TOSS_SECRET_KEY`` (provider=toss 시 필요)
- ``TOSS_API_BASE`` (선택, 기본 https://api.tosspayments.com)

운영 전환:
    PG_PROVIDER=toss
    TOSS_SECRET_KEY=test_sk_xxxxx (또는 live_sk_xxxxx)

dev/test 에서는 sim 이 항상 성공을 반환하고 결과를 누적해 검증 가능.
"""
import base64
import json
import os
import secrets
import urllib.request
from typing import Protocol


class PaymentProvider(Protocol):
    name: str
    def charge(self, *, billing_key: str, total: int, order_no: str,
               customer_email: str | None = None) -> dict: ...
    def refund(self, *, payment_key: str, amount: int,
               reason: str | None = None) -> dict: ...


class SimPaymentProvider:
    """시뮬 — 항상 성공. 토큰은 sim-prefix."""
    name = 'sim'
    charge_log: list[dict] = []
    refund_log: list[dict] = []

    def charge(self, *, billing_key, total, order_no, customer_email=None):
        rec = {
            'billing_key': billing_key, 'total': total,
            'order_no': order_no, 'customer_email': customer_email,
        }
        SimPaymentProvider.charge_log.append(rec)
        return {
            'success': True,
            'payment_key': f'sim-{secrets.token_hex(8)}',
            'pg_tid':      f'sim-tid-{secrets.token_hex(8)}',
            'provider':    'sim',
        }

    def refund(self, *, payment_key, amount, reason=None):
        SimPaymentProvider.refund_log.append({
            'payment_key': payment_key, 'amount': amount, 'reason': reason,
        })
        return {'success': True, 'provider': 'sim'}


class TossPaymentsProvider:
    """Toss Payments — 빌링 자동결제 + 결제 취소.

    - 결제: ``POST /v1/billing/{billingKey}``
    - 환불: ``POST /v1/payments/{paymentKey}/cancel``
    - 인증: HTTP Basic ``base64(secretKey + ':')``

    문서: https://docs.tosspayments.com/reference
    """
    name = 'toss'

    def __init__(self, secret_key: str, api_base: str | None = None):
        if not secret_key:
            raise RuntimeError('TOSS_SECRET_KEY 가 필요합니다.')
        self._key = secret_key
        self._base = (api_base or 'https://api.tosspayments.com').rstrip('/')

    def _auth_header(self) -> str:
        token = base64.b64encode((self._key + ':').encode()).decode()
        return f'Basic {token}'

    def _post(self, path: str, payload: dict, *, timeout: int = 15) -> dict:
        req = urllib.request.Request(
            self._base + path,
            data=json.dumps(payload).encode(),
            headers={
                'Authorization': self._auth_header(),
                'Content-Type':  'application/json',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            try:
                body = json.loads(e.read())
            except Exception:
                body = {'message': str(e)}
            raise _TossError(body.get('code', f'HTTP_{e.code}'),
                             body.get('message', str(e)))
        except Exception as e:
            raise _TossError('TOSS_NETWORK', str(e))

    def charge(self, *, billing_key, total, order_no, customer_email=None):
        try:
            data = self._post(
                f'/v1/billing/{billing_key}',
                {
                    'amount':        total,
                    'orderId':       order_no,
                    'orderName':     f'PathWave 구독 {order_no}',
                    'customerEmail': customer_email,
                    'customerKey':   billing_key,   # 운영에선 사용자 단위로 분리 권장
                },
            )
            return {
                'success':     True,
                'payment_key': data.get('paymentKey'),
                'pg_tid':      data.get('transactionKey') or data.get('paymentKey'),
                'raw':         data,
                'provider':    'toss',
            }
        except _TossError as e:
            return {'success': False, 'error': e.code, 'message': e.message,
                    'provider': 'toss'}

    def refund(self, *, payment_key, amount, reason=None):
        try:
            data = self._post(
                f'/v1/payments/{payment_key}/cancel',
                {
                    'cancelReason': reason or 'admin_refund',
                    'cancelAmount': amount,
                },
            )
            return {'success': True, 'raw': data, 'provider': 'toss'}
        except _TossError as e:
            return {'success': False, 'error': e.code, 'message': e.message,
                    'provider': 'toss'}


class _TossError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f'{code}: {message}')


class ZeropayProvider:
    """제로페이 — 한국간편결제진흥원 (https://www.zeropay.or.kr).

    가맹점 신청 후 발급되는 MID + API Key 필요. 실 API 사양은 가맹점 협의 시
    별도 제공되므로, 키 미설정 시 stub 동작(개발/CI). 운영 활성은 환경변수
    ``ZEROPAY_MID`` + ``ZEROPAY_API_KEY`` 둘 다 주어졌을 때.

    사용자 결정(2026-06-05):
      - 사전 진행: 키만 넣으면 작동하도록 골격 + stub 우선.
      - 운영 활성 시: 제로페이 가맹점 사양 확정 후 charge/refund 의 실 호출 채움.
    """
    name = 'zeropay'

    def __init__(self, mid: str = '', api_key: str = '',
                 api_base: str | None = None):
        self._mid = mid
        self._key = api_key
        self._base = (api_base or 'https://api.zeropay.or.kr').rstrip('/')
        # 키 미설정 = stub (개발/CI/사전 진행). 키 들어오면 실 API.
        self._stub = not (mid and api_key)

    def charge(self, *, billing_key, total, order_no, customer_email=None):
        if self._stub:
            # 개발/CI — 항상 성공 처리해 흐름 검증 (운영 키 확정 전).
            return {
                'success': True,
                'payment_key': f'zp-stub-{secrets.token_hex(8)}',
                'pg_tid':      f'zp-tid-{secrets.token_hex(8)}',
                'provider':    'zeropay',
            }
        # 실 API 호출은 제로페이 가맹점 사양 확정 후 구현.
        # 현 단계는 명시적 실패 — FallbackPaymentProvider 가 토스로 폴백.
        return {
            'success': False,
            'error':   'ZEROPAY_NOT_IMPLEMENTED',
            'message': '제로페이 실 API 미구현 (가맹점 사양 확정 후 활성)',
            'provider': 'zeropay',
        }

    def refund(self, *, payment_key, amount, reason=None):
        if self._stub:
            return {'success': True, 'provider': 'zeropay'}
        return {
            'success': False,
            'error':   'ZEROPAY_NOT_IMPLEMENTED',
            'message': '제로페이 환불 실 API 미구현',
            'provider': 'zeropay',
        }


class FallbackPaymentProvider:
    """Primary 실패 시 Secondary 로 자동 폴백.

    사용자 결정(2026-06-05): 제로페이 1차 → 실패 시 토스 2차 자동 전환.
    매장 결제(Phase 2) · 구독료 결제(Phase 1) 모두 동일 패턴.

    환불은 결제 시 사용된 ``gateway`` 기준으로 분기해야 하므로 호출자가
    명시적으로 ``gateway=`` 인자를 전달한다 (``payments.gateway`` 컬럼 활용).
    """
    name = 'fallback'

    def __init__(self, primary, secondary):
        self.primary = primary
        self.secondary = secondary

    def charge(self, *, billing_key, total, order_no, customer_email=None):
        r = self.primary.charge(
            billing_key=billing_key, total=total,
            order_no=order_no, customer_email=customer_email,
        )
        if r.get('success'):
            return r
        # 폴백
        from models.log import logger
        logger.warning('[PG] %s 결제 실패 (%s) → %s 로 폴백',
                       self.primary.name,
                       r.get('error') or r.get('message') or '',
                       self.secondary.name)
        r2 = self.secondary.charge(
            billing_key=billing_key, total=total,
            order_no=order_no, customer_email=customer_email,
        )
        if r2.get('success'):
            r2 = dict(r2)
            r2['fallback_from'] = self.primary.name
        return r2

    def refund(self, *, payment_key, amount, reason=None, gateway=None):
        """호출자가 결제 시 사용된 gateway 를 ``payments.gateway`` 에서 읽어 전달."""
        target = self.primary if gateway == self.primary.name else self.secondary
        return target.refund(payment_key=payment_key, amount=amount, reason=reason)


# ── factory ──────────────────────────────────────────────────────────────────
def _build_single(name: str):
    """단일 PG 인스턴스 생성. PG_PROVIDER + FALLBACK_PRIMARY/SECONDARY 에서 사용."""
    if name == 'toss':
        return TossPaymentsProvider(
            secret_key=os.environ.get('TOSS_SECRET_KEY', ''),
            api_base=os.environ.get('TOSS_API_BASE') or None,
        )
    if name == 'zeropay':
        return ZeropayProvider(
            mid=os.environ.get('ZEROPAY_MID', ''),
            api_key=os.environ.get('ZEROPAY_API_KEY', ''),
            api_base=os.environ.get('ZEROPAY_API_BASE') or None,
        )
    return SimPaymentProvider()


def get_payment_provider() -> PaymentProvider:
    """ENV ``PG_PROVIDER`` 기반 단일/폴백 provider 반환.

    값:
      - ``sim``      : 시뮬 (개발/CI)
      - ``toss``     : 토스페이먼츠 단일
      - ``zeropay``  : 제로페이 단일 (키 미설정 시 stub)
      - ``fallback`` : FALLBACK_PRIMARY → 실패 시 FALLBACK_SECONDARY
    """
    name = os.environ.get('PG_PROVIDER', 'sim').lower()
    if name == 'fallback':
        primary   = os.environ.get('FALLBACK_PRIMARY',   'zeropay').lower()
        secondary = os.environ.get('FALLBACK_SECONDARY', 'toss').lower()
        return FallbackPaymentProvider(
            primary=_build_single(primary),
            secondary=_build_single(secondary),
        )
    return _build_single(name)
