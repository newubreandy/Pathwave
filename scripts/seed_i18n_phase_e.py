"""Phase E — 알림/쿠폰사용/채팅 도메인 compliance 텍스트 i18n 시드 (ko only).

memory 의 ui_legal_compliance 화면별 안내 매트릭스를 기반으로 키 도출.
한국어만 입력 → 22개 언어는 admin-web "🌐 자동 번역 22개" 버튼으로 채움.

idempotent — 같은 (key, lang) 은 update.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, init_db


# (key, ko) 만. en/22개 언어는 admin-web 자동 번역으로.
SEED_KEYS: list[tuple[str, str]] = [
    # ── 알림 도메인 ─────────────────────────────────────────
    ('notif.permission_title',       '알림 권한이 필요합니다'),
    ('notif.permission_body',
     '스탬프 적립, 쿠폰 발급, 매장 공지를 놓치지 않으려면 알림 권한을 허용해 주세요.'),
    ('notif.permission_required_label',
     '필수 알림 (스탬프/쿠폰/시스템 공지)'),
    ('notif.permission_marketing_label',
     '마케팅 알림 (이벤트/할인 안내)'),
    ('notif.permission_marketing_hint',
     '마케팅 알림은 선택입니다. 동의하지 않아도 서비스 이용에 제한이 없습니다.'),
    ('notif.permission_allow',       '허용하기'),
    ('notif.permission_skip',        '나중에'),
    ('notif.inbox_title',            '알림'),
    ('notif.inbox_personal_tab',     '인박스'),
    ('notif.inbox_system_tab',       '공지'),
    ('notif.inbox_empty_personal',
     '받은 알림이 없습니다. 매장 방문 시 스탬프/쿠폰 알림이 표시됩니다.'),
    ('notif.inbox_empty_system',     '시스템 공지가 없습니다.'),
    ('notif.marketing_disclaimer',
     '본 알림은 마케팅 정보입니다. 수신 거부는 설정 > 알림 동의에서 가능합니다.'),

    # provider/admin 발송
    ('notif.send_title',             '알림 발송'),
    ('notif.send_kind_general',      '일반 알림 (필수 동의 사용자 전체)'),
    ('notif.send_kind_marketing',    '마케팅 알림 (별도 동의자만)'),
    ('notif.send_kind_warning',
     '⚠️ 마케팅 동의를 하지 않은 사용자에게 발송되지 않습니다. 정보통신망법 준수.'),

    # ── 쿠폰사용 도메인 ────────────────────────────────────
    ('coupon.use_title',             '쿠폰 사용'),
    ('coupon.use_confirm',           '이 쿠폰을 사용하시겠습니까?'),
    ('coupon.use_btn',               '사용하기'),
    ('coupon.used_label',            '사용 완료'),
    ('coupon.terms_title',           '쿠폰 사용 안내'),
    ('coupon.terms_condition',
     '• 본 쿠폰은 발급 매장에서만 사용 가능합니다.'),
    ('coupon.terms_expiry',
     '• 유효기간 내에만 사용 가능하며, 만료 시 자동 소멸됩니다.'),
    ('coupon.terms_exclusion',
     '• 일부 메뉴/상품 (주류·담배 등 법정 제외 품목) 은 사용이 제한될 수 있습니다.'),
    ('coupon.terms_transfer',
     '• 본 쿠폰은 양도/현금 환불이 불가합니다.'),
    ('coupon.terms_dispute',
     '• 사용 거부/오류는 발급 매장에 직접 문의해 주세요. PathWave 는 매장-사용자 간 분쟁의 당사자가 아닙니다.'),
    ('coupon.expires_at_label',      '유효기간'),
    ('coupon.facility_only_label',   '사용 가능 매장'),

    # provider 사용 처리
    ('coupon.staff_use_title',       '고객 쿠폰 사용 처리'),
    ('coupon.staff_use_btn',         '사용 처리'),
    ('coupon.staff_use_warning',
     '실제 매장에서 혜택을 제공한 후에만 사용 처리해 주세요. 처리 후에는 되돌릴 수 없습니다.'),

    # admin 통계
    ('coupon.admin_stats_title',     '쿠폰 통계'),
    ('coupon.admin_stats_issued',    '발급'),
    ('coupon.admin_stats_used',      '사용'),
    ('coupon.admin_stats_expired',   '만료'),

    # ── 채팅 도메인 ────────────────────────────────────────
    ('chat.guideline_title',         '채팅 이용 안내'),
    ('chat.guideline_business_hours',
     '운영자 응답은 매장 영업시간 내에 진행됩니다. 영업시간 외 문의는 다음 영업일에 처리됩니다.'),
    ('chat.guideline_no_spam',
     '욕설/광고/스팸 메시지는 운영자가 차단할 수 있습니다.'),
    ('chat.guideline_privacy',
     '카드번호, 비밀번호 등 민감 정보는 채팅으로 보내지 마세요.'),
    ('chat.guideline_dispute',
     '결제/환불 분쟁은 매장 또는 결제대행사(PG)에 문의해야 신속 처리됩니다.'),

    # admin 모니터링
    ('chat.admin_monitor_title',     '채팅 모니터링'),
    ('chat.admin_monitor_hint',
     '욕설/광고/스팸 신고가 들어온 방을 우선 확인하고, 필요 시 사용자 차단 또는 매장 안내를 발송합니다.'),
]


def seed() -> None:
    init_db()
    db = get_db()

    inserted, updated = 0, 0
    for key, ko in SEED_KEYS:
        row = db.execute(
            "SELECT id FROM translations WHERE key=? AND lang='ko'", (key,)
        ).fetchone()
        if row:
            db.execute(
                """UPDATE translations
                   SET value=?, source='seed', verified=1,
                       updated_at=datetime('now')
                   WHERE id=?""",
                (ko, row['id'])
            )
            updated += 1
        else:
            db.execute(
                """INSERT INTO translations (key, lang, value, source, verified)
                   VALUES (?, 'ko', ?, 'seed', 1)""",
                (key, ko)
            )
            inserted += 1
    db.commit()
    db.close()

    print('Phase E i18n compliance 시드 완료:')
    print(f'  keys           : {len(SEED_KEYS)}')
    print(f'  inserted (ko)  : {inserted}')
    print(f'  updated  (ko)  : {updated}')
    print(f'  남은 22개 언어 : admin-web "🌐 자동 번역 22개" 버튼으로 채우기')


if __name__ == '__main__':
    seed()
