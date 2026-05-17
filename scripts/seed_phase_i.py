"""Phase I — 고객센터 + FAQ + 신고 도메인 시드.

내용:
- i18n DB: support.* / faq.* / report.* compliance 키 (ko only)
- support_categories: 사용자/사장 카테고리 마스터
- faqs: B2C 사용자 10개 + B2B 사장 10개 (ko)
- support_tickets: 샘플 3건 (각 카테고리 대표 시나리오)

idempotent.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, init_db


# ── i18n keys (ko) ────────────────────────────────────────────────────────────
I18N_KEYS: list[tuple[str, str]] = [
    # 고객센터 공통
    ('support.title',                '고객센터'),
    ('support.business_hours',
     '운영시간: 평일 09:00 ~ 18:00 (주말·공휴일 휴무)'),
    ('support.response_eta',
     '답변 예상 시간: 영업일 기준 1~3일 이내'),
    ('support.privacy_notice',
     '문의 내용은 응대 목적으로 3년간 보관되며 그 외 용도로 사용되지 않습니다.'),
    ('support.create_btn',           '문의 작성'),
    ('support.subject_label',        '제목'),
    ('support.body_label',           '내용'),
    ('support.category_label',       '카테고리'),
    ('support.status_open',          '접수'),
    ('support.status_replied',       '답변 완료'),
    ('support.status_closed',        '종료'),
    ('support.priority_label',       '우선순위'),
    ('support.send_btn',             '보내기'),
    ('support.reply_placeholder',    '답변을 입력하세요...'),
    ('support.empty_user',           '아직 작성한 문의가 없습니다.'),
    ('support.empty_admin',          '처리 대기 중인 문의가 없습니다.'),
    ('support.thread_title',         '대화 내역'),
    ('support.add_message',          '추가 메시지'),

    # 카테고리 (사용자)
    ('support.cat.user.usage',       '사용법'),
    ('support.cat.user.beacon',      '비콘 / WiFi 자동 연결'),
    ('support.cat.user.coupon',      '쿠폰 / 스탬프'),
    ('support.cat.user.payment',     '결제 / 환불'),
    ('support.cat.user.etc',         '기타 문의'),
    # 카테고리 (사장)
    ('support.cat.provider.store_ops','매장 운영'),
    ('support.cat.provider.beacon',  '비콘 등록 / 관리'),
    ('support.cat.provider.payment', '결제 / PG'),
    ('support.cat.provider.settlement','정산'),
    ('support.cat.provider.staff',   '직원 / 권한'),

    # FAQ
    ('faq.title',                    'FAQ (자주 묻는 질문)'),
    ('faq.search_placeholder',       'FAQ 검색...'),
    ('faq.empty',                    '검색 결과가 없습니다. 문의로 보내주시면 답변드리겠습니다.'),
    ('faq.helpful_label',            '도움이 되었나요?'),

    # 신고
    ('report.title',                 '신고'),
    ('report.reason_label',          '신고 사유'),
    ('report.reason_spam',           '스팸 / 광고'),
    ('report.reason_abuse',          '욕설 / 폭언'),
    ('report.reason_illegal',        '불법 행위'),
    ('report.reason_inappropriate',  '부적절한 콘텐츠'),
    ('report.reason_other',          '기타'),
    ('report.detail_label',          '상세 설명 (선택)'),
    ('report.submit_btn',            '신고하기'),
    ('report.submitted',             '신고가 접수되었습니다. 운영자가 확인 후 처리합니다.'),
    ('report.privacy_notice',
     '신고자 정보는 운영자만 확인하며, 처리 외 목적으로 사용되지 않습니다.'),
    ('report.status_open',           '접수'),
    ('report.status_in_review',      '검토 중'),
    ('report.status_action_taken',   '조치 완료'),
    ('report.status_dismissed',      '반려'),
]


# ── 카테고리 마스터 ──────────────────────────────────────────────────────────
CATEGORIES = [
    # 사용자
    ('user', 'usage',      'support.cat.user.usage',      10),
    ('user', 'beacon',     'support.cat.user.beacon',     20),
    ('user', 'coupon',     'support.cat.user.coupon',     30),
    ('user', 'payment',    'support.cat.user.payment',    40),
    ('user', 'etc',        'support.cat.user.etc',        90),
    # 사장
    ('provider', 'store_ops',  'support.cat.provider.store_ops',  10),
    ('provider', 'beacon',     'support.cat.provider.beacon',     20),
    ('provider', 'payment',    'support.cat.provider.payment',    30),
    ('provider', 'settlement', 'support.cat.provider.settlement', 40),
    ('provider', 'staff',      'support.cat.provider.staff',      50),
]


# ── FAQ (사용자 10 + 사장 10, ko) ────────────────────────────────────────────
FAQS_USER = [
    ('usage',   'PathWave 는 어떻게 사용하나요?',
                'PathWave 가 설치된 매장에 입장하면 비콘이 자동 감지되어 WiFi / 스탬프 / 쿠폰이 자동 처리됩니다. 별도 조작 없이 입장만 하면 됩니다.'),
    ('usage',   '회원가입에 본인인증이 필요한가요?',
                '만 14~18세는 보호자 초대 코드가 필요합니다. 만 19세 이상은 이메일 또는 소셜 로그인으로 가입 가능합니다.'),
    ('beacon',  '매장에 들어왔는데 WiFi 가 자동 연결되지 않아요',
                'Bluetooth + 위치 권한이 모두 허용되어 있어야 합니다. 설정 > 권한에서 확인해 주세요. 비콘에서 5~10m 이내에 있어야 감지됩니다.'),
    ('beacon',  'iOS 에서 WiFi 자동 연결 권한은 어떻게 주나요?',
                '설정 > PathWave > "WiFi 자동 연결" 권한을 허용해 주세요. Android 는 시스템 설정의 위치 권한이 활성화되어야 합니다.'),
    ('coupon',  '스탬프가 적립되지 않아요',
                '매장 비콘 감지 후 자동 적립됩니다. 같은 매장에서 정책의 쿨다운 시간(기본 60분) 내 재방문은 1회만 적립됩니다.'),
    ('coupon',  '쿠폰은 어떻게 사용하나요?',
                '쿠폰 화면에서 "사용하기" 버튼을 누르면 매장 직원에게 화면을 보여주세요. 매장에서 직접 사용 처리합니다.'),
    ('coupon',  '발급받은 쿠폰을 다른 매장에서 쓸 수 있나요?',
                '쿠폰은 발급한 매장에서만 사용 가능합니다. 양도 / 현금 환불은 불가합니다.'),
    ('payment', '결제 정보는 안전한가요?',
                '카드 정보는 등록된 PG 사(토스페이먼츠 등) 가 직접 처리하며 PathWave 서버에는 저장되지 않습니다.'),
    ('payment', '환불은 어떻게 받나요?',
                '결제 내역에서 직접 환불 요청하거나 support@pathwave.co.kr 로 문의 주세요. 구독 결제 후 7일 이내 미사용 시 전액 환불 가능합니다.'),
    ('etc',     '회원 탈퇴는 어떻게 하나요?',
                '설정 > 회원 탈퇴 메뉴에서 진행 가능합니다. 즉시 로그인 / 알림이 차단되며 14일 후 재가입 가능합니다.'),
]

FAQS_PROVIDER = [
    ('store_ops',  '매장 정보는 어디서 수정하나요?',
                   'provider-web 의 매장 정보 메뉴에서 매장명 / 주소 / 영업시간 / 사진 등을 수정할 수 있습니다. 슈퍼 어드민 승인 후 즉시 반영됩니다.'),
    ('store_ops',  '매장을 일시 정지할 수 있나요?',
                   '매장 정보에서 "휴업" 토글로 비활성화 가능합니다. 비활성화 동안 비콘이 자동으로 inactive 상태가 됩니다.'),
    ('beacon',     '비콘 등록은 어떻게 하나요?',
                   '슈퍼 어드민이 CSV 로 일괄 입고한 비콘을 사장님이 SN 으로 claim 합니다. Major 는 매장 ID 자동, Minor 는 1~3 등 직접 지정 가능 (미지정 시 자동 순번).'),
    ('beacon',     '비콘 배터리가 부족해요',
                   '비콘 자체 또는 사장님이 배터리 상태를 보고합니다. 20% 이하면 슈퍼 어드민에게 자동 알림이 전송되어 교체 비콘이 발송됩니다.'),
    ('payment',    'PG 사는 어떻게 변경하나요?',
                   '운영팀에 문의해 주세요. 환경변수 PG_PROVIDER 변경 후 PG 사 계약 / 인증이 필요합니다.'),
    ('payment',    '결제 실패는 어떻게 처리하나요?',
                   '결제 내역에서 실패 사유 확인 후 카드 변경 또는 PG 사 문의가 필요합니다. 자동결제 실패가 3회 연속이면 구독이 만료됩니다.'),
    ('settlement', '정산은 언제 받나요?',
                   '매월 말일 마감 후 익월 10일 정산됩니다. 정산 내역은 결제 메뉴 > 정산 탭에서 확인 가능합니다.'),
    ('settlement', '세금 계산서는 어떻게 발행되나요?',
                   '결제 시 등록한 사업자 정보로 자동 발행됩니다. 사업자 정보 변경은 매장 정보 메뉴에서 수정 후 다음 정산부터 적용됩니다.'),
    ('staff',      '직원 권한은 어떻게 다른가요?',
                   'admin = 매장 운영 / 정책 / 직원 초대 / 결제 정보 접근 가능. staff = 스탬프 / 쿠폰 처리 / 채팅 응대만 가능. 직원 행동 책임은 사장에게 있습니다.'),
    ('staff',      '직원 초대 메일이 안 와요',
                   '스팸함을 확인하거나 이메일 주소를 다시 확인해 주세요. 재발송 버튼으로 다시 보낼 수 있고, 초대 만료(기본 7일) 후에는 새로 초대해야 합니다.'),
]


# ── 샘플 ticket 3건 ───────────────────────────────────────────────────────────
SAMPLE_TICKETS = [
    # user_id 는 시드된 alice/bob 등. facility_account_id 는 owner1.
    ('user',     None,  'usage',     '앱이 자꾸 꺼져요',
     '아이폰 16 Pro 에서 매장 진입 후 앱이 백그라운드로 가면 1~2분 뒤 꺼집니다.',
     'open',   'normal'),
    ('user',     None,  'coupon',    '쿠폰을 받았는데 사용이 안 됩니다',
     '환영 쿠폰을 받아서 매장에서 보여줬는데 "이미 사용된 쿠폰" 이라고 나옵니다.',
     'open',   'high'),
    ('provider', None,  'beacon',    '비콘 1개가 inactive 로 자꾸 빠져요',
     'BP108B-000003 비콘이 매일 새벽 3시쯤 inactive 로 빠집니다. 배터리는 90% 이상입니다.',
     'replied','normal'),
]


def _seed_i18n(db) -> tuple[int, int]:
    inserted, updated = 0, 0
    for key, ko in I18N_KEYS:
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
    return inserted, updated


def _seed_categories(db) -> int:
    n = 0
    for kind, code, label_key, sort_order in CATEGORIES:
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
                """INSERT INTO support_categories (kind, code, label_key, sort_order, active)
                   VALUES (?,?,?,?,1)""",
                (kind, code, label_key, sort_order)
            )
            n += 1
    return n


def _seed_faqs(db) -> int:
    n = 0
    sort = 0
    for category, q, a in FAQS_USER + FAQS_PROVIDER:
        sort += 10
        kind = 'user' if (category, q, a) in FAQS_USER else 'provider'
        row = db.execute(
            "SELECT id FROM faqs WHERE kind=? AND lang='ko' AND question=?",
            (kind, q)
        ).fetchone()
        if row:
            db.execute(
                """UPDATE faqs
                   SET answer=?, category=?, sort_order=?, active=1,
                       updated_at=datetime('now')
                   WHERE id=?""",
                (a, category, sort, row['id'])
            )
        else:
            db.execute(
                """INSERT INTO faqs
                     (kind, category, question, answer, lang, sort_order, active)
                   VALUES (?,?,?,?,'ko',?,1)""",
                (kind, category, q, a, sort)
            )
            n += 1
    return n


def _seed_tickets(db) -> int:
    # 시드된 사용자 / 사장 lookup
    alice = db.execute("SELECT id FROM users WHERE email='alice@pathwave.test'").fetchone()
    owner1 = db.execute("SELECT id FROM facility_accounts WHERE email='owner1@pathwave.test'").fetchone()
    if not alice or not owner1:
        print('  ⚠️ alice@/owner1@ 미존재 — seed_phase_c.py 먼저 실행 권장')
        return 0
    n = 0
    for kind, _, category, subject, body, status, priority in SAMPLE_TICKETS:
        # 동일 (kind+subject) 이미 있으면 skip
        existing = db.execute(
            "SELECT id FROM support_tickets WHERE kind=? AND subject=?",
            (kind, subject)
        ).fetchone()
        if existing:
            continue
        user_id = alice['id'] if kind == 'user' else None
        fa_id   = owner1['id'] if kind == 'provider' else None
        cur = db.execute(
            """INSERT INTO support_tickets
                 (kind, user_id, facility_account_id, category, subject, body, status, priority)
               VALUES (?,?,?,?,?,?,?,?)""",
            (kind, user_id, fa_id, category, subject, body, status, priority)
        )
        tid = cur.lastrowid
        db.execute(
            "INSERT INTO support_messages (ticket_id, sender, body) VALUES (?, 'user', ?)",
            (tid, body)
        )
        if status == 'replied':
            reply_body = (
                '안녕하세요. 비콘 새벽 inactive 는 매장 영업시간 외 자동 절전 모드로 보입니다. '
                'StampForm 의 BLE 자동 적립 정책에서 영업시간 설정을 확인해 주세요.'
            )
            db.execute(
                """INSERT INTO support_messages (ticket_id, sender, sender_admin_id, body)
                   VALUES (?, 'admin', NULL, ?)""",
                (tid, reply_body)
            )
            db.execute(
                "UPDATE support_tickets SET replied_at=datetime('now') WHERE id=?",
                (tid,)
            )
        n += 1
    return n


def seed() -> None:
    init_db()
    db = get_db()

    i18n_inserted, i18n_updated = _seed_i18n(db)
    db.commit()

    cat_inserted = _seed_categories(db)
    db.commit()

    faq_inserted = _seed_faqs(db)
    db.commit()

    ticket_inserted = _seed_tickets(db)
    db.commit()
    db.close()

    print('Phase I 시드 완료:')
    print(f'  i18n keys           : {len(I18N_KEYS)} (inserted {i18n_inserted}, updated {i18n_updated})')
    print(f'  support_categories  : {cat_inserted} inserted (총 {len(CATEGORIES)} 기대)')
    print(f'  faqs                : {faq_inserted} inserted (사용자 10 + 사장 10)')
    print(f'  sample tickets      : {ticket_inserted} inserted (목표 3)')


if __name__ == '__main__':
    seed()
