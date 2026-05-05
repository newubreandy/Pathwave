"""PR #51 — SQLite → PostgreSQL 데이터 이관 스크립트.

운영 PostgreSQL 로 첫 전환 시 1회 실행. SQLite 의 모든 테이블을 읽어 PostgreSQL
에 INSERT. 시퀀스(SERIAL) 값도 마지막 row id 로 동기화.

사전 조건
--------
1. PostgreSQL DB 가 비어 있어야 함 (또는 본 스크립트가 모든 테이블 truncate)
2. ``DATABASE_URL=postgresql://...`` 설정
3. ``app.py`` 가 한 번이라도 실행되어 PostgreSQL 측에 init_db() 가 완료된 상태
   (또는 init_db 동작은 별도 PR 에서 PostgreSQL 호환 검증)

사용법
------
    PATHWAVE_SQLITE=/Users/.../pathwave.db \
    DATABASE_URL=postgresql://user:pw@host/db \
    python3 scripts/migrate_sqlite_to_postgres.py [--truncate]

옵션:
    --truncate   대상 PostgreSQL 의 기존 데이터를 먼저 삭제 (재이관 시 필수)
    --dry-run    실제 INSERT 없이 row 개수만 보고
"""
import argparse
import os
import sqlite3
import sys
from typing import List


# 이관 순서 — FK 의존성 따라 부모 → 자식
TABLES_IN_ORDER = [
    'super_admin_accounts',
    'users',
    'facility_accounts',
    'staff_accounts',
    'email_codes',
    'beacons',
    'facilities',
    'facility_images',
    'facility_hours',
    'facility_translations',
    'wifi_profiles',
    'invitations',
    'stamp_cards',
    'stamps',
    'coupons',
    'coupon_redemptions',
    'notifications',
    'notification_recipients',
    'notification_settings',
    'push_tokens',
    'chat_rooms',
    'chat_messages',
    'service_subscriptions',
    'payments',
    'billing_keys',
    'sales_daily',
    'beacon_battery_history',
    'announcements',
    'announcement_reads',
    'consents',
    'policies',
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--truncate', action='store_true',
                        help='대상 PostgreSQL 의 모든 테이블 truncate 후 이관')
    parser.add_argument('--dry-run', action='store_true', help='실제 INSERT 없이 row 개수만 출력')
    args = parser.parse_args()

    sqlite_path = os.environ.get('PATHWAVE_SQLITE') or 'pathwave.db'
    if not os.path.isfile(sqlite_path):
        print(f'[migrate] SQLite 파일이 없습니다: {sqlite_path}')
        return 1

    pg_url = os.environ.get('DATABASE_URL', '').strip()
    if not pg_url:
        print('[migrate] DATABASE_URL 이 설정되지 않았습니다.')
        return 1

    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        print('[migrate] psycopg[binary] 가 필요합니다. pip install "psycopg[binary]"')
        return 1

    src = sqlite3.connect(sqlite_path)
    src.row_factory = sqlite3.Row

    if pg_url.startswith('postgres://'):
        pg_url = 'postgresql://' + pg_url[len('postgres://'):]
    dst = psycopg.connect(pg_url, row_factory=dict_row)

    try:
        existing_tables = _list_tables(src)
        targets: List[str] = [t for t in TABLES_IN_ORDER if t in existing_tables]
        unknown = [t for t in existing_tables if t not in TABLES_IN_ORDER]
        if unknown:
            print(f'[migrate] 알 수 없는 테이블 (스크립트 미정의): {unknown}')

        if args.truncate and not args.dry_run:
            print('[migrate] PostgreSQL 측 truncate (역순)...')
            with dst.cursor() as cur:
                for t in reversed(targets):
                    cur.execute(f'TRUNCATE TABLE "{t}" RESTART IDENTITY CASCADE')
            dst.commit()

        total_inserted = 0
        for t in targets:
            count = _migrate_table(src, dst, t, dry_run=args.dry_run)
            total_inserted += count
            print(f'  • {t:30s} {count:>6} row')

        if not args.dry_run:
            print('[migrate] 시퀀스 동기화...')
            _sync_sequences(dst, targets)
            dst.commit()

        print(f'\n[migrate] 완료. 총 {total_inserted} row 이관.')
        return 0
    finally:
        src.close()
        dst.close()


def _list_tables(src: sqlite3.Connection) -> List[str]:
    rows = src.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    ).fetchall()
    return [r['name'] for r in rows]


def _migrate_table(src, dst, table: str, *, dry_run: bool) -> int:
    rows = src.execute(f'SELECT * FROM "{table}"').fetchall()
    if not rows:
        return 0
    if dry_run:
        return len(rows)

    cols = list(rows[0].keys())
    placeholders = ', '.join(['%s'] * len(cols))
    quoted = ', '.join([f'"{c}"' for c in cols])
    sql = f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders})'

    inserted = 0
    with dst.cursor() as cur:
        for r in rows:
            try:
                cur.execute(sql, tuple(r))
                inserted += 1
            except Exception as e:
                print(f'    ! {table} row 실패: {e}', file=sys.stderr)
    dst.commit()
    return inserted


def _sync_sequences(dst, tables: List[str]) -> None:
    """SERIAL 컬럼의 next val 을 max(id)+1 로 맞춤. 마이그레이션 후 필수."""
    with dst.cursor() as cur:
        for t in tables:
            try:
                cur.execute(
                    "SELECT pg_get_serial_sequence(%s, 'id') AS seq", (t,)
                )
                row = cur.fetchone()
                seq = row.get('seq') if row else None
                if not seq:
                    continue
                cur.execute(f'SELECT COALESCE(MAX(id), 0) AS m FROM "{t}"')
                max_row = cur.fetchone()
                max_id = max_row.get('m', 0) if max_row else 0
                if max_id > 0:
                    cur.execute(f"SELECT setval(%s, %s)", (seq, max_id))
            except Exception as e:
                print(f'    ! {t} 시퀀스 동기화 실패: {e}', file=sys.stderr)


if __name__ == '__main__':
    sys.exit(main())
