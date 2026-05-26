"""P13: 환불·청소년 보호·쿠키 정책 DB 시드.

phase1 plan §P13 = "환불·청소년보호·쿠키 정책 — BE policy KIND 추가 +
admin Policies + mobile/provider 노출".

KIND 추가
- refund            (환불 정책)
- youth_protection  (청소년 보호 정책)
- cookie            (쿠키 정책)

3 KIND × ko/en × 초기 버전 v1.0 = 6 row INSERT.
admin-web 의 정책 관리 화면에서 추후 본문 수정 가능 (PATCH /api/admin/policies).

사용
- 로컬 dev: ./venv/bin/python scripts/seed_policies_p13.py
- prod    : admin-web 'Policies' 페이지에서 직접 입력 권장 (변경 이력 추적)
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / 'pathwave.db'

VERSION = 'v1.0'
EFFECTIVE_AT = '2026-05-26'   # 출시일까지 작성된 시점 (사용자 정정 가능)


POLICIES = {
    'refund': {
        'ko': {
            'title': '환불 정책',
            'body': """주식회사 트리거소프트(이하 "회사")는 PathWave 서비스의 결제 환불에 관하여 다음과 같이 정합니다.

1. 환불 원칙
- 디지털 콘텐츠·서비스 이용권은 사용을 시작한 시점부터 환불이 제한됩니다.
- 시설관리자(점주) 의 PathWave 서비스 구독료는 결제일로부터 7일 이내 미사용 분에 한해 환불 가능합니다.

2. 즉시 환불 (100%)
- 결제 후 1시간 이내 + 서비스 이용이 한 번도 없는 경우.
- 회사의 시스템 오류로 중복/오인 결제된 경우.

3. 일부 환불
- 정기결제(구독) 중도 해지 시: 잔여 일수 비례 환불 (수수료 5% 차감).
- 일회성 결제: 사용 내역에 따라 협의.

4. 환불 불가
- 이미 사용한 디지털 콘텐츠·쿠폰·스탬프 보상 등.
- 결제일로부터 30일 경과한 항목.

5. 환불 신청
- PathWave 앱 또는 시설관리자 웹의 [마이페이지 > 결제 내역 > 환불 요청] 메뉴.
- 또는 고객센터(support@pathwave.co.kr) 로 문의.
- 처리: 영업일 기준 3~5일 이내.

6. 결제수단별 환불 처리
- 신용카드: 카드사 정책에 따라 5~7 영업일.
- 계좌이체: 별도 안내 후 본인 계좌로 입금.

7. 분쟁 해결
- 환불 관련 분쟁은 「전자상거래 등에서의 소비자보호에 관한 법률」 및 회사의 이용약관에 따릅니다.

본 환불 정책은 2026년 5월 26일부터 시행합니다.""",
        },
        'en': {
            'title': 'Refund Policy',
            'body': """Trigger Soft Co., Ltd. ("Company") establishes the following refund policy for PathWave services.

1. General Principle
- Digital content and service tickets are non-refundable once usage has begun.
- Provider (facility owner) subscription fees may be refunded within 7 days of payment if unused.

2. Immediate Refund (100%)
- Within 1 hour of payment AND no service usage.
- Duplicate or erroneous charges caused by system errors.

3. Partial Refund
- Cancellation of recurring subscription mid-term: Pro-rated refund of remaining days (5% processing fee deducted).
- One-time payments: Subject to usage and negotiation.

4. Non-refundable
- Digital content / coupons / stamp rewards already used.
- Items past 30 days from payment date.

5. Refund Request
- Via PathWave app or provider web: [My Page > Payment History > Request Refund].
- Or contact support@pathwave.co.kr.
- Processing: Within 3-5 business days.

6. Refund Method
- Credit card: 5-7 business days per card issuer policy.
- Bank transfer: To the registered account after verification.

