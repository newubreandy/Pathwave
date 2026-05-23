"""PathWave — 개발 체크리스트 + 서비스 신청·운영비용 엑셀 2개 생성 (v2).

수정사항 (2026-05-23):
  1. 외부 서비스 신청 시점 = 2026-06-02 주(법인카드 수취 후)
  2. 이전 작업 + 남은 작업 모두 기능별 정리 (File 1)
  3. 패스웨이브 + 트리거소프트 도메인/이메일 2종 분리
  4. 알림톡 비용 현실화 (매장당 2건 × 50명 = 100건/매장/월 기준)
  5. 초기 세팅비 vs 월별 운영비 시트 분리

산출:
  docs/exports/pathwave_dev_checklist.xlsx
  docs/exports/pathwave_services_and_costs.xlsx
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

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
# FILE 1 — 개발 체크리스트 (기능별 + 이전/현재/남은)
# ═══════════════════════════════════════════════════════════════════════════
def build_dev_checklist():
    wb = Workbook()
    wb.remove(wb.active)
    today = '2026-05-23'

    # ── Sheet: 기능별 전체 현황 ────────────────────────────────────────
    ws = wb.create_sheet('기능별 전체 현황')
    ws['A1'] = 'PathWave 기능별 전체 작업 현황 — 이전 완료 + Phase 1 진행 + 남은 작업'
    ws['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
    ws.merge_cells('A1:F1')

    headers = ['도메인/기능', '단계', '항목', '내용', '상태', '비고']
    ws.append([])
    ws.append(headers)
    header_row = ws.max_row

    # (도메인, 단계, 항목, 내용, 상태, 비고)
    # 단계: 이전 완료 / Phase 1 / 남은
    # 각 도메인을 sub-feature 단위로 상세하게 분리.
    items = [
        # ════════ 인증/회원가입 ════════
        ('인증/회원가입', '이전 완료', 'BE — 이메일 인증·가입',
         '/api/auth send-code·verify-code·register·login, email_codes 테이블, bcrypt, JWT',
         '✅', ''),
        ('인증/회원가입', '이전 완료', 'BE — 5종 소셜 로그인',
         '/api/auth/social/{google,apple,facebook,kakao,naver}, Firebase 토큰 검증, 동의 처리',
         '✅', '실 키는 카카오·네이버 검수 후'),
        ('인증/회원가입', '이전 완료', 'BE — 동의·약관·미성년자',
         '8 KIND 정책 등록, record_consents 감사 로그, parent_invite 코드 발급',
         '✅', ''),
        ('인증/회원가입', '이전 완료', 'BE — 회원 탈퇴 + 14일 그레이스',
         '/api/auth/delete-account, soft delete, deleted_at, 14일 후 재가입',
         '✅', ''),
        ('인증/회원가입', '이전 완료', 'BE — 모바일 비밀번호 재설정',
         '/api/auth/forgot-password·reset-password (users 테이블 전용)',
         '✅', ''),
        ('인증/회원가입', '이전 완료', 'BE — 시설 계정 가입·로그인',
         '/api/facility/send-code·register·login, facility_accounts, 운영자 승인 대기',
         '✅', ''),
        ('인증/회원가입', '이전 완료', 'mobile — 가입 5단계',
         'consent → 본인인증 → 이메일/소셜 → 약관 동의 → 완료',
         '✅', ''),
        ('인증/회원가입', '이전 완료', 'mobile — 로그인/비번 재설정 UI',
         'login_screen, forgot_password_screen (2단계)',
         '✅', ''),
        ('인증/회원가입', '이전 완료', 'provider — 회원가입·로그인 UI',
         '실제 폼·소셜로그인·매장 정보 입력',
         '✅', '폼은 dev 우회로 가려졌었음 → P4에서 복구'),
        ('인증/회원가입', 'Phase 1 ✅', 'P4 — provider dev 우회 제거',
         'DEV_AUTO_LOGIN을 import.meta.env.DEV 게이트, Login 자동토큰 useEffect 제거, Signup 게스트 게이트',
         '✅', '출시 빌드에서 실 로그인폼 노출'),
        ('인증/회원가입', 'Phase 1 ✅', 'P4 — 시설 비번 재설정 신규',
         'BE /api/facility/forgot-password·reset-password 신규 + provider ForgotPassword 페이지·라우트',
         '✅', '갭리스트 오기: 파일 없었음'),
        ('인증/회원가입', '남은', '실 키 검증',
         '카카오·네이버 검수 완료 후 실 소셜 로그인 통합 테스트',
         '⬜', '외부 서비스 활성화 후'),

        # ════════ 매장 정보 ════════
        ('매장 정보', '이전 완료', 'BE — 매장 CRUD',
         '/api/facilities CRUD + 이미지 갤러리 + 다국어 번역 캐시',
         '✅', ''),
        ('매장 정보', '이전 완료', 'admin — 매장 관리',
         'admin Stores 페이지, 비콘 매핑, 번역 등록',
         '✅', ''),
        ('매장 정보', '이전 완료', 'mobile — 매장 상세 화면',
         'facility_screen (이미지/영업시간/주소/채팅 진입)',
         '✅', ''),
        ('매장 정보', '이전 완료', 'provider — StoreInfo UI 골격',
         '편집/저장/지도/이미지 업로드/비콘 claim — UI 완성, 데이터는 mock',
         '✅', '데이터 연동은 P5'),
        ('매장 정보', 'Phase 1 ✅', 'P5 — provider StoreInfo 실연동',
         '하드코딩 제거 → StoreService.list/update PATCH 실 연동, 실 fid로 비콘 claim',
         '✅', ''),
        ('매장 정보', 'Phase 1 ✅', 'P5 — Settings 푸터 → PwFooter',
         '하드코딩 회사정보 제거 → CompanyInfoService 실 법인정보',
         '✅', ''),
        ('매장 정보', 'Phase 1 ✅', 'P5 — dead code 정리',
         'Facilities.jsx (1계정1매장 정책 위반 + 라우트 미연결) 삭제',
         '✅', ''),
        ('매장 정보', '남은', 'P8c — 스키마 갭',
         'facilities 테이블에 category/holidays/detailAddress 컬럼 추가 또는 UI 정리 (현재 비영속)',
         '⬜', '별도 작업 칩 등록됨'),

        # ════════ 결제·구독 ════════
        ('결제·구독', '이전 완료', 'BE — billing API 전체',
         '/api/billing cards·subscriptions·payments·refund·extend·receipt-email + PG provider 추상화(sim/toss)',
         '✅', ''),
        ('결제·구독', '이전 완료', 'admin — Payments + Subscriptions',
         'adminApi.listPayments/listSubscriptions/refundPayment 실연동 + 환불 모달',
         '✅', '이미 정합 — P7에서 변경 없음'),
        ('결제·구독', '이전 완료', 'provider — PaymentManagement·Subscriptions UI 골격',
         '다단계 결제 흐름/카드 입력 모달/구독 카드 UI 완성, 데이터는 mock + localStorage',
         '✅', '데이터 연동은 P7'),
        ('결제·구독', 'Phase 1 ✅', 'P7 — BillingService 신규',
         'provider /api/billing 래퍼 (cards/subscriptions/payments/receipt-email), PCI 주석',
         '✅', ''),
        ('결제·구독', 'Phase 1 ✅', 'P7 — 카드 평문저장 제거 (C6)',
         'localStorage pathwave_payment_card + audit 큐 완전 제거, registerCard(brand, last4)만 전송',
         '✅', 'PCI 준수, 전체 PAN/CVC 미전송'),
        ('결제·구독', 'Phase 1 ✅', 'P7 — Payment/Subscription/ServiceRequest 실연동',
         '모든 MOCK_* 제거, 결제 흐름을 PaymentManagement/ServiceRequest 모두 동일 백엔드로 통합',
         '✅', ''),
        ('결제·구독', '남은', '토스 키 활성화',
         '토스페이먼츠 심사 통과 후 PG_PROVIDER=toss + 실 결제 end-to-end 검증',
         '⬜', '외부 심사 1~2주'),

        # ════════ 쿠폰 ════════
        ('쿠폰', '이전 완료', 'BE — 쿠폰 발행/사용/만료',
         '/api/coupons issue/use/expire, 정책 설정, 통계',
         '✅', ''),
        ('쿠폰', '이전 완료', 'mobile — 쿠폰함 화면',
         'coupons_screen (active/used/expired 탭), 사용 다이얼로그',
         '✅', '쿠폰 사용 silent error 잔존 → P9에서 수정'),
        ('쿠폰', '이전 완료', 'provider — Coupons·CouponForm UI',
         '쿠폰 목록·생성·통계 UI 완성, 데이터는 mock',
         '✅', '데이터 연동은 P9'),
        ('쿠폰', '이전 완료', 'admin — 쿠폰 통계',
         'admin abuse·coupon stats',
         '✅', 'CouponStats placeholder 일부 → P11'),
        ('쿠폰', 'Phase 1 — 남은', 'P9 — provider Coupons 실연동',
         'mock→/api/coupons 실연동, 쿠폰 발행/회수 정상 흐름',
         '⬜', ''),
        ('쿠폰', 'Phase 1 — 남은', 'P9 — mobile 쿠폰 사용 silent error',
         '사용 실패 시 사용자 피드백 + 목록 갱신',
         '⬜', ''),
        ('쿠폰', 'Phase 1 — 남은', 'P22 — 회원 QR 사용 흐름',
         '손님 마이페이지 QR → provider 스캔/코드입력 → 적립·사용',
         '⬜', 'P9 이후 병행'),

        # ════════ 스탬프 ════════
        ('스탬프', '이전 완료', 'BE — 스탬프 적립/리워드',
         '/api/stamps accrue/list, 시설별 정책, BLE 비콘 감지 자동 적립',
         '✅', ''),
        ('스탬프', '이전 완료', 'mobile — 스탬프 화면',
         'stamps_screen (시설별 카드, 진행률, 보상)',
         '✅', ''),
        ('스탬프', '이전 완료', 'provider — Stamps·StampForm UI',
         '스탬프 정책·통계 UI 완성, 데이터는 mock',
         '✅', '데이터 연동은 P9'),
        ('스탬프', 'Phase 1 — 남은', 'P9 — provider Stamps 실연동',
         'mock→/api/stamps 실연동',
         '⬜', ''),
        ('스탬프', 'Phase 1 — 남은', 'P22 — 수동 적립(staff 모드)',
         '회원 QR 스캔 → 스탬프 수동 적립 (auto/staff 모드 선택)',
         '⬜', ''),

        # ════════ 채팅 ════════
        ('채팅', '이전 완료', 'BE — chat 전체 API',
         '/api/chat rooms·messages·SSE 스트림·read + chat_blocks 테이블 + is_blocked 가드',
         '✅', ''),
        ('채팅', '이전 완료', 'BE — abuse_reports + chat_blocks',
         '/api/abuse-reports + /api/admin/abuse-reports + /api/blocks',
         '✅', ''),
        ('채팅', '이전 완료', 'mobile — 채팅 화면',
         'chat_list_screen + chat_detail_screen (SSE 실시간) + 신고/차단 메뉴 + 가이드라인 모달',
         '✅', '재연결 미지원이었음 → P8'),
        ('채팅', '이전 완료', 'provider — CustomerChat UI',
         '대화창 UI 완성, 데이터는 DUMMY_CHATS 7개 더미',
         '✅', '데이터 연동은 P8'),
        ('채팅', '이전 완료', 'provider — ChatService 메서드',
         'openRoom/listRooms/listMessages/sendMessage/markRead/subscribe(SSE) 다 작성됨',
         '✅', '호출만 안 되고 있었음'),
        ('채팅', '이전 완료', 'admin — ChatMonitor UI',
         '신고 큐 테이블 UI 완성, /api/chat/reports 호출(없는 엔드포인트) → placeholder',
         '✅', 'BE 엔드포인트만 필요 — P8'),
        ('채팅', 'Phase 1 ✅', 'P8 — provider CustomerChat 실연동',
         'DUMMY 제거 → ChatService 5종 호출, 30초 폴링 + 낙관적 전송 + SSE 정리',
         '✅', ''),
        ('채팅', 'Phase 1 ✅', 'P8 — admin /api/chat/reports BE',
         'abuse_reports → 신고 큐 변환 (room_name·reason·reporter·status), super_admin 가드',
         '✅', 'ChatMonitor UI 무변경, 데이터만 실 표시'),
        ('채팅', 'Phase 1 ✅', 'P8 — mobile SSE 끊김 재연결',
         'StreamController 기반 재작성, 지수 backoff(1→30s), ?after_id=로 누락 보충',
         '✅', '⚠ app.py 재시작 후 활성'),
        ('채팅', '남은 — P8b', '번역 캐시 스키마',
         'chat_messages 또는 별도 번역 캐시 테이블 (message_id, lang → translated_text)',
         '⬜', ''),
        ('채팅', '남은 — P8b', '뷰어별 언어 번역 + translator 연결',
         'list_messages·SSE 응답에 ?lang= 기준 번역 포함, translator.py 통합',
         '⬜', 'DeepL/Google Translate 키 활성화 후 — USP 기능'),

        # ════════ 알림 (Inbox + Push) ════════
        ('알림 (Inbox + Push)', '이전 완료', 'BE — 알림 API',
         '/api/notifications inbox·announcements·read + notification_preferences (카테고리별)',
         '✅', ''),
        ('알림 (Inbox + Push)', '이전 완료', 'BE — FCM + APNs',
         'FCM (firebase-admin) + APNs (HTTP/2 JWT ES256) + multi-platform 라우팅',
         '✅', '실 키는 Firebase 활성화 후'),
        ('알림 (Inbox + Push)', '이전 완료', 'mobile — 알림 화면 + 권한 동의',
         'notifications_screen (인박스/공지 탭) + notification_permission_dialog',
         '✅', '라우팅 보강 필요 → P10'),
        ('알림 (Inbox + Push)', '이전 완료', 'provider — Notifications UI',
         '받은 알림 + 시스템 공지 UI 완성, 데이터는 mockInbox 14건',
         '✅', '데이터 연동은 P10'),
        ('알림 (Inbox + Push)', '이전 완료', 'admin — 공지 CRUD + 발송',
         'admin Announcements CRUD + 실 푸시 발송 통합',
         '✅', ''),
        ('알림 (Inbox + Push)', 'Phase 1 — 남은', 'P10 — provider Notifications 실연동',
         'mockInbox 제거 → 실 /api/notifications 연동',
         '⬜', ''),
        ('알림 (Inbox + Push)', 'Phase 1 — 남은', 'P10 — mobile 알림 라우팅',
         '알림 종류별 화면 이동 (coupon→쿠폰함, chat→채팅 등)',
         '⬜', ''),

        # ════════ WiFi (1회 연결) ════════
        ('WiFi (1회 연결)', '이전 완료', 'BE — wifi_profiles + handshake',
         '/api/beacon/wifi handshake (LIMIT 1 단일 반환) + wifi_profiles 기본 스키마',
         '✅', '로밍은 LIMIT 1 → 묶음 반환으로 확장 필요(P15)'),
        ('WiFi (1회 연결)', '이전 완료', 'mobile — native plugin',
         'iOS NEHotspotConfiguration + Android WifiNetworkSuggestion (자동 가입 요청)',
         '✅', '1회 연결만, 로밍 미지원'),
        ('WiFi (1회 연결)', '이전 완료', 'mobile — WifiConnectScreen',
         'BLE 핸드셰이크 → WiFi 정보 전달 + OS 자동 가입 트리거',
         '✅', ''),
        ('WiFi (1회 연결)', '이전 완료', 'provider — WifiSettings UI',
         'WiFi 등록·수정·비활성 UI 완성, 사진 첨부 + 가짜 OCR 자동입력',
         '✅', 'OCR 허위는 P6에서 제거됨'),

        # ════════ WiFi 로밍 (B 풀스코프) ════════
        ('WiFi 로밍 (B)', 'Phase 1 — 남은', 'P14 — 데이터 모델 재설계',
         'wifi_profiles 확장 + beacon_wifi·units·wifi_access_grant·devices 신규 + beacons.role(wifi/cashier)',
         '⬜', '6월 말~7월 초'),
        ('WiFi 로밍 (B)', 'Phase 1 — 남은', 'P15 — WiFi 등록·연동',
         'handshake 묶음 반환(LIMIT 1 제거) + admin WiFi 등록화면 신규 + provider WifiSettings 실연동 + 비콘 role UI',
         '⬜', 'C10·C13 해소'),
        ('WiFi 로밍 (B)', 'Phase 1 — 남은', 'P16 — mobile WiFi 클라이언트',
         '비콘→WiFi 묶음 fetch·캐시 + BSSID 검증 + "WiFi 변경됨" 흐름 + 손님 자동/승인 + home 진입점',
         '⬜', ''),
        ('WiFi 로밍 (B)', 'Phase 1 — 남은', 'P17 — .mobileconfig 다건',
         '.mobileconfig 생성·다건 설치 (서명은 Apple 인증서 확보 후 적용)',
         '⬜', ''),
        ('WiFi 로밍 (B)', 'Phase 1 — 남은', 'P18 — credential_mode managed',
         '비번 교체 리마인드 + 인가 손님 자동 전파 + 알림 연동',
         '⬜', 'v1 flag 비공개 (코드만 완성)'),
        ('WiFi 로밍 (B)', 'Phase 1 — 남은', 'P19 — units/grant 관리',
         '호실·자리 시간제 권한 관리 UI (admin/provider)',
         '⬜', 'v1 flag 비공개'),

        # ════════ 비콘 ════════
        ('비콘 (인벤토리/claim/모니터)', '이전 완료', 'BE — beacons lifecycle',
         'beacons 테이블 inventory→active→inactive/lost, claim API',
         '✅', ''),
        ('비콘 (인벤토리/claim/모니터)', '이전 완료', 'admin — Beacons UI',
         '인벤토리 CSV 입고, claim 모니터, 배터리·펌웨어 표시',
         '✅', ''),
        ('비콘 (인벤토리/claim/모니터)', '이전 완료', 'provider — 비콘 claim 흐름',
         'StoreInfo 내 비콘 claim UI + listBeacons',
         '✅', '실 fid는 P5에서 해소'),
        ('비콘 (인벤토리/claim/모니터)', 'Phase 1 — 남은', 'P15 (병합)',
         'beacons.role(wifi/cashier) 컬럼 추가 + admin·provider UI',
         '⬜', ''),

        # ════════ i18n (12언어) ════════
        ('i18n (12언어)', '이전 완료', 'BE — translations API',
         'translations 테이블, GET /api/i18n/{lang}, DeepL 통합 모듈, admin CRUD UI',
         '✅', ''),
        ('i18n (12언어)', '이전 완료', 'admin — i18n CRUD',
         '키별 다국어 입력·수정·자동번역 트리거',
         '✅', ''),
        ('i18n (12언어)', '이전 완료', 'mobile — supportedLocales 7개',
         '7개 언어 기본 + 일부 화면만 i18n 적용 (대부분 한글 하드코딩)',
         '✅', '12개로 확장 + 전 화면 → P2'),
        ('i18n (12언어)', 'Phase 1 ✅', 'P2 — mobile I18nService DB 통일',
         '12 supportedLocales, 전 화면·위젯 t() 전환, ko 시드 203→550',
         '✅', ''),
        ('i18n (12언어)', 'Phase 1 ✅', 'P2 — DeepL 일괄번역 스크립트',
         'translate_i18n_deepl.py 작성 — 키 활성화 시 22언어×549건 배치',
         '✅', '키 활성화 후 실행'),
        ('i18n (12언어)', '남은', '11개 언어 batch 번역',
         'DeepL API 키 활성화 후 batch 실행 (현재 ko만)',
         '⬜', 'DeepL 키 활성화 후'),

        # ════════ 정책/약관 ════════
        ('정책/약관', '이전 완료', 'BE — policies API + 8 KIND',
         'terms·privacy·location·marketing·push·camera·storage·third_party·age14 등록·버전관리',
         '✅', ''),
        ('정책/약관', '이전 완료', 'mobile/provider — policy_view 화면',
         '약관 본문 노출, 푸터·설정·동의 흐름에서 진입',
         '✅', '?lang=ko 강제 문제 잔존 → P13'),
        ('정책/약관', '이전 완료', 'admin — Policies CRUD',
         '약관 등록·버전 발행 UI',
         '✅', ''),
        ('정책/약관', 'Phase 1 — 남은', 'P13 — 환불·청소년·쿠키 3종',
         'BE policy KIND 추가 + admin Policies + mobile/provider 노출 + policy_view 언어 정합',
         '⬜', 'C14 해소'),

        # ════════ 디자인 시스템 ════════
        ('디자인 시스템', '이전 완료', 'mobile — PwTheme 다크 + 보라',
         'PwTheme + 13종 Pw* 위젯 (Radio·Checkbox·Dropdown·Chip 4종은 P1에서 추가)',
         '✅', ''),
        ('디자인 시스템', '이전 완료', 'provider-web — 다크 + 녹색',
         'provider 디자인 시스템 통합 PR #66~#87 (게스트 진입 포함)',
         '✅', '게스트 진입은 P4에서 dev 게이트'),
        ('디자인 시스템', '이전 완료', 'admin-web — 다크 + 블루',
         'admin 다크 톤 통합 PR #65',
         '✅', ''),
        ('디자인 시스템', 'Phase 1 ✅', 'P1 — mobile 기반 단일화',
         '테마 단일화(AppTheme+NeuTheme→1) + 시스템 폰트 + neu/ 위젯 통합 + Pw* 4종 신규',
         '✅', ''),
        ('디자인 시스템', 'Phase 1 ✅', 'P3 — 웹 alert/confirm → 공용 모달',
         'provider 16곳 + admin 17곳의 네이티브 alert/confirm → useDialog() 비동기 모달, 색 토큰 정합(보라 잔존 2곳→녹색)',
         '✅', ''),

        # ════════ 슈퍼어드민 (admin-web) ════════
        ('슈퍼어드민', '이전 완료', 'admin — 기본 7페이지',
         'Login + Dashboard + Beacons + Approvals + Battery + Announcements + Stores',
         '✅', 'PR #36~#38'),
        ('슈퍼어드민', '이전 완료', 'admin — Payments + Subscriptions + 환불',
         '결제/구독 관리 + 환불 모달 — 실 API 연동 완료',
         '✅', 'PR #39'),
        ('슈퍼어드민', '이전 완료', 'admin — Policies + Translations + Audit + Reports',
         '약관·번역·감사 로그·신고 관리',
         '✅', ''),
        ('슈퍼어드민', '이전 완료', 'admin — 채팅 신고/차단 (PR #142)',
         'abuse_reports admin 처리 + chat_blocks',
         '✅', '/api/chat/reports 변환만 P8에서 추가'),
        ('슈퍼어드민', 'Phase 1 — 남은', 'P11 — Dashboard 가짜데이터 제거',
         '실 통계 API 연동',
         '⬜', ''),
        ('슈퍼어드민', 'Phase 1 — 남은', 'P11 — StaffMonitor·CouponStats placeholder',
         '실 데이터 연동',
         '⬜', ''),
        ('슈퍼어드민', 'Phase 1 — 남은', 'P20 — app-versions UI',
         '백엔드 routes/version.py 완성 — admin UI만 신규',
         '⬜', 'C11 해소'),

        # ════════ 직원 관리 ════════
        ('직원 관리', '이전 완료', 'BE — staff API',
         '직원 초대/권한/관리 백엔드',
         '✅', ''),
        ('직원 관리', '이전 완료', 'provider — StaffManagement UI',
         '직원 목록·초대·권한 UI 완성, 데이터는 mock',
         '✅', '데이터 연동은 P11'),
        ('직원 관리', '이전 완료', 'mobile — MemberProfile UI',
         '회원 프로필 mock UI',
         '✅', 'mobile 직원 기능은 v1 비공개'),
        ('직원 관리', 'Phase 1 — 남은', 'P11 — provider StaffManagement 실연동',
         'mock→실 staff API 연동',
         '⬜', ''),
        ('직원 관리', 'Phase 1 — 남은', 'P11 — admin StaffMonitor 실연동',
         '시설별 직원 모니터링',
         '⬜', ''),

        # ════════ mobile 핵심 화면 (심의 직격) ════════
        ('mobile 심의 직격', '이전 완료', 'consent 단계',
         '8 KIND 동의 + 미성년자 보호 + 약관 본문',
         '✅', 'placeholder 노출 버그 존재 → P12'),
        ('mobile 심의 직격', '이전 완료', 'settings 화면',
         '계정·알림·약관·고객지원·회원탈퇴',
         '✅', 'dev API URL 노출 + 앱 버전 하드코딩 → P12'),
        ('mobile 심의 직격', 'Phase 1 — 남은', 'P12 — consent placeholder 제거',
         '⚠ placeholder 본문 노출 버그 수정',
         '⬜', '심의 reject 방지'),
        ('mobile 심의 직격', 'Phase 1 — 남은', 'P12 — 동의 로드 실패 dead-end 복구',
         '네트워크 오류 시 재시도/안내',
         '⬜', ''),
        ('mobile 심의 직격', 'Phase 1 — 남은', 'P12 — settings dev 정보 제거 + 앱 버전 동적',
         'API URL 노출 제거 + package_info_plus로 버전 동적화',
         '⬜', 'C9 해소'),

        # ════════ 앱 버전관리 ════════
        ('앱 버전관리', '이전 완료', 'BE — routes/version.py + app_versions 테이블',
         'admin GET/PUT /api/admin/app-versions, mobile GET /api/version',
         '✅', '코드 완성 — admin UI만 필요'),
        ('앱 버전관리', 'Phase 1 — 남은', 'P20 — admin app-versions UI',
         '버전 등록·강제업데이트/권장 토글·OS별',
         '⬜', ''),
        ('앱 버전관리', 'Phase 1 — 남은', 'P20 — mobile OS 최소버전 게이트',
         'splash에서 버전 체크 → 강제 업데이트 모달',
         '⬜', 'splash 화면 ⏰ 처리 일부 존재'),

        # ════════ 심의 메타 자산 ════════
        ('심의 메타 자산', '이전 완료', '동의 흐름·약관 노출',
         '8 KIND + 미성년자 + UGC 가이드라인 (채팅)',
         '✅', '심의 reject 방지 대부분 완료'),
        ('심의 메타 자산', 'Phase 1 — 남은', 'P21 — iOS PrivacyInfo.xcprivacy',
         'iOS 17.4+ 필수 — 데이터 수집/추적 명시',
         '⬜', '심의 reject 방지'),
        ('심의 메타 자산', 'Phase 1 — 남은', 'P21 — Bundle ID 확정',
         'co.triggersoft.pathwave 등 최종 결정',
         '⬜', ''),
        ('심의 메타 자산', 'Phase 1 — 남은', 'P21 — Android Photo Picker',
         'Android 13+ 신규 권한 모델 적용',
         '⬜', ''),
        ('심의 메타 자산', 'Phase 1 — 남은', 'P21 — 계정삭제 웹 URL',
         'Google Play 정책 — 앱 외부 웹에서도 계정 삭제 가능 URL 제공',
         '⬜', ''),

        # ════════ OCR ════════
        ('OCR', '이전 완료', 'runOcrMock (가짜)',
         'WifiSettings·ServiceRequest 사진 선택 시 랜덤 가짜 ID/PW 자동입력 — 심의 reject 위험',
         '✅', 'P6에서 제거'),
        ('OCR', 'Phase 1 ✅', 'P6 — OCR 허위 제거',
         'runOcrMock 삭제 → 정직한 수동입력 UI, 사진은 참고 첨부로 재정의',
         '✅', 'C5 해소'),

        # ════════ 회사 정보 (footer) ════════
        ('회사 정보 (footer)', '이전 완료', 'BE — company_info API (Phase M)',
         '슈퍼어드민 입력값 GET /api/company-info',
         '✅', ''),
        ('회사 정보 (footer)', '이전 완료', 'mobile/provider PwFooter',
         'CompanyInfoService 실연동 — DB값 + i18n fallback',
         '✅', ''),
        ('회사 정보 (footer)', 'Phase 1 ✅', 'P5 — Settings 푸터 통일',
         'provider Settings 하드코딩 푸터 → PwFooter',
         '✅', ''),
        ('회사 정보 (footer)', '남은', '실 법인정보 입력',
         '슈퍼어드민이 트리거소프트 실 정보(법인등록번호 등) admin에서 입력',
         '⬜', '법인 등기 완료 — 등록만 남음'),

        # ════════ 운영 인프라 ════════
        ('운영 인프라', '이전 완료', 'BE — 보안 강화',
         'SECRET_KEY/AES_KEY ENV 강제 + CORS 화이트리스트 + rate-limit (PR #35)',
         '✅', ''),
        ('운영 인프라', '이전 완료', 'BE — provider 추상화',
         'PG provider(sim/toss) + Email provider(stub/sendgrid/smtp) + Push provider(stub/fcm/apns)',
         '✅', '키 활성화 시 즉시 전환'),
        ('운영 인프라', '이전 완료', 'BE — gunicorn/wsgi + Sentry',
         '프로덕션 배포 골격 + Sentry 통합',
         '✅', ''),
        ('운영 인프라', '이전 완료', 'BE — PostgreSQL 어댑터',
         'DATABASE_URL ENV 자동 분기 (sqlite ↔ pg 호환)',
         '✅', ''),
        ('운영 인프라', '남은', '실 호스팅 배포',
         'AWS/Render/Railway 중 선택 + 실 도메인 + Postgres + 환경변수 키 주입',
         '⬜', '외부 서비스 활성화 후'),

        # ════════ 후속 단계 (Phase 2~5) ════════
        ('Phase 2~4 테스트', '남은', 'W7 — 6 페르소나 테스트 시드',
         '외국인/한국인/소규모/중대형/직원/슈퍼어드민 시나리오 데이터 + walk-through 검증',
         '⬜', '7월 중순~하순'),
        ('Phase 5 제출', '남은', '스토어 메타데이터 + 빌드',
         'iOS/Android 빌드 + 스크린샷 + 메타데이터(다국어) + 심의 제출',
         '⬜', '7월 하순~8월 초'),
    ]

    last_domain = ''
    for it in items:
        ws.append(it)
        r = ws.max_row
        # 도메인 변경 시 SUBHEADER 표시
        if it[0] != last_domain:
            ws.cell(row=r, column=1).font = Font(name=FONT, bold=True)
            ws.cell(row=r, column=1).fill = SUBHEADER_FILL
            last_domain = it[0]
        # 단계 색상
        stage = it[1]
        stage_fill = {'이전 완료': DONE_FILL, 'Phase 1': ACTIVE_FILL, '남은': TODO_FILL}.get(stage)
        if stage_fill:
            ws.cell(row=r, column=2).fill = stage_fill
            ws.cell(row=r, column=2).alignment = Alignment(horizontal='center', vertical='center')
        # 상태 색상
        status = it[4]
        status_fill = {'✅': DONE_FILL, '◑': PARTIAL_FILL, '🔄': ACTIVE_FILL, '⬜': TODO_FILL}.get(status)
        if status_fill:
            ws.cell(row=r, column=5).fill = status_fill
            ws.cell(row=r, column=5).alignment = Alignment(horizontal='center', vertical='center')

    apply_table(ws, header_row, ws.max_row, len(headers))
    for i, w in enumerate([24, 12, 28, 60, 8, 30], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[header_row].height = 28

    # ── Sheet: Phase 1 PR 체크리스트 ────────────────────────────────────
    ws2 = wb.create_sheet('Phase 1 PR 체크리스트')
    pr_headers = ['PR', '분류', '도메인', '콘솔/영역', '내용 요약',
                  '상태', '진척율', '담당', '시작일', '목표일', '완료일',
                  '검증 시나리오 / 메모']
    ws2.append(pr_headers)

    prs = [
        ('P1', '인프라', 'mobile 디자인 기반', 'mobile',
         '테마 단일화 + 시스템 폰트 + Pw* 위젯 4종',
         '✅', '1인', '2026-05-21', '2026-05-22', today, ''),
        ('P2', '인프라', 'mobile i18n', 'mobile·BE',
         '12언어 단일화 + 전 화면 t() + ko 시드 550 + DeepL 스크립트',
         '✅', '1인', '2026-05-21', '2026-05-22', today, ''),
        ('P3', '인프라', '웹 디자인 시스템', 'provider·admin',
         'alert/confirm 33곳 → useDialog 공용 모달 + 색 토큰',
         '✅', '1인', '2026-05-21', '2026-05-22', today, ''),
        ('P4', 'Critical', '인증 우회 제거', 'provider·admin·BE',
         'DEV_AUTO_LOGIN env 게이트 + 실 로그인폼 + /forgot-password 정식',
         '✅', '1인', today, today, today, '⚠ app.py 재시작 필요'),
        ('P5', 'Critical', '매장·회사정보 실연동', 'provider',
         'StoreInfo 실연동 + PwFooter + dead code 정리',
         '✅', '1인', today, today, today, ''),
        ('P6', 'Critical', 'OCR 허위 제거', 'provider',
         '가짜 OCR 자동입력 제거 → 정직한 수동입력 UI',
         '✅', '1인', today, today, today, ''),
        ('P7', 'Critical', '결제·구독 실연동', 'provider·admin',
         '카드 localStorage 제거(PCI) + BillingService + 실연동',
         '✅', '1인', today, today, today, ''),
        ('P8', 'Critical', '채팅 도메인', 'mobile·provider·admin·BE',
         'provider CustomerChat + admin ChatMonitor + BE 신고 API + mobile SSE 재연결',
         '◑', '1인', today, today, today, '번역=P8b 분리, ⚠ app.py 재시작'),
        ('P8b', 'Critical', '채팅 자동 번역', 'mobile·provider·BE',
         '번역 캐시 스키마 + 뷰어별 언어 + translator↔chat 연결',
         '⬜', '1인', '', '키 확보 후', '', 'Google/DeepL 키 확보 후'),
        ('P9', 'Critical', '쿠폰·스탬프 실연동', 'mobile·provider',
         'Coupons·Stamps mock→실연동',
         '⬜', '1인', '', '2026-06-중', '', ''),
        ('P10', 'Critical', '알림 도메인', 'mobile·provider·admin',
         'Notifications 실연동 + mobile 라우팅',
         '⬜', '1인', '', '2026-06-중', '', ''),
        ('P11', 'Critical', '대시보드·직원', 'provider·admin·BE',
         'Dashboard·StaffManagement 실연동',
         '⬜', '1인', '', '2026-06-중', '', ''),
        ('P12', 'Critical', 'mobile 심의 직격', 'mobile·BE',
         'consent placeholder + dev 정보 제거 + 앱 버전 동적화',
         '⬜', '1인', '', '2026-06-중', '', ''),
        ('P13', 'Critical', '약관 3종', 'mobile·provider·admin·BE',
         '환불·청소년·쿠키 정책',
         '⬜', '1인', '', '2026-06-중', '', ''),
        ('P14', 'WiFi 로밍 B', 'WiFi 데이터 모델', 'BE',
         'wifi_profiles 확장 + beacon_wifi·units·grant·devices',
         '⬜', '1인', '', '2026-06-말~7월초', '', ''),
        ('P15', 'WiFi 로밍 B', 'WiFi 등록·연동', 'provider·admin·BE',
         'handshake 묶음 + admin WiFi 등록 + provider WifiSettings',
         '⬜', '1인', '', '2026-07-초', '', ''),
        ('P16', 'WiFi 로밍 B', 'mobile WiFi 클라이언트', 'mobile',
         '비콘→WiFi 묶음 fetch + BSSID 검증',
         '⬜', '1인', '', '2026-07-초', '', ''),
        ('P17', 'WiFi 로밍 B', '.mobileconfig 다건', 'BE·mobile·iOS',
         '.mobileconfig 생성·다건 설치',
         '⬜', '1인', '', '2026-07-중', '', '서명은 인증서 후'),
        ('P18', 'WiFi 로밍 B', 'credential_mode managed', 'BE·provider·mobile',
         '비번 교체 리마인드 + 인가 손님 자동 전파',
         '⬜', '1인', '', '2026-07-중', '', 'v1 flag 비공개'),
        ('P19', 'WiFi 로밍 B', 'units/grant 관리', 'admin·provider·BE',
         '호실·자리 시간제 권한 UI',
         '⬜', '1인', '', '2026-07-중', '', 'v1 flag 비공개'),
        ('P20', '심의 마무리', '앱 버전관리', 'admin·mobile',
         'admin app-versions UI + mobile OS 최소버전 게이트',
         '⬜', '1인', '', '2026-07-중', '', ''),
        ('P21', '심의 마무리', '심의 메타 자산', 'mobile·iOS',
         'PrivacyInfo.xcprivacy + Bundle ID + Photo Picker',
         '⬜', '1인', '', '2026-07-중', '', ''),
        ('P22', '회원 QR 운영', '쿠폰·스탬프 회원 QR', 'mobile·provider·BE',
         '회원 QR + provider 스캔/코드입력 + 친구초대 QR',
         '⬜', '1인', '', '2026-07-초~중', '', 'P9 이후 병행'),
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
        fill = {'✅': DONE_FILL, '◑': PARTIAL_FILL, '🔄': ACTIVE_FILL,
                '🔎': ACTIVE_FILL, '⬜': TODO_FILL}.get(status)
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
    for i, w in enumerate([6, 12, 22, 18, 50, 8, 9, 9, 12, 18, 12, 30], 1):
        ws2.column_dimensions[get_column_letter(i)].width = w
    ws2.row_dimensions[1].height = 28

    # ── Sheet: 단계별 일정 ──────────────────────────────────────────────
    ws3 = wb.create_sheet('단계별 일정')
    ws3.append(['단계', '내용', '예상 기간', '누적', '비고'])
    schedule = [
        ('이전 작업 (~Phase 0)', 'PR #1~#51 + 디자인 통합 + 51 PR 머지', '~수개월', '2026-05-21', '완료 — 코드 측면 출시 직전'),
        ('Phase 0 전수 감사', '갭 리스트 14 Critical + High 발굴', '~1일', '2026-05-21', '완료'),
        ('Phase 1 인프라', 'P1~P3', '~4일', '2026-05-22', '완료'),
        ('Phase 1 Critical', 'P4~P13 (10 PR)', '~2주', '2026-06-중', 'P4~P8 완료'),
        ('Phase 1 WiFi 로밍 B', 'P14~P19 (6 PR)', '~2.5~3주', '2026-07-초~중', 'feature flag'),
        ('Phase 1 회원 QR', 'P22 (P9 이후 병행)', '~1주', '2026-07-초~중', ''),
        ('Phase 1 심의 마무리', 'P20~P21', '~3일', '2026-07-중', ''),
        ('Phase 2~4 테스트·시드', '6 페르소나 + 시나리오 검증', '~1.5주', '2026-07-중~하순', ''),
        ('Phase 5 제출 준비', '빌드 + 스토어 메타데이터', '며칠', '2026-07-하순', ''),
        ('출시', '앱스토어/Play 공개', '—', '2026-07-하순~8월 초', ''),
        ('외부 서비스 신청 시작', '법인카드 수취 후 일괄 신청', '~1주 (심사 1~2주)', '2026-06-02 주', '카카오·솔라피·토스 심사 병행'),
    ]
    for row in schedule:
        ws3.append(row)
    apply_table(ws3, 1, len(schedule) + 1, 5)
    for i, w in enumerate([22, 38, 16, 18, 36], 1):
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
        ('총 PR 수 (Phase 1)',  "=COUNTA('Phase 1 PR 체크리스트'!A2:A30)"),
        ('완료 (✅)',           "=COUNTIF('Phase 1 PR 체크리스트'!F2:F30,\"✅\")"),
        ('부분 완료 (◑)',      "=COUNTIF('Phase 1 PR 체크리스트'!F2:F30,\"◑\")"),
        ('진행중 (🔄)',        "=COUNTIF('Phase 1 PR 체크리스트'!F2:F30,\"🔄\")"),
        ('검토중 (🔎)',        "=COUNTIF('Phase 1 PR 체크리스트'!F2:F30,\"🔎\")"),
        ('대기 (⬜)',           "=COUNTIF('Phase 1 PR 체크리스트'!F2:F30,\"⬜\")"),
        ('가중 평균 진척율',   "=AVERAGE('Phase 1 PR 체크리스트'!G2:G30)"),
        ('업데이트 일자',       today),
        ('외부 서비스 신청 시작', '2026-06-02 주 (법인카드 수취 후)'),
        ('목표 출시일',         '2026-07-하순~8월 초'),
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
    ws4.column_dimensions['B'].width = 40
    ws4.append([])
    ws4.cell(row=ws4.max_row + 1, column=1).value = '사용 방법'
    ws4.cell(row=ws4.max_row, column=1).font = Font(name=FONT, bold=True, color='1F4E78')
    for line in [
        '① "기능별 전체 현황": 도메인별 이전 완료/Phase 1/남은 작업을 한눈에',
        '② "Phase 1 PR 체크리스트": F열 상태 드롭다운(⬜→🔄→🔎→◑→✅) 갱신',
        '③ 진척율 자동 계산: ⬜=0% · 🔄=50% · ◑=70% · 🔎=90% · ✅=100%',
        '④ "단계별 일정": 출시까지의 큰 그림 일정',
        '⑤ 요약은 PR 체크리스트 상태를 실시간 집계',
    ]:
        ws4.append([line])
        ws4.cell(row=ws4.max_row, column=1).font = Font(name=FONT, color='505050')

    out = 'docs/exports/pathwave_dev_checklist.xlsx'
    force_workbook_font(wb)
    wb.save(out)
    return out


# ═══════════════════════════════════════════════════════════════════════════
# FILE 2 — 서비스 신청 + 초기 세팅비 + 월별 운영비
# ═══════════════════════════════════════════════════════════════════════════
def build_services_costs():
    wb = Workbook()
    wb.remove(wb.active)

    # ── Sheet: 서비스 신청 체크리스트 ────────────────────────────────────
    ws = wb.create_sheet('서비스 신청 체크리스트')
    headers = ['우선순위', '카테고리', '서비스', '제공사', '필수/선택',
               '월 추정 (₩)', '초기 세팅비 (₩)', '가입 계정',
               '신청 상태', '신청 예정', '활성 예정', '환경변수 / 비고']
    ws.append(headers)
    # (pri, cat, name, vendor, req, monthly, initial, account, status, applied, activated, env_note)
    # 우선순위 1=출시 직전 필수, 2=출시 직후, 3=후속/선택
    # 신청 예정 = 2026-06-02 주(법인카드 수취 후) 기준
    services = [
        # === 우선순위 1 (6/2주 즉시 신청) ===
        (1, '결제',       '토스페이먼츠',           'Toss Payments',                 '필수', 0,     0,     'admin@pathwave', '대기', '2026-06-02', '2026-06-16', 'TOSS_SECRET_KEY · 심사 1~2주 (가장 김)'),
        (1, '스토어',     'Apple Developer',         'Apple',                         '필수', 10725, 128700,'admin@pathwave', '대기', '2026-06-02', '2026-06-03', '$99/년 일시불, 이메일 이관 어려움'),
        (1, '스토어',     'Google Play Console',     'Google',                        '필수', 0,     32500, 'admin@pathwave', '대기', '2026-06-02', '2026-06-03', '$25 일회성'),
        (1, '도메인',     'pathwave.co.kr (서비스)',  'Cloudflare / 가비아',            '필수', 2500,  30000, 'admin@pathwave', '대기', '2026-06-02', '2026-06-02', '연 3만원 ÷ 12'),
        (1, '도메인',     'triggersoft.kr (법인)',    'Cloudflare / 가비아',            '필수', 2500,  30000, 'admin@triggersoft', '대기', '2026-06-02', '2026-06-02', '법인 사업·세무·회계용'),
        (1, '호스팅',     'Cloudflare DNS/Tunnel',    'Cloudflare',                    '필수', 0,     0,     'admin@pathwave', '대기', '2026-06-02', '2026-06-02', '무료 — DNS + dev 서버 외부 접근'),
        (1, '호스팅',     '백엔드 서버',              'AWS EC2 / Render / Railway',    '필수', 50000, 0,     'admin@pathwave', '대기', '2026-06-02', '2026-06-09', 'Flask + gunicorn'),
        (1, '호스팅',     'PostgreSQL DB',           'AWS RDS / Supabase / Neon',     '필수', 30000, 0,     'admin@pathwave', '대기', '2026-06-02', '2026-06-09', 'DATABASE_URL'),
        (1, '호스팅',     '프론트 정적 호스팅',       'Vercel / Netlify / CFP',        '필수', 0,     0,     'admin@pathwave', '대기', '2026-06-02', '2026-06-03', '무료 tier'),
        (1, '인증/푸시',  'Firebase Auth + FCM',     'Google',                        '필수', 0,     0,     'dev@pathwave',   '대기', '2026-06-02', '2026-06-03', 'FIREBASE_CREDENTIALS · 무료 tier'),
        (1, '이메일도메인','Google Workspace (Pathwave)','Google',                    '필수', 9100,  0,     'admin@pathwave', '대기', '2026-06-02', '2026-06-02', '$7 × 1계정 + 4 alias (admin/dev/support/noreply/info)'),
        (1, '이메일도메인','Google Workspace (Triggersoft)','Google',                 '필수', 9100,  0,     'admin@triggersoft','대기','2026-06-02', '2026-06-02', '$7 × 1계정 (법인 운영)'),

        # === 우선순위 2 (6/2주 신청 — 심사 1~2주) ===
        (2, '소셜로그인', '카카오 로그인',            'Kakao',                         '필수', 0,     0,     'info@pathwave',  '대기', '2026-06-02', '2026-06-16', 'KAKAO_REST_KEY · 검수 1~2주'),
        (2, '소셜로그인', '네이버 로그인',            'Naver',                         '필수', 0,     0,     'info@pathwave',  '대기', '2026-06-02', '2026-06-09', 'NAVER_CLIENT_ID'),
        (2, '알림톡/SMS', '솔라피 알림톡',            'Solapi',                        '필수', 0,     0,     'dev@pathwave',   '대기', '2026-06-02', '2026-06-16', '템플릿 사전심사 1~2주, 건당 9원 (사용량 기반)'),
        (2, '알림톡/SMS', '솔라피 SMS 인증',          'Solapi',                        '필수', 0,     0,     'dev@pathwave',   '대기', '2026-06-02', '2026-06-09', '건당 8~15원'),
        (2, '이메일',     'SendGrid',                'Twilio',                        '필수', 0,     0,     'dev@pathwave',   '대기', '2026-06-02', '2026-06-03', '무료 100통/일 · 발신: support@'),
        (2, '모니터링',   'Sentry',                  'Sentry',                        '필수', 0,     0,     'dev@pathwave',   '대기', '2026-06-02', '2026-06-03', '무료 5K events/월'),
        (2, '지도',       'Google Maps API',         'Google',                        '필수', 0,     0,     'dev@pathwave',   '대기', '2026-06-02', '2026-06-03', '월 $200 무료 크레딧'),

        # === 우선순위 3 (후속·선택) ===
        (3, '본인인증',   'NICE / KCB / PASS',        '본인인증 사업자',                '선택', 2500,  100000,'admin@pathwave', '대기', '2026-06-말', '2026-07-중', '계약 보증금 + 건당 30~80원'),
        (3, '번역',       'Google Translate / DeepL', 'Google / DeepL',                '선택', 30000, 0,     'dev@pathwave',   '대기', '2026-07-초', '2026-07-중', 'P8b 채팅 자동번역 USP'),
        (3, '자동화 S2',  'Channeltalk',              'Channel.io',                    '선택', 0,     0,     'dev@pathwave',   '대기', '출시 후',    '',           '무료~5만원/월'),
        (3, '자동화 S2',  'ChatGPT API',              'OpenAI',                        '선택', 30000, 0,     'dev@pathwave',   '대기', '출시 후',    '',           'OPENAI_API_KEY · 응대 자동화'),
        (3, '자동화 S2',  'Make.com',                 'Make',                          '선택', 0,     0,     'dev@pathwave',   '대기', '출시 후',    '',           '무료~$9~30/월'),
        (3, '자동화 S2',  'Buffer / Metricool',       'Buffer / Metricool',            '선택', 0,     0,     'info@pathwave',  '대기', '출시 후',    '',           'SNS 자동 게시'),
        (3, '자동화 S3',  'HubSpot CRM',              'HubSpot',                       '선택', 0,     0,     'admin@pathwave', '대기', '+3개월',     '',           '$20~50/월'),
        (3, '자동화 S2',  'Twilio Voice',             'Twilio',                        '선택', 0,     0,     'admin@pathwave', '대기', '+3개월',     '',           'AI 음성 통화'),
    ]
    for s in services:
        ws.append(s)
    for r in range(2, len(services) + 2):
        ws.cell(row=r, column=6).font = INPUT_FONT
        ws.cell(row=r, column=6).number_format = KRW_FMT
        ws.cell(row=r, column=7).font = INPUT_FONT
        ws.cell(row=r, column=7).number_format = KRW_FMT
        for col in (10, 11):
            ws.cell(row=r, column=col).font = INPUT_FONT
        status = ws.cell(row=r, column=9).value
        fill = {'활성': DONE_FILL, '검수중': PARTIAL_FILL, '신청중': ACTIVE_FILL,
                '대기': TODO_FILL, '보류': PARTIAL_FILL}.get(status)
        if fill:
            ws.cell(row=r, column=9).fill = fill
            ws.cell(row=r, column=9).alignment = Alignment(horizontal='center', vertical='center')
        pri = ws.cell(row=r, column=1).value
        pri_color = {1: 'FFC7CE', 2: 'FFEB9C', 3: 'F2F2F2'}.get(pri)
        if pri_color:
            ws.cell(row=r, column=1).fill = PatternFill('solid', start_color=pri_color)
            ws.cell(row=r, column=1).alignment = Alignment(horizontal='center', vertical='center')
            ws.cell(row=r, column=1).font = Font(name=FONT, bold=True)
    # 합계
    last_r = ws.max_row
    ws.append(['', '', '', '합계', '', f'=SUM(F2:F{last_r})', f'=SUM(G2:G{last_r})', '', '', '', '', ''])
    tot = ws.max_row
    for c in (6, 7):
        ws.cell(row=tot, column=c).number_format = KRW_FMT
        ws.cell(row=tot, column=c).font = Font(name=FONT, bold=True)
        ws.cell(row=tot, column=c).fill = ASSUME_FILL
    ws.cell(row=tot, column=4).font = Font(name=FONT, bold=True)

    dv1 = DataValidation(type='list', formula1='"대기,신청중,검수중,활성,보류"', allow_blank=True)
    dv1.add(f'I2:I{len(services)+1}')
    ws.add_data_validation(dv1)
    dv2 = DataValidation(type='list', formula1='"1,2,3"', allow_blank=True)
    dv2.add(f'A2:A{len(services)+1}')
    ws.add_data_validation(dv2)

    apply_table(ws, 1, tot, len(headers))
    for i, w in enumerate([8, 14, 28, 22, 11, 14, 14, 18, 11, 13, 13, 38], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 36

    # ── Sheet: 초기 세팅비 (1회성) ────────────────────────────────────────
    ws_init = wb.create_sheet('초기 세팅비 (1회성)')
    ws_init['A1'] = '초기 세팅비 — 출시 전 1회성 / 연 1회 비용'
    ws_init['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
    ws_init.merge_cells('A1:D1')
    ws_init.append([])
    ws_init.append(['항목', '금액 (₩)', '주기', '비고'])
    init_items = [
        ('Apple Developer Program 첫 회비',           128700, '연 1회', '$99/년 (USD 1=₩1,300)'),
        ('Google Play Console 등록비',                 32500, '일회성', '$25 일회성'),
        ('도메인 첫 등록 — pathwave.co.kr',            30000, '연 1회', '서비스 도메인'),
        ('도메인 첫 등록 — triggersoft.kr',            30000, '연 1회', '법인 운영 도메인'),
        ('Mac mini M1 16GB/256GB 중고 (선택)',        800000, '일회성', '자본 여유 시 — 24/7 운영 베이스'),
        ('Mac mini 주변 (외장 SSD, 케이블 등)',        80000, '일회성', 'Mac mini 옵션 시'),
        ('NICE 본인인증 계약 보증금 (선택)',          100000, '일회성', '미성년자 확인 도입 시'),
        ('카카오 로그인 검수',                              0, '일회성', '무료, 1~2주 소요'),
        ('네이버 로그인 가입',                              0, '일회성', '무료'),
        ('솔라피 알림톡 템플릿 등록·심사',                  0, '일회성', '무료, 1~2주 소요'),
        ('토스페이먼츠 가맹점 가입',                        0, '일회성', '무료, 심사 1~2주'),
        ('사업자등록 (홈택스)',                             0, '일회성', '무료 — 법인등기 후 즉시'),
        ('통신판매업 신고',                                 0, '일회성', '무료 — 구청'),
        ('위치기반서비스사업 신고',                         0, '일회성', '무료 — 방통위, 수 주 소요'),
    ]
    for it in init_items:
        ws_init.append(it)
        r = ws_init.max_row
        ws_init.cell(row=r, column=2).font = INPUT_FONT
        ws_init.cell(row=r, column=2).number_format = KRW_FMT
    # 합계 (옵션 미포함/포함)
    last_init = ws_init.max_row
    ws_init.append(['소계 — 필수만 (Mac mini·본인인증 제외)',
                    '=SUM(B4:B7)+SUM(B11:B17)', '', 'Mac mini·NICE 옵션 제외'])
    ws_init.append(['소계 — 옵션 포함 (Mac mini + NICE)',
                    f'=SUM(B4:B{last_init})', '', '전체 포함'])
    for r in (ws_init.max_row - 1, ws_init.max_row):
        ws_init.cell(row=r, column=2).number_format = KRW_FMT
        ws_init.cell(row=r, column=2).font = Font(name=FONT, bold=True)
        ws_init.cell(row=r, column=2).fill = ASSUME_FILL
        ws_init.cell(row=r, column=1).font = Font(name=FONT, bold=True)
        ws_init.cell(row=r, column=1).fill = ASSUME_FILL
    apply_table(ws_init, 3, ws_init.max_row, 4)
    for i, w in enumerate([42, 16, 12, 36], 1):
        ws_init.column_dimensions[get_column_letter(i)].width = w

    # ── Sheet: 월별 운영비 시나리오 (MAU 1K / 10K / 100K) ────────────
    ws2 = wb.create_sheet('월별 운영비 시나리오')
    ws2['A1'] = '월별 운영비 시나리오 — MAU 규모별 (사용량 기반 반복 비용만)'
    ws2['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
    ws2.merge_cells('A1:E1')
    ws2.append([])
    ws2.append(['항목', 'MAU 1K (매장 10)', 'MAU 10K (매장 100)', 'MAU 100K (매장 500)', '비고'])
    # 알림톡 재산정: 매장당 월 2건 × 평균 50명 = 100건/매장/월
    scen = [
        ('서버 + DB',                          80000,  200000, 1500000, 'Render→Railway→AWS RDS 점진'),
        ('도메인 (2개 × 월할)',                5000,   5000,   5000,    'pathwave + triggersoft 연 3만원 × 2 ÷ 12'),
        ('알림톡 (매장당 100건/월)',          9000,   90000,  450000,  '매장 × 100건 × 9원'),
        ('SMS 인증 + 본인인증',               5000,   30000,  200000,  '회원가입·결제 시'),
        ('이메일 (SendGrid)',                 0,      5000,   50000,   '무료 100통/일'),
        ('Google Workspace (2계정 × $7)',     18200,  18200,  18200,   'pathwave + triggersoft'),
        ('모니터링 (Sentry)',                 0,      0,      50000,   '무료 5K → 대규모만 유료'),
        ('Firebase / 로그인',                 0,      0,      20000,   '무료 tier'),
        ('Google Maps (초과분)',              0,      0,      30000,   '월 $200 크레딧'),
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
    for i, w in enumerate([34, 22, 22, 22, 36], 1):
        ws2.column_dimensions[get_column_letter(i)].width = w

    # ── 월별 연간 시트 빌더 ────────────────────────────────────────────
    def year_sheet(name, year, recurring_data, one_time_data, assumptions_note):
        ws = wb.create_sheet(name)
        ws['A1'] = f'{year}년 월별 운영비 (반복 + 일회성)'
        ws['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
        ws.merge_cells('A1:N1')
        ws['A2'] = f'※ {assumptions_note}'
        ws['A2'].font = Font(name=FONT, italic=True, color='808080')
        ws.merge_cells('A2:N2')
        ws.append([])
        head = ['항목'] + [f'{m}월' for m in range(1, 13)] + ['연 합계']
        ws.append(head)
        header_row = ws.max_row

        # 반복 비용 섹션
        ws.append(['【 반복 비용 (월 정액·사용량) 】'] + ['']*13)
        sect_r = ws.max_row
        ws.cell(row=sect_r, column=1).font = Font(name=FONT, bold=True, color='1F4E78')
        ws.cell(row=sect_r, column=1).fill = SUBHEADER_FILL

        rec_labels = [
            '서버 + DB', '도메인 (월할)', '알림톡 (사용량)', 'SMS + 본인인증',
            '이메일 (SendGrid)', 'Google Workspace (2계정)', '모니터링',
            'Firebase / 로그인', 'Google Maps (초과분)', '번역 API (P8b)',
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
        rec_end = ws.max_row

        # 일회성/초기 세팅비 섹션
        ws.append(['【 초기 세팅비 / 1회성 】'] + ['']*13)
        sect2_r = ws.max_row
        ws.cell(row=sect2_r, column=1).font = Font(name=FONT, bold=True, color='1F4E78')
        ws.cell(row=sect2_r, column=1).fill = SUBHEADER_FILL

        for label, monthly in one_time_data:
            ws.append([label] + list(monthly))
            r = ws.max_row
            ws.cell(row=r, column=14).value = f'=SUM(B{r}:M{r})'
            for c in range(2, 14):
                ws.cell(row=r, column=c).number_format = KRW_FMT
                ws.cell(row=r, column=c).font = INPUT_FONT
            ws.cell(row=r, column=14).number_format = KRW_FMT
            ws.cell(row=r, column=14).font = Font(name=FONT, bold=True)
        last_item = ws.max_row

        # 월 합계 (반복 + 일회성, 섹션 헤더 제외)
        ws.append(['월 합계'] +
                  [f'=SUM({get_column_letter(c)}{sect_r+1}:{get_column_letter(c)}{rec_end})+SUM({get_column_letter(c)}{sect2_r+1}:{get_column_letter(c)}{last_item})'
                   for c in range(2, 14)] +
                  [f'=SUM(B{last_item+1}:M{last_item+1})'])
        total_r = ws.max_row
        for c in range(2, 15):
            ws.cell(row=total_r, column=c).number_format = KRW_FMT
            ws.cell(row=total_r, column=c).font = Font(name=FONT, bold=True)
            ws.cell(row=total_r, column=c).fill = ASSUME_FILL
        ws.cell(row=total_r, column=1).font = Font(name=FONT, bold=True)
        ws.cell(row=total_r, column=1).fill = ASSUME_FILL

        # 누계
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
        ws.column_dimensions['A'].width = 34
        for c in range(2, 15):
            ws.column_dimensions[get_column_letter(c)].width = 11
        return total_r

    # 2026년 — 1~5월 코드만(0), 6/2주 외부 신청 시작 → 6월 도메인·Workspace,
    # 7월 Apple/Google Play·Mac mini 일시불 + 8월 출시
    # 반복(월 정액·사용량)
    R2026 = [
        # 서버+DB — 7월 셋업, 8월 출시
        [0,0,0,0,0,0,    30000, 80000, 80000, 80000, 80000, 80000],
        # 도메인 (월할) — 6월부터 (연 3만원 × 2 = 6만원/년 ÷ 12 = 5,000/월)
        [0,0,0,0,0,5000, 5000, 5000, 5000, 5000, 5000, 5000],
        # 알림톡 — 출시 후 점진, 매장 5~10개 가정
        [0,0,0,0,0,0,    0, 5000, 6000, 8000, 9000, 9000],
        # SMS + 본인인증
        [0,0,0,0,0,0,    0, 2000, 3000, 4000, 5000, 5000],
        # 이메일 (SendGrid 무료 tier 내)
        [0]*12,
        # Workspace 2계정 — 6/2주부터
        [0,0,0,0,0,18200, 18200, 18200, 18200, 18200, 18200, 18200],
        # 모니터링
        [0]*12,
        # Firebase
        [0]*12,
        # Maps
        [0]*12,
        # 번역 API (P8b — 2026년 미가동)
        [0]*12,
    ]
    # 일회성 (1회 발생 — 그 월에 일시불)
    O2026 = [
        ('도메인 첫 등록 (pathwave + triggersoft)', [0,0,0,0,0,60000, 0,0,0,0,0,0]),
        ('Apple Developer ($99/년)',                 [0]*6 + [128700] + [0]*5),
        ('Google Play Console ($25)',                [0]*6 + [32500]  + [0]*5),
        ('Mac mini 중고 (선택, 자본 여유 시)',       [0]*6 + [800000] + [0]*5),
        ('NICE 본인인증 보증금 (선택)',              [0]*6 + [100000] + [0]*5),
    ]
    total_r_2026 = year_sheet('2026년 월별', 2026, R2026, O2026,
        '출시 = 2026-07 하순~08-초. 1~5월 코드 작업. 6/2주 법인카드 수취 → 외부 서비스 일괄 신청. '
        '6월 도메인·Workspace 셋업, 7월 Apple/Google Play 결제 + Mac mini·NICE(옵션), 8월 출시 후 MAU 0~1K')

    # 2027년 — 분기별 점진 성장, 매장수 기준 알림톡
    R2027 = [
        # 서버+DB — 분기별 스케일업
        [80000,80000,80000, 100000,100000,100000, 150000,150000,150000, 200000,200000,200000],
        # 도메인 (월할)
        [5000]*12,
        # 알림톡 — 매장수: Q1 20~30, Q2 50, Q3 100, Q4 200 (매장당 100건 × 9원)
        [18000,22500,27000, 36000,40500,45000, 63000,72000,90000, 135000,153000,180000],
        # SMS + 본인인증
        [5000,6000,7000, 10000,12000,15000, 18000,22000,28000, 35000,40000,45000],
        # 이메일
        [0,0,0, 0,0,3000, 3000,5000,5000, 8000,10000,12000],
        # Workspace
        [18200]*12,
        # 모니터링
        [0,0,0, 0,0,0, 0,0,30000, 30000,30000,30000],
        # Firebase
        [0]*9 + [10000,15000,20000],
        # Maps
        [0]*9 + [10000,20000,30000],
        # 번역 API (P8b 가동 — USP)
        [0,0,0, 10000,15000,20000, 25000,30000,40000, 50000,60000,80000],
    ]
    O2027 = [
        ('Apple Developer (연 갱신)', [0]*6 + [128700] + [0]*5),
        ('Google Play Console',        [0]*12),
        ('Mac mini',                   [0]*12),
        ('NICE 본인인증',              [0]*12),
        ('도메인 (연 갱신)',           [0,0,0,0,0,60000] + [0]*6),
    ]
    total_r_2027 = year_sheet('2027년 월별', 2027, R2027, O2027,
        '점진 성장 가정 — Q1: 매장 20~30(MAU 1~2K), Q2: 매장 50(MAU 3~5K), Q3: 매장 100(MAU 5~10K), '
        'Q4: 매장 200(MAU 10K+). 알림톡 = 매장당 100건/월 × 9원 (현실적 가정)')

    # ── Sheet: 연간 합계 (대시보드) ───────────────────────────────────
    ws_sum = wb.create_sheet('연간 합계', 0)
    ws_sum['A1'] = 'PathWave 운영비 — 연간 합계 (2026·2027)'
    ws_sum['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
    ws_sum.merge_cells('A1:D1')
    ws_sum.append([])
    ws_sum.append(['연도', '연 합계 (₩)', '월 평균 (₩)', '비고'])
    ws_sum.append(['2026', f"='2026년 월별'!N{total_r_2026}", '=B4/5',
                   '6월 외부 신청 시작, 8~12월 (5개월) 실 운영 + 7월 1회성 포함'])
    ws_sum.append(['2027', f"='2027년 월별'!N{total_r_2027}", '=B5/12',
                   '12개월 — Q1~Q4 점진 성장 + 도메인·Apple 연 갱신'])
    ws_sum.append(['2년 합계', '=SUM(B4:B5)', '—', ''])
    for r in (3, 4, 5, 6):
        for c in (1, 2, 3, 4):
            ws_sum.cell(row=r, column=c).border = BORDER
    for c in (1, 2, 3, 4):
        ws_sum.cell(row=3, column=c).font = HEADER_FONT
        ws_sum.cell(row=3, column=c).fill = HEADER_FILL
        ws_sum.cell(row=3, column=c).alignment = Alignment(horizontal='center')
    for r in (4, 5, 6):
        ws_sum.cell(row=r, column=2).number_format = KRW_FMT
        ws_sum.cell(row=r, column=2).font = LINK_FONT
        ws_sum.cell(row=r, column=3).number_format = KRW_FMT
    ws_sum.cell(row=6, column=1).font = Font(name=FONT, bold=True)
    ws_sum.cell(row=6, column=2).fill = ASSUME_FILL
    ws_sum.cell(row=6, column=2).font = Font(name=FONT, bold=True)
    ws_sum.column_dimensions['A'].width = 14
    ws_sum.column_dimensions['B'].width = 18
    ws_sum.column_dimensions['C'].width = 18
    ws_sum.column_dimensions['D'].width = 60

    ws_sum.append([])
    note_r = ws_sum.max_row + 1
    ws_sum.cell(row=note_r, column=1).value = '주요 가정 / 변경점 (2026-05-23 갱신)'
    ws_sum.cell(row=note_r, column=1).font = Font(name=FONT, bold=True, color='1F4E78')
    for n in [
        '① 외부 서비스 신청 시작 = 2026-06-02 주 (법인카드 수취 후). 그 전 = 코드 작업만, 비용 거의 0',
        '② 이메일·도메인: 패스웨이브(서비스 — pathwave.co.kr) + 트리거소프트(법인 — triggersoft.kr) 분리',
        '   Google Workspace 2계정 ($7×2 = ₩18,200/월), 패스웨이브는 4 alias로 5메일 운영',
        '③ 알림톡 비용 현실화 — 매장당 월 2건 쿠폰/이벤트 × 평균 50명 = 100건/매장/월 × 9원',
        '   MAU 1K(매장 10) ₩9,000 / MAU 10K(매장 100) ₩90,000 / MAU 100K(매장 500) ₩450,000',
        '④ 초기 세팅비(Apple·Play·도메인·Mac mini·NICE)는 별도 시트로 분리, 월별 시트에서는 발생 월에 일시불 표시',
        '⑤ 환율: USD 1 = ₩1,300 (변동 시 가정 갱신)',
        '⑥ 토스페이먼츠 수수료(2.9% + 33원)는 결제 발생 시 매출 차감 — 운영비 미포함',
        '⑦ Mac mini 옵션 80만원·NICE 보증금 10만원 — 자본 여유 시 도입 (필수 아님)',
        '⑧ 모든 외부 서비스 키는 법인카드 발급 후 법인 명의 가입 (개인 → 법인 이관 어려움)',
        '⑨ 자동화 도구(Stage 2~3 — Channeltalk·ChatGPT·Make 등) = 출시 후 매출 발생 시 단계적 도입',
    ]:
        ws_sum.append([n])
        ws_sum.cell(row=ws_sum.max_row, column=1).font = Font(name=FONT, color='505050')

    ws_sum.append([])
    ws_sum.cell(row=ws_sum.max_row + 1, column=1).value = '사용 방법'
    ws_sum.cell(row=ws_sum.max_row, column=1).font = Font(name=FONT, bold=True, color='1F4E78')
    for line in [
        '① "서비스 신청 체크리스트": I열 신청 상태(대기→신청중→검수중→활성) 갱신',
        '② "초기 세팅비": 출시 전 1회성 비용 — 필수만 vs 옵션 포함 두 합계',
        '③ "월별 운영비 시나리오": MAU 1K/10K/100K 별 매월 발생 비용',
        '④ "2026/2027년 월별": 반복 + 1회성 통합 cash flow view, 누계 자동 계산',
        '⑤ "연간 합계": 연·월 평균 + 주요 가정',
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
