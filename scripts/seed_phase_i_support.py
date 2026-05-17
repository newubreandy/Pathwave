"""Phase I — 고객센터 + FAQ + 신고 도메인 시드 (ko only).

memory 의 콘솔 영향도 매트릭스 + ui_legal_compliance + i18n 글로벌 전략 기반.
한국어만 입력 → 22 언어는 admin-web 자동 번역 위임.

시드 내용
---------
1) support_categories: user(B2C) 5개 + provider(B2B) 5개
2) faqs: user(B2C) 10개 + provider(B2B) 10개 (모두 lang='ko')
3) support_tickets: 샘플 3건 (user 2, provider 1)
4) translations(ko): support.* / faq.* / report.* / admin_support.* / nav.support / nav.faq

idempotent (UNIQUE 충돌 시 skip / 기존 row 갱신).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, init_db


CATEGORIES_USER: list[tuple[str, str, int]] = [
    # (code, label_key, sort_order)
    ('usage',   'support_cat.user.usage',   10),
    ('beacon',  'support_cat.user.beacon',  20),
    ('coupon',  'support_cat.user.coupon',  30),
    ('payment', 'support_cat.user.payment', 40),
    ('etc',     'support_cat.user.etc',     90),
]

CATEGORIES_PROVIDER: list[tuple[str, str, int]] = [
    ('store',     'support_cat.provider.store',     10),
    ('beacon',    'support_cat.provider.beacon',    20),
    ('payment',   'support_cat.provider.payment',   30),
    ('billing',   'support_cat.provider.billing',   40),
    ('staff',     'support_cat.provider.staff',     50),
]

FAQS_USER_KO: list[tuple[str, str, str]] = [
    # (category, question, answer)
    ('usage', 'PathWave 는 어떤 서비스인가요?',
     'PathWave 는 매장 방문 시 비콘 신호를 자동으로 감지해 무료 WiFi 연결, '
     '스탬프 적립, 쿠폰 발급을 한 번에 처리해 주는 매장 멤버십 서비스입니다.'),
    ('usage', '회원가입은 어떻게 하나요?',
     '앱을 처음 실행하면 이메일/소셜 로그인(카카오/네이버/구글/애플) 중 선택해 '
     '간편하게 가입할 수 있습니다. 만 14세 미만은 부모 초대 코드가 필요합니다.'),
    ('beacon', '비콘이 감지되지 않아요.',
     '1) 휴대폰 블루투스가 켜져 있는지 확인해 주세요.\n'
     '2) 앱 설정에서 위치 권한이 "항상 허용" 으로 되어 있는지 확인해 주세요.\n'
     '3) 매장 안에서 다시 한 번 비콘 감지를 시도해 주세요.'),
    ('beacon', 'WiFi 자동 연결이 안 돼요.',
     '비콘이 정상 감지된 뒤 30 초 이내에 자동 연결됩니다. 안 될 경우 매장 입구 근처에서 '
     '한 번 더 시도하거나, 앱에서 수동으로 비밀번호 복사 후 연결할 수 있습니다.'),
    ('coupon', '스탬프는 어떻게 적립하나요?',
     '매장에서 결제 후 직원에게 PathWave 회원이라고 말씀하시면 즉시 적립됩니다. '
     '비콘 자동 적립을 운영하는 매장에서는 방문 시 자동으로 적립됩니다.'),
    ('coupon', '쿠폰은 어디서 확인하나요?',
     '마이페이지 > 내 쿠폰 메뉴에서 보유한 쿠폰과 사용 내역을 확인할 수 있습니다.'),
    ('coupon', '쿠폰을 사용했는데 적용이 안 됐어요.',
     '결제 시 매장 직원에게 쿠폰 화면을 보여 주시면 처리됩니다. 적용 누락 시 매장 영수증과 '
     '쿠폰 번호를 함께 고객센터로 문의해 주세요.'),
    ('payment', '결제는 어디서 진행되나요?',
     'PathWave 는 매장 결제를 대행하지 않습니다. 결제는 매장 POS 또는 카드 단말기에서 '
     '직접 진행되며, PathWave 는 멤버십 혜택(스탬프/쿠폰)만 자동 적용합니다.'),
    ('etc', '탈퇴 후 재가입은 언제 가능한가요?',
     '탈퇴 신청 후 7 일이 지나면 동일한 이메일로 재가입할 수 있습니다.'),
    ('etc', '개인정보는 어떻게 보호되나요?',
     'PathWave 는 개인정보보호법에 따라 회원정보를 암호화하여 저장하며, 위치 정보는 '
     '매장 방문 감지 용도로만 사용됩니다. 자세한 내용은 개인정보처리방침을 확인해 주세요.'),
]

FAQS_PROVIDER_KO: list[tuple[str, str, str]] = [
    ('store',   '매장 등록은 어떻게 하나요?',
     '사장님 콘솔(provider.pathwave.kr) > 매장안내 메뉴에서 매장 정보(상호/주소/영업시간/사진)를 '
     '입력하고 저장합니다. 등록 후 어드민 승인 절차를 거쳐 실제 사용자에게 노출됩니다.'),
    ('store',   '영업시간을 바꾸려면?',
     '매장안내 > 매장 정보 편집에서 영업시간을 수정한 뒤 저장하세요. 변경 사항은 즉시 '
     '사용자 앱에 반영됩니다.'),
    ('beacon',  '비콘은 어디서 받나요?',
     '서비스 신청 > 와이파이 서비스등록 후 PathWave 본사에서 비콘을 발송해 드립니다. '
     '수령 후 매장 코드와 매칭하면 자동으로 활성화됩니다.'),
    ('beacon',  '비콘 배터리는 얼마나 오래 가나요?',
     'FSC-BP108B 모델 기준 약 2 년입니다. 배터리 잔량은 어드민 콘솔에서 모니터링되며, '
     '20 % 이하로 떨어지면 자동으로 교체 안내가 발송됩니다.'),
    ('payment', '결제 PG 사는 어디인가요?',
     '운영 환경에서는 토스페이먼츠를 사용합니다. 개발/테스트 환경에서는 sim 모드로 '
     '실제 결제 없이 흐름을 검증할 수 있습니다.'),
    ('payment', '카드 정보는 안전한가요?',
     '카드 정보는 PathWave 서버에 저장되지 않습니다. PG 사에서 발급한 빌링키만 보관하며, '
     '실제 카드 데이터는 PG 사 PCI-DSS 환경에서 처리됩니다.'),
    ('billing', '정산 주기는 어떻게 되나요?',
     'PathWave 구독료는 월간/연간(2개월 무료) 중 선택할 수 있으며, 자동 결제일 7 일 전 '
     '이메일로 안내됩니다. 구독 해지 시 다음 결제 주기부터 적용됩니다.'),
    ('billing', '세금계산서/현금영수증은?',
     '결제 내역 > 영수증 발급에서 세금계산서/현금영수증을 신청할 수 있습니다. 이메일로 '
     'PDF 가 발송됩니다.'),
    ('staff',   '직원 계정을 추가하려면?',
     '직원 관리 > 직원 초대에서 이메일과 권한(admin/staff)을 입력해 초대 메일을 발송합니다. '
     '초대받은 사람이 링크를 클릭해 비밀번호를 설정하면 즉시 사용할 수 있습니다.'),
    ('staff',   '직원 권한 차이는?',
     'admin 은 정책 수정 + 직원 초대 + 결제 정보 접근까지 가능하고, staff 는 스탬프/쿠폰 '
     '처리 + 채팅 응대만 가능합니다.'),
]


I18N_KEYS_KO: list[tuple[str, str]] = [
    # ─ nav (3 콘솔 공통) ─────────────────────────
    ('nav.support',                 '고객센터'),
    ('nav.faq',                     '자주 묻는 질문'),
    ('nav.support_stats',           '고객센터 통계'),
    ('nav.reports',                 '신고 관리'),

    # ─ support 공통 ──────────────────────────────
    ('support.title',               '고객센터'),
    ('support.subtitle',            '문의 작성 · 진행 상황 확인 · 자주 묻는 질문'),
    ('support.business_hours',      '운영시간: 평일 09:00~18:00 (주말/공휴일 휴무)'),
    ('support.response_time',       '응답 예상 시간: 영업일 1~3일 이내'),
    ('support.privacy_notice',
     '문의 내용에 포함된 개인정보는 상담 처리 목적으로만 사용되며 처리 완료 후 3년간 '
     '보관됩니다. (개인정보보호법 §15·§21)'),
    ('support.new_ticket',          '문의 작성'),
    ('support.my_tickets',          '내 문의 내역'),
    ('support.empty_tickets',       '아직 작성한 문의가 없습니다.'),
    ('support.category_label',      '카테고리'),
    ('support.subject_label',       '제목'),
    ('support.body_label',          '내용'),
    ('support.submit_btn',          '문의 보내기'),
    ('support.status_open',         '답변 대기'),
    ('support.status_replied',      '답변 완료'),
    ('support.status_closed',       '종결'),
    ('support.priority_low',        '낮음'),
    ('support.priority_normal',     '보통'),
    ('support.priority_high',       '높음'),
    ('support.priority_urgent',     '긴급'),
    ('support.thread_title',        '대화 내역'),
    ('support.reply_placeholder',   '답변에 추가 의견이 있으면 입력하세요.'),
    ('support.created_at',          '작성일'),
    ('support.last_reply_at',       '마지막 응답'),
    ('support.create_success',      '문의가 접수되었습니다. 영업일 기준 1~3일 이내 답변드리겠습니다.'),
    ('support.create_failed',       '문의 접수에 실패했습니다. 잠시 후 다시 시도해 주세요.'),

    # ─ 지원 카테고리 (B2C user) ──────────────────
    ('support_cat.user.usage',     '사용법'),
    ('support_cat.user.beacon',    '비콘/WiFi'),
    ('support_cat.user.coupon',    '쿠폰/스탬프'),
    ('support_cat.user.payment',   '결제'),
    ('support_cat.user.etc',       '기타'),

    # ─ 지원 카테고리 (B2B provider) ──────────────
    ('support_cat.provider.store',    '매장 운영'),
    ('support_cat.provider.beacon',   '비콘'),
    ('support_cat.provider.payment',  '결제'),
    ('support_cat.provider.billing',  '정산'),
    ('support_cat.provider.staff',    '직원'),

    # ─ FAQ 페이지 ────────────────────────────────
    ('faq.title',                   '자주 묻는 질문'),
    ('faq.subtitle',                '궁금한 점을 카테고리에서 찾아보세요.'),
    ('faq.all_categories',          '전체'),
    ('faq.empty',                   '해당 카테고리의 FAQ 가 없습니다.'),
    ('faq.search_placeholder',      '키워드로 검색'),

    # ─ 신고 ──────────────────────────────────────
    ('report.title',                '신고하기'),
    ('report.subtitle',
     '부적절한 매장 정보 / 사용자 / 채팅 / 리뷰 를 신고할 수 있습니다.'),
    ('report.target_facility',      '매장'),
    ('report.target_user',          '사용자'),
    ('report.target_review',        '리뷰'),
    ('report.target_chat',          '채팅'),
    ('report.reason_label',         '신고 사유'),
    ('report.reason_spam',          '스팸/광고'),
    ('report.reason_inappropriate', '부적절한 콘텐츠'),
    ('report.reason_fraud',         '사기/허위 정보'),
    ('report.reason_etc',           '기타'),
    ('report.reason_text_label',    '추가 설명 (선택)'),
    ('report.submit_btn',           '신고 제출'),
    ('report.submit_success',
     '신고가 접수되었습니다. PathWave 운영팀이 영업일 기준 3일 이내 처리합니다.'),
    ('report.privacy_notice',
     '신고자 정보는 처리 외 목적으로 사용되지 않으며 외부에 공개되지 않습니다.'),

    # ─ ADMIN 콘솔 ────────────────────────────────
    ('admin_support.inbox_title',    '문의 inbox'),
    ('admin_support.tab_user',       '사용자'),
    ('admin_support.tab_provider',   '사장님'),
    ('admin_support.filter_all',     '전체'),
    ('admin_support.filter_open',    '답변 대기'),
    ('admin_support.filter_replied', '답변 완료'),
    ('admin_support.filter_closed',  '종결'),
    ('admin_support.col_subject',    '제목'),
    ('admin_support.col_category',   '카테고리'),
    ('admin_support.col_priority',   '우선순위'),
    ('admin_support.col_status',     '상태'),
    ('admin_support.col_created',    '접수일'),
    ('admin_support.col_actions',    '관리'),
    ('admin_support.reply_btn',      '답변'),
    ('admin_support.close_btn',      '종결'),
    ('admin_support.reply_and_close','답변 + 종결'),
    ('admin_support.reply_placeholder','답변 내용을 입력하세요.'),
    ('admin_support.stats_title',    '고객센터 통계'),
    ('admin_support.stats_avg_response','평균 응답시간 (시간)'),
    ('admin_support.stats_total_tickets','총 접수'),
    ('admin_support.stats_open_now', '대기 중'),
    ('admin_support.stats_replied',  '응답 완료'),
    ('admin_support.faq_title',      'FAQ 관리'),
    ('admin_support.faq_new',        'FAQ 추가'),
    ('admin_support.faq_edit',       'FAQ 수정'),
    ('admin_support.faq_q_label',    '질문'),
    ('admin_support.faq_a_label',    '답변'),
    ('admin_support.faq_active',     '공개'),
    ('admin_support.faq_lang',       '언어'),
    ('admin_support.faq_kind_user',  '사용자 FAQ'),
    ('admin_support.faq_kind_provider','사장님 FAQ'),
    ('admin_support.delete_confirm', '정말 삭제하시겠습니까?'),
    ('admin_support.reports_title',  '신고 관리'),
]


SAMPLE_TICKETS = [
    # (kind, requester_id_lookup, category, subject, body, status, priority)
    ('user',     None, 'beacon',
     '비콘이 감지되지 않습니다.',
     '강남역 카페에서 30분 머물렀는데 비콘 감지가 한 번도 안 됩니다. 블루투스/위치 권한 모두 허용 상태입니다.',
     'open', 'normal'),
    ('user',     None, 'coupon',
     '쿠폰이 사라졌어요.',
     '어제 발급받은 5천원 쿠폰이 마이페이지에서 안 보입니다. 결제 전이라 사용한 적 없습니다.',
     'replied', 'high'),
    ('provider', None, 'payment',
     '결제 PG 변경 가능 여부 문의',
     '현재 sim 모드로 테스트 중인데 운영 전환 시 토스 외에 다른 PG 사용도 가능한지 문의드립니다.',
     'open', 'normal'),
]


def upsert_translation(db, key: str, value: str) -> None:
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


def upsert_category(db, kind: str, code: str, label_key: str, sort_order: int) -> None:
    row = db.execute(
        "SELECT id FROM support_categories WHERE kind=? AND code=?",
        (kind, code)
    ).fetchone()
    if row:
        db.execute(
            "UPDATE support_categories SET label_key=?, sort_order=?, active=1 WHERE id=?",
            (label_key, sort_order, row['id'])
        )
    else:
        db.execute(
            "INSERT INTO support_categories (kind, code, label_key, sort_order, active) "
            "VALUES (?,?,?,?,1)",
            (kind, code, label_key, sort_order)
        )


def upsert_faq(db, kind: str, category: str, q: str, a: str, order: int) -> None:
    row = db.execute(
        "SELECT id FROM faqs WHERE kind=? AND lang='ko' AND question=?",
        (kind, q)
    ).fetchone()
    if row:
        db.execute(
            "UPDATE faqs SET category=?, answer=?, sort_order=?, active=1, "
            "updated_at=datetime('now') WHERE id=?",
            (category, a, order, row['id'])
        )
    else:
        db.execute(
            "INSERT INTO faqs (kind, category, question, answer, lang, sort_order, active) "
            "VALUES (?,?,?,?, 'ko', ?, 1)",
            (kind, category, q, a, order)
        )


def main() -> None:
    init_db()
    db = get_db()

    # 1) i18n keys
    for key, value in I18N_KEYS_KO:
        upsert_translation(db, key, value)

    # 2) 카테고리
    for code, label_key, order in CATEGORIES_USER:
        upsert_category(db, 'user', code, label_key, order)
    for code, label_key, order in CATEGORIES_PROVIDER:
        upsert_category(db, 'provider', code, label_key, order)

    # 3) FAQ
    for i, (cat, q, a) in enumerate(FAQS_USER_KO, start=1):
        upsert_faq(db, 'user', cat, q, a, i * 10)
    for i, (cat, q, a) in enumerate(FAQS_PROVIDER_KO, start=1):
        upsert_faq(db, 'provider', cat, q, a, i * 10)

    # 4) 샘플 티켓 (실제 user/facility_account 가 있을 때만)
    sample_user = db.execute(
        "SELECT id FROM users WHERE deleted_at IS NULL ORDER BY id LIMIT 1"
    ).fetchone()
    sample_facility = db.execute(
        "SELECT id FROM facility_accounts ORDER BY id LIMIT 1"
    ).fetchone()
    user_id = sample_user['id'] if sample_user else None
    facility_id = sample_facility['id'] if sample_facility else None

    for kind, _ph, cat, subj, body, status, priority in SAMPLE_TICKETS:
        rid = user_id if kind == 'user' else facility_id
        if not rid:
            continue
        # 중복 방지 — 동일 subject 가 있으면 skip
        exist = db.execute(
            "SELECT id FROM support_tickets WHERE kind=? AND subject=?",
            (kind, subj)
        ).fetchone()
        if exist:
            continue
        cur = db.execute(
            """INSERT INTO support_tickets
                 (kind, requester_id, category, subject, body, status, priority)
               VALUES (?,?,?,?,?,?,?)""",
            (kind, rid, cat, subj, body, status, priority)
        )
        tid = cur.lastrowid
        db.execute(
            "INSERT INTO support_messages (ticket_id, sender, sender_id, body) "
            "VALUES (?,?,?,?)",
            (tid, kind, rid, body)
        )
        if status == 'replied':
            db.execute(
                "INSERT INTO support_messages (ticket_id, sender, sender_id, body) "
                "VALUES (?, 'admin', NULL, ?)",
                (tid, '안녕하세요 PathWave 입니다. 빠르게 확인해 드리겠습니다.')
            )
            db.execute(
                "UPDATE support_tickets SET last_reply_at=datetime('now'), "
                "updated_at=datetime('now') WHERE id=?",
                (tid,)
            )

    db.commit(); db.close()
    print('[seed_phase_i_support] done.')


if __name__ == '__main__':
    main()
