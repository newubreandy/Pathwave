"""PathWave — 개발 체크리스트 + 서비스 신청·운영비용 엑셀 2개 생성 (v4).

수정사항 (2026-05-23 — 사용자 피드백):
  1. 환율 $1 = ₩1,500
  2. 서버 = 국내 클라우드(가비아/NHN/네이버) — AWS 제외
  3. 상표등록 2건(패스웨이브 + 트리거소프트) 초기 세팅비 추가
  4. 매장당 월 1만원 매출 — 손익분기점(BEP) 시트 추가
  5. "주체" 컬럼 (사용자 / 시설관리자 / 슈퍼어드민 / 공통-BE / 인프라) 가장 앞에
  6. 각 도메인 sub-feature 를 주체별로 분리 (체크리스트 분리 관리)
  7. 푸시 = 자체구축 표기 (FCM 무료지만 사용자 정책상 — 단 Android 현실적 한계는 비고)
  8. Phase 1.5 — 개발환경 서버 구축 + 통합 테스트 단계 추가
  9. 서비스 신청 시트에 "가격 상세" + "신청 링크" 컬럼
  10. 1회성 비용은 월별 시트에서 제외 → "초기 세팅비" 시트에만 집계

산출:
  docs/exports/pathwave_dev_checklist.xlsx
  docs/exports/pathwave_services_and_costs.xlsx
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

USD_KRW = 1500  # 환율 가정

FONT = '맑은 고딕'
HEADER_FONT = Font(name=FONT, bold=True, color='FFFFFF', size=11)
HEADER_FILL = PatternFill('solid', start_color='1F4E78')
SUBHEADER_FILL = PatternFill('solid', start_color='D9E1F2')
INPUT_FONT  = Font(name=FONT, color='0000FF')
LINK_FONT   = Font(name=FONT, color='008000')
ASSUME_FILL = PatternFill('solid', start_color='FFFFCC')
DONE_FILL    = PatternFill('solid', start_color='C6EFCE')
PARTIAL_FILL = PatternFill('solid', start_color='FFEB9C')
ACTIVE_FILL  = PatternFill('solid', start_color='BDD7EE')
TODO_FILL    = PatternFill('solid', start_color='F2F2F2')
THIN = Side(border_style='thin', color='BFBFBF')
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical='top')

KRW_FMT = '₩#,##0;(₩#,##0);-'
PCT_FMT = '0.0%;-0.0%;-'
DATE_FMT = 'yyyy-mm-dd'

# 주체별 색상
ACTOR_COLOR = {
    '사용자':       'E2EFDA',  # 연한 녹색 — mobile 앱
    '시설관리자':   'FFF2CC',  # 연한 노랑 — provider
    '슈퍼어드민':   'FCE4D6',  # 연한 주황 — admin
    '공통-BE':      'DEEBF7',  # 연한 파랑 — 백엔드
    '인프라':       'EAEAEA',  # 회색 — 운영
}


def force_workbook_font(wb, font_name=None):
    fn = font_name or FONT
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                f = cell.font
                cell.font = Font(name=fn, size=f.size, bold=f.bold, italic=f.italic,
                                 color=f.color, underline=f.underline, strike=f.strike)


def apply_table(ws, header_row, last_row, last_col, freeze=True):
    for c in range(1, last_col + 1):
        cell = ws.cell(row=header_row, column=c)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = BORDER
    for r in range(header_row + 1, last_row + 1):
        for c in range(1, last_col + 1):
            cell = ws.cell(row=r, column=c)
            cell.border = BORDER
            if not cell.alignment.wrap_text:
                cell.alignment = WRAP
    if freeze:
        ws.freeze_panes = ws.cell(row=header_row + 1, column=1).coordinate


# ═══════════════════════════════════════════════════════════════════════════
# FILE 1 — 개발 체크리스트 (주체별 + 기능별 sub-feature 단위)
# ═══════════════════════════════════════════════════════════════════════════
def build_dev_checklist():
    wb = Workbook()
    wb.remove(wb.active)
    today = '2026-05-23'

    # ── Sheet: 기능별 전체 현황 ────────────────────────────────────────
    ws = wb.create_sheet('기능별 전체 현황')
    ws['A1'] = 'PathWave 기능별 전체 작업 현황 — 주체별 + 이전 완료 / Phase 1 / 남은'
    ws['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
    ws.merge_cells('A1:G1')

    headers = ['주체', '도메인/기능', '단계', '항목', '내용', '상태', '비고']
    ws.append([])
    ws.append(headers)
    header_row = ws.max_row

    # (주체, 도메인, 단계, 항목, 내용, 상태, 비고)
    items = [
        # ════════ 인증/회원가입 ════════
        ('공통-BE',    '인증/회원가입', '이전 완료', '이메일 인증·가입 API', '/api/auth send-code·verify-code·register·login + email_codes + bcrypt + JWT', '✅', ''),
        ('공통-BE',    '인증/회원가입', '이전 완료', '5종 소셜 로그인 BE', 'Google·Apple·Facebook·Kakao·Naver 토큰 검증 + 동의 처리', '✅', '실 키는 카카오·네이버 검수 후'),
        ('공통-BE',    '인증/회원가입', '이전 완료', '동의·약관·미성년자 BE', '8 KIND 정책 + record_consents 감사 + parent_invite 코드', '✅', ''),
        ('공통-BE',    '인증/회원가입', '이전 완료', '회원 탈퇴 + 14일 그레이스', '/api/auth/delete-account + soft delete + deleted_at', '✅', ''),
        ('공통-BE',    '인증/회원가입', '이전 완료', '모바일 비번 재설정 BE', '/api/auth/forgot-password·reset-password (users 테이블)', '✅', ''),
        ('공통-BE',    '인증/회원가입', '이전 완료', '시설 계정 가입·로그인 BE', '/api/facility send-code·register·login + 운영자 승인 대기', '✅', ''),
        ('공통-BE',    '인증/회원가입', 'Phase 1 ✅', 'P4 — 시설 비번 재설정 BE 신규', '/api/facility/forgot-password·reset-password 신규 (email_codes 재활용)', '✅', ''),
        ('사용자',     '인증/회원가입', '이전 완료', 'mobile 가입 5단계', 'consent → 본인인증 → 이메일/소셜 → 약관 동의 → 완료', '✅', ''),
        ('사용자',     '인증/회원가입', '이전 완료', 'mobile 로그인·비번재설정', 'login_screen + forgot_password_screen (2단계 코드)', '✅', ''),
        ('사용자',     '인증/회원가입', '이전 완료', 'mobile 회원 탈퇴', 'delete_account_screen + 14일 그레이스', '✅', ''),
        ('시설관리자', '인증/회원가입', '이전 완료', 'provider 회원가입·로그인 UI', '실 폼 + 소셜로그인 + 매장 정보 입력', '✅', '폼은 dev 우회로 가려졌었음'),
        ('시설관리자', '인증/회원가입', 'Phase 1 ✅', 'P4 — provider dev 우회 제거', 'DEV_AUTO_LOGIN env 게이트 + Login 자동토큰 제거 + Signup 게스트 게이트', '✅', '출시 빌드에서 실 로그인폼 노출'),
        ('시설관리자', '인증/회원가입', 'Phase 1 ✅', 'P4 — provider ForgotPassword 페이지', '/forgot-password 라우트 + 2단계 UI + AuthService 메서드', '✅', ''),
        ('슈퍼어드민', '인증/회원가입', '이전 완료', 'admin Login + 관리자 인증', 'admin-web Login + JWT + RequireAuth', '✅', ''),
        ('공통-BE',    '인증/회원가입', '남은', '실 키 검증', '카카오·네이버 검수 완료 후 실 소셜로그인 통합 테스트', '⬜', '외부 활성화 후'),

        # ════════ 매장 정보 ════════
        ('공통-BE',    '매장 정보', '이전 완료', '매장 CRUD API', '/api/facilities CRUD + 이미지 갤러리 + 다국어 번역 캐시', '✅', ''),
        ('사용자',     '매장 정보', '이전 완료', 'mobile 매장 상세 화면', 'facility_screen — 이미지/영업시간/주소/채팅 진입', '✅', ''),
        ('시설관리자', '매장 정보', '이전 완료', 'provider StoreInfo UI 골격', '편집/저장/지도/이미지/비콘 claim UI 완성, 데이터는 mock', '✅', '데이터 연동은 P5'),
        ('시설관리자', '매장 정보', 'Phase 1 ✅', 'P5 — provider StoreInfo 실연동', 'StoreService.list/update PATCH 실연동 + 실 fid 비콘 claim', '✅', ''),
        ('시설관리자', '매장 정보', 'Phase 1 ✅', 'P5 — Settings 푸터 PwFooter', 'CompanyInfoService → 실 법인정보', '✅', ''),
        ('시설관리자', '매장 정보', 'Phase 1 ✅', 'P5 — dead code 정리', 'Facilities.jsx (1계정1매장 위반) 삭제', '✅', ''),
        ('슈퍼어드민', '매장 정보', '이전 완료', 'admin Stores 관리', '매장 관리 + 비콘 매핑 + 번역 등록', '✅', ''),
        ('공통-BE',    '매장 정보', '남은', 'P8c — 스키마 갭', 'facilities 테이블 category/holidays/detailAddress 추가 또는 UI 정리', '⬜', '별도 작업 칩'),

        # ════════ 결제·구독 ════════
        ('공통-BE',    '결제·구독', '이전 완료', 'billing API 전체', '/api/billing cards·subscriptions·payments·refund·extend·receipt-email + PG 추상화', '✅', ''),
        ('시설관리자', '결제·구독', '이전 완료', 'provider PaymentManagement·Subscriptions UI 골격', '다단계 결제 흐름/카드 입력/구독 카드 UI, 데이터는 mock + localStorage 평문저장', '✅', ''),
        ('시설관리자', '결제·구독', 'Phase 1 ✅', 'P7 — BillingService 신규', 'provider /api/billing 래퍼 7종 메서드', '✅', ''),
        ('시설관리자', '결제·구독', 'Phase 1 ✅', 'P7 — 카드 평문저장 제거 (C6)', 'localStorage pathwave_payment_card + audit 큐 완전 제거, brand+last4만 전송', '✅', 'PCI 준수'),
        ('시설관리자', '결제·구독', 'Phase 1 ✅', 'P7 — 결제 흐름 통합', 'PaymentManagement·Subscriptions·ServiceRequest 동일 백엔드로 통합 + 호텔H 기본값 제거', '✅', ''),
        ('슈퍼어드민', '결제·구독', '이전 완료', 'admin Payments + Subscriptions + 환불', 'adminApi.listPayments/listSubscriptions/refundPayment 실연동 + 환불 모달', '✅', '이미 정합'),
        ('공통-BE',    '결제·구독', '남은', '토스 키 활성화', '토스페이먼츠 심사 통과 후 PG_PROVIDER=toss + 실 결제 검증', '⬜', '외부 1~2주'),

        # ════════ 쿠폰 ════════
        ('공통-BE',    '쿠폰', '이전 완료', '쿠폰 발행/사용/만료 API', '/api/coupons issue·use·expire + 정책 + 통계', '✅', ''),
        ('사용자',     '쿠폰', '이전 완료', 'mobile 쿠폰함', 'coupons_screen (active/used/expired 탭) + 사용 다이얼로그', '✅', '쿠폰 사용 silent error 잔존'),
        ('사용자',     '쿠폰', 'Phase 1 — 남은', 'P9 — mobile silent error 수정', '사용 실패 시 사용자 피드백 + 목록 갱신', '⬜', ''),
        ('사용자',     '쿠폰', 'Phase 1 — 남은', 'P22 — 회원 QR (사용자 측)', 'mobile 마이페이지 회원 QR (URL 토큰)', '⬜', ''),
        ('시설관리자', '쿠폰', '이전 완료', 'provider Coupons·CouponForm UI', '쿠폰 목록·생성·통계 UI 완성, 데이터는 mock', '✅', ''),
        ('시설관리자', '쿠폰', 'Phase 1 — 남은', 'P9 — provider Coupons 실연동', 'mock → /api/coupons 실연동, 발행/회수 정상 흐름', '⬜', ''),
        ('시설관리자', '쿠폰', 'Phase 1 — 남은', 'P22 — provider 스캔/적립', '회원 QR 스캔/코드입력 → 적립·사용', '⬜', ''),
        ('슈퍼어드민', '쿠폰', '이전 완료', 'admin 쿠폰 통계', 'admin coupon stats API + UI', '✅', 'CouponStats placeholder 일부 → P11'),

        # ════════ 스탬프 ════════
        ('공통-BE',    '스탬프', '이전 완료', '스탬프 적립/리워드 API', '/api/stamps accrue/list + 시설별 정책 + BLE 자동 적립', '✅', ''),
        ('사용자',     '스탬프', '이전 완료', 'mobile 스탬프 화면', 'stamps_screen — 시설별 카드/진행률/보상', '✅', ''),
        ('시설관리자', '스탬프', '이전 완료', 'provider Stamps·StampForm UI', '정책·통계 UI 완성, 데이터는 mock', '✅', ''),
        ('시설관리자', '스탬프', 'Phase 1 — 남은', 'P9 — provider Stamps 실연동', 'mock → /api/stamps 실연동', '⬜', ''),
        ('시설관리자', '스탬프', 'Phase 1 — 남은', 'P22 — 수동 적립(staff)', '회원 QR 스캔 → 스탬프 수동 적립 (auto/staff 모드)', '⬜', ''),

        # ════════ 채팅 ════════
        ('공통-BE',    '채팅', '이전 완료', 'chat 전체 API', '/api/chat rooms·messages·SSE 스트림·read + chat_blocks + is_blocked 가드', '✅', ''),
        ('공통-BE',    '채팅', '이전 완료', 'abuse_reports + chat_blocks', '/api/abuse-reports + /api/admin/abuse-reports + /api/blocks', '✅', ''),
        ('공통-BE',    '채팅', 'Phase 1 ✅', 'P8 — /api/chat/reports 신규', 'abuse_reports → ChatMonitor용 신고 큐 변환, super_admin 가드', '✅', '⚠ app.py 재시작 후 활성'),
        ('사용자',     '채팅', '이전 완료', 'mobile 채팅 화면', 'chat_list_screen + chat_detail_screen (SSE 실시간) + 신고/차단 + 가이드라인 모달', '✅', '재연결 미지원이었음'),
        ('사용자',     '채팅', 'Phase 1 ✅', 'P8 — mobile SSE 재연결', 'StreamController 기반, 지수 backoff(1→30s), ?after_id= 누락 보충', '✅', ''),
        ('사용자',     '채팅', '남은 — P8b', '뷰어별 번역 표시', 'list_messages·SSE 응답에 ?lang= 기준 번역 포함 → mobile UI 노출', '⬜', 'USP 기능'),
        ('시설관리자', '채팅', '이전 완료', 'provider CustomerChat UI 골격', '대화창 UI 완성, 데이터는 DUMMY_CHATS 7개 더미', '✅', ''),
        ('시설관리자', '채팅', '이전 완료', 'provider ChatService 메서드', 'openRoom/listRooms/listMessages/sendMessage/markRead/subscribe(SSE) 다 작성됨', '✅', '호출만 안 되고 있었음'),
        ('시설관리자', '채팅', 'Phase 1 ✅', 'P8 — provider CustomerChat 실연동', 'DUMMY 제거 → ChatService 5종 호출 + 30초 폴링 + 낙관적 전송 + SSE 정리', '✅', ''),
        ('시설관리자', '채팅', '남은 — P8b', 'provider 번역 표시', 'CustomerChat translation 필드 실데이터 노출', '⬜', ''),
        ('슈퍼어드민', '채팅', '이전 완료', 'admin abuse + chat_blocks 처리', 'admin abuse_reports CRUD + chat_blocks 관리', '✅', 'PR #142'),
        ('슈퍼어드민', '채팅', '이전 완료', 'admin ChatMonitor UI', '신고 큐 테이블 UI 완성, /api/chat/reports 엔드포인트만 없었음', '✅', ''),
        ('공통-BE',    '채팅', '남은 — P8b', '번역 캐시 스키마', 'chat_message_translations 캐시 테이블 + translator.py 연결', '⬜', 'DeepL/Google Translate 키 후'),

        # ════════ 알림 (Inbox + Push) ════════
        ('공통-BE',    '알림', '이전 완료', '알림 API + 카테고리', '/api/notifications inbox·announcements·read + notification_preferences', '✅', ''),
        ('공통-BE',    '알림', '이전 완료', 'iOS APNs 직접 (PR #50)', 'APNs HTTP/2 + JWT ES256 — Apple 인증서/키만 필요', '✅', '자체구축 — Firebase 미사용'),
        ('공통-BE',    '알림', '이전 완료', 'Android 푸시', 'FCM 통합 (PR #44) — Google Play Services 의존', '✅', '⚠ 현실적으로 Android 자체구축 불가, FCM 무료 무제한이라 그대로 사용 권장'),
        ('사용자',     '알림', '이전 완료', 'mobile 알림 화면 + 권한 동의', 'notifications_screen (인박스/공지 탭) + notification_permission_dialog', '✅', '라우팅 보강 필요'),
        ('사용자',     '알림', 'Phase 1 — 남은', 'P10 — mobile 알림 라우팅', '알림 종류별 화면 이동 (coupon→쿠폰함, chat→채팅)', '⬜', ''),
        ('시설관리자', '알림', '이전 완료', 'provider Notifications UI', '받은 알림 + 시스템 공지 UI 완성, 데이터는 mockInbox 14건', '✅', ''),
        ('시설관리자', '알림', 'Phase 1 — 남은', 'P10 — provider Notifications 실연동', 'mockInbox 제거 → /api/notifications 실연동', '⬜', ''),
        ('슈퍼어드민', '알림', '이전 완료', 'admin 공지 CRUD + 발송', 'admin Announcements CRUD + 실 푸시 발송 통합', '✅', ''),

        # ════════ WiFi (1회 연결) ════════
        ('공통-BE',    'WiFi (1회 연결)', '이전 완료', 'wifi_profiles + handshake', '/api/beacon/wifi handshake (LIMIT 1) + wifi_profiles 기본', '✅', '로밍은 LIMIT 1 → 묶음 반환으로 확장 필요'),
        ('사용자',     'WiFi (1회 연결)', '이전 완료', 'mobile native plugin', 'iOS NEHotspotConfiguration + Android WifiNetworkSuggestion (자동 가입)', '✅', '1회 연결만'),
        ('사용자',     'WiFi (1회 연결)', '이전 완료', 'mobile WifiConnectScreen', 'BLE 핸드셰이크 → WiFi 정보 전달 + OS 자동 가입 트리거', '✅', ''),
        ('시설관리자', 'WiFi (1회 연결)', '이전 완료', 'provider WifiSettings UI', 'WiFi 등록·수정·비활성 UI 완성, 가짜 OCR 자동입력 있었음', '✅', 'OCR 제거됨'),
        ('시설관리자', 'WiFi (1회 연결)', 'Phase 1 ✅', 'P6 — OCR 허위 제거', 'runOcrMock 삭제 → 정직한 수동입력 UI, 사진은 참고 첨부로 재정의', '✅', 'C5 해소'),

        # ════════ WiFi 로밍 (B 풀스코프) ════════
        ('공통-BE',    'WiFi 로밍', 'Phase 1 — 남은', 'P14 — 데이터 모델 재설계', 'wifi_profiles 확장 + beacon_wifi·units·wifi_access_grant·devices + beacons.role', '⬜', '6/말~7/초'),
        ('공통-BE',    'WiFi 로밍', 'Phase 1 — 남은', 'P15 — handshake 묶음 + BE', 'handshake LIMIT 1 제거 → 묶음 반환', '⬜', ''),
        ('시설관리자', 'WiFi 로밍', 'Phase 1 — 남은', 'P15 — provider WifiSettings 실연동 + 비콘 role', '비콘 role(wifi/cashier) UI + WiFi 실연동', '⬜', ''),
        ('슈퍼어드민', 'WiFi 로밍', 'Phase 1 — 남은', 'P15 — admin WiFi 등록화면', '슈퍼어드민용 WiFi 등록 신규 화면', '⬜', 'C10 해소'),
        ('사용자',     'WiFi 로밍', 'Phase 1 — 남은', 'P16 — mobile WiFi 클라이언트', '비콘→WiFi 묶음 fetch·캐시 + BSSID 검증 + "WiFi 변경됨" + 손님 자동/승인 + home 진입점', '⬜', ''),
        ('사용자',     'WiFi 로밍', 'Phase 1 — 남은', 'P17 — .mobileconfig 다건', '.mobileconfig 생성·다건 설치 (서명은 Apple 인증서 후)', '⬜', ''),
        ('공통-BE',    'WiFi 로밍', 'Phase 1 — 남은', 'P18 — credential_mode managed', '비번 교체 리마인드 + 인가 손님 자동 전파 + 알림 연동', '⬜', 'v1 flag 비공개'),
        ('슈퍼어드민', 'WiFi 로밍', 'Phase 1 — 남은', 'P19 — units/grant 관리', '호실·자리 시간제 권한 관리 UI', '⬜', 'v1 flag 비공개'),

        # ════════ 비콘 ════════
        ('공통-BE',    '비콘', '이전 완료', 'beacons lifecycle API', 'beacons 테이블 inventory→active→inactive/lost + claim API', '✅', ''),
        ('슈퍼어드민', '비콘', '이전 완료', 'admin Beacons 인벤토리', '인벤토리 CSV 입고 + claim 모니터 + 배터리·펌웨어 표시', '✅', ''),
        ('시설관리자', '비콘', '이전 완료', 'provider 비콘 claim 흐름', 'StoreInfo 내 비콘 claim UI + listBeacons', '✅', '실 fid는 P5 해소'),
        ('공통-BE',    '비콘', 'Phase 1 — 남은', 'P15 (병합) — beacons.role', 'beacons.role(wifi/cashier) 컬럼 + admin·provider UI', '⬜', ''),

        # ════════ i18n (12언어) ════════
        ('공통-BE',    'i18n', '이전 완료', 'translations API + DeepL 통합', 'translations 테이블 + GET /api/i18n/{lang} + DeepL 모듈', '✅', ''),
        ('슈퍼어드민', 'i18n', '이전 완료', 'admin i18n CRUD', '키별 다국어 입력·수정·자동번역 트리거', '✅', ''),
        ('사용자',     'i18n', '이전 완료', 'mobile supportedLocales 7개', '7개 언어 기본, 일부 화면만 적용', '✅', '12개로 확장 + 전 화면 → P2'),
        ('사용자',     'i18n', 'Phase 1 ✅', 'P2 — mobile I18nService 통일', '12 supportedLocales + 전 화면 t() 전환 + ko 시드 203→550', '✅', ''),
        ('공통-BE',    'i18n', 'Phase 1 ✅', 'P2 — DeepL 일괄번역 스크립트', 'translate_i18n_deepl.py — 키 활성화 시 22언어×549건 배치', '✅', ''),
        ('공통-BE',    'i18n', '남은', 'DeepL batch 실행', '11개 언어 batch 번역 (현재 ko만)', '⬜', 'DeepL 키 활성화 후'),

        # ════════ 정책/약관 ════════
        ('공통-BE',    '정책/약관', '이전 완료', 'policies API + 8 KIND', 'terms·privacy·location·marketing·push·camera·storage·third_party·age14 등록·버전관리', '✅', ''),
        ('사용자',     '정책/약관', '이전 완료', 'mobile policy_view', '약관 본문 + 푸터·설정·동의 흐름 진입', '✅', '?lang=ko 강제 → P13'),
        ('시설관리자', '정책/약관', '이전 완료', 'provider policy_view', '약관 본문 노출', '✅', ''),
        ('슈퍼어드민', '정책/약관', '이전 완료', 'admin Policies CRUD', '약관 등록·버전 발행 UI', '✅', ''),
        ('공통-BE',    '정책/약관', 'Phase 1 — 남은', 'P13 — 환불·청소년·쿠키 3종', 'BE policy KIND 추가 + admin Policies + mobile/provider 노출', '⬜', 'C14 해소'),

        # ════════ 디자인 시스템 ════════
        ('사용자',     '디자인 시스템', '이전 완료', 'mobile PwTheme + 보라', 'PwTheme 다크 + Pw* 위젯 13종 (4종은 P1에서 추가)', '✅', ''),
        ('시설관리자', '디자인 시스템', '이전 완료', 'provider 다크 + 녹색', 'provider 디자인 시스템 통합 PR #66~#87', '✅', ''),
        ('슈퍼어드민', '디자인 시스템', '이전 완료', 'admin 다크 + 블루', 'admin 다크 톤 통합 PR #65', '✅', ''),
        ('사용자',     '디자인 시스템', 'Phase 1 ✅', 'P1 — mobile 기반 단일화', '테마 단일화 + 시스템 폰트 + Pw* 4종 신규(Radio·Checkbox·Dropdown·Chip)', '✅', ''),
        ('시설관리자', '디자인 시스템', 'Phase 1 ✅', 'P3 — 웹 공용 모달', 'alert/confirm 33곳 → useDialog() + 색 토큰 정합 (provider 16 + admin 17)', '✅', ''),

        # ════════ 슈퍼어드민 (대시보드·통계) ════════
        ('슈퍼어드민', '대시보드·통계', '이전 완료', 'admin 기본 7페이지', 'Login + Dashboard + Beacons + Approvals + Battery + Announcements + Stores', '✅', 'PR #36~#38'),
        ('슈퍼어드민', '대시보드·통계', '이전 완료', 'admin Payments·Subscriptions·환불', '결제/구독 관리 + 환불 모달 — 실 API 연동', '✅', 'PR #39'),
        ('슈퍼어드민', '대시보드·통계', '이전 완료', 'admin Policies·Translations·Audit·Reports', '약관·번역·감사·신고 관리', '✅', ''),
        ('슈퍼어드민', '대시보드·통계', 'Phase 1 — 남은', 'P11 — Dashboard 가짜데이터 제거', '실 통계 API 연동', '⬜', ''),
        ('슈퍼어드민', '대시보드·통계', 'Phase 1 — 남은', 'P11 — StaffMonitor·CouponStats placeholder', '실 데이터 연동', '⬜', ''),
        ('슈퍼어드민', '대시보드·통계', 'Phase 1 — 남은', 'P20 — app-versions UI', '백엔드 완성, admin UI만 신규', '⬜', 'C11 해소'),

        # ════════ 직원 관리 ════════
        ('공통-BE',    '직원 관리', '이전 완료', '백엔드 staff API', '직원 초대/권한/관리 백엔드', '✅', ''),
        ('시설관리자', '직원 관리', '이전 완료', 'provider StaffManagement UI', '직원 목록·초대·권한 UI 완성, 데이터는 mock', '✅', ''),
        ('시설관리자', '직원 관리', 'Phase 1 — 남은', 'P11 — provider StaffManagement 실연동', 'mock → 실 staff API 연동', '⬜', ''),
        ('슈퍼어드민', '직원 관리', 'Phase 1 — 남은', 'P11 — admin StaffMonitor 실연동', '시설별 직원 모니터링', '⬜', ''),

        # ════════ mobile 심의 직격 ════════
        ('사용자',     '심의 직격', '이전 완료', 'consent 단계 + 동의', '8 KIND 동의 + 미성년자 보호 + 약관 본문', '✅', 'placeholder 노출 버그'),
        ('사용자',     '심의 직격', '이전 완료', 'settings 화면', '계정·알림·약관·고객지원·회원탈퇴', '✅', 'dev API URL 노출 + 앱 버전 하드코딩'),
        ('사용자',     '심의 직격', 'Phase 1 — 남은', 'P12 — consent placeholder 제거', 'placeholder 본문 노출 버그 수정', '⬜', '심의 reject 방지'),
        ('사용자',     '심의 직격', 'Phase 1 — 남은', 'P12 — 동의 로드 실패 복구', '네트워크 오류 시 재시도/안내', '⬜', ''),
        ('사용자',     '심의 직격', 'Phase 1 — 남은', 'P12 — settings dev 정보 제거 + 앱 버전 동적', 'API URL 제거 + package_info_plus', '⬜', 'C9 해소'),

        # ════════ 앱 버전관리 ════════
        ('공통-BE',    '앱 버전관리', '이전 완료', 'BE routes/version.py + app_versions', 'GET/PUT /api/admin/app-versions + 모바일 GET /api/version', '✅', '코드 완성 — admin UI만 필요'),
        ('슈퍼어드민', '앱 버전관리', 'Phase 1 — 남은', 'P20 — admin app-versions UI', '버전 등록·강제업데이트/권장 토글·OS별', '⬜', ''),
        ('사용자',     '앱 버전관리', 'Phase 1 — 남은', 'P20 — mobile 최소버전 게이트', 'splash 버전 체크 → 강제 업데이트 모달', '⬜', '일부 처리 존재'),

        # ════════ 심의 메타 자산 ════════
        ('인프라',     '심의 메타', 'Phase 1 — 남은', 'P21 — iOS PrivacyInfo.xcprivacy', 'iOS 17.4+ 필수 — 데이터 수집/추적 명시', '⬜', '심의 reject 방지'),
        ('인프라',     '심의 메타', 'Phase 1 — 남은', 'P21 — Bundle ID 확정', 'co.triggersoft.pathwave 등 최종', '⬜', ''),
        ('인프라',     '심의 메타', 'Phase 1 — 남은', 'P21 — Android Photo Picker', 'Android 13+ 신규 권한 모델', '⬜', ''),
        ('인프라',     '심의 메타', 'Phase 1 — 남은', 'P21 — 계정삭제 웹 URL', 'Google Play 정책 — 앱 외부 웹 URL 제공', '⬜', ''),

        # ════════ 회사 정보 (footer) ════════
        ('공통-BE',    '회사 정보', '이전 완료', 'company_info API (Phase M)', '슈퍼어드민 입력값 GET /api/company-info', '✅', ''),
        ('사용자',     '회사 정보', '이전 완료', 'mobile PwFooter', 'CompanyInfoService 실연동 — DB값 + i18n fallback', '✅', ''),
        ('시설관리자', '회사 정보', '이전 완료', 'provider PwFooter', 'CompanyInfoService 실연동', '✅', ''),
        ('슈퍼어드민', '회사 정보', '남은', '실 법인정보 입력', '슈퍼어드민이 트리거소프트 실 정보 admin에서 입력', '⬜', '법인 등기 완료 — 등록만 남음'),

        # ════════ 운영 인프라 ════════
        ('인프라',     '운영 인프라', '이전 완료', 'BE 보안 강화', 'SECRET_KEY/AES_KEY ENV + CORS 화이트리스트 + rate-limit (PR #35)', '✅', ''),
        ('인프라',     '운영 인프라', '이전 완료', 'BE provider 추상화', 'PG(sim/toss) + Email(stub/sendgrid/smtp) + Push(stub/fcm/apns) 추상화', '✅', '키 활성화 시 즉시 전환'),
        ('인프라',     '운영 인프라', '이전 완료', 'BE gunicorn/wsgi + Sentry', '프로덕션 배포 골격 + Sentry 통합', '✅', ''),
        ('인프라',     '운영 인프라', '이전 완료', 'BE PostgreSQL 어댑터', 'DATABASE_URL ENV 자동 분기 (sqlite ↔ pg)', '✅', ''),
        ('인프라',     '운영 인프라', 'Phase 1.5 — 남은', '개발환경 서버 구축', '국내 클라우드(가비아 G클라우드 등) + Postgres + 환경변수 키 주입', '⬜', '코드 완료 후 출시 전 단계'),
        ('인프라',     '운영 인프라', 'Phase 1.5 — 남은', '통합 테스트 (3콘솔 + mobile)', '실 서버 + 실 키 + 3콘솔 + mobile 실 기기 walk-through', '⬜', ''),
        ('인프라',     '운영 인프라', '남은', '운영 서버 배포', '개발환경 검증 → 운영 서버 전환', '⬜', '심의 제출 직전'),

        # ════════ 후속 단계 (Phase 2~5) ════════
        ('인프라',     'Phase 2~4 테스트', '남은', 'W7 — 6 페르소나 테스트 시드', '외국인/한국인/소규모/중대형/직원/슈퍼어드민 시나리오 + walk-through', '⬜', '7월 중순~하순'),
        ('인프라',     'Phase 5 제출', '남은', '스토어 메타데이터 + 빌드', 'iOS/Android 빌드 + 스크린샷 + 메타데이터(다국어) + 심의 제출', '⬜', '7월 하순~8월 초'),
    ]

    last_domain = ''
    for it in items:
        ws.append(it)
        r = ws.max_row
        # 주체 색상
        actor_color = ACTOR_COLOR.get(it[0])
        if actor_color:
            ws.cell(row=r, column=1).fill = PatternFill('solid', start_color=actor_color)
            ws.cell(row=r, column=1).alignment = Alignment(horizontal='center', vertical='center')
            ws.cell(row=r, column=1).font = Font(name=FONT, bold=True)
        # 도메인 강조
        if it[1] != last_domain:
            ws.cell(row=r, column=2).font = Font(name=FONT, bold=True)
            ws.cell(row=r, column=2).fill = SUBHEADER_FILL
            last_domain = it[1]
        # 상태 색상
        status_fill = {'✅': DONE_FILL, '◑': PARTIAL_FILL, '🔄': ACTIVE_FILL, '⬜': TODO_FILL}.get(it[5])
        if status_fill:
            ws.cell(row=r, column=6).fill = status_fill
            ws.cell(row=r, column=6).alignment = Alignment(horizontal='center', vertical='center')

    apply_table(ws, header_row, ws.max_row, len(headers))
    for i, w in enumerate([12, 22, 16, 32, 56, 8, 28], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[header_row].height = 28

    # ── Sheet: Phase 1 PR 체크리스트 ────────────────────────────────────
    ws2 = wb.create_sheet('Phase 1 PR 체크리스트')
    pr_headers = ['PR', '분류', '주체 영향', '도메인', '내용 요약',
                  '상태', '진척율', '담당', '시작일', '목표일', '완료일', '비고']
    ws2.append(pr_headers)
    prs = [
        ('P1', '인프라', '사용자', 'mobile 디자인 기반', '테마 단일화 + 시스템 폰트 + Pw* 4종', '✅', '1인', '2026-05-21', '2026-05-22', today, ''),
        ('P2', '인프라', '사용자·공통', 'mobile i18n', '12언어 + 전 화면 t() + ko 시드 550 + DeepL 스크립트', '✅', '1인', '2026-05-21', '2026-05-22', today, ''),
        ('P3', '인프라', '시설관리자·슈퍼어드민', '웹 디자인 시스템', 'alert/confirm 33곳 → useDialog + 색 토큰', '✅', '1인', '2026-05-21', '2026-05-22', today, ''),
        ('P4', 'Critical', '시설관리자·공통', '인증 우회 제거', 'DEV_AUTO_LOGIN env 게이트 + 실 로그인폼 + /forgot-password 정식', '✅', '1인', today, today, today, '⚠ app.py 재시작 필요'),
        ('P5', 'Critical', '시설관리자', '매장·회사정보 실연동', 'StoreInfo 실연동 + PwFooter + dead code 정리', '✅', '1인', today, today, today, ''),
        ('P6', 'Critical', '시설관리자', 'OCR 허위 제거', '가짜 OCR 자동입력 → 정직한 수동입력 UI', '✅', '1인', today, today, today, ''),
        ('P7', 'Critical', '시설관리자', '결제·구독 실연동', '카드 localStorage 제거(PCI) + BillingService + 실연동', '✅', '1인', today, today, today, ''),
        ('P8', 'Critical', '전체', '채팅 도메인', 'provider 실연동 + admin BE + mobile SSE 재연결', '◑', '1인', today, today, today, '번역=P8b, ⚠ app.py 재시작'),
        ('P8b', 'Critical', '전체', '채팅 자동 번역', '번역 캐시 + 뷰어별 언어 + translator 연결', '⬜', '1인', '', '키 확보 후', '', 'DeepL 키 후'),
        ('P9', 'Critical', '사용자·시설관리자', '쿠폰·스탬프 실연동', 'mock→실연동 + 사용 silent error', '⬜', '1인', '', '2026-06-중', '', ''),
        ('P10', 'Critical', '전체', '알림 도메인', 'provider 실연동 + mobile 라우팅', '⬜', '1인', '', '2026-06-중', '', ''),
        ('P11', 'Critical', '시설관리자·슈퍼어드민', '대시보드·직원', 'Dashboard·StaffManagement 실연동', '⬜', '1인', '', '2026-06-중', '', ''),
        ('P12', 'Critical', '사용자', 'mobile 심의 직격', 'consent placeholder + dev 정보 제거 + 버전 동적화', '⬜', '1인', '', '2026-06-중', '', ''),
        ('P13', 'Critical', '전체', '약관 3종', '환불·청소년·쿠키 정책', '⬜', '1인', '', '2026-06-중', '', ''),
        ('P14', 'WiFi 로밍 B', '공통', 'WiFi 데이터 모델', 'wifi_profiles 확장 + 신규 테이블', '⬜', '1인', '', '2026-06-말~7월초', '', ''),
        ('P15', 'WiFi 로밍 B', '시설관리자·슈퍼어드민', 'WiFi 등록·연동', 'handshake 묶음 + admin 등록 + provider WifiSettings', '⬜', '1인', '', '2026-07-초', '', ''),
        ('P16', 'WiFi 로밍 B', '사용자', 'mobile WiFi 클라이언트', '비콘→WiFi 묶음 + BSSID 검증', '⬜', '1인', '', '2026-07-초', '', ''),
        ('P17', 'WiFi 로밍 B', '사용자', '.mobileconfig 다건', '다건 설치', '⬜', '1인', '', '2026-07-중', '', '서명은 인증서 후'),
        ('P18', 'WiFi 로밍 B', '시설관리자·사용자', 'credential_mode managed', '비번 교체 리마인드 + 자동 전파', '⬜', '1인', '', '2026-07-중', '', 'v1 flag 비공개'),
        ('P19', 'WiFi 로밍 B', '슈퍼어드민·시설관리자', 'units/grant 관리', '호실·자리 시간제 권한', '⬜', '1인', '', '2026-07-중', '', 'v1 flag 비공개'),
        ('P20', '심의 마무리', '슈퍼어드민·사용자', '앱 버전관리', 'admin app-versions UI + mobile 게이트', '⬜', '1인', '', '2026-07-중', '', ''),
        ('P21', '심의 마무리', '인프라', '심의 메타 자산', 'PrivacyInfo + Bundle ID + Photo Picker', '⬜', '1인', '', '2026-07-중', '', ''),
        ('P22', '회원 QR', '사용자·시설관리자', '쿠폰·스탬프 회원 QR', '회원 QR + provider 스캔/코드입력', '⬜', '1인', '', '2026-07-초~중', '', ''),
    ]
    for row in prs:
        ws2.append(row)
    for r in range(2, len(prs) + 2):
        status_cell = ws2.cell(row=r, column=6).coordinate
        ws2.cell(row=r, column=7).value = (
            f'=IF({status_cell}="✅",1,IF({status_cell}="🔄",0.5,'
            f'IF({status_cell}="◑",0.7,IF({status_cell}="🔎",0.9,0))))'
        )
        ws2.cell(row=r, column=7).number_format = PCT_FMT
        status = ws2.cell(row=r, column=6).value
        fill = {'✅': DONE_FILL, '◑': PARTIAL_FILL, '🔄': ACTIVE_FILL, '🔎': ACTIVE_FILL, '⬜': TODO_FILL}.get(status)
        if fill:
            ws2.cell(row=r, column=6).fill = fill
            ws2.cell(row=r, column=6).alignment = Alignment(horizontal='center', vertical='center')
        for col in (9, 10, 11):
            ws2.cell(row=r, column=col).number_format = DATE_FMT
            ws2.cell(row=r, column=col).font = INPUT_FONT
        ws2.cell(row=r, column=8).font = INPUT_FONT
    dv = DataValidation(type='list', formula1='"⬜,🔄,🔎,◑,✅"', allow_blank=True)
    dv.add(f'F2:F{len(prs)+1}')
    ws2.add_data_validation(dv)
    apply_table(ws2, 1, len(prs) + 1, len(pr_headers))
    for i, w in enumerate([6, 12, 20, 22, 46, 8, 9, 9, 12, 18, 12, 28], 1):
        ws2.column_dimensions[get_column_letter(i)].width = w
    ws2.row_dimensions[1].height = 28

    # ── Sheet: 단계별 일정 ──────────────────────────────────────────────
    ws3 = wb.create_sheet('단계별 일정')
    ws3.append(['단계', '내용', '예상 기간', '누적', '비고'])
    schedule = [
        ('이전 작업 (~Phase 0)', 'PR #1~#51 + 디자인 통합', '~수개월', '2026-05-21', '완료'),
        ('Phase 0 전수 감사', '갭 14 Critical + High 발굴', '~1일', '2026-05-21', '완료'),
        ('Phase 1 인프라', 'P1~P3', '~4일', '2026-05-22', '완료'),
        ('Phase 1 Critical', 'P4~P13', '~2주', '2026-06-중', 'P4~P8 완료'),
        ('Phase 1 WiFi 로밍 B', 'P14~P19', '~2.5~3주', '2026-07-초~중', 'flag 비공개'),
        ('Phase 1 회원 QR', 'P22 (P9 이후 병행)', '~1주', '2026-07-초~중', ''),
        ('Phase 1 심의 마무리', 'P20~P21', '~3일', '2026-07-중', ''),
        ('Phase 1.5 — 개발환경 구축', '국내 클라우드 서버 + Postgres + 환경변수 키 주입', '~3일', '2026-07-중', '신규 — 운영 반영 전'),
        ('Phase 1.5 — 통합 테스트', '실 서버 + 실 키 + 3콘솔 + mobile 실기기 walk-through', '~4일', '2026-07-중~하순', '신규'),
        ('Phase 2~4 페르소나 검증', '6 페르소나 시나리오', '~1주', '2026-07-하순', ''),
        ('Phase 5 제출', '빌드 + 스토어 메타데이터', '며칠', '2026-07-하순', ''),
        ('출시', '앱스토어/Play 공개', '—', '2026-07-하순~8월 초', ''),
        ('외부 서비스 신청', '법인카드 수취 후 일괄', '~1주 (심사 1~2주)', '2026-06-02 주', '병행'),
    ]
    for row in schedule:
        ws3.append(row)
    apply_table(ws3, 1, len(schedule) + 1, 5)
    for i, w in enumerate([26, 50, 16, 18, 36], 1):
        ws3.column_dimensions[get_column_letter(i)].width = w
    ws3.row_dimensions[1].height = 28

    # ── Sheet: 요약 ────────────────────────────────────────────────────
    ws4 = wb.create_sheet('요약', 0)
    ws4['A1'] = 'PathWave 개발 체크리스트 요약'
    ws4['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
    ws4.merge_cells('A1:C1')
    ws4.append([])
    ws4.append(['지표', '값'])
    for c in (1, 2):
        ws4.cell(row=3, column=c).font = HEADER_FONT
        ws4.cell(row=3, column=c).fill = HEADER_FILL
        ws4.cell(row=3, column=c).alignment = Alignment(horizontal='center')
        ws4.cell(row=3, column=c).border = BORDER
    summary = [
        ('총 PR 수 (Phase 1)',   "=COUNTA('Phase 1 PR 체크리스트'!A2:A30)"),
        ('완료 (✅)',            "=COUNTIF('Phase 1 PR 체크리스트'!F2:F30,\"✅\")"),
        ('부분 완료 (◑)',       "=COUNTIF('Phase 1 PR 체크리스트'!F2:F30,\"◑\")"),
        ('진행중 (🔄)',         "=COUNTIF('Phase 1 PR 체크리스트'!F2:F30,\"🔄\")"),
        ('검토중 (🔎)',         "=COUNTIF('Phase 1 PR 체크리스트'!F2:F30,\"🔎\")"),
        ('대기 (⬜)',            "=COUNTIF('Phase 1 PR 체크리스트'!F2:F30,\"⬜\")"),
        ('가중 평균 진척율',    "=AVERAGE('Phase 1 PR 체크리스트'!G2:G30)"),
        ('업데이트 일자',        today),
        ('외부 서비스 신청 시작', '2026-06-02 주'),
        ('Phase 1.5 개발환경+테스트', '2026-07 중~하순 (신규 단계)'),
        ('목표 출시일',          '2026-07-하순~8월 초'),
    ]
    for i, (label, value) in enumerate(summary):
        r = 4 + i
        ws4.cell(row=r, column=1).value = label
        ws4.cell(row=r, column=2).value = value
        for c in (1, 2):
            ws4.cell(row=r, column=c).border = BORDER
        if label == '가중 평균 진척율':
            ws4.cell(row=r, column=2).number_format = PCT_FMT
            ws4.cell(row=r, column=2).fill = ASSUME_FILL
        if isinstance(value, str) and value.startswith('='):
            ws4.cell(row=r, column=2).font = LINK_FONT
    ws4.column_dimensions['A'].width = 28
    ws4.column_dimensions['B'].width = 42
    ws4.append([])
    ws4.cell(row=ws4.max_row + 1, column=1).value = '주체 컬러 범례'
    ws4.cell(row=ws4.max_row, column=1).font = Font(name=FONT, bold=True, color='1F4E78')
    for actor, color in ACTOR_COLOR.items():
        ws4.append([actor, ''])
        ws4.cell(row=ws4.max_row, column=1).fill = PatternFill('solid', start_color=color)
        ws4.cell(row=ws4.max_row, column=1).font = Font(name=FONT, bold=True)
        desc = {
            '사용자': 'mobile 앱 사용자 (앱 손님)',
            '시설관리자': 'provider-web 점주',
            '슈퍼어드민': 'admin-web 운영자',
            '공통-BE': '백엔드 (다중 영향)',
            '인프라': '운영 인프라/도구/심의 메타',
        }.get(actor, '')
        ws4.cell(row=ws4.max_row, column=2).value = desc

    out = 'docs/exports/pathwave_dev_checklist.xlsx'
    force_workbook_font(wb)
    wb.save(out)
    return out


# ═══════════════════════════════════════════════════════════════════════════
# FILE 2 — 서비스 신청 (가격+링크) + 초기 세팅비 + 월별 운영비 + BEP
# ═══════════════════════════════════════════════════════════════════════════
def build_services_costs():
    wb = Workbook()
    wb.remove(wb.active)

    # ── Sheet: 서비스 신청 체크리스트 (가격 상세 + 신청 링크) ─────────
    ws = wb.create_sheet('서비스 신청 체크리스트')
    headers = ['우선순위', '카테고리', '서비스', '제공사', '필수/선택',
               '가격 상세', '신청 링크', '가입 계정',
               '신청 상태', '신청 예정', '활성 예정', '환경변수 / 비고']
    ws.append(headers)
    # (pri, cat, name, vendor, req, price_detail, link, account, status, applied, activated, env_note)
    services = [
        # === 우선순위 1 ===
        (1, '결제',       '토스페이먼츠',           'Toss Payments',                '필수', '거래 수수료 2.9% + 33원/건 (가입 무료)',          'https://merchant.tosspayments.com/',                  'admin@pathwave',    '대기', '2026-06-02', '2026-06-16', 'TOSS_SECRET_KEY · 심사 1~2주'),
        (1, '스토어',     'Apple Developer Program', 'Apple',                        '필수', '$99/년 (₩148,500 @1500)',                         'https://developer.apple.com/programs/enroll/',         'admin@pathwave',    '대기', '2026-06-02', '2026-06-03', '이메일 이관 어려움 — admin@ 필수'),
        (1, '스토어',     'Google Play Console',     'Google',                        '필수', '$25 일회성 (₩37,500 @1500)',                      'https://play.google.com/console/u/0/signup',           'admin@pathwave',    '대기', '2026-06-02', '2026-06-03', ''),
        (1, '도메인',     'pathwave.co.kr (서비스)',  '가비아',                         '필수', '연 3만원 (월 ~₩2,500)',                           'https://www.gabia.com/',                               'admin@pathwave',    '대기', '2026-06-02', '2026-06-02', ''),
        (1, '도메인',     'triggersoft.kr (법인)',    '가비아',                         '필수', '연 3만원 (월 ~₩2,500)',                           'https://www.gabia.com/',                               'admin@triggersoft', '대기', '2026-06-02', '2026-06-02', '법인 사업·세무·회계'),
        (1, '호스팅',     'Cloudflare DNS/Tunnel',    'Cloudflare',                    '필수', '무료',                                            'https://dash.cloudflare.com/sign-up',                  'admin@pathwave',    '대기', '2026-06-02', '2026-06-02', 'DNS + dev 외부 접근'),
        (1, '호스팅',     '가비아 G클라우드 (서버+DB)','가비아',                         '필수', '월 ~5만원 (Light 통합)',                          'https://cloud.gabia.com/',                             'admin@pathwave',    '대기', '2026-06-02', '2026-06-09', '국내 클라우드 — AWS 대신'),
        (1, '호스팅',     'NHN Cloud (백업 옵션)',    'NHN Cloud',                     '선택', '월 5~7만원 (m2.c2m4)',                            'https://www.toast.com/kr',                             'admin@pathwave',    '대기', '검토',       '',           '가비아 대체 옵션'),
        (1, '호스팅',     '네이버 클라우드 (백업 옵션)','Naver Cloud',                   '선택', '월 3~7만원 (micro)',                              'https://www.ncloud.com/',                              'admin@pathwave',    '대기', '검토',       '',           '가비아 대체 옵션'),
        (1, '호스팅',     '프론트 정적 호스팅',       'Vercel / Netlify / CFP',        '필수', '무료 tier',                                       'https://vercel.com/signup',                            'admin@pathwave',    '대기', '2026-06-02', '2026-06-03', 'admin-web + provider-web'),
        (1, '인증',       'Firebase Auth',           'Google',                        '필수', '무료 (10K MAU)',                                   'https://console.firebase.google.com/',                 'dev@pathwave',      '대기', '2026-06-02', '2026-06-03', '인증 전용 — 푸시는 자체구축'),
        (1, '푸시(iOS)',  'APNs (Apple Push)',       'Apple',                         '필수', '무료 (Apple Developer 포함)',                      'https://developer.apple.com/account/resources/',       'admin@pathwave',    '대기', '2026-06-03', '2026-06-09', '자체구축 — APNs HTTP/2 + JWT (PR #50)'),
        (1, '푸시(Android)','FCM 또는 자체 (현실 한계)','Google',                       '필수', '무료 무제한',                                      'https://console.firebase.google.com/',                 'dev@pathwave',      '대기', '검토',       '',           '⚠ Android 백그라운드 푸시는 FCM 외 사실상 불가 (Google Play Services 의존). 사용자 정책상 자체구축 원할 경우 in-app WebSocket fallback 만 가능'),
        (1, '이메일도메인','Google Workspace (Pathwave)','Google',                     '필수', '$7/계정/월 (₩10,500 @1500) + alias 4 무료',       'https://workspace.google.com/',                        'admin@pathwave',    '대기', '2026-06-02', '2026-06-02', '5개 alias (admin/dev/support/noreply/info)'),
        (1, '이메일도메인','Google Workspace (Triggersoft)','Google',                   '필수', '$7/계정/월 (₩10,500 @1500)',                      'https://workspace.google.com/',                        'admin@triggersoft', '대기', '2026-06-02', '2026-06-02', '법인 운영 1계정'),
        (1, '상표등록',   '상표등록 — 패스웨이브',     '특허청 (셀프 또는 변리사)',       '필수', '셀프 약 27만원 / 변리사 위탁 50~80만원',          'https://www.patent.go.kr/',                            'admin@triggersoft', '대기', '2026-06-09', '심사 6~12개월', '출원료 56,000 + 등록료 211,000 (10년) — 셀프'),
        (1, '상표등록',   '상표등록 — 트리거소프트',   '특허청 (셀프 또는 변리사)',       '필수', '셀프 약 27만원 / 변리사 위탁 50~80만원',          'https://www.patent.go.kr/',                            'admin@triggersoft', '대기', '2026-06-09', '심사 6~12개월', '법인명 상표'),

        # === 우선순위 2 (6/2주 신청, 심사 1~2주) ===
        (2, '소셜로그인', '카카오 로그인',            'Kakao',                          '필수', '무료',                                            'https://developers.kakao.com/',                        'info@pathwave',     '대기', '2026-06-02', '2026-06-16', '검수 1~2주'),
        (2, '소셜로그인', '네이버 로그인',            'Naver',                          '필수', '무료',                                            'https://developers.naver.com/',                        'info@pathwave',     '대기', '2026-06-02', '2026-06-09', ''),
        (2, '알림톡/SMS', '솔라피 알림톡',            'Solapi',                        '필수', '건당 7~9원 (사용량)',                              'https://solapi.com/',                                  'dev@pathwave',      '대기', '2026-06-02', '2026-06-16', '템플릿 사전심사 1~2주'),
        (2, '알림톡/SMS', '솔라피 SMS 인증',          'Solapi',                        '필수', '건당 8~15원 (LMS 28~35원)',                       'https://solapi.com/',                                  'dev@pathwave',      '대기', '2026-06-02', '2026-06-09', '회원가입 인증'),
        (2, '이메일',     'SendGrid',                'Twilio',                        '필수', '무료 100통/일',                                    'https://signup.sendgrid.com/',                         'dev@pathwave',      '대기', '2026-06-02', '2026-06-03', '발신: support@'),
        (2, '모니터링',   'Sentry',                  'Sentry',                        '필수', '무료 5K events/월',                                'https://sentry.io/signup/',                            'dev@pathwave',      '대기', '2026-06-02', '2026-06-03', '백엔드 통합 완료'),
        (2, '지도',       'Google Maps API',         'Google',                        '필수', '월 $200 무료 크레딧',                              'https://console.cloud.google.com/',                    'dev@pathwave',      '대기', '2026-06-02', '2026-06-03', '카드 등록 필수'),

        # === 우선순위 3 ===
        (3, '본인인증',   'NICE / KCB / PASS',        '본인인증 사업자',                '선택', '계약 보증금 ~10만원 + 건당 30~80원',              'https://www.niceinfo.co.kr/',                          'admin@pathwave',    '대기', '2026-06-말', '2026-07-중', '미성년자 확인'),
        (3, '번역',       'DeepL Pro',               'DeepL',                         '선택', '무료 500K chars/월 / Starter ~€5/월',             'https://www.deepl.com/pro',                            'dev@pathwave',      '대기', '2026-07-초', '2026-07-중', 'P8b 채팅 자동번역 USP'),
        (3, '번역',       'Google Translate (대안)',  'Google',                        '선택', '$20/1M chars',                                    'https://console.cloud.google.com/',                    'dev@pathwave',      '대기', '대안',       '',           ''),
        (3, '자동화 S2',  'Channeltalk',              'Channel.io',                    '선택', '무료~5만원/월',                                    'https://channel.io/ko',                                'dev@pathwave',      '대기', '출시 후',    '',           ''),
        (3, '자동화 S2',  'ChatGPT API',              'OpenAI',                        '선택', '$0.15~3/M tokens',                                'https://platform.openai.com/signup',                   'dev@pathwave',      '대기', '출시 후',    '',           '응대 자동화'),
        (3, '자동화 S2',  'Make.com',                 'Make',                          '선택', '무료~$9~30/월',                                    'https://www.make.com/en/register',                     'dev@pathwave',      '대기', '출시 후',    '',           '노코드 허브'),
        (3, '자동화 S2',  'Buffer / Metricool',       'Buffer / Metricool',            '선택', '$6~15/월',                                        'https://buffer.com/pricing',                           'info@pathwave',     '대기', '출시 후',    '',           'SNS 자동'),
        (3, '자동화 S3',  'HubSpot CRM',              'HubSpot',                       '선택', '$20~50/월',                                        'https://www.hubspot.com/',                             'admin@pathwave',    '대기', '+3개월',     '',           ''),
        (3, '자동화 S2',  'Twilio Voice',             'Twilio',                        '선택', '분당 100~500원',                                   'https://www.twilio.com/',                              'admin@pathwave',    '대기', '+3개월',     '',           'AI 음성'),
    ]
    for s in services:
        ws.append(s)
    for r in range(2, len(services) + 2):
        # 신청 링크는 hyperlink
        link = ws.cell(row=r, column=7).value
        if link and isinstance(link, str) and link.startswith('http'):
            ws.cell(row=r, column=7).hyperlink = link
            ws.cell(row=r, column=7).font = Font(name=FONT, color='0563C1', underline='single')
        for col in (10, 11):
            ws.cell(row=r, column=col).font = INPUT_FONT
        status = ws.cell(row=r, column=9).value
        fill = {'활성': DONE_FILL, '검수중': PARTIAL_FILL, '신청중': ACTIVE_FILL,
                '대기': TODO_FILL, '검토': PARTIAL_FILL, '대안': TODO_FILL, '보류': PARTIAL_FILL}.get(status)
        if fill:
            ws.cell(row=r, column=9).fill = fill
            ws.cell(row=r, column=9).alignment = Alignment(horizontal='center', vertical='center')
        pri = ws.cell(row=r, column=1).value
        pri_color = {1: 'FFC7CE', 2: 'FFEB9C', 3: 'F2F2F2'}.get(pri)
        if pri_color:
            ws.cell(row=r, column=1).fill = PatternFill('solid', start_color=pri_color)
            ws.cell(row=r, column=1).alignment = Alignment(horizontal='center', vertical='center')
            ws.cell(row=r, column=1).font = Font(name=FONT, bold=True)
    dv1 = DataValidation(type='list', formula1='"대기,신청중,검수중,활성,검토,대안,보류"', allow_blank=True)
    dv1.add(f'I2:I{len(services)+1}')
    ws.add_data_validation(dv1)
    apply_table(ws, 1, ws.max_row, len(headers))
    for i, w in enumerate([7, 12, 28, 22, 9, 32, 38, 18, 10, 13, 13, 36], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 36

    # ── Sheet: 초기 세팅비 (1회성 / 연 1회) ────────────────────────────────
    ws_init = wb.create_sheet('초기 세팅비 (1회성)')
    ws_init['A1'] = '초기 세팅비 — 출시 전 1회성 / 연 1회 비용 (월별 시트에 분산 안 함)'
    ws_init['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
    ws_init.merge_cells('A1:D1')
    ws_init.append([])
    ws_init.append(['항목', '금액 (₩)', '주기', '비고'])
    init_items = [
        ('Apple Developer Program — 첫 회비',          148500, '연 1회',   '$99 × 1500'),
        ('Google Play Console — 등록비',                37500, '일회성',   '$25 일회성'),
        ('도메인 — pathwave.co.kr',                     30000, '연 1회',   '서비스 도메인 (가비아)'),
        ('도메인 — triggersoft.kr',                     30000, '연 1회',   '법인 도메인 (가비아)'),
        ('상표등록 — 패스웨이브 (셀프 출원)',           267000, '일회성',   '출원 56,000 + 등록 211,000 (10년) — 변리사 위탁 시 50~80만'),
        ('상표등록 — 트리거소프트 (셀프 출원)',          267000, '일회성',   '동일 — 법인명 상표'),
        ('Mac mini M1 16GB/256GB 중고 (선택)',          800000, '일회성',   '자본 여유 시 — 24/7 운영 베이스'),
        ('Mac mini 주변기기 (외장 SSD 등, 선택)',        80000, '일회성',   'Mac mini 옵션 시'),
        ('NICE 본인인증 — 계약 보증금 (선택)',          100000, '일회성',   '미성년자 확인 도입 시'),
        ('카카오 로그인 검수',                                0, '일회성',   '무료, 1~2주'),
        ('네이버 로그인 가입',                                0, '일회성',   '무료'),
        ('솔라피 알림톡 템플릿 등록·심사',                    0, '일회성',   '무료, 1~2주'),
        ('토스페이먼츠 가맹점 가입',                          0, '일회성',   '무료, 심사 1~2주'),
        ('사업자등록 (홈택스)',                               0, '일회성',   '무료'),
        ('통신판매업 신고',                                   0, '일회성',   '무료'),
        ('위치기반서비스사업 신고',                           0, '일회성',   '무료, 수 주 소요'),
        ('Cloudflare / Firebase / Sentry 가입',               0, '일회성',   '무료'),
        ('Google Workspace 초기 셋업',                        0, '일회성',   '월 정액에 포함'),
    ]
    for it in init_items:
        ws_init.append(it)
        r = ws_init.max_row
        ws_init.cell(row=r, column=2).font = INPUT_FONT
        ws_init.cell(row=r, column=2).number_format = KRW_FMT
    last_init = ws_init.max_row
    # 합계 (필수만 / 옵션 포함)
    ws_init.append(['소계 — 필수만 (Mac mini·NICE 제외)',
                    '=SUM(B4:B9)+SUM(B14:B21)', '', ''])
    ws_init.append(['소계 — 옵션 포함 (Mac mini + NICE)',
                    f'=SUM(B4:B{last_init})', '', '전체 포함'])
    for r in (ws_init.max_row - 1, ws_init.max_row):
        ws_init.cell(row=r, column=2).number_format = KRW_FMT
        ws_init.cell(row=r, column=2).font = Font(name=FONT, bold=True)
        ws_init.cell(row=r, column=2).fill = ASSUME_FILL
        ws_init.cell(row=r, column=1).font = Font(name=FONT, bold=True)
        ws_init.cell(row=r, column=1).fill = ASSUME_FILL
    apply_table(ws_init, 3, ws_init.max_row, 4)
    for i, w in enumerate([46, 16, 12, 44], 1):
        ws_init.column_dimensions[get_column_letter(i)].width = w

    # ── Sheet: 월별 운영비 시나리오 (반복만, MAU 1K / 10K / 100K) ─────
    ws2 = wb.create_sheet('월별 운영비 시나리오')
    ws2['A1'] = '월별 운영비 시나리오 — 반복 비용만 (1회성 제외)'
    ws2['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
    ws2.merge_cells('A1:E1')
    ws2.append([])
    ws2.append(['항목', 'MAU 1K (매장 10)', 'MAU 10K (매장 100)', 'MAU 100K (매장 500)', '비고'])
    scen = [
        ('서버 (가비아 G클라우드)',                 50000,  150000, 600000, '국내 — Light → Standard → 분리·HA'),
        ('DB (PG 통합/분리)',                        0,      30000,  200000, '초기 서버 포함 → MAU 10K부터 분리'),
        ('도메인 (2개 × 월할)',                     5000,   5000,   5000,   'pathwave + triggersoft'),
        ('알림톡 (매장당 100건/월 × 9원)',          9000,   90000,  450000, '매장 × 100건 × 9원'),
        ('SMS + 본인인증',                          5000,   30000,  200000, '회원가입·결제'),
        ('이메일 (SendGrid)',                       0,      5000,   50000,  '무료 100통/일'),
        ('Google Workspace (2계정 × $7)',           21000,  21000,  21000,  'pathwave + triggersoft @1500'),
        ('Sentry 모니터링',                         0,      0,      50000,  '무료 5K → 대규모 유료'),
        ('Firebase Auth',                            0,      0,      20000,  '무료 10K MAU → 초과 유료'),
        ('Google Maps (초과분)',                    0,      0,      30000,  '월 $200 크레딧'),
        ('푸시 (APNs + FCM — 무료)',                0,      0,      0,      'APNs 자체구축 + FCM 무료'),
    ]
    start = ws2.max_row + 1
    for row in scen:
        ws2.append(row)
        r = ws2.max_row
        for c in (2, 3, 4):
            ws2.cell(row=r, column=c).number_format = KRW_FMT
            ws2.cell(row=r, column=c).font = INPUT_FONT
    end = ws2.max_row
    ws2.append(['월 운영비 합계',
                f'=SUM(B{start}:B{end})',
                f'=SUM(C{start}:C{end})',
                f'=SUM(D{start}:D{end})',
                ''])
    total_row = ws2.max_row
    for c in (2, 3, 4):
        ws2.cell(row=total_row, column=c).number_format = KRW_FMT
        ws2.cell(row=total_row, column=c).font = Font(name=FONT, bold=True)
        ws2.cell(row=total_row, column=c).fill = ASSUME_FILL
    ws2.cell(row=total_row, column=1).font = Font(name=FONT, bold=True)
    ws2.cell(row=total_row, column=1).fill = ASSUME_FILL
    apply_table(ws2, 3, total_row, 5)
    for i, w in enumerate([34, 22, 22, 22, 38], 1):
        ws2.column_dimensions[get_column_letter(i)].width = w

    # ── Sheet: 손익분기점 (BEP) ────────────────────────────────────────
    ws_bep = wb.create_sheet('손익분기점 (BEP)')
    ws_bep['A1'] = '손익분기점 — 매장당 월 ₩10,000 매출 가정'
    ws_bep['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
    ws_bep.merge_cells('A1:E1')
    ws_bep.append([])
    ws_bep.append(['시나리오', '월 운영비 (₩)', '매장 수', '월 매출 (₩)', '월 손익 (₩)'])
    ws_bep.append(['MAU 1K (매장 10)',   "='월별 운영비 시나리오'!B15", 10,  '=C4*10000', '=D4-B4'])
    ws_bep.append(['MAU 10K (매장 100)', "='월별 운영비 시나리오'!C15", 100, '=C5*10000', '=D5-B5'])
    ws_bep.append(['MAU 100K (매장 500)', "='월별 운영비 시나리오'!D15", 500, '=C6*10000', '=D6-B6'])
    ws_bep.append([])
    ws_bep.append(['손익분기 매장 수 (각 시나리오)', '', '', '', ''])
    ws_bep.append(['MAU 1K 운영비 → BEP 매장 수',   "=B4/10000", '', '', '운영비 ÷ 1만원'])
    ws_bep.append(['MAU 10K 운영비 → BEP 매장 수',  "=B5/10000", '', '', ''])
    ws_bep.append(['MAU 100K 운영비 → BEP 매장 수', "=B6/10000", '', '', ''])
    for r in (3,):
        for c in (1, 2, 3, 4, 5):
            ws_bep.cell(row=r, column=c).font = HEADER_FONT
            ws_bep.cell(row=r, column=c).fill = HEADER_FILL
            ws_bep.cell(row=r, column=c).alignment = Alignment(horizontal='center')
            ws_bep.cell(row=r, column=c).border = BORDER
    for r in (4, 5, 6):
        for c in (1, 2, 3, 4, 5):
            ws_bep.cell(row=r, column=c).border = BORDER
        ws_bep.cell(row=r, column=2).font = LINK_FONT
        ws_bep.cell(row=r, column=2).number_format = KRW_FMT
        ws_bep.cell(row=r, column=3).font = INPUT_FONT
        ws_bep.cell(row=r, column=4).number_format = KRW_FMT
        ws_bep.cell(row=r, column=5).number_format = KRW_FMT
        ws_bep.cell(row=r, column=5).font = Font(name=FONT, bold=True)
        ws_bep.cell(row=r, column=5).fill = ASSUME_FILL
    for r in (9, 10, 11):
        for c in (1, 2, 3, 4, 5):
            ws_bep.cell(row=r, column=c).border = BORDER
        ws_bep.cell(row=r, column=2).number_format = '#,##0'
        ws_bep.cell(row=r, column=2).font = Font(name=FONT, bold=True)
        ws_bep.cell(row=r, column=2).fill = ASSUME_FILL
    ws_bep.cell(row=8, column=1).font = Font(name=FONT, bold=True, color='1F4E78')
    ws_bep.column_dimensions['A'].width = 32
    ws_bep.column_dimensions['B'].width = 18
    ws_bep.column_dimensions['C'].width = 14
    ws_bep.column_dimensions['D'].width = 18
    ws_bep.column_dimensions['E'].width = 18
    ws_bep.append([])
    ws_bep.cell(row=ws_bep.max_row + 1, column=1).value = '⚠ 매장당 월 1만원 매출 — 구조적 손익 분석 필요'
    ws_bep.cell(row=ws_bep.max_row, column=1).font = Font(name=FONT, bold=True, color='C00000')
    for n in [
        '· 매장당 매출 1만원은 인건비·자본비용 미반영 시점. 손익분기는 비용 회수만 의미',
        '· 매장 100개 미달 시 적자 — 초기에는 자본 투자 + B2B 영업 + 광고/스폰서 등 보완 매출 필요',
        '· 매장 증가 = 알림톡·SMS 사용량 증가 (비례) → 단가 협상력 필요',
        '· 자동화(Stage 2~3) 도구 도입 시 인건비 절감 효과로 BEP 낮춤',
        '· 추후 부가 수익원(번역 API 유료 / 광고 / 데이터 분석 등) 검토 필요',
    ]:
        ws_bep.append([n])
        ws_bep.cell(row=ws_bep.max_row, column=1).font = Font(name=FONT, color='505050')

    # ── 월별 연간 시트 빌더 (반복만, 1회성 제외) ─────────────────────
    def year_sheet(name, year, recurring_data, assumptions_note):
        ws = wb.create_sheet(name)
        ws['A1'] = f'{year}년 월별 운영비 (반복 비용만 — 1회성은 초기 세팅비 시트 참조)'
        ws['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
        ws.merge_cells('A1:N1')
        ws['A2'] = f'※ {assumptions_note}'
        ws['A2'].font = Font(name=FONT, italic=True, color='808080')
        ws.merge_cells('A2:N2')
        ws.append([])
        head = ['항목'] + [f'{m}월' for m in range(1, 13)] + ['연 합계']
        ws.append(head)
        header_row = ws.max_row

        rec_labels = [
            '서버 (가비아 G클라우드)', 'DB (PG)', '도메인 (월할)',
            '알림톡 (사용량)', 'SMS + 본인인증', '이메일 (SendGrid)',
            'Google Workspace (2계정)', 'Sentry', 'Firebase Auth',
            'Google Maps (초과)', '번역 API (P8b)',
        ]
        for label, monthly in zip(rec_labels, recurring_data):
            ws.append([label] + list(monthly))
            r = ws.max_row
            ws.cell(row=r, column=14).value = f'=SUM(B{r}:M{r})'
            for c in range(2, 14):
                ws.cell(row=r, column=c).number_format = KRW_FMT
                ws.cell(row=r, column=c).font = INPUT_FONT
            ws.cell(row=r, column=14).number_format = KRW_FMT
            ws.cell(row=r, column=14).font = Font(name=FONT, bold=True)
        last_item = ws.max_row

        ws.append(['월 운영비 합계 (반복만)'] +
                  [f'=SUM({get_column_letter(c)}{header_row+1}:{get_column_letter(c)}{last_item})'
                   for c in range(2, 14)] +
                  [f'=SUM(B{last_item+1}:M{last_item+1})'])
        total_r = ws.max_row
        for c in range(2, 15):
            ws.cell(row=total_r, column=c).number_format = KRW_FMT
            ws.cell(row=total_r, column=c).font = Font(name=FONT, bold=True)
            ws.cell(row=total_r, column=c).fill = ASSUME_FILL
        ws.cell(row=total_r, column=1).font = Font(name=FONT, bold=True)
        ws.cell(row=total_r, column=1).fill = ASSUME_FILL

        ws.append(['누계'] +
                  [f'={get_column_letter(c)}{total_r}' if c == 2
                   else f'={get_column_letter(c-1)}{total_r+1}+{get_column_letter(c)}{total_r}'
                   for c in range(2, 14)] +
                  [f'=N{total_r}'])
        cum_r = ws.max_row
        for c in range(2, 15):
            ws.cell(row=cum_r, column=c).number_format = KRW_FMT
            ws.cell(row=cum_r, column=c).font = LINK_FONT
        ws.cell(row=cum_r, column=1).font = Font(name=FONT, italic=True)

        apply_table(ws, header_row, cum_r, 14)
        ws.column_dimensions['A'].width = 30
        for c in range(2, 15):
            ws.column_dimensions[get_column_letter(c)].width = 11
        return total_r

    # 2026 — 1~5월 코드만(0), 6월 도메인·Workspace, 7월 서버 셋업, 8월 출시
    R2026 = [
        # 서버 — 7월 셋업, 8월부터 정상
        [0,0,0,0,0,0, 30000, 50000, 50000, 50000, 50000, 50000],
        # DB — 통합 (서버 포함, 별도 0)
        [0]*12,
        # 도메인 (월할) — 6월부터
        [0,0,0,0,0,5000, 5000, 5000, 5000, 5000, 5000, 5000],
        # 알림톡 — 출시 후 점진 (매장 0→10)
        [0,0,0,0,0,0, 0, 5000, 7000, 8000, 9000, 9000],
        # SMS + 본인인증
        [0,0,0,0,0,0, 0, 2000, 3000, 4000, 5000, 5000],
        # 이메일 (무료)
        [0]*12,
        # Workspace 2계정 — 6/2주부터
        [0,0,0,0,0,21000, 21000, 21000, 21000, 21000, 21000, 21000],
        # Sentry
        [0]*12,
        # Firebase Auth
        [0]*12,
        # Maps
        [0]*12,
        # 번역 (P8b — 2026 미가동)
        [0]*12,
    ]
    total_r_2026 = year_sheet('2026년 월별', 2026, R2026,
        '출시 = 2026-07 하순~08-초. 1~5월 코드 작업(비용 0). 6월 외부 신청 시작(도메인·Workspace). '
        '7월 서버 셋업 + Apple/Google Play(1회성은 별도). 8월 출시 후 MAU 0~1K, 매장 0→10')

    # 2027 — 분기별 점진 성장, 매장 20→200
    R2027 = [
        # 서버 — 분기별 스케일업
        [50000,50000,50000, 80000,80000,80000, 120000,120000,120000, 150000,150000,150000],
        # DB — Q3부터 분리
        [0,0,0, 0,0,0, 20000,20000,20000, 30000,30000,30000],
        # 도메인
        [5000]*12,
        # 알림톡 — 매장 20→30→50→100→200 (매장당 100건 × 9원)
        [18000,22500,27000, 36000,40500,45000, 63000,72000,90000, 135000,153000,180000],
        # SMS + 본인인증
        [5000,6000,7000, 10000,12000,15000, 18000,22000,28000, 35000,40000,45000],
        # 이메일
        [0,0,0, 0,3000,3000, 5000,5000,5000, 8000,10000,12000],
        # Workspace
        [21000]*12,
        # Sentry
        [0,0,0, 0,0,0, 0,0,30000, 30000,30000,30000],
        # Firebase Auth — MAU 10K+ 일부 유료
        [0]*9 + [10000,15000,20000],
        # Maps
        [0]*9 + [10000,20000,30000],
        # 번역 (P8b 가동)
        [0,0,0, 10000,15000,20000, 25000,30000,40000, 50000,60000,80000],
    ]
    total_r_2027 = year_sheet('2027년 월별', 2027, R2027,
        '점진 성장 — Q1: 매장 20~30(MAU 1~2K), Q2: 50(MAU 3~5K), Q3: 100(MAU 5~10K), '
        'Q4: 200(MAU 10K+). 알림톡 = 매장당 100건/월 × 9원')

    # ── Sheet: 연간 합계 (대시보드) ───────────────────────────────────
    ws_sum = wb.create_sheet('연간 합계', 0)
    ws_sum['A1'] = 'PathWave 운영비 — 연간 합계 (반복 + 초기 1회성 별도)'
    ws_sum['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
    ws_sum.merge_cells('A1:D1')
    ws_sum.append([])
    ws_sum.append(['항목', '금액 (₩)', '월 평균 (₩)', '비고'])
    ws_sum.append(['2026 반복 운영비 (8~12월 5개월)', f"='2026년 월별'!N{total_r_2026}", '=B4/5', '월별 반복만'])
    ws_sum.append(['2027 반복 운영비 (12개월)',       f"='2027년 월별'!N{total_r_2027}", '=B5/12', '월별 반복만'])
    ws_sum.append(['초기 세팅비 — 필수만',             "='초기 세팅비 (1회성)'!B22", '—', '2026 출시 전 한번에'])
    ws_sum.append(['초기 세팅비 — 옵션 포함',           "='초기 세팅비 (1회성)'!B23", '—', 'Mac mini + NICE 포함'])
    ws_sum.append(['2년 운영비 합계 (반복)',           '=B4+B5', '—', ''])
    ws_sum.append(['2년 총합 (반복 + 필수 1회성)',     '=B4+B5+B6', '—', '전체 출시 + 2년 운영'])
    for r in (3, 4, 5, 6, 7, 8, 9):
        for c in (1, 2, 3, 4):
            ws_sum.cell(row=r, column=c).border = BORDER
    for c in (1, 2, 3, 4):
        ws_sum.cell(row=3, column=c).font = HEADER_FONT
        ws_sum.cell(row=3, column=c).fill = HEADER_FILL
        ws_sum.cell(row=3, column=c).alignment = Alignment(horizontal='center')
    for r in (4, 5, 6, 7, 8, 9):
        ws_sum.cell(row=r, column=2).number_format = KRW_FMT
        ws_sum.cell(row=r, column=2).font = LINK_FONT
        ws_sum.cell(row=r, column=3).number_format = KRW_FMT
    ws_sum.cell(row=9, column=1).font = Font(name=FONT, bold=True)
    ws_sum.cell(row=9, column=2).fill = ASSUME_FILL
    ws_sum.cell(row=9, column=2).font = Font(name=FONT, bold=True)
    ws_sum.column_dimensions['A'].width = 30
    ws_sum.column_dimensions['B'].width = 18
    ws_sum.column_dimensions['C'].width = 18
    ws_sum.column_dimensions['D'].width = 44

    ws_sum.append([])
    ws_sum.cell(row=ws_sum.max_row + 1, column=1).value = '주요 가정 / 변경점 (2026-05-23 v4)'
    ws_sum.cell(row=ws_sum.max_row, column=1).font = Font(name=FONT, bold=True, color='1F4E78')
    for n in [
        '① 환율 USD 1 = ₩1,500 (이전 1,300 → 보수적 상향)',
        '② 서버 = 국내 클라우드(가비아 G클라우드 또는 NHN/네이버 클라우드) — AWS 제외',
        '③ 도메인·이메일 분리: 패스웨이브(pathwave.co.kr) + 트리거소프트(triggersoft.kr) 2종',
        '④ 푸시: iOS APNs 자체구축(PR #50 완성). Android는 사실상 FCM 외 대안 없음 — FCM 무료',
        '⑤ 알림톡: 매장당 100건/월 × 9원 (현실적 가정 — 매장 100 = ₩90,000)',
        '⑥ 1회성 비용(Apple·Play·도메인·Mac mini·NICE·상표등록)은 월별 시트에서 제외 → 초기 세팅비 시트만',
        '⑦ 상표등록 2건(패스웨이브 + 트리거소프트) 셀프 출원 추가 (각 ₩267,000)',
        '⑧ 매장당 월 ₩10,000 매출 — BEP 시트 참조. 매장 100개 미만은 적자 구조',
        '⑨ Phase 1.5 단계 추가 — 코드 완성 후 개발환경 서버 구축 + 통합 테스트 → 운영 반영',
        '⑩ 토스 수수료(2.9%+33원)는 매출 차감 — 운영비 미포함',
        '⑪ 자동화 도구(Stage 2~3)는 별도 — 출시 후 단계적 도입',
    ]:
        ws_sum.append([n])
        ws_sum.cell(row=ws_sum.max_row, column=1).font = Font(name=FONT, color='505050')

    ws_sum.append([])
    ws_sum.cell(row=ws_sum.max_row + 1, column=1).value = '사용 방법'
    ws_sum.cell(row=ws_sum.max_row, column=1).font = Font(name=FONT, bold=True, color='1F4E78')
    for line in [
        '① "서비스 신청 체크리스트": 가격 상세 + 신청 링크 + 신청 상태 드롭다운',
        '② "초기 세팅비": 출시 전 1회성 — 필수만 vs 옵션 포함 두 합계',
        '③ "월별 운영비 시나리오": MAU 별 반복 비용',
        '④ "2026/2027년 월별": 월별 반복 비용 cash flow (1회성 제외)',
        '⑤ "손익분기점 (BEP)": 매장당 1만원 매출 기준 BEP 매장 수',
        '⑥ "연간 합계": 반복 + 1회성 분리 합산',
    ]:
        ws_sum.append([line])
        ws_sum.cell(row=ws_sum.max_row, column=1).font = Font(name=FONT, color='505050')

    out = 'docs/exports/pathwave_services_and_costs.xlsx'
    force_workbook_font(wb)
    wb.save(out)
    return out


if __name__ == '__main__':
    f1 = build_dev_checklist()
    f2 = build_services_costs()
    print('OK:', f1)
    print('OK:', f2)
