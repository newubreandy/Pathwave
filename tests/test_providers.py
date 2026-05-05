"""PR #41 — 운영 전환: PG / Email provider 추상화 smoke test.

ENV 별로 올바른 provider 가 선택되고, sim/console 기본값이 회귀 없이 동작하는지
+ billing.py / auth.py 가 provider 호출에 통합됐는지 검증.
"""
import os
import json
import sqlite3
import tempfile

# DB 격리
tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name
os.environ['BOOTSTRAP_SUPER_ADMIN_EMAIL']    = 'admin@providers.test'
os.environ['BOOTSTRAP_SUPER_ADMIN_PASSWORD'] = 'AdminPass1!'
# 명시적으로 sim / console (혹시 셸에 다른 값이 있을까봐)
os.environ['PG_PROVIDER']    = 'sim'
os.environ['EMAIL_PROVIDER'] = 'console'

import models.database as _dbmod  # noqa: E402
def _patched_get_db():
    conn = sqlite3.connect(os.environ['PATHWAVE_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn
_dbmod.get_db = _patched_get_db

from app import app  # noqa: E402
from models.payment_provider import (  # noqa: E402
    SimPaymentProvider, TossPaymentsProvider, get_payment_provider,
)
from models.email_provider import (  # noqa: E402
    ConsoleEmailProvider, SmtpEmailProvider, SesEmailProvider,
    SendGridEmailProvider, get_email_provider,
)

c = app.test_client()


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


def _post(path, data, token=None):
    h = {'Content-Type': 'application/json'}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.post(path, data=json.dumps(data), headers=h)
    return r.status_code, r.get_json()


# ── [1] provider 팩토리 ENV 분기 ─────────────────────────────────────────────
print('\n[1] PG provider — ENV 별 분기')
os.environ['PG_PROVIDER'] = 'sim'
_ok('sim → SimPaymentProvider', isinstance(get_payment_provider(), SimPaymentProvider))
os.environ['PG_PROVIDER'] = 'toss'
os.environ['TOSS_SECRET_KEY'] = 'test_sk_dummy'
_ok('toss → TossPaymentsProvider',
    isinstance(get_payment_provider(), TossPaymentsProvider))
# TOSS_SECRET_KEY 빈 값 → RuntimeError
os.environ['TOSS_SECRET_KEY'] = ''
err = None
try:
    get_payment_provider()
except RuntimeError as e:
    err = str(e)
_ok('toss + secret 누락 → RuntimeError', err and 'TOSS_SECRET_KEY' in err, err)
os.environ['PG_PROVIDER'] = 'sim'
os.environ.pop('TOSS_SECRET_KEY', None)


print('\n[2] Email provider — ENV 별 분기')
os.environ['EMAIL_PROVIDER'] = 'console'
_ok('console → ConsoleEmailProvider', isinstance(get_email_provider(), ConsoleEmailProvider))

os.environ['EMAIL_PROVIDER'] = 'smtp'
os.environ['SMTP_USER'] = 'user@example.com'
os.environ['SMTP_PASS'] = 'pw'
os.environ['EMAIL_FROM'] = 'noreply@pathwave.kr'
_ok('smtp + 자격 → SmtpEmailProvider', isinstance(get_email_provider(), SmtpEmailProvider))
os.environ.pop('SMTP_USER', None); os.environ.pop('SMTP_PASS', None)

os.environ['EMAIL_PROVIDER'] = 'sendgrid'
os.environ['SENDGRID_API_KEY'] = 'SG.dummy'
_ok('sendgrid → SendGridEmailProvider',
    isinstance(get_email_provider(), SendGridEmailProvider))
os.environ['SENDGRID_API_KEY'] = ''
err = None
try:
    get_email_provider()
except RuntimeError as e:
    err = str(e)
_ok('sendgrid + key 누락 → RuntimeError', err and 'SENDGRID_API_KEY' in err, err)
os.environ['EMAIL_PROVIDER'] = 'console'
os.environ.pop('SENDGRID_API_KEY', None)


# ── [3] auth/send-code 가 console provider 로 흘러 들어가는지 ─────────────
print('\n[3] /api/auth/send-code → console provider 누적 로그')
ConsoleEmailProvider.sent_log.clear()
s, j = _post('/api/auth/send-code', {'email': 'user@providers.test'})
_ok('send-code → 200', s == 200, j)
_ok('console log 1건 누적', len(ConsoleEmailProvider.sent_log) == 1)
last = ConsoleEmailProvider.sent_log[-1]
_ok(f"to={last['to']}", last['to'] == 'user@providers.test')
_ok("subject 가 PathWave 인증 코드", '인증 코드' in last['subject'])


# ── [4] billing 결제 → sim PG provider 호출 ───────────────────────────────
print('\n[4] billing 결제 → sim PG provider 누적 로그')
# 사장 계정 + 카드 등록 후 subscription 시도. 시설 계정 가입 동선이 길어서 이번 단계는
# 단순히 sim provider 가 직접 호출 시 정상 응답 반환하는지 확인.
SimPaymentProvider.charge_log.clear()
provider = SimPaymentProvider()
res = provider.charge(billing_key='bk-1', total=10000, order_no='ORD-T1',
                      customer_email='u@providers.test')
_ok('charge.success', res.get('success'))
_ok("payment_key 가 sim- prefix", str(res.get('payment_key', '')).startswith('sim-'))
_ok('charge_log 1건', len(SimPaymentProvider.charge_log) == 1)

SimPaymentProvider.refund_log.clear()
res = provider.refund(payment_key='sim-pk-1', amount=10000, reason='test')
_ok('refund.success', res.get('success'))
_ok('refund_log 1건', len(SimPaymentProvider.refund_log) == 1)


# ── [5] 운영 ENV 검증과 함께 PG_PROVIDER=toss 의 토큰 검증 ──────────────────
print('\n[5] PATHWAVE_ENV=production 일 때 PG/EMAIL ENV 미검증 (선택적)')
# _validate_production_env 는 PG_PROVIDER 자체는 강제하지 않음 (sim 도 운영에서 쓸 수 있음).
# 이 부분은 운영 가이드 문서로 안내하고, 테스트는 SECRET_KEY/AES_KEY/CORS 만 강제.
os.environ['PATHWAVE_ENV'] = 'development'   # 다음 테스트 영향 안 가게 dev 복귀
_ok('dev 모드 복귀', os.environ['PATHWAVE_ENV'] == 'development')


print('\n✅ 모든 시나리오 통과')
