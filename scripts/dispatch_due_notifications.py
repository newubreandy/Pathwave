#!/usr/bin/env python3
"""P11 — 예약된 알림 자동 배치 발송 스크립트.

조건
----
- ``status='pending'``
- ``scheduled_at IS NOT NULL AND scheduled_at <= now()``
- 한 번 실행에 최대 ``NOTIFICATION_DISPATCH_BATCH`` 건 (기본 500)

권장 cron (운영 서버):
    */5 * * * * cd /path/to/pathwave && \\
        venv/bin/python scripts/dispatch_due_notifications.py \\
        >> /var/log/pathwave/dispatch.log 2>&1

또는 systemd timer (5분 간격) — 자세한 설치 안내는 docs/ops/scheduler.md (별도).

호출 방식
--------
- 단일 실행: ``python scripts/dispatch_due_notifications.py``
- 모듈 호출: ``from scripts.dispatch_due_notifications import dispatch_due``

출력
----
JSON 한 줄 — ``{now, processed, sent, failed, errors[]}``
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime

# 스크립트가 어디서 실행되든 프로젝트 루트를 sys.path 에 추가
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from models.database import get_db              # noqa: E402
from routes.notification import _dispatch       # noqa: E402


_log = logging.getLogger('dispatch_due_notifications')

DEFAULT_BATCH = 500


def dispatch_due(*, now_iso: str | None = None,
                 batch_limit: int | None = None) -> dict:
    """발송 대상 알림을 배치 처리.

    Parameters
    ----------
    now_iso
        기준 시각 (테스트 주입용). None 이면 ``datetime.utcnow()``.
    batch_limit
        1회 실행 최대 처리 수. None 이면 ``NOTIFICATION_DISPATCH_BATCH`` env
        또는 ``DEFAULT_BATCH``(500).

    Returns
    -------
    {now, processed, sent, failed, errors}
    """
    if now_iso is None:
        now_iso = datetime.utcnow().isoformat()
    if batch_limit is None:
        try:
            batch_limit = int(
                os.environ.get('NOTIFICATION_DISPATCH_BATCH', DEFAULT_BATCH)
            )
        except ValueError:
            batch_limit = DEFAULT_BATCH

    db = get_db()
    rows = db.execute(
        """SELECT id FROM notifications
           WHERE status='pending'
             AND scheduled_at IS NOT NULL
             AND scheduled_at <= ?
           ORDER BY scheduled_at ASC, id ASC
           LIMIT ?""",
        (now_iso, batch_limit)
    ).fetchall()

    processed = sent = failed = 0
    errors: list[dict] = []
    for r in rows:
        nid = r['id']
        try:
            ok, new_status, err = _dispatch(db, nid, force=False)
            db.commit()
            processed += 1
            if ok:
                sent += 1
                _log.info('[dispatch] nid=%s → sent', nid)
            else:
                failed += 1
                errors.append({'nid': nid, 'status': new_status, 'error': err})
                _log.warning('[dispatch] nid=%s → %s (%s)', nid, new_status, err)
        except Exception as e:
            try:
                db.rollback()
            except Exception:
                pass
            failed += 1
            errors.append({'nid': nid, 'error': repr(e)})
            _log.exception('[dispatch] nid=%s 예외', nid)

    db.close()
    return {
        'now':       now_iso,
        'processed': processed,
        'sent':      sent,
        'failed':    failed,
        'errors':    errors,
    }


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(message)s',
    )
    result = dispatch_due()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # 일부 실패가 있어도 cron 은 정상 종료(0). 치명적 오류만 비-0.
    return 0


if __name__ == '__main__':
    sys.exit(main())
