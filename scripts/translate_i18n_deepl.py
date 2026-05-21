"""i18n DB 일괄 번역 — ko 기준 → 22개 언어 (DeepL).

배경
----
translations 테이블에 ko 행은 모두 시드되어 있으나(550+), 다른 언어는
거의 비어 있다. 이 스크립트는 ko 를 원천으로 SUPPORTED_LANGS 전체를
일괄 번역해 채운다. ``services/translation_ai.py`` 의 DeepL 래퍼를 재사용.

전제 — DeepL API 키
-------------------
환경 변수 ``DEEPL_API_KEY`` 가 필요하다 (출시 순서상 2단계 = 법인카드 후
외부 서비스 신청). 키 발급: https://www.deepl.com/pro-api

  export DEEPL_API_KEY='xxxxxxxx:fx'   # free 키는 ':fx' 접미사
  python3 scripts/translate_i18n_deepl.py --run

사용법
------
  --status            현재 언어별 미번역 키 수만 출력 (번역 안 함, 키 불필요)
  --run               실제 번역 실행 — DEEPL_API_KEY 필수
  --allow-stub        키 없이도 stub('[lang] 원문')로 채움 — 개발 결합 테스트용
  --limit N           앞에서 N개 ko 키만 처리 (배치 테스트)
  --lang xx           특정 언어 하나만 (기본: SUPPORTED_LANGS 전체)

idempotent — 이미 값이 있는 (key, lang) 은 건너뛴다. 중단 후 재실행 가능.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, init_db  # noqa: E402
from services.translation_ai import (  # noqa: E402
    SUPPORTED_LANGS, deepl_configured, translate,
)


def _targets() -> list[str]:
    """--lang 지정 시 그 언어만, 아니면 ko 제외 전체."""
    for i, arg in enumerate(sys.argv):
        if arg == '--lang' and i + 1 < len(sys.argv):
            return [sys.argv[i + 1]]
    return [lang for lang in SUPPORTED_LANGS if lang != 'ko']


def _arg_value(name: str) -> str | None:
    for i, arg in enumerate(sys.argv):
        if arg == name and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def show_status() -> None:
    init_db()
    db = get_db()
    ko_keys = {
        r['key'] for r in db.execute(
            "SELECT key FROM translations WHERE lang='ko'"
        ).fetchall()
    }
    print(f'ko 원천 키: {len(ko_keys)}개\n')
    print(f'{"lang":<8}{"있음":>8}{"미번역":>10}')
    print('-' * 26)
    for lang in _targets():
        have = {
            r['key'] for r in db.execute(
                "SELECT key FROM translations WHERE lang=?", (lang,)
            ).fetchall()
        }
        covered = len(ko_keys & have)
        missing = len(ko_keys - have)
        print(f'{lang:<8}{covered:>8}{missing:>10}')
    db.close()
    print()
    print('미번역은 --run 으로 채울 수 있습니다 (DEEPL_API_KEY 필요).')


def run(allow_stub: bool) -> None:
    if not deepl_configured() and not allow_stub:
        print('❌ DEEPL_API_KEY 가 설정되지 않았습니다.')
        print('   export DEEPL_API_KEY=... 후 재실행하거나,')
        print('   개발 결합 테스트는 --allow-stub 로 stub 채움이 가능합니다.')
        sys.exit(1)

    mode = 'DeepL 실번역' if deepl_configured() else 'stub'
    limit = _arg_value('--limit')
    limit_n = int(limit) if limit else None

    init_db()
    db = get_db()
    ko_rows = db.execute(
        "SELECT key, value FROM translations WHERE lang='ko' ORDER BY key"
    ).fetchall()
    if limit_n:
        ko_rows = ko_rows[:limit_n]

    targets = _targets()
    src_tag = 'deepl' if deepl_configured() else 'stub'
    print(f'모드: {mode}  |  ko 키: {len(ko_rows)}  |  대상 언어: {len(targets)}')

    inserted, skipped, failed = 0, 0, 0
    for idx, row in enumerate(ko_rows, 1):
        key, ko_value = row['key'], row['value']
        have = {
            r['lang'] for r in db.execute(
                "SELECT lang FROM translations WHERE key=?", (key,)
            ).fetchall()
        }
        for lang in targets:
            if lang in have:
                skipped += 1
                continue
            try:
                value = translate(ko_value, lang, source_lang='ko')
            except Exception as e:  # noqa: BLE001
                print(f'  ! {key} [{lang}] 실패: {e}')
                failed += 1
                continue
            db.execute(
                """INSERT INTO translations (key, lang, value, source, verified)
                   VALUES (?, ?, ?, ?, 0)""",
                (key, lang, value, src_tag),
            )
            inserted += 1
        if idx % 25 == 0:
            db.commit()
            print(f'  ... {idx}/{len(ko_rows)} 키 처리 (insert {inserted})')
    db.commit()
    db.close()

    print(f'\n✅ 완료 — insert {inserted} / skip {skipped} / fail {failed}')
    if src_tag == 'stub':
        print('   ⚠️ stub 모드 — DeepL 키 확보 후 stub 행 삭제 뒤 재실행 권장:')
        print("   sqlite3 pathwave.db \"DELETE FROM translations WHERE source='stub';\"")


def main() -> None:
    if '--status' in sys.argv:
        show_status()
    elif '--run' in sys.argv:
        run(allow_stub='--allow-stub' in sys.argv)
    else:
        print(__doc__)
        print('플래그를 지정해 주세요: --status | --run [--allow-stub]')


if __name__ == '__main__':
    main()
