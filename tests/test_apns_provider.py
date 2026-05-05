"""PR #50 — APNs Push Provider + Multi-platform 라우팅 통합 테스트."""
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# 임시 .p8 키 생성 (테스트용 — 실 APNs 호출 없음)
import models.age  # noqa: F401  (import path 확인)
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

_priv = ec.generate_private_key(ec.SECP256R1())
_pem = _priv.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode()

tmp_key = tempfile.NamedTemporaryFile(suffix='.p8', delete=False, mode='w')
tmp_key.write(_pem)
tmp_key.close()

os.environ['APNS_KEY_PATH'] = tmp_key.name
os.environ['APNS_KEY_ID'] = 'TESTKID000'
os.environ['APNS_TEAM_ID'] = 'TESTTEAM00'
os.environ['APNS_BUNDLE_ID'] = 'com.triggersoft.pathwave_app'
os.environ['APNS_USE_SANDBOX'] = 'true'

# stub 모드로 강제 (factory 만 검증, 실 발송 mocking)
os.environ['PUSH_PROVIDER'] = 'stub'

from models.push import (  # noqa: E402
    ApnsPushProvider, FcmPushProvider, MultiPlatformPushProvider,
    StubPushProvider, get_push_provider,
)


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


# ── [1] factory 분기 ─────────────────────────────────────────────────────
print('\n[1] PUSH_PROVIDER ENV 분기')
os.environ['PUSH_PROVIDER'] = 'stub'
_ok('stub', isinstance(get_push_provider(), StubPushProvider))

os.environ['PUSH_PROVIDER'] = 'apns'
p = get_push_provider()
_ok('apns → ApnsPushProvider', isinstance(p, ApnsPushProvider))

os.environ['PUSH_PROVIDER'] = 'multi'
m = get_push_provider()
_ok('multi → MultiPlatformPushProvider', isinstance(m, MultiPlatformPushProvider))

# 누락 ENV → RuntimeError
os.environ['APNS_KEY_PATH'] = ''
os.environ['PUSH_PROVIDER'] = 'apns'
err = None
try:
    get_push_provider()
except RuntimeError as e:
    err = str(e)
_ok('apns + 키 누락 → RuntimeError', err and 'APNS_' in err, err)
os.environ['APNS_KEY_PATH'] = tmp_key.name


# ── [2] APNs JWT 캐시 ────────────────────────────────────────────────────
print('\n[2] APNs JWT 생성 + 캐시 재사용')
provider = ApnsPushProvider(
    key_path=tmp_key.name,
    key_id='TESTKID000',
    team_id='TESTTEAM00',
    bundle_id='com.triggersoft.pathwave_app',
    use_sandbox=True,
)
tok1 = provider._get_jwt()
tok2 = provider._get_jwt()
_ok('JWT 생성 OK', isinstance(tok1, str) and len(tok1) > 50)
_ok('두 번째 호출 캐시 재사용 (동일 토큰)', tok1 == tok2)
# JWT 디코드해서 헤더 확인
import jwt as _jwt
decoded_h = _jwt.get_unverified_header(tok1)
_ok(f"alg=ES256 (got {decoded_h.get('alg')})", decoded_h.get('alg') == 'ES256')
_ok(f"kid=TESTKID000 (got {decoded_h.get('kid')})", decoded_h.get('kid') == 'TESTKID000')


# ── [3] APNs send — httpx 200 mock ────────────────────────────────────────
print('\n[3] APNs send 성공 (httpx 200 mock)')
mock_resp = MagicMock()
mock_resp.status_code = 200
mock_resp.headers = {'apns-id': 'mock-apns-id-123'}

with patch('httpx.Client') as mock_client_cls:
    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp
    mock_client_cls.return_value.__enter__.return_value = mock_client

    res = provider.send(
        token='abcdef0123456789' * 4,
        platform='apns',
        title='테스트',
        body='안녕',
        data={'announcement_id': '1'},
    )
    _ok(f'success=True (got {res.get("success")})', res.get('success') == True, res)
    _ok('apns_id 반환', res.get('apns_id') == 'mock-apns-id-123')

    # 호출 인자 검증
    call_args = mock_client.post.call_args
    url = call_args.args[0]
    headers = call_args.kwargs.get('headers', {})
    payload = call_args.kwargs.get('json', {})
    _ok('sandbox URL 사용', 'sandbox.push.apple.com' in url)
    _ok(f'apns-topic = bundle_id', headers.get('apns-topic') == 'com.triggersoft.pathwave_app')
    _ok('aps.alert.title 포함', payload['aps']['alert']['title'] == '테스트')
    _ok('extra data merge', payload.get('announcement_id') == '1')


