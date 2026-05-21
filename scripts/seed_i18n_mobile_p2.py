"""P2 — mobile i18n 키 ko 시드 (코드 defaultValue 추출 방식).

배경
----
Phase 1 P2 에서 mobile 앱의 모든 하드코딩 한글을
``t('키', defaultValue: '한국어')`` 패턴으로 전환했다. 그 결과 mobile 이
사용하는 i18n 키의 대부분이 translations 테이블에 아직 없어, 비한국어
사용자는 한국어 fallback(defaultValue)만 보게 된다.

이 스크립트는 **코드를 단일 진실 원천(single source of truth)** 으로 삼아
``mobile/lib/**/*.dart`` 의 ``t(key, defaultValue:)`` 호출을 직접 파싱하여
ko 행을 시드한다. 손으로 옮긴 dict 가 코드와 어긋나는 drift 를 원천 차단.

동작
----
- 기본(dry-run): 추출 결과만 출력, DB 변경 없음.
- ``--commit``: DB 에 없는 키만 INSERT (lang='ko', source='seed', verified=1).
  이미 존재하는 키는 건드리지 않고, 값이 다르면 경고만 출력.

이후 11개 언어 번역은 ``scripts/translate_i18n_deepl.py`` (DeepL 키 필요).

idempotent — 반복 실행해도 안전.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, init_db  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOBILE_LIB = os.path.join(REPO_ROOT, 'mobile', 'lib')

# `.t('key', defaultValue:` — 키 다음 첫 문자열 인자가 defaultValue.
# 키에 보간(${...})이 들어간 동적 호출은 매칭되지 않음(아래 SUPPLEMENT 로 보충).
_CALL_RE = re.compile(r"\.t\(\s*'([A-Za-z_][\w.]*)'\s*,\s*defaultValue\s*:\s*")

# 동적 키 — 코드에서 'chat.report_reason_${entry.key}' 로 호출되어 정적 추출 불가.
# chat_detail_screen.dart 의 _reasons 맵이 런타임 defaultValue 원천.
SUPPLEMENT: dict[str, str] = {
    'chat.report_reason_spam':          '스팸·광고',
    'chat.report_reason_abuse':         '욕설·혐오',
    'chat.report_reason_illegal':       '불법 정보·사기',
    'chat.report_reason_inappropriate': '부적절한 콘텐츠',
    'chat.report_reason_other':         '기타',
}

_ESCAPE = {'n': '\n', 't': '\t', 'r': '\r'}


def _read_dart_string(text: str, pos: int) -> tuple[str | None, int]:
    """text[pos:] 에서 (인접 연결 가능한) 단일 인용 문자열을 읽어 디코드.

    Dart 의 인접 문자열 리터럴 연결('a' 'b' == 'ab')을 지원한다.
    반환: (디코드된 값, 끝 위치) — 문자열이 아니면 (None, pos).
    """
    n = len(text)
    parts: list[str] = []
    while True:
        while pos < n and text[pos] in ' \t\r\n':
            pos += 1
        if pos >= n or text[pos] != "'":
            break
        pos += 1  # opening quote
        buf: list[str] = []
        while pos < n:
            c = text[pos]
            if c == '\\':
                nxt = text[pos + 1] if pos + 1 < n else ''
                buf.append(_ESCAPE.get(nxt, nxt))
                pos += 2
            elif c == "'":
                pos += 1  # closing quote
                break
            else:
                buf.append(c)
                pos += 1
        parts.append(''.join(buf))
    return (''.join(parts) if parts else None), pos


def extract_pairs() -> tuple[dict[str, str], list[tuple[str, str, str]]]:
    """mobile/lib 전체에서 (key, ko) 추출.

    반환: (pairs, conflicts)
      pairs     — {key: ko}
      conflicts — [(key, 기존값, 무시된값)]  같은 키가 서로 다른 defaultValue 로 등장
    """
    pairs: dict[str, str] = {}
    conflicts: list[tuple[str, str, str]] = []

    for root, _dirs, files in os.walk(MOBILE_LIB):
        for fn in sorted(files):
            if not fn.endswith('.dart'):
                continue
            path = os.path.join(root, fn)
            with open(path, encoding='utf-8') as f:
                content = f.read()
            for m in _CALL_RE.finditer(content):
                key = m.group(1)
                value, _end = _read_dart_string(content, m.end())
                if value is None:
                    continue  # defaultValue 가 문자열 리터럴이 아님 — 스킵
                value = value.strip()
                if not value:
                    continue
                if key in pairs and pairs[key] != value:
                    conflicts.append((key, pairs[key], value))
                    continue
                pairs.setdefault(key, value)

    for key, ko in SUPPLEMENT.items():
        if key in pairs and pairs[key] != ko:
            conflicts.append((key, pairs[key], ko))
        else:
            pairs.setdefault(key, ko)

    return pairs, conflicts


def main() -> None:
    commit = '--commit' in sys.argv

    pairs, conflicts = extract_pairs()
    print(f'추출된 키: {len(pairs)}개  (mobile/lib defaultValue + 동적 보충 {len(SUPPLEMENT)})')
    if conflicts:
        print(f'\n⚠️  defaultValue 충돌 {len(conflicts)}건 — 첫 등장값 채택:')
        for key, kept, ignored in conflicts:
            print(f'   {key}\n     채택: {kept!r}\n     무시: {ignored!r}')

    init_db()
    db = get_db()
    existing = {
        r['key']: r['value']
        for r in db.execute(
            "SELECT key, value FROM translations WHERE lang='ko'"
        ).fetchall()
    }

    to_insert = {k: v for k, v in pairs.items() if k not in existing}
    mismatched = {
        k: (existing[k], v)
        for k, v in pairs.items()
        if k in existing and existing[k] != v
    }

    print(f'\nDB 기존 ko 키 : {len(existing)}개')
    print(f'신규 INSERT   : {len(to_insert)}개')
    print(f'기존 값 불일치 : {len(mismatched)}개 (변경하지 않음 — 검토 필요)')

    if mismatched:
        print('\n── 기존 DB 값 ≠ 코드 defaultValue (수동 검토) ──')
        for k, (db_val, code_val) in sorted(mismatched.items()):
            print(f'   {k}\n     DB  : {db_val!r}\n     코드: {code_val!r}')

    if not commit:
        print('\n[dry-run] 변경 없음. 실제 적용하려면 --commit 플래그 추가.')
        if to_insert:
            print('\n── INSERT 예정 키 (미리보기) ──')
            for k in sorted(to_insert):
                preview = to_insert[k].replace('\n', '\\n')
                if len(preview) > 70:
                    preview = preview[:67] + '...'
                print(f'   {k} = {preview}')
        db.close()
        return

    inserted = 0
    for key in sorted(to_insert):
        db.execute(
            """INSERT INTO translations (key, lang, value, source, verified)
               VALUES (?, 'ko', ?, 'seed', 1)""",
            (key, to_insert[key]),
        )
        inserted += 1
    db.commit()
    db.close()

    print(f'\n✅ 시드 완료 — ko 행 {inserted}개 INSERT.')
    print('   다음 단계: scripts/translate_i18n_deepl.py (DeepL 키 필요)')


if __name__ == '__main__':
    main()
