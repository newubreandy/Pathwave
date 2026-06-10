"""Feature Flag 시스템 (2026-06-08).

설계
----
- DB ``feature_flags`` 테이블에 row 가 있으면 그 값을 사용.
- row 가 없으면 ``DEFAULT_FLAGS`` 의 default 값을 사용.
- 5분 인메모리 캐시 — 어드민 변경 시 ``invalidate_cache()`` 호출 필요.

사용 예
------
1) 라우트 데코레이터:
    @feature_required('chat')
    @auth_bp.route('/api/chat/...')
    def chat_endpoint(): ...

2) 코드 분기:
    if is_enabled('store_payment'):
        ...

3) 클라이언트 응답:
    GET /api/me/features → { features: { wifi_roaming: true, ... } }

모듈 키 정책 (사용자 SOW v1.3):
- 1차 활성(12): wifi_roaming · beacon · stamp · coupon · chat · chat_translate
  · menu_translate · menu_ocr_device · push · email_notify
  · subscription_payment_toss · season_theme
- 1차 비활성(6 — 2차 활성 후보): store_payment · payment_zeropay
  · alipay_wechat · tax_refund · ai_chatbot · social_auto_post
  · voice_call_ai · crm_ads_auto · woorichat_translate_proxy
"""
from __future__ import annotations

import time
from functools import wraps
from typing import Callable

from flask import jsonify

from models.database import get_db


# ── DEFAULT 모듈 키 ───────────────────────────────────────────────────────────
# True = 1차 출시 활성. False = 2차 협의 후 활성.
DEFAULT_FLAGS: dict[str, bool] = {
    # 1차 활성 (12)
    'wifi_roaming':              True,
    'beacon':                    True,
    'stamp':                     True,
    'coupon':                    True,
    'chat':                      True,
    'chat_translate':            True,
    'menu_translate':            True,
    'menu_ocr_device':           True,
    'push':                      True,
    'email_notify':              True,
    'subscription_payment_toss': True,
    'season_theme':              True,
    # 1차 비활성 (코드 골격만, 2차 협의 후 활성)
    'store_payment':             False,
    'payment_zeropay':           False,
    'alipay_wechat':             False,
    'tax_refund':                False,
    'ai_chatbot':                False,
    'social_auto_post':          False,
    'voice_call_ai':             False,
    'crm_ads_auto':              False,
    'woorichat_translate_proxy': False,
    # P18·P19 (Phase 1 W1 WiFi 로밍 — flag 로 v1 비공개)
    'wifi_credential_managed':   False,  # P18 — credential_mode managed 정책 자동 전파
    'wifi_units_grant':          False,  # P19 — units/grant 호실/자리 시간제 권한 UI
    # IA 감사 2026-06-09 — UI 메뉴 가림 전용 flag (P2 이관 도메인)
    'admin_extra_tools':         False,  # admin LNB 부가 운영툴 5종 (StaffMonitor/ChatMonitor/CouponStats/SupportStats/CostMonitor)
    'parent_invite':             False,  # mobile 자녀 초대 메뉴 (유흥·숙박 P2 서비스 제공 시 활성)
}


# ── 인메모리 캐시 ────────────────────────────────────────────────────────────
_CACHE_TTL_SEC = 5 * 60
_cache: dict[str, bool] | None = None
_cache_ts: float = 0.0


def invalidate_cache() -> None:
    """어드민에서 flag 변경 시 호출. 다음 조회 때 DB 재로드."""
    global _cache, _cache_ts
    _cache = None
    _cache_ts = 0.0


def _load() -> dict[str, bool]:
    """DB row 가 있으면 덮어쓰기, 없으면 DEFAULT_FLAGS 그대로."""
    global _cache, _cache_ts
    now = time.time()
    if _cache is not None and (now - _cache_ts) < _CACHE_TTL_SEC:
        return _cache
    merged = dict(DEFAULT_FLAGS)
    try:
        db = get_db()
        rows = db.execute('SELECT key, enabled FROM feature_flags').fetchall()
        db.close()
        for r in rows:
            merged[str(r['key'])] = bool(r['enabled'])
    except Exception:
        # DB 미초기화/연결 실패 — DEFAULT 만 사용.
        pass
    _cache = merged
    _cache_ts = now
    return merged


def is_enabled(key: str) -> bool:
    """모듈 활성 여부."""
    return bool(_load().get(key, False))


def list_features() -> dict[str, bool]:
    """전체 모듈 키 → 활성 여부 매핑 (DEFAULT + DB override)."""
    return dict(_load())


def set_feature(key: str, enabled: bool, *, updated_by: int | None = None) -> None:
    """어드민용 — 모듈 ON/OFF 설정. DB UPSERT + 캐시 무효화."""
    db = get_db()
    db.execute(
        """INSERT INTO feature_flags (key, enabled, updated_by, updated_at)
           VALUES (?, ?, ?, datetime('now'))
           ON CONFLICT(key) DO UPDATE SET
             enabled=excluded.enabled,
             updated_by=excluded.updated_by,
             updated_at=excluded.updated_at""",
        (key, 1 if enabled else 0, updated_by)
    )
    db.commit()
    db.close()
    invalidate_cache()


# ── 라우트 데코레이터 ────────────────────────────────────────────────────────
def feature_required(key: str) -> Callable:
    """라우트에 적용 — 비활성 모듈은 403 응답.

    @feature_required('chat')
    @chat_bp.route('/api/chat/...')
    def my_route(): ...
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not is_enabled(key):
                return jsonify({
                    'success': False,
                    'message': f'기능 비활성: {key}',
                    'feature': key,
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