7. Dispute Resolution
- Refund disputes are governed by the "Act on Consumer Protection in Electronic Commerce" and the Company's Terms of Service.

This Refund Policy is effective from May 26, 2026.""",
        },
    },
    'youth_protection': {
        'ko': {
            'title': '청소년 보호 정책',
            'body': """주식회사 트리거소프트는 「청소년 보호법」 에 따라 청소년이 PathWave 서비스를 안전하게 이용할 수 있도록 다음과 같이 정합니다.

1. 청소년 가입 제한
- 만 14세 미만 가입 차단 (가입 시 본인 생년 검증).
- 만 14~18세 가입 시 법정 보호자의 초대 코드를 발급받아야 합니다.

2. 유해 콘텐츠 차단
- 청소년에게 유해한 매장 카테고리(주점/유흥 등) 의 컨텐츠 노출을 자동 필터링합니다.
- 채팅 메시지의 욕설·음란 표현은 자동 감지 + 마스킹.

3. 사용자 신고 기반 보호
- 부적절한 컨텐츠 / 채팅 발견 시 신고 기능 제공.
- 신고 접수 후 24시간 이내 검토 및 조치.

4. 청소년 보호 책임자
- 성명: 이우상 (대표이사)
- 이메일: youth@pathwave.co.kr
- 연락처: 추후 등록

5. 청소년 본인 권리
- 본인이 가입한 정보의 열람·정정·삭제 요청 권리.
- 법정 보호자가 대신 행사할 수도 있습니다.

6. 신고 채널
- PathWave 앱의 [고객센터 > 신고] 메뉴.
- 이메일: report@pathwave.co.kr.
- 외부: 청소년사이버상담센터 1388.

본 청소년 보호 정책은 2026년 5월 26일부터 시행합니다.""",
        },
        'en': {
            'title': 'Youth Protection Policy',
            'body': """Trigger Soft Co., Ltd. establishes the following policy for the safe use of PathWave services by minors, in accordance with the Youth Protection Act.

1. Age Restriction
- Users under 14 years old are blocked from signup (birth date verified at registration).
- Users aged 14-18 require an invitation code issued by a legal guardian.

2. Harmful Content Filtering
- Categories deemed harmful to minors (bars / nightlife etc.) are automatically filtered.
- Profanity / explicit expressions in chat are auto-detected and masked.

3. User-Reported Protection
- Report function provided for inappropriate content / chat.
- Review and action within 24 hours of report.

4. Youth Protection Officer
- Name: Lee Woo-sang (CEO)
- Email: youth@pathwave.co.kr
- Phone: To be registered.

5. Minor's Rights
- Right to access, correct, or delete their registered information.
- Legal guardians may exercise this right on their behalf.

6. Report Channels
- [Customer Center > Report] menu in the PathWave app.
- Email: report@pathwave.co.kr.
- External: Korea Youth Cyber Counseling Center 1388.

This Youth Protection Policy is effective from May 26, 2026.""",
        },
    },
    'cookie': {
        'ko': {
            'title': '쿠키 정책',
            'body': """주식회사 트리거소프트는 PathWave 서비스 제공을 위해 다음과 같이 쿠키를 사용합니다.

1. 쿠키란?
- 웹사이트 / 앱이 사용자의 기기에 저장하는 작은 텍스트 파일.
- 로그인 상태 유지, 사용자 환경 설정 저장 등에 사용됩니다.

2. 사용 쿠키 종류
가. 필수 쿠키 (Strictly Necessary)
   - 세션 토큰 (JWT 인증 유지)
   - CSRF 보호 토큰
   - 동의 사항 저장
   - ※ 차단 시 서비스 이용이 제한됩니다.

나. 기능성 쿠키 (Functional)
   - 사용자 선호 언어 (i18n)
   - 다크모드 / 라이트모드 설정
   - 최근 검색어

