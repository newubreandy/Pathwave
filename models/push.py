"""푸시 발송 — 플러그블 provider + 사용자 토큰 조회 헬퍼.

플랫폼 별 provider:
  - FCM (Android, iOS via Firebase 통합) — `FcmPushProvider`
  - APNs (iOS native, PR #50) — `ApnsPushProvider`
  - Stub (개발/테스트)

push_tokens.platform 값에 따라 자동으로 적절한 provider 호출.

환경변수
-------
- ``PUSH_PROVIDER`` = ``stub`` (기본) | ``fcm`` | ``apns`` | ``multi``
  - ``multi``: platform 별 자동 분기 (apns/fcm 둘 다 활성)
- FCM:  ``FCM_SERVER_KEY``
- APNs: ``APNS_KEY_PATH`` (.p8) / ``APNS_KEY_ID`` / ``APNS_TEAM_ID`` /
        ``APNS_BUNDLE_ID`` / ``APNS_USE_SANDBOX`` (기본: false)

운영 전환 (다중 플랫폼):
    PUSH_PROVIDER=multi
    FCM_SERVER_KEY=...
    APNS_KEY_PATH=/etc/secrets/AuthKey_XYZ.p8
    APNS_KEY_ID=ABCDE12345
    APNS_TEAM_ID=ABCDE67890
    APNS_BUNDLE_ID=com.triggersoft.pathwave_app

dev/test 에서는 stub 이 콘솔에 출력하고 결과를 리스트로 누적.
"""
import json
import os
import time
import urllib.request
from datetime import datetime
from typing import Protocol


class PushProvider(Protocol):
    name: str
    def send(self, *, token: str, platform: str, title: str, body: str,
             data: dict | None = None) -> dict: ...


_STUB_LOG_PATH = os.environ.get('PUSH_STUB_LOG', '/tmp/pathwave_push_stub.log')


# ── Stub ──────────────────────────────────────────────────────────────────────

class StubPushProvider:
    name = 'stub'
    sent_log: list[dict] = []

    def send(self, *, token, platform, title, body, data=None):
        rec = {'token': token, 'platform': platform,
               'title': title, 'body': body, 'data': data or {}}
        StubPushProvider.sent_log.append(rec)
        try:
            with open(_STUB_LOG_PATH, 'a') as f:
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        except Exception:
            pass
        from models.log import logger as _lg
        _lg.info('[push:stub] %s %s... title=%r', platform, token[:8], title)
        return {'success': True, 'message_id': f'stub-{len(StubPushProvider.sent_log)}'}


# ── FCM ───────────────────────────────────────────────────────────────────────