# ── [4] APNs send — 4xx (BadDeviceToken) ───────────────────────────────────
print('\n[4] APNs send 실패 (400 BadDeviceToken mock)')
mock_resp_bad = MagicMock()
mock_resp_bad.status_code = 400
mock_resp_bad.json.return_value = {'reason': 'BadDeviceToken'}
mock_resp_bad.headers = {}

with patch('httpx.Client') as mock_client_cls:
    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp_bad
    mock_client_cls.return_value.__enter__.return_value = mock_client

    res = provider.send(
        token='invalid',
        platform='apns',
        title='t', body='b',
    )
    _ok('success=False', res.get('success') == False)
    _ok(f'reason=BadDeviceToken (got {res.get("error")})',
        res.get('error') == 'BadDeviceToken')
    _ok('status=400', res.get('status') == 400)


# ── [5] APNs send — fcm 토큰은 거부 ───────────────────────────────────────
print('\n[5] platform mismatch 거부')
res = provider.send(token='x', platform='fcm', title='t', body='b')
_ok('platform=fcm 시 unsupported_platform', res.get('error') == 'unsupported_platform:fcm')


# ── [6] MultiPlatformPushProvider — fcm + apns 라우팅 ──────────────────────
print('\n[6] Multi provider 분기 — fcm 미설정 + apns 설정 시')
os.environ.pop('FCM_SERVER_KEY', None)
multi = MultiPlatformPushProvider()
res = multi.send(token='xx', platform='fcm', title='t', body='b')
_ok('fcm 미설정 → fcm_not_configured', res.get('error') == 'fcm_not_configured')

# apns 는 설정 있음 → 호출 시도 (httpx mock 으로 200)
with patch('httpx.Client') as mock_client_cls:
    mock_client = MagicMock()
    ok_resp = MagicMock()
    ok_resp.status_code = 200
    ok_resp.headers = {'apns-id': 'multi-test'}
    mock_client.post.return_value = ok_resp
    mock_client_cls.return_value.__enter__.return_value = mock_client
    res = multi.send(token='token-ios', platform='apns', title='t', body='b')
    _ok(f'apns 라우팅 성공 (got {res.get("success")})', res.get('success') == True, res)


# ── [7] push_to_users — multi 라우팅 통합 (DB mock) ────────────────────────
print('\n[7] push_to_users 다중 토큰 라우팅')
os.environ['PUSH_PROVIDER'] = 'multi'
os.environ['FCM_SERVER_KEY'] = 'dummy-fcm-key'

# 인메모리 fake db
class _FakeRow(dict):
    def __getitem__(self, k):
        return super().__getitem__(k) if isinstance(k, str) else list(self.values())[k]
class _FakeDb:
    def __init__(self, rows):
        self._rows = rows
    def execute(self, sql, params):
        return self
    def fetchall(self):
        return self._rows

fake_db = _FakeDb([
    _FakeRow({'user_id': 1, 'token': 'fcm-tok-aaaa', 'platform': 'fcm'}),
    _FakeRow({'user_id': 1, 'token': 'apns-tok-bbbb', 'platform': 'apns'}),
    _FakeRow({'user_id': 2, 'token': 'apns-tok-cccc', 'platform': 'apns'}),
])

# 양쪽 다 200 mock
def _mock_urlopen(req, timeout=10):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=MagicMock(read=lambda: b'{"success":1,"results":[{"message_id":"m1"}]}'))
    cm.__exit__ = MagicMock(return_value=False)
    return cm

with patch('urllib.request.urlopen', _mock_urlopen), \
     patch('httpx.Client') as mock_httpx:
    ok_resp = MagicMock()
    ok_resp.status_code = 200
    ok_resp.headers = {'apns-id': 'm'}
    cli = MagicMock()
    cli.post.return_value = ok_resp
    mock_httpx.return_value.__enter__.return_value = cli

    from models.push import push_to_users   # noqa
    result = push_to_users(fake_db, [1, 2], title='t', body='b')
    _ok(f"sent=3 (fcm 1 + apns 2, got {result['sent']})", result['sent'] == 3, result)
    _ok('failed=0', result['failed'] == 0)
    _ok('provider=multi', result['provider'] == 'multi')


print('\n✅ 모든 시나리오 통과')

# Cleanup
sys.path  # avoid lint
os.unlink(tmp_key.name)
