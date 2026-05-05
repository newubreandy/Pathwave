"""SQLite ↔ PostgreSQL 통합 DB 어댑터 (PR #51).

`DATABASE_URL` ENV 가 ``postgres://...`` / ``postgresql://...`` 형식이면 PostgreSQL 사용,
미설정 시 기존 SQLite 파일 사용 (PR #1 부터의 동작 호환).

전체 코드베이스가 ``cursor.execute(sql, params)`` 패턴 + ``?`` 플레이스홀더로 작성됨.
PostgreSQL 은 ``%s`` 만 받으므로, 본 어댑터의 cursor 가 SQL 문자열을 자동 변환.
또한 datetime 함수 등 일부 SQLite 고유 함수를 PostgreSQL 등가식으로 치환.

운영 마이그레이션:
  1. PostgreSQL DB 생성
  2. ``scripts/postgres_init.sql`` 실행 (서버 부팅 전)
  3. ``scripts/migrate_sqlite_to_postgres.py`` 실행 (데이터 이관)
  4. ``DATABASE_URL=postgresql://user:pw@host/db`` 설정
  5. 서버 부팅 — ``init_db()`` 가 어댑터 자동 선택
"""
import os
import re
import sqlite3
from typing import Any


def is_postgres_url(url: str) -> bool:
    return bool(url) and (url.startswith('postgres://') or url.startswith('postgresql://'))


def get_database_url() -> str:
    return (os.environ.get('DATABASE_URL') or '').strip()


def use_postgres() -> bool:
    return is_postgres_url(get_database_url())


# ── SQL 변환 — SQLite ↔ PostgreSQL ───────────────────────────────────────────

# SQLite 의 ``datetime('now')`` 등 → PostgreSQL 의 ``CURRENT_TIMESTAMP`` 류
_SQLITE_TO_PG_FUNCS = [
    # DDL — SERIAL 로 변환 (AUTOINCREMENT 가 INTEGER PRIMARY KEY 에 붙어 있을 때만)
    (re.compile(r'\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b', re.I),
        'SERIAL PRIMARY KEY'),
    # 시간 함수
    (re.compile(r"datetime\(\s*'now'\s*\)", re.I), 'CURRENT_TIMESTAMP'),
    (re.compile(r"date\(\s*'now'\s*\)", re.I),     'CURRENT_DATE'),
    (re.compile(r"datetime\(\s*'now'\s*,\s*'\+(\d+)\s*minutes?'\s*\)", re.I),
        r"(CURRENT_TIMESTAMP + interval '\1 minutes')"),
    (re.compile(r"datetime\(\s*'now'\s*,\s*'\+(\d+)\s*hours?'\s*\)", re.I),
        r"(CURRENT_TIMESTAMP + interval '\1 hours')"),
    (re.compile(r"datetime\(\s*'now'\s*,\s*'\+(\d+)\s*days?'\s*\)", re.I),
        r"(CURRENT_TIMESTAMP + interval '\1 days')"),
    (re.compile(r"datetime\(\s*'now'\s*,\s*'-(\d+)\s*days?'\s*\)", re.I),
        r"(CURRENT_TIMESTAMP - interval '\1 days')"),
    # date('now', 'start of month') — PostgreSQL: date_trunc('month', CURRENT_DATE)
    (re.compile(r"date\(\s*'now'\s*,\s*'start of month'\s*\)", re.I),
        "date_trunc('month', CURRENT_DATE)"),
    # SQLite strftime('%Y-%m-%d', col) → to_char(col::timestamp, 'YYYY-MM-DD')
    (re.compile(r"strftime\(\s*'%Y-%m-%d'\s*,\s*([^)]+?)\s*\)", re.I),
        r"to_char(\1::timestamp, 'YYYY-MM-DD')"),
    # SQLite COALESCE 는 동일, LIKE 도 동일
]


def _translate_sql_for_pg(sql: str) -> str:
    """``?`` → ``%s`` + 일부 SQLite 고유 함수 치환."""
    out = sql
    for pat, repl in _SQLITE_TO_PG_FUNCS:
        out = pat.sub(repl, out)
    # 플레이스홀더 — 단, ``?`` 가 문자열 리터럴 안에 있으면 두면 안 되지만
    # 본 코드베이스는 그런 경우가 없음 (모든 ``?`` 는 placeholder 용).
    out = out.replace('?', '%s')
    return out


