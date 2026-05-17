"""Phase J — 푸터 통일 + 약관 링크 라벨 i18n 시드 (ko only).

memory 의 ui_legal_compliance / brand_strategy / pre_launch_checklist 기반.
3 콘솔(mobile / provider-web / admin-web)이 공통 푸터 키를 사용해서
어드민이 한 번 입력하면 3 콘솔 모두 반영되도록.

idempotent (translations UPSERT).

법인 정보 placeholder 는 그대로 유지 — 법인 등록 후 동일 키 값만 교체하면
3 콘솔 모두 자동 반영됨.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, init_db


# 공통 푸터 키 — 라벨 + placeholder
FOOTER_KEYS: list[tuple[str, str]] = [
    # ── 회사 정보 라벨 / 값 ───────────────────────────
    ('footer.company_name_label',   '상호'),
    ('footer.company_name',         '[법인 등록 후 채워질 예정]'),
    ('footer.ceo_label',            '대표자'),
    ('footer.ceo',                  '[법인 등록 후 채워질 예정]'),
    ('footer.biz_number_label',     '사업자등록번호'),
    ('footer.biz_number',           '[법인 등록 후 채워질 예정]'),
    ('footer.commerce_label',       '통신판매업신고'),
    ('footer.commerce',             '[법인 등록 후 채워질 예정]'),
    ('footer.address_label',        '주소'),
    ('footer.address',              '[법인 등록 후 채워질 예정]'),
    ('footer.phone_label',          '전화'),
    ('footer.phone',                '[법인 등록 후 채워질 예정]'),
    ('footer.email_label',          '이메일'),
    ('footer.email',                'support@pathwave.co.kr'),
    ('footer.hosting_label',        '호스팅 제공자'),
    ('footer.hosting',              '[법인 등록 후 채워질 예정]'),

    # ── 약관/정책 링크 ───────────────────────────────
    ('footer.terms_of_service',     '이용약관'),
    ('footer.privacy_policy',       '개인정보처리방침'),
    ('footer.location_terms',       '위치기반서비스 이용약관'),
    ('footer.marketing_terms',      '마케팅 정보 수신'),
    ('footer.third_party_terms',    '제3자 정보 제공'),

    # ── 도움 링크 ────────────────────────────────────
    ('footer.faq',                  '자주 묻는 질문'),
    ('footer.support',              '고객센터'),
    ('footer.notice_disclaimer',
     '※ PathWave 는 매장 멤버십 플랫폼으로, 매장에서 제공하는 정보·이벤트·혜택의 책임은 등록 업체에 있습니다.'),

    # ── 저작권 ──────────────────────────────────────
    ('footer.copyright',            '© PathWave. All rights reserved.'),

    # ── 정책 뷰어 라벨 (provider-web /policy/:kind, mobile PolicyView) ─
    ('policy.viewer_title',         '약관 보기'),
    ('policy.effective_at_label',   '시행일'),
    ('policy.version_label',        '버전'),
    ('policy.load_failed',          '약관을 불러오지 못했습니다.'),
]


# 마케팅 동의 라벨 (가입 화면 / 설정 화면 공용)
MARKETING_CONSENT_KEYS: list[tuple[str, str]] = [
    ('consent.marketing.title',     '마케팅 정보 수신 동의 (선택)'),
    ('consent.marketing.desc',
     '이벤트·쿠폰·신규 매장 안내를 이메일/푸시로 받습니다. 동의하지 않아도 서비스 이용에 제한이 없습니다.'),
    ('consent.marketing.optional_label', '선택'),
    ('consent.required_label',      '필수'),
    ('consent.legal_notice',
     '정보통신망법 §50 에 따라 마케팅 정보 수신은 별도 동의 후에만 발송됩니다. 언제든지 수신 거부 가능합니다.'),
    ('settings.marketing_toggle',   '마케팅 정보 수신'),
    ('settings.marketing_hint',     '이벤트/쿠폰 안내 푸시·이메일 수신'),
]


# admin-web LNB 그룹 라벨
LNB_GROUP_KEYS: list[tuple[str, str]] = [
    ('nav.group_main',              '메인'),
    ('nav.group_ops',               '운영'),
    ('nav.group_billing',           '결제·정책'),
    ('nav.group_support',           '고객지원'),
    ('nav.group_system',            '시스템'),
]


def upsert_ko(db, key: str, value: str) -> None:
    row = db.execute(
        "SELECT id FROM translations WHERE key=? AND lang='ko'", (key,)
    ).fetchone()
    if row:
        db.execute(
            "UPDATE translations SET value=?, source='seed', verified=1, "
            "updated_at=datetime('now') WHERE id=?",
            (value, row['id'])
        )
    else:
        db.execute(
            "INSERT INTO translations (key, lang, value, verified, source) "
            "VALUES (?, 'ko', ?, 1, 'seed')",
            (key, value)
        )


def main() -> None:
    init_db()  # init_db 에서 _bootstrap_policies 자동 실행됨
    db = get_db()

    for key, value in FOOTER_KEYS:
        upsert_ko(db, key, value)
    for key, value in MARKETING_CONSENT_KEYS:
        upsert_ko(db, key, value)
    for key, value in LNB_GROUP_KEYS:
        upsert_ko(db, key, value)

    db.commit(); db.close()
    print('[seed_phase_j_footer] done. footer/policy/marketing/LNB 키 ko 등록 완료.')


if __name__ == '__main__':
    main()
