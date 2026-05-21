"""i18n DB 이중 불릿 수정 — terms_* 키의 '• ' 접두사 제거.

배경
----
mobile 의 `_TermsBullet` 위젯(coupons_screen / stamps_screen)은 항목 텍스트
앞에 '• ' 를 직접 붙인다. 그런데 translations 테이블의 약관 항목 키 14개는
ko 값 자체에도 '• ' 가 박혀 있어 화면에 `• • 텍스트` 로 이중 렌더된다.

불릿은 위젯이 소유하므로 DB 값에서 '• ' 접두사를 제거하는 것이 정답.
DeepL 일괄번역(scripts/translate_i18n_deepl.py) 실행 전에 처리해야
잘못된 불릿이 22개 언어로 복제되지 않는다.

idempotent — 접두사가 이미 없으면 건너뛴다. 기본 dry-run / --commit 시 적용.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, init_db  # noqa: E402

# _TermsBullet 위젯으로 렌더되는 약관 항목 키 — 위젯이 '• ' 를 붙이므로
# DB 값에는 불릿이 없어야 한다.
BULLET_KEYS: list[str] = [
    'coupon.terms_condition',
    'coupon.terms_dispute',
    'coupon.terms_exclusion',
    'coupon.terms_expiry',
    'coupon.terms_transfer',
    'coupon_issue.terms_exclusion',
    'coupon_issue.terms_expiry',
    'coupon_issue.terms_facility_only',
    'coupon_issue.terms_source',
    'stamp.terms_accrual',
    'stamp.terms_cooldown',
    'stamp.terms_dispute',
    'stamp.terms_expiry',
    'stamp.terms_reward',
]

# 제거 대상 접두사 변형 ('•' = U+2022).
_PREFIXES = ('• ', '•  ', '•')


def _strip_bullet(value: str) -> str:
    s = value.lstrip()
    for p in _PREFIXES:
        if s.startswith(p):
            return s[len(p):].lstrip()
    return value


def main() -> None:
    commit = '--commit' in sys.argv

    init_db()
    db = get_db()
    # BULLET_KEYS 의 모든 언어 행을 대상으로 (현재는 ko 뿐이지만 방어적으로 전체).
    placeholders = ','.join('?' * len(BULLET_KEYS))
    rows = db.execute(
        f"SELECT id, key, lang, value FROM translations "
        f"WHERE key IN ({placeholders})",
        BULLET_KEYS,
    ).fetchall()

    changes: list[tuple[int, str, str, str, str]] = []
    for r in rows:
        new_val = _strip_bullet(r['value'])
        if new_val != r['value']:
            changes.append((r['id'], r['key'], r['lang'], r['value'], new_val))

    print(f'대상 키: {len(BULLET_KEYS)}개  |  검사한 행: {len(rows)}개')
    print(f"불릿 제거 필요: {len(changes)}개 행\n")
    for _id, key, lang, old, new in changes:
        print(f'  [{lang}] {key}')
        print(f'    - {old!r}')
        print(f'    + {new!r}')

    if not changes:
        print('변경할 행 없음 — 이미 정리됨.')
        db.close()
        return

    if not commit:
        print('\n[dry-run] 변경 없음. 적용하려면 --commit 추가.')
        db.close()
        return

    for _id, _key, _lang, _old, new in changes:
        db.execute(
            "UPDATE translations SET value=?, updated_at=datetime('now') "
            "WHERE id=?",
            (new, _id),
        )
    db.commit()
    db.close()
    print(f'\n✅ {len(changes)}개 행 불릿 제거 완료.')


if __name__ == '__main__':
    main()
