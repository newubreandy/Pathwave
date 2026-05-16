"""Phase F — 스탬프 적립 + 쿠폰 발급 도메인 i18n 시드 (ko only).

memory 의 ui_legal_compliance 화면별 안내 매트릭스 (스탬프/쿠폰 발급) 기반.
한국어만 입력 → 22개 언어는 admin-web "🌐 자동 번역 22개" 버튼으로 채움.

idempotent.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, init_db


SEED_KEYS: list[tuple[str, str]] = [
    # ── 스탬프 적립 (mobile + provider 공용 안내) ─────────────
    ('stamp.title',                  '스탬프'),
    ('stamp.empty',                  '아직 적립된 스탬프가 없습니다. 매장에서 비콘이 감지되면 자동 적립됩니다.'),
    ('stamp.terms_title',            '스탬프 적립 안내'),
    ('stamp.terms_accrual',
     '• 매장 비콘이 감지되면 매장 정책에 따라 자동 적립됩니다.'),
    ('stamp.terms_cooldown',
     '• 동일 매장에서 정책의 쿨다운 시간(기본 60분) 내 재방문은 1회만 적립됩니다.'),
    ('stamp.terms_expiry',
     '• 적립된 스탬프는 매장 정책의 만료 기간이 지나면 자동 소멸됩니다.'),
    ('stamp.terms_reward',
     '• 임계 적립 수에 도달하면 자동으로 보상 쿠폰이 발급됩니다.'),
    ('stamp.terms_dispute',
     '• 적립 누락은 매장에 직접 문의해 주세요. PathWave 는 매장-사용자 간 분쟁의 당사자가 아닙니다.'),
    ('stamp.expires_at_label',      '만료일'),
    ('stamp.cooldown_label',        '재적립 쿨다운'),
    ('stamp.threshold_label',       '보상 기준 적립 수'),

    # provider 스탬프 정책 폼
    ('stamp.policy_title',           '스탬프 정책'),
    ('stamp.policy_single_active',
     '⚠️ 매장당 활성 정책은 1개 입니다. 새 정책을 저장하면 기존 활성 정책은 자동으로 비활성화됩니다.'),
    ('stamp.policy_auto_label',      'BLE 자동 적립 사용'),
    ('stamp.policy_auto_hint',
     '꺼두면 사장이 직접 사용자별로 수동 적립합니다. 켜면 비콘 감지 시 자동 적립됩니다.'),
    ('stamp.policy_cooldown_hint',
     '동일 사용자가 매장에서 재적립 가능한 최소 간격(분). 기본 60분 권장.'),
    ('stamp.policy_expires_hint',
     '적립 후 N일 뒤 자동 만료. 비워두면 무기한.'),

    # ── 쿠폰 발급 (provider 생성 / mobile 발급 받기) ─────────
    ('coupon_issue.title',           '쿠폰 발급'),
    ('coupon_issue.received',        '발급된 쿠폰이 도착했습니다'),
    ('coupon_issue.terms_title',     '쿠폰 발급 안내'),
    ('coupon_issue.terms_source',
     '• 본 쿠폰은 매장 정책 또는 스탬프 보상으로 발급됩니다.'),
    ('coupon_issue.terms_facility_only',
     '• 사용 가능 매장 / 메뉴 / 시간대는 쿠폰 상세에 표시된 조건에 따릅니다.'),
    ('coupon_issue.terms_expiry',
     '• 유효기간이 지나면 자동 소멸되며, 사용/환불이 불가합니다.'),
    ('coupon_issue.terms_exclusion',
     '• 주류·담배 등 법정 제외 품목은 사용이 제한될 수 있습니다.'),

    # provider 쿠폰 생성 폼
    ('coupon_issue.form_title',      '쿠폰 만들기'),
    ('coupon_issue.form_title_label','쿠폰 이름'),
    ('coupon_issue.form_benefit_label', '혜택 내용'),
    ('coupon_issue.form_validity_label','유효기간 (일)'),
    ('coupon_issue.form_validity_hint',
     '발급일로부터 N일. 비워두면 무기한 — 단, 운영 효율을 위해 30~90일 권장.'),
    ('coupon_issue.form_target_label', '발급 대상'),
    ('coupon_issue.form_target_single','사용자 1명 (수동 발급)'),
    ('coupon_issue.form_target_welcome','첫 방문 환영 자동 발급'),
    ('coupon_issue.form_target_reward','스탬프 임계 도달 시 자동 발급'),
    ('coupon_issue.form_compliance',
     '⚠️ 본 쿠폰의 사용 조건은 매장이 정합니다. 발급 후 조건 변경은 신규 쿠폰으로만 가능합니다.'),
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

    print('Phase F 스탬프/쿠폰발급 i18n 시드 완료:')
    print(f'  keys           : {len(SEED_KEYS)}')
    print(f'  inserted (ko)  : {inserted}')
    print(f'  updated  (ko)  : {updated}')


if __name__ == '__main__':
    seed()
