"""번역 프로바이더 — 플러그블 인터페이스.

환경변수
-------
- ``TRANSLATION_PROVIDER`` = ``stub`` (기본) | ``google``
- ``TRANSLATION_API_KEY``  Google Translate v2 API 키 (provider=google 일 때)

사용
---
    from models.translator import get_translator
    t = get_translator()
    t.translate("카페모카", source='ko', target='en')  # → "Cafe Mocha"
"""
import json
import os
import urllib.parse
import urllib.request
from typing import Protocol


class TranslatorError(RuntimeError):
    """번역 호출 실패 (네트워크/키 오류 등)."""


class Translator(Protocol):
    name: str
    def translate(self, text: str, *, source: str, target: str) -> str: ...


class StubTranslator:
    """``[lang] {원문}`` 형식 — API 키 없이 동작. 개발/테스트 용."""
    name = 'stub'

    def translate(self, text: str, *, source: str, target: str) -> str:
        if not text or source == target:
            return text
        return f'[{target}] {text}'


class GoogleTranslator:
    """Google Cloud Translation v2 REST API."""
    name = 'google'
    _ENDPOINT = 'https://translation.googleapis.com/language/translate/v2'

    def __init__(self, api_key: str):
        if not api_key:
            raise TranslatorError('TRANSLATION_API_KEY가 필요합니다.')
        self._key = api_key

    def translate(self, text: str, *, source: str, target: str) -> str:
        if not text or source == target:
            return text
        # 'zh-CN'/'zh-TW' 등은 Google이 받음. 'zh' 단독은 'zh-CN'으로 매핑 가정.
        target_g = 'zh-CN' if target == 'zh' else target
        params = {
            'key':    self._key,
            'q':      text,
            'source': source,
            'target': target_g,
            'format': 'text',
        }
        url = f'{self._ENDPOINT}?{urllib.parse.urlencode(params)}'
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            raise TranslatorError(f'Google Translate 호출 실패: {e}') from e
        try:
            return data['data']['translations'][0]['translatedText']
        except (KeyError, IndexError) as e:
            raise TranslatorError(f'예상치 못한 응답: {data}') from e


def get_translator() -> Translator:
    name = os.environ.get('TRANSLATION_PROVIDER', 'stub').strip().lower()
    if name == 'google':
        return GoogleTranslator(os.environ.get('TRANSLATION_API_KEY', ''))
    return StubTranslator()