다. 분석 쿠키 (Analytics) - 출시 후 도입 예정
   - 익명화된 페이지 방문 기록.
   - Google Analytics 등 외부 도구.
   - 별도 동의 후에만 사용.

라. 광고 쿠키 (Advertising) - 사용 안 함
   - PathWave 는 v1 에서 광고 쿠키를 사용하지 않습니다.

3. 쿠키 거부 / 삭제
- 브라우저 설정에서 직접 삭제 가능.
- 모바일 앱: [설정 > 데이터 관리 > 캐시 삭제].
- 필수 쿠키 거부 시 서비스 이용 불가.

4. 제3자 쿠키
- 외부 SDK (Firebase / Sentry 등) 가 자체 쿠키를 설정할 수 있습니다.
- 해당 서비스의 개인정보처리방침을 별도 확인해 주세요.

본 쿠키 정책은 2026년 5월 26일부터 시행합니다.""",
        },
        'en': {
            'title': 'Cookie Policy',
            'body': """Trigger Soft Co., Ltd. uses cookies for the PathWave service as follows.

1. What are Cookies?
- Small text files stored by websites / apps on the user's device.
- Used for maintaining login state, saving user preferences, etc.

2. Types of Cookies Used
a. Strictly Necessary Cookies
   - Session token (JWT authentication)
   - CSRF protection token
   - Consent record
   - Note: Blocking these limits service availability.

b. Functional Cookies
   - User language preference (i18n)
   - Dark mode / light mode settings
   - Recent searches

c. Analytics Cookies — to be introduced after launch
   - Anonymized page visit records.
   - External tools such as Google Analytics.
   - Only used after separate consent.

d. Advertising Cookies — not used
   - PathWave v1 does not use advertising cookies.

3. Refusing / Deleting Cookies
- Can be deleted directly in browser settings.
- Mobile app: [Settings > Data Management > Clear Cache].
- Refusing necessary cookies disables the service.

4. Third-Party Cookies
- External SDKs (Firebase / Sentry etc.) may set their own cookies.
- Please refer to those services' privacy policies separately.

This Cookie Policy is effective from May 26, 2026.""",
        },
    },
}


def main():
    if not DB_PATH.exists():
        print(f'❌ DB 없음: {DB_PATH}')
        sys.exit(1)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    inserted = 0
    skipped = 0

    for kind, langs in POLICIES.items():
        for lang, payload in langs.items():
            # 이미 (kind, lang, version) 조합 존재하면 skip (멱등)
            existing = cur.execute(
                """SELECT id FROM policies
                   WHERE kind=? AND lang=? AND version=?""",
                (kind, lang, VERSION),
            ).fetchone()
            if existing:
                print(f'  skip  {kind}/{lang}/{VERSION} (id={existing[0]})')
                skipped += 1
                continue
            cur.execute(
                """INSERT INTO policies
                   (kind, lang, version, title, body, change_log, effective_at,
                    created_by_admin_id, created_at, email_notified)
                   VALUES (?, ?, ?, ?, ?, ?, ?, NULL, datetime('now'), 0)""",
                (kind, lang, VERSION, payload['title'], payload['body'],
                 'P13 initial seed', EFFECTIVE_AT),
            )
            print(f'  ✅ INSERT {kind}/{lang}/{VERSION} (rowid={cur.lastrowid})')
            inserted += 1

    con.commit()

    # 검증
    print('\n=== 시드 후 policies 현황 ===')
    for kind in POLICIES:
        rows = cur.execute(
            "SELECT lang, version, title FROM policies WHERE kind=? ORDER BY lang",
            (kind,),
        ).fetchall()
        for lang, ver, title in rows:
            print(f'   {kind:18s} {lang}/{ver}  — {title}')

    con.close()
    print(f'\n완료. inserted={inserted}, skipped={skipped}')
    print('admin-web 의 정책 관리 화면에서 본문 수정 가능 (PATCH /api/admin/policies).')


if __name__ == '__main__':
    main()
