"""Phase I — 고객센터(support) 화면 i18n 시드 (ko only).

대상 파일:
  mobile/lib/screens/support/support_screen.dart

Dart 코드는 이미 전부 context.t() 래핑 완료 — DB 시드만 누락됐던 상태.
한국어만 입력 → 22개 언어는 admin-web "자동 번역" 버튼으로 채움.

idempotent.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, init_db


SEED_KEYS: list[tuple[str, str]] = [
    # ── 공통 (mobile.common.*) ───────────────────────────────────────────
    ('mobile.common.unselected',                        '선택 안 함'),
    ('mobile.common.change',                            '변경'),
    ('mobile.common.submit',                            '제출하기'),

    # ── 고객센터 탭/타이틀 (mobile.support.*) ────────────────────────────
    ('mobile.support.title',                            '고객센터'),
    ('mobile.support.tab_my_tickets',                   '내 문의'),
    ('mobile.support.tab_report',                       '신고하기'),

    # ── FAQ 탭 ────────────────────────────────────────────────────────────
    ('mobile.support.faq_search_hint',                  'FAQ 검색'),
    ('mobile.support.business_hours_faq',
     '영업시간 평일 09:00–18:00 · 주말·공휴일 제외\n평균 응답시간 1–2 영업일'),
    ('mobile.support.faq_load_failed',                  'FAQ를 불러오지 못했습니다.'),
    ('mobile.support.faq_empty',                        'FAQ가 없습니다.'),
    ('mobile.support.search_empty',                     '검색 결과가 없습니다.'),
    ('mobile.support.search_empty_hint',                '다른 키워드로 검색해 보세요.'),

    # ── FAQ 카테고리 라벨 ─────────────────────────────────────────────────
    ('mobile.support.cat_usage',                        '서비스 이용'),
    ('mobile.support.cat_beacon',                       '비콘 / WiFi'),
    ('mobile.support.cat_coupon',                       '쿠폰'),
    ('mobile.support.cat_payment',                      '결제'),
    ('mobile.support.cat_etc',                          '기타'),

    # ── 내 문의 탭 ────────────────────────────────────────────────────────
    ('mobile.support.business_hours_ticket',
     '영업시간 평일 09:00–18:00 · 평균 응답시간 1–2 영업일'),
    ('mobile.support.compose',                          '문의 작성'),
    ('mobile.support.ticket_load_failed',               '문의 내역을 불러오지 못했습니다.'),
    ('mobile.support.ticket_empty',                     '문의 내역이 없습니다.'),
    ('mobile.support.ticket_empty_hint',
     '궁금한 점이 있으시면 우측 하단 + 버튼으로 문의를 남겨주세요.'),
    ('mobile.support.ticket_default_subject',           '문의'),

    # ── 문의 상태 칩 ─────────────────────────────────────────────────────
    ('mobile.support.status_open',                      '접수됨'),
    ('mobile.support.status_in_progress',               '처리중'),
    ('mobile.support.status_closed',                    '완료'),

    # ── 문의 작성 시트 ────────────────────────────────────────────────────
    ('mobile.support.category_label',                   '카테고리 (선택)'),
    ('mobile.support.subject_label',                    '제목'),
    ('mobile.support.subject_hint',                     '문의 제목을 입력하세요'),
    ('mobile.support.subject_required',                 '제목을 입력해 주세요'),
    ('mobile.support.body_label',                       '내용'),
    ('mobile.support.body_hint',                        '문의 내용을 상세히 작성해 주세요'),
    ('mobile.support.body_required',                    '내용을 입력해 주세요'),
    ('mobile.support.privacy_notice',
     '개인정보 처리방침에 따라 문의 내용은 상담 처리 목적으로만 사용되며 1년 후 자동 삭제됩니다.'),
    ('mobile.support.submit_failed',                    '제출 실패'),

    # ── 신고하기 탭 ───────────────────────────────────────────────────────
    ('mobile.support.report_notice',
     '※ 허위 신고는 서비스 이용에 제한이 있을 수 있습니다.\n검토 후 7 영업일 이내에 조치합니다.'),
    ('mobile.support.report_target_label',              '신고할 시설'),
    ('mobile.support.facility_search_hint',             '시설명을 검색하세요 (2자 이상)'),
    ('mobile.support.photo_load_failed',                '사진을 불러오지 못했습니다'),
    ('mobile.support.facility_required',                '신고할 시설을 먼저 선택해 주세요.'),
    ('mobile.support.report_received',
     '신고가 접수되었습니다. 검토 후 조치하겠습니다.'),
    ('mobile.support.report_failed',                    '신고 실패'),

    # ── 신고 사유 ─────────────────────────────────────────────────────────
    ('mobile.support.reason_spam',                      '스팸 / 광고'),
    ('mobile.support.reason_abuse',                     '욕설 / 혐오'),
    ('mobile.support.reason_illegal',                   '불법 정보'),
    ('mobile.support.reason_inappropriate',             '부적절한 콘텐츠'),
    ('mobile.support.reason_other',                     '기타'),

    # ── 증빙 사진 + 상세 ─────────────────────────────────────────────────
    ('mobile.support.attachment_label',                 '증빙 사진 (선택, 최대 3장)'),
    ('mobile.support.detail_label',                     '상세 사유 (선택)'),
    ('mobile.support.detail_hint',                      '추가 설명이 있으면 입력해 주세요'),
    ('mobile.support.report_privacy_notice',
     '※ 신고 내용은 「개인정보 보호법」에 따라 처리 목적으로만 사용하며 처리 완료 후 파기됩니다.'),
    ('mobile.support.report_submit',                    '신고 제출'),
    ('mobile.support.add_photo',                        '사진 추가'),

    # ── 시설 확인 다이얼로그 ──────────────────────────────────────────────
    ('mobile.support.confirm_facility_title',           '이 시설이 맞나요?'),
    ('mobile.support.report_this_facility',             '이 시설 신고'),
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

    print('Phase I 고객센터 i18n 시드 완료:')
    print(f'  keys           : {len(SEED_KEYS)}')
    print(f'  inserted (ko)  : {inserted}')
    print(f'  updated  (ko)  : {updated}')


if __name__ == '__main__':
    seed()
