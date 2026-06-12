"""알림 예약 발송 스케줄러 (출시 1단계 잔여 #2 — 2026-06-12).

배경
----
notifications.status='pending' 은 "스케줄러가 시각 도래 시 dispatch" 가
설계(routes/notification.py 모듈 docstring)였으나 실체가 없던 갭.
예약 알림이 영원히 pending 으로 남았다.

동작
----
- 데몬 스레드 1개가 POLL_SEC 주기로 도래분을 조회 → routes.notification._dispatch.
- _dispatch 가 quota 차감 / recipients 등록 / push / status='sent' 전부 처리
  (실패 시 status 보존 + 다음 틱 재시도 — unpaid 전환 등은 _dispatch 내부 정책).

시간 비교
--------
scheduled_at 은 UTC naive ISO("2026-06-12T07:00:00", create 라우트가
utcnow 기준 검증·변환 후 저장). sqlite datetime('now') 도 UTC 이지만
공백 구분자라 문자열 비교가 깨지므로 datetime(scheduled_at) 으로 정규화 비교.

배포 전제
--------
단일 프로세스 전제 (app.py 직접 실행). gunicorn 다중 워커 / 다중 인스턴스로
가면 워커마다 스레드가 떠 중복 발송 위험 — 그 단계에서는 이 모듈을 끄고
cron(또는 celery beat) 단일 잡으로 _tick() 을 호출하도록 전환할 것.
"""
import threading
import time
import traceback

POLL_SEC = 30
_started = False


def _tick() -> int:
    """도래한 pending 예약을 일괄 발송. 발송 시도 건수 반환."""
    # 순환 import 회피 — app 초기화 완료 후 런타임 import.
    from models.database import get_db
    from routes.notification import _dispatch

    db = get_db()
    try:
        rows = db.execute(
            """SELECT id FROM notifications
                WHERE status='pending'
                  AND scheduled_at IS NOT NULL
                  AND datetime(scheduled_at) <= datetime('now')
                ORDER BY datetime(scheduled_at) ASC
                LIMIT 20"""
        ).fetchall()
        for r in rows:
            try:
                ok, status, err = _dispatch(db, r['id'])
                # _dispatch 는 commit 을 호출자에 위임 (라우트와 동일 계약) —
                # 건별 즉시 commit (한 건 실패가 앞선 발송을 롤백하지 않도록).
                db.commit()
                print(f"[notif-scheduler] id={r['id']} → "
                      f"{'sent' if ok else status}{f' ({err})' if err else ''}")
            except Exception:
                db.rollback()
                traceback.print_exc()
        return len(rows)
    finally:
        db.close()


def start() -> None:
    """데몬 폴링 스레드 기동 (중복 호출 안전)."""
    global _started
    if _started:
        return
    _started = True

    def _loop():
        while True:
            try:
                _tick()
            except Exception:
                traceback.print_exc()
            time.sleep(POLL_SEC)

    threading.Thread(target=_loop, daemon=True, name='notif-scheduler').start()
    print(f'[notif-scheduler] started (poll {POLL_SEC}s)')
