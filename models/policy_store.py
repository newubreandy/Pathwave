"""정책(policies) DB 조회/저장 헬퍼 + 파일 fallback (PR #45 정적 파일 호환).

DB 가 우선이며, DB 에 해당 (kind, lang) 의 게시된(=effective_at <= now) 항목이
없으면 ``static/policies/<kind>.<lang>.md`` 파일로 fallback.

이렇게 하면 PR #45 의 정적 파일이 그대로 동작하고, 운영자가 admin-web 에서
새 버전을 발행하면 자동으로 DB 본문이 우선됨.
"""
import os
from datetime import datetime


_POLICIES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'static', 'policies'
)


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _read_file(kind: str, lang: str) -> tuple[str, bool]:
    path = os.path.join(_POLICIES_DIR, f'{kind}.{lang}.md')
    if not os.path.isfile(path):
        return '', False
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read(), True
    except Exception:
        return '', False


def get_active(db, kind: str, lang: str = 'ko') -> dict:
    """현재 시점에 시행 중인 가장 최신 정책 1건. DB 미존재 시 파일 fallback."""
    now = _now_iso()
    row = db.execute(
        """SELECT * FROM policies
           WHERE kind=? AND lang=? AND effective_at <= ?
           ORDER BY effective_at DESC, id DESC
           LIMIT 1""",
        (kind, lang, now)
    ).fetchone()
    if row:
        return _row_to_dict(row)

    # DB 미존재 → static 파일 fallback
    body, exists = _read_file(kind, lang)
    if not exists and lang != 'ko':
        body, exists = _read_file(kind, 'ko')
    return {
        'id': None,
        'kind': kind,
        'lang': lang if exists else 'ko',
        'version': 'unspecified',
        'body': body or f'# {kind}\n\n본문은 운영 전 등록 예정입니다. (placeholder)',
        'change_log': None,
        'effective_at': None,
        'created_at': None,
        'email_notified': 0,
        'needs_content': not exists,
        'source': 'static_file' if exists else 'placeholder',
    }


def list_versions(db, kind: str, lang: str = 'ko', *, include_pending: bool = True) -> list[dict]:
    """특정 정책의 모든 버전 (최신순). include_pending=False 면 시행 중/과거만."""
    if include_pending:
        rows = db.execute(
            """SELECT * FROM policies
               WHERE kind=? AND lang=?
               ORDER BY effective_at DESC, id DESC""",
            (kind, lang)
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT * FROM policies
               WHERE kind=? AND lang=? AND effective_at <= ?
               ORDER BY effective_at DESC, id DESC""",
            (kind, lang, _now_iso())
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_by_version(db, kind: str, version: str, lang: str = 'ko') -> dict | None:
    row = db.execute(
        "SELECT * FROM policies WHERE kind=? AND lang=? AND version=?",
        (kind, lang, version)
    ).fetchone()
    return _row_to_dict(row) if row else None


def get_by_id(db, pid: int) -> dict | None:
    row = db.execute("SELECT * FROM policies WHERE id=?", (pid,)).fetchone()
    return _row_to_dict(row) if row else None


def list_all_active_kinds(db, lang: str = 'ko') -> list[dict]:
    """모든 kind 의 현재 시행 중 버전 한 번에 (admin 대시보드용)."""
    from models.consent import VALID_KINDS
    out = []
    for kind in sorted(VALID_KINDS):
        out.append({'kind': kind, **get_active(db, kind, lang)})
    return out


def list_pending(db) -> list[dict]:
    """미시행(effective_at > now) 예약된 정책 목록."""
    rows = db.execute(
        """SELECT * FROM policies
           WHERE effective_at > ?
           ORDER BY effective_at ASC""",
        (_now_iso(),)
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def insert(db, *, kind: str, lang: str, version: str, title: str | None,
           body: str, change_log: str | None, effective_at: str,
           admin_id: int | None) -> int:
    cur = db.execute(
        """INSERT INTO policies
             (kind, lang, version, title, body, change_log,
              effective_at, created_by_admin_id)
           VALUES (?,?,?,?,?,?,?,?)""",
        (kind, lang, version, title, body, change_log, effective_at, admin_id)
    )
    return cur.lastrowid


def update(db, pid: int, *, title: str | None = None, body: str | None = None,
           change_log: str | None = None, effective_at: str | None = None) -> bool:
    fields, vals = [], []
    if title is not None: fields.append('title=?'); vals.append(title)
    if body is not None: fields.append('body=?'); vals.append(body)
    if change_log is not None: fields.append('change_log=?'); vals.append(change_log)
    if effective_at is not None: fields.append('effective_at=?'); vals.append(effective_at)
    if not fields:
        return False
    vals.append(pid)
    db.execute(f"UPDATE policies SET {', '.join(fields)} WHERE id=?", vals)
    return True


def delete(db, pid: int) -> bool:
    cur = db.execute("DELETE FROM policies WHERE id=?", (pid,))
    return cur.rowcount > 0


def mark_email_notified(db, pid: int) -> None:
    db.execute("UPDATE policies SET email_notified=1 WHERE id=?", (pid,))


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _row_to_dict(row) -> dict:
    if row is None:
        return None
    return {
        'id':              row['id'],
        'kind':            row['kind'],
        'lang':            row['lang'],
        'version':         row['version'],
        'title':           row['title'],
        'body':            row['body'],
        'change_log':      row['change_log'],
        'effective_at':    row['effective_at'],
        'created_by_admin_id': row['created_by_admin_id'],
        'created_at':      row['created_at'],
        'email_notified':  bool(row['email_notified']),
    }
