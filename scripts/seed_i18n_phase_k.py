"""Phase K — 문의 상세(support_detail) 화면 i18n 시드 (ko only).

대상 파일:
  mobile/lib/screens/support/support_detail_screen.dart

Dart 코드는 이미 context.t() 래핑 완료 — DB 시드만 누락됐던 상태.
한국어만 입력 → 22개 언어는 admin-web "자동 번역" 버튼으로 채움.

idempotent.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, init_db


SEED_KEYS: list[tuple[str, str]] = [
    # ── 문의 상세 화면 (mobile.support.*) ───────────────────────────────
    ('mobile.support.detail_title',   '문의 상세'),
    ('mobile.support.no_messages',    '아직 메시지가 없습니다.'),
    ('mobile.support.message_hint',   '추가 문의 내용을 입력하세요'),
    ('mobile.support.send',           '전송'),
    ('mobile.support.send_failed',    '전송 실패'),
    ('mobile.support.admin',          '관리자'),
]


def seed() -> None:
    init_db()
    db = get_db()

    inserted, updated = 0, 0
    for key, ko in SEED_KEYS:
        row = db.execute(
            "SELECT id FROM translations WHERE key=? AND lang='ko'", (key,)
        ).fetchone()
        if row:
            db.execute(
                """UPDATE translations
                   SET value=?, source='seed', verified=1,
                       updated_at=datetime('now')
                   WHERE id=?""",
                (ko, row['id'])
            )
            updated += 1
        else:
            db.execute(
                """INSERT INTO translations (key, lang, value, source, verified)
                   VALUES (?, 'ko', ?, 'seed', 1)""",
                (key, ko)
            )
            inserted += 1
    db.commit()
    db.close()

    print('Phase K 문의 상세 i18n 시드 완료:')
    print(f'  keys           : {len(SEED_KEYS)}')
    print(f'  inserted (ko)  : {inserted}')
    print(f'  updated  (ko)  : {updated}')


if __name__ == '__main__':
    seed()
