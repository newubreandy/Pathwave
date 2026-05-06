"""정적 정책 파일 (static/policies/*.ko.md) 을 DB 에 v1.0 으로 일괄 등록.

PR #45 의 정적 파일이 placeholder 로 fallback 되고 있을 때, 운영 출범 전에
DB 로 초기 버전을 옮겨 admin-web 의 정책 관리 / 메일 공지 / 버전 추적이 작동하도록.

사용:
    PYTHONPATH=. /path/to/python scripts/register_policies_from_static.py

이미 DB 에 같은 (kind, version) 이 있으면 skip.
"""
import os
import sys
from datetime import datetime, timedelta

# repo root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from models.database import init_db, get_db                              # noqa: E402
from models.consent import VALID_KINDS                                   # noqa: E402
from models import policy_store                                          # noqa: E402

POLICIES_DIR = os.path.join(ROOT, 'static', 'policies')
LANG = 'ko'
VERSION = '0.1'

# 즉시 시행 (1분 전으로 설정 — get_active 의 effective_at <= now 조건 충족)
EFFECTIVE_AT = (datetime.utcnow() - timedelta(minutes=1)).isoformat()

KIND_TITLE = {
    'terms':        '서비스 이용약관',
    'privacy':      '개인정보 수집·이용 동의',
    'location':     '위치 정보 이용 동의',
    'age14':        '만 14세 이상 동의',
    'camera':       '카메라 접근 권한',
    'storage':      '저장공간 접근 권한',
    'push':         '푸시 알림 동의',
    'marketing':    '마케팅 정보 수신 동의',
    'third_party':  '제3자 정보 제공 동의',
}


def main() -> int:
    init_db()  # 테이블 보장
    db = get_db()

    inserted, skipped, missing = [], [], []

    for kind in sorted(VALID_KINDS):
        path = os.path.join(POLICIES_DIR, f'{kind}.{LANG}.md')
        if not os.path.isfile(path):
            missing.append(kind)
            continue

        # 이미 같은 버전 있으면 skip
        existing = policy_store.get_by_version(db, kind, VERSION, LANG)
        if existing:
            skipped.append(f'{kind} v{VERSION} (id={existing["id"]})')
            continue

        with open(path, 'r', encoding='utf-8') as f:
            body = f.read()

        title = KIND_TITLE.get(kind, kind)
        change_log = '정적 파일에서 v1.0 초기 등록'

        pid = policy_store.insert(
            db,
            kind=kind, lang=LANG, version=VERSION,
            title=title, body=body, change_log=change_log,
            effective_at=EFFECTIVE_AT, admin_id=None,
        )
        inserted.append(f'{kind} v{VERSION} (id={pid})')

    db.commit()
    db.close()

    print(f'Inserted ({len(inserted)}):')
    for s in inserted: print('  +', s)
    print(f'Skipped existing ({len(skipped)}):')
    for s in skipped: print('  =', s)
    if missing:
        print(f'Missing static files ({len(missing)}):')
        for s in missing: print('  -', s)
    return 0


if __name__ == '__main__':
    sys.exit(main())
