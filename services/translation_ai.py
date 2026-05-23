"""DeepL 자동 번역 래퍼 (Phase D — i18n 인프라 stub).

운영 시
-------
ENV DEEPL_API_KEY 가 설정되면 실제 DeepL API 호출. 없으면 stub 동작 — 입력 텍스트
앞에 ``[lang]`` 접두사만 붙여 반환하여 admin-web 흐름을 결합 테스트 가능.

DeepL 키 발급 후 (https://www.deepl.com/pro-api), 환경 변수만 세팅하면 본번역으로 전환됩니다.
"""
from __future__ import annotations

import os
import urllib.parse
import urllib.request
import json
from typing import Iterable


# DeepL 언어 코드 매핑 — DeepL 의 코드와 ISO 표준이 다른 경우만 명시.
# https://www.deepl.com/docs-api/translate-text/translate-text
_DEEPL_TARGET = {
    'ko':    'KO',
    'en':    'EN-US',     # 영국식 영어가 필요하면 EN-GB
    'ja':    'JA',
    'zh-CN': 'ZH-HANS',
    'zh-TW': 'ZH-HANT',
    'vi':    'VI',
    'th':    'TH',
    'tl':    'EN-US',     # DeepL 미지원 — fallback 으로 영어 (메모리 i18n 전략의 한계 사항)
    'id':    'ID',
    'ms':    'MS',
    'ru':    'RU',
    'hi':    'EN-US',     # DeepL 미지원 — 영어 fallback
    'es':    'ES',
    'de':    'DE',
    'fr':    'FR',
    'pt':    'PT-PT',
    'it':    'IT',
    'nl':    'NL',
    'pl':    'PL',
    'ar':    'AR',
    'tr':    'TR',
    'he':    'EN-US',     # DeepL 미지원 — 영어 fallback
    'sv':    'SV',
}

# memory 의 Phase 1 (10개) + Phase 2 (13개) 합 23개 — supported langs single source of truth.
SUPPORTED_LANGS = (
    # Phase 1
    'ko', 'en', 'zh-CN', 'ja', 'zh-TW', 'vi', 'th', 'tl', 'id', 'ms',
    # Phase 2
    'ru', 'hi', 'es', 'de', 'fr', 'pt', 'it', 'nl', 'pl',
    'ar', 'tr', 'he', 'sv',
)


def normalize_supported_lang(code: str | None, fallback: str = 'en') -> str:
    """디바이스/토큰/쿼리 언어 코드를 ``SUPPORTED_LANGS`` 안으로 정규화 (P8b 공통).

    Rules
    -----
    - 정확 일치 우선 (예 ``ko``, ``zh-CN``)
    - ``zh-Hant`` / ``-TW`` → ``zh-TW``, 그 외 ``zh*`` → ``zh-CN``
    - 언어 prefix(예 ``en-US`` → ``en``) 매칭
    - 매칭 실패 → ``fallback`` (P8b 정책: 영어)

    사용처: ``routes/chat.py`` viewer_lang, ``models/push.py`` token lang.
    """
    if not code:
        return fallback
    code = code.strip()
    if not code:
        return fallback
    if code in SUPPORTED_LANGS:
        return code
    if code.startswith('zh'):
        if 'Hant' in code or 'TW' in code:
            return 'zh-TW' if 'zh-TW' in SUPPORTED_LANGS else fallback
        return 'zh-CN' if 'zh-CN' in SUPPORTED_LANGS else fallback
    prefix = code.split('-', 1)[0]
    if prefix in SUPPORTED_LANGS:
        return prefix
    return fallback


def deepl_configured() -> bool:
    return bool(os.environ.get('DEEPL_API_KEY', '').strip())


def translate(text: str, target_lang: str, source_lang: str = 'ko') -> str:
    """source_lang → target_lang 번역. DeepL 키 미설정 시 stub.

    stub 형식: ``[<TARGET_LANG_UPPER>] <원문>``. 이렇게 하면 admin-web UI/캐시/페치
    흐름은 그대로 검증 가능하고, 실제 키 받은 뒤에는 이 함수만 swap.
    """
    if target_lang == source_lang:
        return text
    if not deepl_configured():
        return f'[{target_lang}] {text}'

    api_key = os.environ['DEEPL_API_KEY'].strip()
    # Free key suffix ':fx' 자동 라우팅
    base = ('https://api-free.deepl.com/v2/translate'
            if api_key.endswith(':fx')
            else 'https://api.deepl.com/v2/translate')
    target = _DEEPL_TARGET.get(target_lang, target_lang.upper())
    src    = _DEEPL_TARGET.get(source_lang, source_lang.upper()).split('-')[0]
    body = urllib.parse.urlencode({
        'text': text,
        'target_lang': target,
        'source_lang': src,
        'preserve_formatting': '1',
    }).encode()
    req = urllib.request.Request(
        base,
        data=body,
        headers={
            'Authorization': f'DeepL-Auth-Key {api_key}',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            return data['translations'][0]['text']
    except Exception:
        # 운영에서 실패해도 stub fallback — UI 가 깨지지 않게.
        return f'[{target_lang}!err] {text}'


def translate_to_all(text: str, source_lang: str = 'ko',
                     targets: Iterable[str] | None = None) -> dict[str, str]:
    """source_lang 한 텍스트를 supported 전체(또는 명시 targets)로 일괄 번역.

    반환 형식: ``{lang: translated_text}``. source_lang 도 결과에 포함.
    """
    out: dict[str, str] = {source_lang: text}
    pool = list(targets) if targets is not None else list(SUPPORTED_LANGS)
    for lang in pool:
        if lang == source_lang:
            continue
        out[lang] = translate(text, lang, source_lang=source_lang)
    return out
