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


def get_payment_provider() -> PaymentProvider:
    name = os.environ.get('PG_PROVIDER', 'sim').lower()
    if name == 'toss':
        return TossPaymentsProvider(
            secret_key=os.environ.get('TOSS_SECRET_KEY', ''),
            api_base=os.environ.get('TOSS_API_BASE') or None,
        )
    return SimPaymentProvider()
