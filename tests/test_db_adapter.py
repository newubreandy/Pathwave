"""PR #51 — DB adapter 단위 테스트.

PostgreSQL 인스턴스가 없는 환경에서도 SQL 변환 로직 + 어댑터 인터페이스 호환성을
검증. 실제 PostgreSQL 호출은 별도 ENV (`DATABASE_URL=postgresql://...`) 시
수동/통합 테스트로 검증.
"""
import os
import sqlite3
import tempfile

# 어댑터 import (psycopg 미설치 환경에서도 import 가능하도록 lazy)
from models import db_adapter


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


# ── [1] use_postgres / get_database_url 분기 ─────────────────────────────
print('\n[1] DATABASE_URL ENV 분기')
os.environ.pop('DATABASE_URL', None)
_ok('미설정 → use_postgres=False', db_adapter.use_postgres() == False)

os.environ['DATABASE_URL'] = 'sqlite:///some.db'
_ok('sqlite URL → use_postgres=False', db_adapter.use_postgres() == False)

os.environ['DATABASE_URL'] = 'postgres://u:p@h/db'
_ok('postgres:// → use_postgres=True', db_adapter.use_postgres() == True)

os.environ['DATABASE_URL'] = 'postgresql://u:p@h/db'
_ok('postgresql:// → use_postgres=True', db_adapter.use_postgres() == True)

os.environ.pop('DATABASE_URL', None)


# ── [2] SQL 자동 변환 — _translate_sql_for_pg ────────────────────────────
print('\n[2] SQL placeholder + 함수 변환')
t = db_adapter._translate_sql_for_pg

_ok("? → %s", t("SELECT * FROM x WHERE id=?") == "SELECT * FROM x WHERE id=%s")
_ok("multiple ?", t("INSERT INTO x VALUES (?, ?, ?)")
    == "INSERT INTO x VALUES (%s, %s, %s)")

_ok("AUTOINCREMENT → SERIAL",
    'SERIAL PRIMARY KEY' in t("CREATE TABLE x (id INTEGER PRIMARY KEY AUTOINCREMENT)"))

_ok("datetime('now') → CURRENT_TIMESTAMP",
    "CURRENT_TIMESTAMP" in t("INSERT INTO x VALUES (datetime('now'))"))

_ok("datetime('now', '+5 minutes')",
    "interval '5 minutes'" in t("SELECT datetime('now', '+5 minutes')"))

_ok("date('now', 'start of month')",
    "date_trunc('month', CURRENT_DATE)" in t("WHERE created_at >= date('now', 'start of month')"))

_ok("strftime → to_char",
    "to_char(" in t("SELECT strftime('%Y-%m-%d', created_at) FROM x"))


# ── [3] _PgRow 인터페이스 ─────────────────────────────────────────────────
print('\n[3] _PgRow — sqlite3.Row 호환')
row = db_adapter._PgRow({'id': 1, 'name': 'foo'})
_ok("row['name']", row['name'] == 'foo')
_ok("row[0]",       row[0] == 1)
_ok("'name' in row", 'name' in row)
_ok("row.keys()",   list(row.keys()) == ['id', 'name'])


# ── [4] SQLite 경로 — 실 connection 동작 (회귀) ──────────────────────────
print('\n[4] SQLite open_connection — 회귀')
tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
conn = db_adapter.open_connection(sqlite_path=tmp.name)
_ok("sqlite3.Connection 반환 (use_postgres=False)",
    isinstance(conn, sqlite3.Connection))
conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY AUTOINCREMENT, v TEXT)")
conn.execute("INSERT INTO t (v) VALUES (?)", ('hello',))
conn.commit()
row = conn.execute("SELECT * FROM t WHERE id=?", (1,)).fetchone()
_ok("INSERT/SELECT round-trip", row['v'] == 'hello')
conn.close()


# ── [5] add_column_if_missing 호환성 (SQLite) ────────────────────────────
print('\n[5] _add_column_if_missing — SQLite 회귀')
# database.py 의 헬퍼는 use_postgres() 분기 — SQLite 경로 검증
os.environ['PATHWAVE_DB'] = tmp.name
import models.database as _dbmod
def _patched_get_db():
    c = sqlite3.connect(os.environ['PATHWAVE_DB'])
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c
_dbmod.get_db = _patched_get_db

db = _patched_get_db()
_dbmod._add_column_if_missing(db, 't', 'extra', 'extra INTEGER')
db.commit()
cols = {r['name'] for r in db.execute('PRAGMA table_info(t)').fetchall()}
_ok("extra 컬럼 추가됨", 'extra' in cols)
# 두 번째 호출 — no-op
_dbmod._add_column_if_missing(db, 't', 'extra', 'extra INTEGER')
db.commit()
_ok("idempotent (재호출 OK)", True)
db.close()
os.unlink(tmp.name)


# ── [6] init_db 호환 — DB 비었을 때 모든 테이블 생성 ─────────────────────
print('\n[6] init_db — SQLite 회귀 (모든 테이블 생성 + bootstrap admin)')
tmp2 = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp2.close()
os.environ['PATHWAVE_DB'] = tmp2.name
os.environ['BOOTSTRAP_SUPER_ADMIN_EMAIL'] = 'init@adapter.test'
os.environ['BOOTSTRAP_SUPER_ADMIN_PASSWORD'] = 'AdminPass1!'

# 모듈 다시 import — DB_PATH 가 환경에 의존하지 않으므로 patched_get_db 로 우회
_dbmod.get_db = _patched_get_db

# init_db 호출 (내부적으로 db.executescript + bootstrap)
_dbmod.init_db()

# 테이블 존재 확인 (대표 몇 개)
db = _patched_get_db()
tables = {r['name'] for r in db.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()}
expected = {
    'users', 'facilities', 'beacons', 'consents', 'policies',
    'super_admin_accounts', 'invitations',
}
missing = expected - tables
_ok(f"필수 테이블 모두 존재 (missing={missing})", not missing)

# Super admin bootstrap 동작
admin_count = db.execute("SELECT COUNT(*) AS n FROM super_admin_accounts").fetchone()['n']
_ok(f"super admin 1명 부트스트랩됨 (got {admin_count})", admin_count == 1)
db.close()
os.unlink(tmp2.name)


print('\n✅ 모든 시나리오 통과')
