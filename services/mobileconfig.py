"""P17 — iOS .mobileconfig (Apple Configuration Profile) 생성.

매장의 모든 active WiFi 를 1개 ``.mobileconfig`` 파일로 묶어 다건 설치.
iOS 사용자가 1회 설치 → 모든 WiFi 자동 추가. 무중단 로밍 핵심.

서명
---
출시 v1 은 unsigned 발행 (iOS 가 '확인되지 않음' 경고를 표시하지만 설치 가능).
Apple Developer Program 인증서 발급 후 CMS 서명 적용 — 별도 PR.

ENV
---
- ``MOBILECONFIG_ORG``        기본 'PathWave'
- ``MOBILECONFIG_IDENT_BASE`` 기본 'com.pathwave'

사용
---
    from services.mobileconfig import generate_mobileconfig
    blob = generate_mobileconfig(facility={'id':1,'name':'Cafe'}, wifis=[...])
    return Response(blob, mimetype='application/x-apple-aspen-config')
"""
import os
import plistlib
import uuid as _uuid


_ORG        = os.environ.get('MOBILECONFIG_ORG', 'PathWave')
_IDENT_BASE = os.environ.get('MOBILECONFIG_IDENT_BASE', 'com.pathwave')


def _encryption_type(wifi: dict) -> str:
    """Apple EncryptionType 결정 — 'WPA'|'WEP'|'Any'|'None'.

    단순 휴리스틱 — 비밀번호 있으면 WPA(=WPA/WPA2 PSK), 없으면 None.
    P18(managed) 도입 시 RADIUS/802.1X 옵션 추가.
    """
    return 'WPA' if (wifi.get('password') or '').strip() else 'None'


def generate_mobileconfig(*, facility: dict, wifis: list[dict]) -> bytes:
    """매장 + wifi 목록 → ``.mobileconfig`` XML plist bytes.

    Parameters
    ----------
    facility : ``{'id': int, 'name': str}``
    wifis    : list of ``{'id', 'ssid', 'password', 'scope', 'credential_mode',
                          'bssid', 'country'}``

    Raises
    ------
    ValueError — wifis 가 비어있을 때.

    Returns
    -------
    bytes — XML plist (iOS 표준 .mobileconfig 포맷)
    """
    if not wifis:
        raise ValueError('wifis 가 비어있어 .mobileconfig 생성 불가')

    fid   = facility.get('id')
    fname = facility.get('name', f'Facility {fid}')

    payload_contents = []
    for w in wifis:
        ssid     = (w.get('ssid') or '').strip()
        if not ssid:
            continue
        password = (w.get('password') or '').strip()
        wifi_payload = {
            'PayloadType':        'com.apple.wifi.managed',
            'PayloadVersion':     1,
            'PayloadIdentifier':  f'{_IDENT_BASE}.wifi.{fid}.{w.get("id", 0)}',
            'PayloadUUID':        str(_uuid.uuid4()),
            'PayloadDisplayName': ssid,
            'SSID_STR':           ssid,
            'HIDDEN_NETWORK':     False,
            'AutoJoin':           True,
            'EncryptionType':     _encryption_type(w),
        }
        if password:
            wifi_payload['Password'] = password
        payload_contents.append(wifi_payload)

    if not payload_contents:
        raise ValueError('유효한 WiFi 항목이 없습니다 (모두 ssid 누락)')

    profile = {
        'PayloadType':         'Configuration',
        'PayloadVersion':      1,
        'PayloadIdentifier':   f'{_IDENT_BASE}.venue.{fid}',
        'PayloadUUID':         str(_uuid.uuid4()),
        'PayloadDisplayName':  f'{_ORG} - {fname}',
        'PayloadDescription':  f'{fname} WiFi 자동 설정 ({len(payload_contents)}개 네트워크)',
        'PayloadOrganization': _ORG,
        'PayloadContent':      payload_contents,
    }
    return plistlib.dumps(profile, fmt=plistlib.FMT_XML)
