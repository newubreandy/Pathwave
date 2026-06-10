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

# ── 1차 무제한 정책 (사용자 결정 2026-06-08) ────────────────────────────────
# 푸시 인프라(FCM/APNs) 비용은 0 이므로 1차 출시는 quota 한도 미적용.
# 등급별 한도 정책은 2차에서 도입 (notification_plans 테이블 + 어드민 CRUD).
# ``_UNLIMITED_P1=True`` 가 켜져 있으면 모든 발송이 quota 검증을 우회한다.
# 2차 활성화 시 이 플래그를 False 로 변경하고 아래 원본 로직이 다시 동작한다.
# ────────────────────────────────────────────────────────────────────────────
_UNLIMITED_P1 = True

# UI 가 _UNLIMITED_P1 일 때 표시할 큰 가용량 상수.
_UNLIMITED_DISPLAY = 999_999


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def get_available_quota(db, account_id: int) -> int:
    """발송 가능한 총 quota 잔량 (미만료 row 합계).

    1차 무제한 정책이 활성이면 항상 큰 값 반환.
    """
    if _UNLIMITED_P1:
        return _UNLIMITED_DISPLAY
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

    1차 무제한 정책이 활성이면 차감 없이 무조건 True 반환.
    """
    if amount <= 0:
        return True
    if _UNLIMITED_P1:
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
    if _UNLIMITED_P1:
        return {
            'purchased': 0,
            'used':      0,
            'available': _UNLIMITED_DISPLAY,
            'expired':   0,
            'unlimited': True,
        }
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
