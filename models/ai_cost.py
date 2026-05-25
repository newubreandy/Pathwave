"""C-D-4-pre — 외부 AI API 사용량/비용 추적 + 임계점 알림.

PathWave 가 호출하는 외부 유료 API (DeepL/Anthropic/GCV 등) 사용량을
기록하고, 월 누적 비용이 사용자 정의 임계점에 도달하면 슈퍼어드민
알림을 트리거.

핵심 함수
--------
- ``record_usage(db, provider, operation, units, ...)`` — usage 1건 기록
- ``estimate_cost_usd(provider, operation, units)`` — provider 단가표 기반 추정
- ``month_total_usd(db, year, month)`` — 해당 월 누적 비용
- ``compute_alerts(monthly_usd)`` — 임계점 별 알림 객체 산출 (50/80/100%)

가격 단가 (2026-05 기준)
- DeepL Pro:      $25 / 1M chars  → $0.000025 per char
- Anthropic Claude 3.5 Sonnet (입력 + 출력 평균):
                  ~$0.000017 per token  (보수 평균치)
- Google Cloud Vision OCR: $1.5 / 1000 images  (월 첫 1000장 무료)
- SendGrid:       $0 ~ Pro 플랜은 고정 → 사용량 단가 없음 (집계 X)

환률 (네이버 기준 2026-05-25)
- $1 = ₩1,510.20  (env KRW_PER_USD 로 변경 가능)
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional


# ─── 환률 ─────────────────────────────────────────────────────────────────
DEFAULT_KRW_PER_USD = 1510.20


def krw_per_usd() -> float:
    try:
        v = float(os.environ.get('KRW_PER_USD') or DEFAULT_KRW_PER_USD)
        if v > 0:
            return v
    except (TypeError, ValueError):
        pass
    return DEFAULT_KRW_PER_USD


def usd_to_krw(usd: float) -> float:
    return round(usd * krw_per_usd(), 1)


# ─── 임계점 ───────────────────────────────────────────────────────────────
COST_THRESHOLD_USD = float(os.environ.get('AI_COST_THRESHOLD_USD') or 100.0)


def threshold_usd() -> float:
    """월 누적 비용 임계점 (USD). env 로 변경 가능."""
    try:
        v = float(os.environ.get('AI_COST_THRESHOLD_USD') or COST_THRESHOLD_USD)
        if v > 0:
            return v
    except (TypeError, ValueError):
        pass
    return COST_THRESHOLD_USD


# ─── 단가 ─────────────────────────────────────────────────────────────────
# 단위: 1건당 USD.
# provider+operation 별 호출 시 units 와 곱해서 cost_usd 산출.
_PRICING = {
    # DeepL Pro — chars 기반
    ('deepl', 'translate'):         0.000025,
    # Anthropic Claude 3.5 Sonnet — tokens 평균 (input $3/M + output $15/M, 4:1 가정)
    ('anthropic', 'translate'):     0.000017,
    ('anthropic', 'image-analyze'): 0.000017,
    # Google Cloud Vision OCR — image 기반 (월 1000장 무료 — 무료분은 호출 측에서 0 처리)
    ('gcv', 'ocr'):                 0.0015,
    # MyMemory 등 무료 provider
    ('mymemory', 'translate'):      0.0,
    # 기타
    ('stub', 'translate'):          0.0,
    ('stub', 'ocr'):                0.0,
    ('stub', 'image-analyze'):      0.0,
}


def estimate_cost_usd(provider: str, operation: str, units: int) -> float:
    """provider+operation+units 로 추정 비용 (USD) 계산.

    매칭 단가 없으면 0 반환 (안전 default — 호출 측이 명시적으로 override 가능).
    """
    if units <= 0:
        return 0.0
    unit_price = _PRICING.get((provider, operation), 0.0)
    return round(units * unit_price, 6)


# ─── 기록/집계 ────────────────────────────────────────────────────────────
def record_usage(db, *, provider: str, operation: str, units: int,
                 cost_usd: Optional[float] = None,
                 status: str = 'ok',
                 facility_id: Optional[int] = None,
                 user_id: Optional[int] = None,
                 actor_role: Optional[str] = None,
                 commit: bool = True) -> int:
    """ai_usage_logs 에 1건 기록. cost_usd 미명시 시 단가표로 자동 계산.

    @return 새 row id
    """
    if cost_usd is None:
        cost_usd = estimate_cost_usd(provider, operation, units)
    cur = db.execute(
        """INSERT INTO ai_usage_logs
            (provider, operation, units, cost_usd, status,
             facility_id, user_id, actor_role)
           VALUES (?,?,?,?,?,?,?,?)""",
        (provider, operation, units, cost_usd, status,
         facility_id, user_id, actor_role),
    )
    if commit:
        db.commit()
    return cur.lastrowid


def month_window(year: int, month: int) -> tuple[str, str]:
    """해당 월의 [start, next_month_start) ISO 문자열 (UTC)."""
    start = datetime(year, month, 1)
    if month == 12:
        nxt = datetime(year + 1, 1, 1)
    else:
        nxt = datetime(year, month + 1, 1)
    return start.isoformat(), nxt.isoformat()


def month_total_usd(db, year: int, month: int) -> dict:
    """해당 월 누적 비용 + provider 별 합계.

    @return {
        'total_usd':     float,
        'total_krw':     float,
        'by_provider':   {provider: usd, ...},
        'by_operation':  {operation: usd, ...},
        'call_count':    int,
    }
    """
    start, nxt = month_window(year, month)
    rows = db.execute(
        """SELECT provider, operation, COALESCE(SUM(cost_usd), 0) AS s,
                  COUNT(*) AS n
             FROM ai_usage_logs
            WHERE created_at >= ? AND created_at < ?
            GROUP BY provider, operation""",
        (start, nxt),
    ).fetchall()
    total = 0.0
    by_p, by_o = {}, {}
    cnt = 0
    for r in rows:
        s = r['s'] or 0.0
        total += s
        by_p[r['provider']]  = by_p.get(r['provider'], 0.0)  + s
        by_o[r['operation']] = by_o.get(r['operation'], 0.0) + s
        cnt += r['n']
    return {
        'total_usd':    round(total, 4),
        'total_krw':    usd_to_krw(total),
        'by_provider':  {k: round(v, 4) for k, v in by_p.items()},
        'by_operation': {k: round(v, 4) for k, v in by_o.items()},
        'call_count':   cnt,
    }


# ─── 알림 산출 ────────────────────────────────────────────────────────────
def compute_alerts(monthly_usd: float) -> list[dict]:
    """월 누적 USD 기준 활성 알림 목록.

    임계점:
    - 50% — 정보성 배지 (팝업 X)
    - 80% — 팝업 (24h snooze)
    - 100% — 팝업 (2h snooze, critical 스타일) + 번역 호출 차단

    @return [{'id', 'level', 'title', 'body', 'snooze_hours'}, ...]
    """
    th = threshold_usd()
    pct = (monthly_usd / th) * 100 if th > 0 else 0
    alerts = []

    if pct >= 50:
        alerts.append({
            'id':    'cost-50',
            'level': 'info',
            'kind':  'badge',                   # 사이드바 배지만
            'title': '외부 AI 비용 50% 도달',
            'body':  (f'월 사용 ${monthly_usd:.2f} / 임계점 ${th:.0f} '
                      f'({pct:.0f}%). 사용량 추세 확인 권장.'),
            'snooze_hours': None,
        })
    if pct >= 80:
        alerts.append({
            'id':    'cost-80',
            'level': 'warn',
            'kind':  'popup',
            'title': '⚠️ 외부 AI 비용 80% 도달 — AI 서버 전환 PoC 시작 권장',
            'body':  (f'월 사용 ${monthly_usd:.2f} / 임계점 ${th:.0f} ({pct:.0f}%). '
                      f'자체 모델 전환 가이드(docs/translation_cost_runaway_plan.md) 검토.'),
            'snooze_hours': 24,
        })
    if pct >= 100:
        alerts.append({
            'id':    'cost-100',
            'level': 'critical',
            'kind':  'popup',
            'title': '🚨 외부 AI 비용 임계점 초과 — 번역 호출 자동 차단됨',
            'body':  (f'월 사용 ${monthly_usd:.2f} / 임계점 ${th:.0f} ({pct:.0f}%). '
                      f'채팅 자동 번역 일시 중단. 즉시 자체 모델 전환 작업 필요.'),
            'snooze_hours': 2,
        })
    return alerts


def is_translation_blocked(monthly_usd: float) -> bool:
    """월 누적이 100% 초과 시 True — 번역 호출 측이 이 함수로 체크."""
    return monthly_usd >= threshold_usd()
