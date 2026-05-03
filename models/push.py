"""푸시 발송 — 플러그블 provider + 사용자 토큰 조회 헬퍼.

환경변수
-------
- ``PUSH_PROVIDER`` = ``stub`` (기본) | ``fcm``
- ``FCM_SERVER_KEY`` (provider=fcm 시 필요)

운영 전환:
    PUSH_PROVIDER=fcm
    FCM_SERVER_KEY=AAAA...

dev/test에서는 stub이 콘솔에 출력하고 결과를 리스트로 누적해 검증 가능.
"""
import json
import os
import urllib.request
from typing import Protocol


class PushProvider(Protocol):
    name: str
    def send(self, *, token: str, platform: str, title: str, body: str,
             data: dict | None = None) -> dict: ...


_STUB_LOG_PATH = os.environ.get('PUSH_STUB_LOG', '/tmp/pathwave_push_stub.log')


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
        print(f'[push:stub] {platform} {token[:8]}... title={title!r}', flush=True)
        return {'success': True, 'message_id': f'stub-{len(StubPushProvider.sent_log)}'}


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


def get_push_provider() -> PushProvider:
    name = os.environ.get('PUSH_PROVIDER', 'stub').lower()
    if name == 'fcm':
        return FcmPushProvider(os.environ.get('FCM_SERVER_KEY', ''))
    return StubPushProvider()


def push_to_users(db, user_ids: list[int], *, title: str, body: str,
                  data: dict | None = None) -> dict:
    """user_ids에 등록된 모든 토큰으로 푸시 발송. 결과 카운트 반환."""
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