# ── 어댑터 인터페이스 ────────────────────────────────────────────────────────

class _PgRow:
    """psycopg dict_row 결과를 sqlite3.Row 처럼 ``row['col']`` + ``row.keys()`` 지원."""
    __slots__ = ('_d',)
    def __init__(self, d: dict):
        self._d = d
    def __getitem__(self, k):
        if isinstance(k, int):
            return list(self._d.values())[k]
        return self._d[k]
    def __contains__(self, k):
        return k in self._d
    def keys(self):
        return self._d.keys()
    def __iter__(self):
        return iter(self._d.values())
    def __repr__(self):
        return f'_PgRow({self._d!r})'


class _PgCursor:
    """sqlite3.Cursor 인터페이스 흉내. SQL 자동 변환 + Row 객체 통일."""
    def __init__(self, raw):
        self._raw = raw
        self._last_returning = None

    def execute(self, sql: str, params: tuple | list = ()):
        translated = _translate_sql_for_pg(sql)
        # AUTOINCREMENT INSERT 후 lastrowid 가 필요한 경우, RETURNING id 자동 추가는
        # 코드 변경 부담이 크므로 cur.lastrowid 호출 시 별도 RETURNING 처리한다 (아래).
        self._raw.execute(translated, tuple(params))
        return self

    def fetchone(self):
        row = self._raw.fetchone()
        return _PgRow(row) if row is not None else None

    def fetchall(self):
        return [_PgRow(r) for r in self._raw.fetchall()]

    @property
    def rowcount(self):
        return self._raw.rowcount

    @property
    def lastrowid(self):
        # SQLite 호환 — 직전 INSERT 의 PK. PostgreSQL 은 ``RETURNING id`` 로 받아야 함.
        # 본 어댑터는 INSERT 후 ``SELECT lastval()`` 로 시퀀스의 마지막 값을 조회.
        # (단, 다중 connection 환경에서 race 방지 위해 ``lastval()`` 은 같은 세션 안)
        try:
            self._raw.execute('SELECT lastval()')
            return self._raw.fetchone()[0]
        except Exception:
            return None

    def close(self):
        try: self._raw.close()
        except Exception: pass


class _PgConnectionWrapper:
    """sqlite3.Connection 인터페이스 흉내. ``execute / commit / close / row_factory``."""
    row_factory = None   # SQLite 호환 표시용 (실 사용 안 함)

    def __init__(self, raw):
        self._raw = raw

    def execute(self, sql: str, params: tuple | list = ()):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def executescript(self, script: str):
        # PostgreSQL 은 multi-statement 지원하므로 그대로 실행.
        translated = _translate_sql_for_pg(script)
        cur = self._raw.cursor()
        try:
            cur.execute(translated)
        finally:
            cur.close()

    def cursor(self):
        return _PgCursor(self._raw.cursor())

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        try: self._raw.close()
        except Exception: pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ── 팩토리 ───────────────────────────────────────────────────────────────────

def open_connection(*, sqlite_path: str | None = None) -> Any:
    """``DATABASE_URL`` 우선 → PostgreSQL, 미설정 시 ``sqlite_path`` 로 SQLite.

    반환 타입은 sqlite3.Connection 또는 _PgConnectionWrapper.
    호출 측 코드(get_db) 는 동일한 인터페이스(execute/commit/close)만 사용.
    """
    if use_postgres():
        try:
            import psycopg
        except ImportError as e:
            raise RuntimeError(
                'PostgreSQL 사용 시 psycopg[binary] 가 필요합니다. '
                'pip install "psycopg[binary]"'
            ) from e
        from psycopg.rows import dict_row
        url = get_database_url()
        # postgres:// → postgresql:// (psycopg3 권장)
        if url.startswith('postgres://'):
            url = 'postgresql://' + url[len('postgres://'):]
        conn = psycopg.connect(url, row_factory=dict_row)
        # SQLite 코드가 commit 을 명시적으로 호출하므로 autocommit=False 유지 (기본).
        return _PgConnectionWrapper(conn)

    # SQLite (기본)
    path = sqlite_path or os.environ.get(
        'PATHWAVE_DB',
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pathwave.db')
    )
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn
