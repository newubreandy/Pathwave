"""Phase G — 결제 / 구독 / 직원 도메인 i18n 시드 (ko only).

memory 의 ui_legal_compliance + 출시 외부 서비스 정책 (PG=sim/toss 추상화) 기반.
한국어만 입력 → 22 언어는 admin-web 자동 번역 위임.

idempotent.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, init_db


SEED_KEYS: list[tuple[str, str]] = [
    # ── 결제 (billing.*) ─────────────────────────────────
    ('billing.title',                '결제 관리'),
    ('billing.cards_title',          '결제 수단'),
    ('billing.card_add',             '카드 추가'),
    ('billing.card_empty',           '등록된 결제 수단이 없습니다.'),
    ('billing.payments_title',       '결제 내역'),
    ('billing.payments_empty',       '결제 내역이 없습니다.'),
    ('billing.pg_label',             '결제대행사 (PG)'),
    ('billing.pg_sim',               '시뮬레이션 (sim) — 개발/테스트 환경'),
    ('billing.pg_toss',              '토스페이먼츠 (toss) — 운영 환경'),
    ('billing.pg_info_title',        '결제대행사 정보'),
    ('billing.pg_info_body',
     'PathWave 의 결제 처리는 등록된 PG 사를 통해 안전하게 진행됩니다. 카드 정보는 PathWave 서버에 저장되지 않습니다.'),
    ('billing.autopay_consent_title','자동결제 동의'),
    ('billing.autopay_consent_body',
     '구독 결제 시 등록된 카드로 매월 자동 결제됩니다. 동의 후 언제든지 해지 가능합니다.'),
    ('billing.refund_policy_title',  '환불 정책'),
    ('billing.refund_policy_1',
     '• 구독 결제 후 7일 이내 미사용 시 전액 환불 가능합니다.'),
    ('billing.refund_policy_2',
     '• 7일 경과 또는 서비스 이용 후에는 일할 계산 환불 또는 환불 불가입니다 (이용 약관에 따름).'),
    ('billing.refund_policy_3',
     '• 환불 요청은 결제 내역에서 직접 진행하거나 support@pathwave.co.kr 로 문의해 주세요.'),
    ('billing.receipt_label',        '영수증 이메일'),
    ('billing.amount_label',         '결제 금액'),
    ('billing.vat_label',            '부가세 (VAT 10%)'),
    ('billing.total_label',          '합계 (부가세 포함)'),
    ('billing.compliance_warning',
     '⚠️ 부가세 별도 표시는 전자상거래법 위반입니다. 모든 금액은 부가세 포함 가격으로 표시됩니다.'),

    # ── 구독 (subscription.*) ────────────────────────────
    ('subscription.title',           '구독 플랜'),
    ('subscription.active',          '활성 구독'),
    ('subscription.expired',         '만료'),
    ('subscription.canceled',        '해지됨'),
    ('subscription.plan_wifi',       'WiFi 자동 연결'),
    ('subscription.plan_event',      '이벤트 알림'),
    ('subscription.plan_notification','매장 알림 발송'),
    ('subscription.period_monthly',  '월간'),
    ('subscription.period_yearly',   '연간 (2개월 무료)'),
    ('subscription.start_at',        '시작일'),
    ('subscription.end_at',          '만료일'),
    ('subscription.cancel_btn',      '구독 해지'),
    ('subscription.cancel_confirm',
     '구독을 해지하시겠습니까? 현재 결제 주기까지는 계속 이용 가능합니다.'),
    ('subscription.cancel_warning',
     '⚠️ 해지 후에는 자동 갱신되지 않으며, 만료일 후 매장 서비스가 중단됩니다.'),
    ('subscription.renewal_notice',
     '자동 갱신 7일 전 이메일로 안내됩니다. 갱신 원치 않으면 미리 해지해 주세요.'),
    ('subscription.compliance_terms',
     '구독 결제는 자동결제 동의 + 정기결제 약관 동의 후에만 진행됩니다.'),

    # ── 직원 관리 (staff_mgmt.*) ──────────────────────────
    ('staff_mgmt.title',             '직원 관리'),
    ('staff_mgmt.invite_btn',        '직원 초대'),
    ('staff_mgmt.invite_email_label','초대할 직원 이메일'),
    ('staff_mgmt.role_label',        '권한'),
    ('staff_mgmt.role_admin',
     'admin (매장 운영) — 정책 수정, 직원 초대, 결제 정보 접근'),
    ('staff_mgmt.role_staff',
     'staff (제한) — 스탬프/쿠폰 처리, 채팅 응대만 가능'),
    ('staff_mgmt.invite_expires',    '초대 만료 (시간)'),
    ('staff_mgmt.invite_expires_hint','기본 168시간 (7일). 만료 후 재발급 필요.'),
    ('staff_mgmt.invite_sent',       '초대 이메일이 발송되었습니다.'),
    ('staff_mgmt.invite_resend',     '재발송'),
    ('staff_mgmt.invite_revoke',     '초대 취소'),
    ('staff_mgmt.status_pending',    '수락 대기'),
    ('staff_mgmt.status_accepted',   '활성'),
    ('staff_mgmt.status_expired',    '만료'),
    ('staff_mgmt.status_revoked',    '취소됨'),
    ('staff_mgmt.compliance_title',  '직원 권한 안내'),
    ('staff_mgmt.compliance_1',
     '• 초대된 직원은 사장님 매장 1곳에만 접근 가능합니다 (1계정 1매장 정책).'),
    ('staff_mgmt.compliance_2',
     '• admin 권한 직원은 결제 정보를 볼 수 있으니 신중히 부여해 주세요.'),
    ('staff_mgmt.compliance_3',
     '• 직원 행동에 대한 책임은 매장 사장에게 있습니다.'),

    # admin 모니터링
    ('staff_mgmt.admin_monitor_title','직원 활동 모니터링'),
    ('staff_mgmt.admin_monitor_hint',
     '의심 활동(쿠폰 대량 사용 처리, 새벽 시간 채팅 등)이 감지되면 매장 사장에게 알림이 전송됩니다.'),
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

    print('Phase G 결제/구독/직원 i18n 시드 완료:')
    print(f'  keys           : {len(SEED_KEYS)}')
    print(f'  inserted (ko)  : {inserted}')
    print(f'  updated  (ko)  : {updated}')


if __name__ == '__main__':
    seed()
