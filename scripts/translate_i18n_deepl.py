"""translations 테이블 일괄 번역 (DeepL) — 출시 외부서비스 단계 1회 실행물.

배경 (2026-06-12)
----------------
ko 925 키 대비 en 20 키 (2%) — mobile 은 t(key, defaultValue) 폴백이라
앱이 깨지진 않지만 en 사용자에게 한국어가 노출된다. DeepL 키 도착 시
이 스크립트 1회 실행으로 누락분을 일괄 채운다 (번역 결과는 DB 에
저장되어 재사용 — 호출 비용 1회 원칙).

사용
----
  # 미리보기 (API 호출 없음 — 대상 키 수만 집계)
  ./venv/bin/python scripts/translate_i18n_deepl.py --dry-run

  # en 만 (Phase 1 기본)
  DEEPL_API_KEY=... ./venv/bin/python scripts/translate_i18n_deepl.py

  # Phase 2 — 한국 방문 관광객 우선 10개 언어
  DEEPL_API_KEY=... ./venv/bin/python scripts/translate_i18n_deepl.py \
      --langs en,zh-CN,ja,zh-TW,vi,th,id

특성
----
- 멱등: (key, lang) 이미 존재하면 skip — 재실행 안전.
- {placeholder} 변수 보호: <keep>...</keep> XML 태그로 감싸 DeepL 이
  번역하지 않도록 (tag_handling=xml + ignore_tags=keep) 하고 복원.
- DeepL 미지원 언어 (tl/ms 등) 는 자동 skip 후 목록 출력 — 별도 처리.
- 배치 50키/요청, 실패 배치는 건너뛰고 계속 (마지막에 요약).

env
---
- DEEPL_API_KEY  : 필수 (dry-run 제외)
- DEEPL_API_URL  : 기본 https://api-free.deepl.com/v2/translate
                   (유료 키면 https://api.deepl.com/v2/translate)
- PATHWAVE_DB    : DB 경로 오버라이드 (기본 ../pathwave.db)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import urllib.parse
import urllib.request

DB_PATH = os.environ.get('PATHWAVE_DB') or os.path.join(
    os.path.dirname(__file__), '..', 'pathwave.db')
API_KEY = os.environ.get('DEEPL_API_KEY', '').strip()
API_URL = os.environ.get('DEEPL_API_URL',
                         'https://api-free.deepl.com/v2/translate')

# 앱 lang 코드 → DeepL target_lang. 미지원은 None (skip + 보고).
DEEPL_TARGET = {
    'en': 'EN-US', 'ja': 'JA', 'zh-CN': 'ZH-HANS', 'zh-TW': 'ZH-HANT',
    'de': 'DE', 'fr': 'FR', 'es': 'ES', 'it': 'IT', 'nl': 'NL',
    'pl': 'PL', 'pt': 'PT-PT', 'ru': 'RU', 'tr': 'TR', 'sv': 'SV',
    'id': 'ID', 'ar': 'AR', 'th': 'TH', 'vi': 'VI', 'he': 'HE',
    # DeepL 미지원 (2026 기준) — 별도 공급자 필요:
    'tl': None, 'ms': None, 'hi': None,
}

_PLACEHOLDER = re.compile(r'\{[a-zA-Z0-9_]+\}')
BATCH = 50


def _protect(text: str) -> str:
    """{var} → <keep>{var}</keep> (DeepL ignore_tags)."""
    return _PLACEHOLDER.sub(lambda m: f'<keep>{m.group(0)}</keep>', text)


def _restore(text: str) -> str:
    return text.replace('<keep>', '').replace('</keep>', '')


def _deepl_batch(texts: list[str], target: str) -> list[str]:
    """DeepL 호출 — texts 순서 보존 반환."""
    params = [('auth_key', API_KEY), ('source_lang', 'KO'),
              ('target_lang', target), ('tag_handling', 'xml'),
              ('ignore_tags', 'keep')]
    params += [('text', _protect(t)) for t in texts]
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(API_URL, data=data, method='POST')
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode())
    return [_restore(tr['text']) for tr in body['translations']]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--langs', default='en',
                    help='쉼표 구분 대상 언어 (기본 en)')
    ap.add_argument('--dry-run', action='store_true',
                    help='API 호출 없이 대상 집계만')
    args = ap.parse_args()

    langs = [l.strip() for l in args.langs.split(',') if l.strip()]
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    ko_rows = db.execute(
        "SELECT key, value FROM translations WHERE lang='ko'").fetchall()
    ko_map = {r['key']: r['value'] for r in ko_rows}
    print(f'ko 원본 키: {len(ko_map)}')

    grand_total = 0
    unsupported: list[str] = []
    for lang in langs:
        target = DEEPL_TARGET.get(lang)
        existing = {r['key'] for r in db.execute(
            "SELECT key FROM translations WHERE lang=?", (lang,))}
        missing = [k for k in ko_map if k not in existing]
        print(f'\n[{lang}] 기존 {len(existing)} / 누락 {len(missing)}'
              + (f' / DeepL target={target}' if target else ' / ❌ DeepL 미지원'))
        if target is None:
            unsupported.append(lang)
            continue
        if args.dry_run or not missing:
            continue
        if not API_KEY:
            print('  ❌ DEEPL_API_KEY 미설정 — 중단', file=sys.stderr)
            return 1

        done = 0
        for i in range(0, len(missing), BATCH):
            chunk = missing[i:i + BATCH]
            try:
                results = _deepl_batch([ko_map[k] for k in chunk], target)
            except Exception as e:                          # noqa: BLE001
                print(f'  ⚠️ 배치 {i//BATCH + 1} 실패 — skip: {e}',
                      file=sys.stderr)
                continue
            db.executemany(
                """INSERT OR IGNORE INTO translations (key, lang, value)
                   VALUES (?, ?, ?)""",
                [(k, lang, v) for k, v in zip(chunk, results)])
            db.commit()
            done += len(chunk)
            print(f'  … {done}/{len(missing)}')
        grand_total += done
        print(f'  ✅ {lang}: {done} 키 저장')

    db.close()
    if args.dry_run:
        print('\n(dry-run — DB 무변경)')
    if unsupported:
        print(f'\n⚠️ DeepL 미지원 언어 (별도 공급자 필요): {unsupported}')
    print(f'\n총 저장: {grand_total}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
