"""P11 — 알림(푸시) quota 조회/차감 헬퍼.

결제 단위로 ``notification_quota`` row 가 누적된다 (감사 추적용).
유효 quota = 만료 안 됨 + 잔량 있음. 차감은 만료가 가까운 row 부터 (FIFO).

사용
---
    from services.notification_quota import (
        get_available_quota, consume_quota, quota_summary,
    )
    available = get_available_quota(db, account_id)
    if available >= needed:
        consume_quota(db, account_id, amount=needed)
"""
from datetime import datetime


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def get_available_quota(db, account_id: int) -> int:
    """발송 가능한 총 quota 잔량 (미만료 row 합계).

    Returns
    -------
    int — 0 이상.
    """
    row = db.execute(
        """SELECT COALESCE(SUM(quantity_purchased - quantity_used), 0) AS rem
           FROM notification_quota
           WHERE facility_account_id=?
             AND quantity_purchased > quantity_used
             AND (expires_at IS NULL OR expires_at > datetime('now'))""",
        (account_id,)
    ).fetchone()
    return int(row['rem'] or 0)


def consume_quota(db, account_id: int, amount: int = 1) -> bool:
    """quota ``amount`` 차감. 부족하면 False (변경 X), 성공하면 True.

    만료가 가까운(``expires_at ASC``) row 부터 차감 (FIFO).
    호출자가 별도 commit 책임.
    """
    if amount <= 0:
        return True
    if get_available_quota(db, account_id) < amount:
        return False

    rows = db.execute(
        """SELECT id, quantity_purchased - quantity_used AS rem
           FROM notification_quota
           WHERE facility_account_id=?
             AND quantity_purchased > quantity_used
             AND (expires_at IS NULL OR expires_at > datetime('now'))
           ORDER BY expires_at ASC, id ASC""",
        (account_id,)
    ).fetchall()

    need = amount
    for r in rows:
        if need <= 0:
            break
        take = min(int(r['rem']), need)
        if take <= 0:
            continue
        db.execute(
            """UPDATE notification_quota
                 SET quantity_used = quantity_used + ?
               WHERE id=?""",
            (take, r['id'])
        )
        need -= take
    return need == 0


def quota_summary(db, account_id: int) -> dict:
    """UI 표시용 quota 통계.

    Returns
    -------
    {
      'purchased': int,   # 누적 결제 수량
      'used':      int,   # 누적 사용
      'available': int,   # 지금 발송 가능 (미만료 + 잔량)
      'expired':   int,   # 만료된 미사용분
    }
    """
    rows = db.execute(
        """SELECT quantity_purchased, quantity_used, expires_at
           FROM notification_quota WHERE facility_account_id=?""",
        (account_id,)
    ).fetchall()
    now = _now_iso()
    purchased = used = available = expired = 0
    for r in rows:
        qp = int(r['quantity_purchased'] or 0)
        qu = int(r['quantity_used'] or 0)
        purchased += qp
        used      += qu
        rem = qp - qu
        if rem <= 0:
            continue
        if r['expires_at'] and r['expires_at'] <= now:
            expired += rem
        else:
            available += rem
    return {
        'purchased': purchased,
        'used':      used,
        'available': available,
        'expired':   expired,
    }