class FcmPushProvider:
    """FCM HTTP v1 (legacy /send) — 단순 구현. 실 서비스에선 v1 + OAuth2 권장."""
    name = 'fcm'
    _ENDPOINT = 'https://fcm.googleapis.com/fcm/send'

    def __init__(self, server_key: str):
        if not server_key:
            raise RuntimeError('FCM_SERVER_KEY가 필요합니다.')
        self._key = server_key

    def send(self, *, token, platform, title, body, data=None):
        if platform != 'fcm':
            return {'success': False, 'error': f'unsupported_platform:{platform}'}
        payload = {'to': token,
                   'notification': {'title': title, 'body': body},
                   'data': data or {}}
        req = urllib.request.Request(
            self._ENDPOINT,
            data=json.dumps(payload).encode(),
            headers={'Authorization': f'key={self._key}',
                     'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return {'success': True, 'response': json.loads(resp.read())}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ── APNs (PR #50) ─────────────────────────────────────────────────────────────

class ApnsPushProvider:
    """APNs HTTP/2 + JWT (token-based authentication, p8 키).

    Apple Developer Program 에서 .p8 키 발급 필요:
      Certificates → Keys → Apple Push Notifications service (APNs)
      → 발급된 Key ID + Team ID + .p8 파일 경로 + Bundle ID

    문서: https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns
    """
    name = 'apns'
    _PROD_HOST = 'https://api.push.apple.com'
    _SANDBOX_HOST = 'https://api.sandbox.push.apple.com'
    _JWT_TTL_S = 3000  # 50분 (Apple 권장: 1시간 미만 갱신)

    def __init__(self, *, key_path: str, key_id: str, team_id: str,
                 bundle_id: str, use_sandbox: bool = False):
        if not all([key_path, key_id, team_id, bundle_id]):
            raise RuntimeError(
                'APNS_KEY_PATH / APNS_KEY_ID / APNS_TEAM_ID / APNS_BUNDLE_ID 가 모두 필요합니다.'
            )
        if not os.path.isfile(key_path):
            raise RuntimeError(f'APNs key file not found: {key_path}')
        self._key_id = key_id
        self._team_id = team_id
        self._bundle_id = bundle_id
        self._host = self._SANDBOX_HOST if use_sandbox else self._PROD_HOST
        with open(key_path, 'r') as f:
            self._private_key_pem = f.read()
        self._jwt_cache: tuple[str, float] | None = None   # (token, expires_at_unix)

    def _get_jwt(self) -> str:
        now = time.time()
        if self._jwt_cache:
            tok, exp = self._jwt_cache
            if exp - now > 60:
                return tok
        # JWT 생성 (ES256, kid header)
        import jwt as _jwt
        payload = {'iss': self._team_id, 'iat': int(now)}
        tok = _jwt.encode(
            payload,
            self._private_key_pem,
            algorithm='ES256',
            headers={'kid': self._key_id, 'alg': 'ES256', 'typ': 'JWT'},
        )
        self._jwt_cache = (tok, now + self._JWT_TTL_S)
        return tok

    def send(self, *, token, platform, title, body, data=None):
        if platform != 'apns':
            return {'success': False, 'error': f'unsupported_platform:{platform}'}
        try:
            import httpx   # local import, 선택 의존성
        except ImportError as e:
            return {'success': False, 'error': f'httpx not installed: {e}'}
        try:
            jwt_token = self._get_jwt()
        except Exception as e:
            return {'success': False, 'error': f'jwt_sign_failed: {e}'}

        url = f'{self._host}/3/device/{token}'
        payload = {
            'aps': {
                'alert': {'title': title, 'body': body},
                'sound': 'default',
            },
        }
        if data:
            for k, v in data.items():
                payload[k] = v
        headers = {
            'authorization': f'bearer {jwt_token}',
            'apns-topic':    self._bundle_id,
            'apns-push-type': 'alert',
            'apns-priority': '10',
            'content-type':  'application/json',
        }
        try:
            with httpx.Client(http2=True, timeout=10.0) as client:
                resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                return {'success': True, 'apns_id': resp.headers.get('apns-id')}
            # 4xx/5xx → APNs reason 추출
            reason = ''
            try:
                reason = resp.json().get('reason', '')
            except Exception:
                reason = resp.text[:200]
            return {'success': False, 'status': resp.status_code, 'error': reason}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ── Multi-platform (PR #50) ───────────────────────────────────────────────────

class MultiPlatformPushProvider:
    """platform 별 자동 분기. push_tokens.platform 컬럼 기반 라우팅."""
    name = 'multi'

    def __init__(self):
        # 두 sub-provider 를 lazy 로 보관 (env 확인 시점에 인스턴스화).
        self._fcm: FcmPushProvider | None = None
        self._apns: ApnsPushProvider | None = None

    def _fcm_provider(self) -> FcmPushProvider | None:
        if self._fcm is None:
            key = os.environ.get('FCM_SERVER_KEY', '')
            if key:
                try:
                    self._fcm = FcmPushProvider(key)
                except Exception:
                    return None
        return self._fcm

    def _apns_provider(self) -> ApnsPushProvider | None:
        if self._apns is None:
            try:
                self._apns = ApnsPushProvider(
                    key_path=os.environ.get('APNS_KEY_PATH', ''),
                    key_id=os.environ.get('APNS_KEY_ID', ''),
                    team_id=os.environ.get('APNS_TEAM_ID', ''),
                    bundle_id=os.environ.get('APNS_BUNDLE_ID', ''),
                    use_sandbox=os.environ.get('APNS_USE_SANDBOX', 'false').lower()
                                in ('1', 'true', 'yes'),
                )
            except Exception:
                return None
        return self._apns

    def send(self, *, token, platform, title, body, data=None):
        if platform == 'fcm':
            p = self._fcm_provider()
            if p is None:
                return {'success': False, 'error': 'fcm_not_configured'}
            return p.send(token=token, platform=platform, title=title, body=body, data=data)
        if platform == 'apns':
            p = self._apns_provider()
            if p is None:
                return {'success': False, 'error': 'apns_not_configured'}
            return p.send(token=token, platform=platform, title=title, body=body, data=data)
        return {'success': False, 'error': f'unsupported_platform:{platform}'}


# ── Factory ───────────────────────────────────────────────────────────────────

def get_push_provider() -> PushProvider:
    name = os.environ.get('PUSH_PROVIDER', 'stub').lower()
    if name == 'fcm':
        return FcmPushProvider(os.environ.get('FCM_SERVER_KEY', ''))
    if name == 'apns':
        return ApnsPushProvider(
            key_path=os.environ.get('APNS_KEY_PATH', ''),
            key_id=os.environ.get('APNS_KEY_ID', ''),
            team_id=os.environ.get('APNS_TEAM_ID', ''),
            bundle_id=os.environ.get('APNS_BUNDLE_ID', ''),
            use_sandbox=os.environ.get('APNS_USE_SANDBOX', 'false').lower()
                        in ('1', 'true', 'yes'),
        )
    if name == 'multi':
        return MultiPlatformPushProvider()
    return StubPushProvider()


def push_to_users(db, user_ids: list[int], *, title: str, body: str,
                  data: dict | None = None) -> dict:
    """user_ids 에 등록된 모든 토큰으로 푸시 발송. platform 별 자동 분기.

    Provider 선택:
      - PUSH_PROVIDER=stub|fcm|apns: 단일 (mismatched platform 토큰은 실패)
      - PUSH_PROVIDER=multi: platform 별 자동 라우팅 (운영 권장)
    """
    if not user_ids:
        return {'sent': 0, 'failed': 0, 'no_tokens': 0}
    placeholders = ','.join('?' * len(user_ids))
    rows = db.execute(
        f"SELECT user_id, token, platform FROM push_tokens WHERE user_id IN ({placeholders})",
        user_ids
    ).fetchall()
    tokens_by_user = {}
    for r in rows:
        tokens_by_user.setdefault(r['user_id'], []).append((r['token'], r['platform']))
    sent, failed = 0, 0
    no_tokens = sum(1 for u in user_ids if u not in tokens_by_user)
    provider = get_push_provider()
    for uid, tokens in tokens_by_user.items():
        for token, platform in tokens:
            res = provider.send(token=token, platform=platform,
                                title=title, body=body, data=data)
            if res.get('success'):
                sent += 1
            else:
                failed += 1
    return {'sent': sent, 'failed': failed, 'no_tokens': no_tokens,
            'provider': provider.name}
