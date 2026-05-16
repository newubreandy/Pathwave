"""Phase D — i18n DB 인프라 초기 시드.

memory 의 글로벌 i18n 전략을 따라:
- Phase 1 (10개 언어) 의 핵심 키 ~20 개를 ko + en 으로 초기 적재 (DB 베이스라인)
- 다른 21개 언어는 admin-web 의 자동번역 버튼으로 채우는 흐름을 가정
- idempotent — 같은 (key, lang) 은 update

PR #118 (provider-web ko/en locales 추가) 의 키 네이밍 패턴 유지:
- `auth.*`, `store.*`, `nav.*`, `common.*` 등 도메인 그룹 prefix
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, init_db


# (key, ko, en) 순. 23개 언어 전체는 admin-web 자동번역 버튼 1회 클릭으로 채워짐.
SEED_KEYS: list[tuple[str, str, str]] = [
    # 공통
    ('common.save',           '저장',                'Save'),
    ('common.cancel',         '취소',                'Cancel'),
    ('common.confirm',        '확인',                'Confirm'),
    ('common.delete',         '삭제',                'Delete'),
    ('common.close',          '닫기',                'Close'),
    ('common.loading',        '불러오는 중...',       'Loading...'),

    # 인증
    ('auth.login',            '로그인',              'Log in'),
    ('auth.logout',           '로그아웃',            'Log out'),
    ('auth.signup',           '회원가입',            'Sign up'),
    ('auth.email',            '이메일',              'Email'),
    ('auth.password',         '비밀번호',            'Password'),

    # 네비게이션 (mobile 하단 탭)
    ('nav.home',              '홈',                  'Home'),
    ('nav.search',            '검색',                'Search'),
    ('nav.mypage',            '마이',                'My'),
    ('nav.notifications',     '알림',                'Alerts'),

    # 매장 (provider-web StoreInfo + mobile facility_screen 공용)
    ('store.title',           '매장 정보',           'Store info'),
    ('store.label_beacons',   '비콘 목록',           'Beacons'),
    ('store.claim_beacon',    '비콘 등록',           'Claim beacon'),
    ('store.beacon_assigned', '비콘이 매장에 할당되었습니다.', 'Beacon assigned to store.'),

    # 알림
    ('notif.empty',           '알림이 없습니다.',     'No notifications.'),
]


def seed() -> None:
    init_db()
    db = get_db()

    inserted, updated = 0, 0
    for key, ko, en in SEED_KEYS:
        for lang, value in (('ko', ko), ('en', en)):
            row = db.execute(
                "SELECT id FROM translations WHERE key=? AND lang=?",
                (key, lang)
            ).fetchone()
            if row:
                db.execute(
                    """UPDATE translations
                       SET value=?, source='seed', verified=1,
                           updated_at=datetime('now')
                       WHERE id=?""",
                    (value, row['id'])
                )
                updated += 1
            else:
                db.execute(
                    """INSERT INTO translations
                         (key, lang, value, source, verified)
                       VALUES (?,?,?,'seed',1)""",
                    (key, lang, value)
                )
                inserted += 1
    db.commit()
    db.close()

    print('Phase D i18n seed 완료:')
    print(f'  keys                 : {len(SEED_KEYS)}')
    print(f'  inserted (key,lang)  : {inserted}')
    print(f'  updated  (key,lang)  : {updated}')
    print(f'  languages seeded     : ko, en')
    print(f'  남은 21개 언어       : admin-web 자동 번역 버튼으로 채우기')


if __name__ == '__main__':
    seed()
