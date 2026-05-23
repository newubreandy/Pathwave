"""PathWave — 개발 체크리스트 + 서비스 신청·운영비용 엑셀 2개 생성.

산출:
  docs/exports/pathwave_dev_checklist.xlsx         — 개발 PR 체크리스트
  docs/exports/pathwave_services_and_costs.xlsx    — 외부 서비스 신청 체크리스트 + 월별/연간 운영비
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# ─────────── 공통 스타일 ─────────────────────────────────────────────────────
# 한글 글리프 포함 폰트 (Korean Windows·Mac Office 표준).
# 시스템에 없으면 Excel/Numbers 가 시스템 한글 폰트로 자동 대체.
FONT = '맑은 고딕'
HEADER_FONT = Font(name=FONT, bold=True, color='FFFFFF', size=11)
HEADER_FILL = PatternFill('solid', start_color='1F4E78')
INPUT_FONT  = Font(name=FONT, color='0000FF')           # 파랑 — 사용자 입력
LINK_FONT   = Font(name=FONT, color='008000')           # 녹색 — 시트간 링크
ASSUME_FILL = PatternFill('solid', start_color='FFFFCC') # 노랑 — 주요 가정
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
    """워크북 전 셀에 한글 폰트 강제. 기존 bold/color/italic/size 보존."""
    fn = font_name or FONT
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is None and not cell.font.bold and not cell.fill.fgColor.rgb:
                    continue
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
            if not cell.font.name:
                cell.font = Font(name=FONT)
    if freeze:
        ws.freeze_panes = ws.cell(row=header_row + 1, column=1).coordinate


# ═══════════════════════════════════════════════════════════════════════════
# FILE 1 — 개발 PR 체크리스트
# ═══════════════════════════════════════════════════════════════════════════
def build_dev_checklist():
    wb = Workbook()
    wb.remove(wb.active)

    # ── Sheet: PR 체크리스트 ──────────────────────────────────────────────
    ws = wb.create_sheet('PR 체크리스트')
    headers = ['PR', '분류', '도메인', '콘솔/영역', '내용 요약',
               '상태', '진척율', '담당', '시작일', '목표일', '완료일',
               '검증 시나리오 / 메모']
    ws.append(headers)

    # (PR, 분류, 도메인, 콘솔, 내용, 상태, 담당, 시작, 목표, 완료, 검증메모)
    today = '2026-05-23'
    prs = [
        ('P1', '인프라', 'mobile 디자인 기반', 'mobile',
         '테마 단일화 + 시스템 폰트 + neu/ 위젯 통합 + Pw* 4종 추가',
         '✅', '1인', '2026-05-21', '2026-05-22', today,
         '시뮬레이터 렌더 확인, 위젯 일관성'),
        ('P2', '인프라', 'mobile i18n', 'mobile·BE',
         'I18nService DB 통일 + 12언어 + 전 화면 t() 전환 + ko 시드 550 + DeepL 스크립트',
         '✅', '1인', '2026-05-21', '2026-05-22', today,
         '전 화면 grep clean, flutter analyze pass'),
        ('P3', '인프라', '웹 디자인 시스템', 'provider·admin',
         'alert/confirm 33곳→useDialog 공용 모달 + 색 토큰 정합',
         '✅', '1인', '2026-05-21', '2026-05-22', today,
         '두 콘솔 build + grep clean'),
        ('P4', 'Critical', '인증 우회 제거', 'provider·admin·BE',
         'DEV_AUTO_LOGIN env 게이트 + 실 로그인폼 복구 + /forgot-password 정식 구현(BE 2 API + 페이지)',
         '✅', '1인', today, today, today,
         'BE 2 API test client 통과(미존재 이메일 200/잘못된 코드 400). ⚠ app.py 재시작 필요'),
        ('P5', 'Critical', '매장·회사정보 실연동', 'provider',
         'StoreInfo 하드코딩 제거 + StoreService 실연동 + PwFooter + dead code Facilities 삭제',
         '✅', '1인', today, today, today,
         'res.facilities 데이터 접근 검증, build 통과'),
        ('P6', 'Critical', 'OCR 허위 제거', 'provider',
         'WifiSettings·ServiceRequest runOcrMock 제거 → 정직한 수동입력 UI',
         '✅', '1인', today, today, today,
         'OCR 잔여 참조 0건 grep, build 통과'),
        ('P7', 'Critical', '결제·구독 실연동', 'provider·admin',
         '카드 localStorage 평문저장 제거(PCI) + BillingService + Payment/Subscription/ServiceRequest 실연동',
         '✅', '1인', today, today, today,
         'localStorage 카드저장 0건 + PAN/CVC 전송 0건 grep, build 통과'),
        ('P8', 'Critical', '채팅 도메인', 'mobile·provider·admin·BE',
         'provider CustomerChat 실연동 + admin ChatMonitor + BE /api/chat/reports + mobile SSE 재연결',
         '◑', '1인', today, today, today,
         '번역=P8b 분리. BE 라우트 등록/401 가드 검증. ⚠ app.py 재시작 필요'),
        ('P8b', 'Critical', '채팅 자동 번역', 'mobile·provider·BE',
         'chat_messages 번역 캐시 스키마 + 뷰어별 언어 + translator↔chat 연결',
         '⬜', '1인', '', '키 확보 후', '',
         'Google/DeepL 키 확보(출시 2단계) 후 진행 — USP 기능'),
        ('P9', 'Critical', '쿠폰·스탬프 실연동', 'mobile·provider',
         'Coupons·Stamps mock→실연동 + 쿠폰 사용 silent error 수정',
         '⬜', '1인', '', '2026-06-중', '',
         '캐셔 게이트는 P22'),
        ('P10', 'Critical', '알림 도메인', 'mobile·provider·admin',
         'provider Notifications 실연동 + mobile 알림 라우팅 + 알림 탭 보강',
         '⬜', '1인', '', '2026-06-중', '',
         ''),
        ('P11', 'Critical', '대시보드·직원', 'provider·admin·BE',
         'Dashboard·StaffManagement 실연동 + admin 가짜데이터 제거 + StaffMonitor·CouponStats placeholder 해소',
         '⬜', '1인', '', '2026-06-중', '',
         ''),
        ('P12', 'Critical', 'mobile 심의 직격 화면', 'mobile·BE',
         'consent placeholder 제거 + 동의 로드 실패 복구 + settings dev 정보 제거 + 앱 버전 동적화',
         '⬜', '1인', '', '2026-06-중', '',
         '심의 직격 — 출시 전 필수'),
        ('P13', 'Critical', '약관 3종', 'mobile·provider·admin·BE',
         '환불·청소년·쿠키 정책 BE/admin/노출 + policy_view 언어 정합',
         '⬜', '1인', '', '2026-06-중', '',
         ''),
        ('P14', 'WiFi 로밍 B', 'WiFi 데이터 모델 재설계', 'BE',
         'wifi_profiles 확장 + beacon_wifi·units·grant·devices 신규 + beacons.role',
         '⬜', '1인', '', '2026-06-말~7월초', '',
         'P15~P19 기반'),
        ('P15', 'WiFi 로밍 B', 'WiFi 등록·연동', 'provider·admin·BE',
         'handshake 묶음 반환 + admin WiFi 등록화면 + provider WifiSettings 실연동 + 비콘 role UI',
         '⬜', '1인', '', '2026-07-초', '',
         'C10·C13 해소'),
        ('P16', 'WiFi 로밍 B', 'mobile WiFi 클라이언트', 'mobile',
         '비콘→WiFi 묶음 fetch·캐시 + BSSID 검증 + 손님 자동/승인 + home 보강',
         '⬜', '1인', '', '2026-07-초', '',
         ''),
        ('P17', 'WiFi 로밍 B', '.mobileconfig 다건 설치', 'BE·mobile·iOS',
         '.mobileconfig 생성·다건 설치 (서명은 인증서 도착 후)',
         '⬜', '1인', '', '2026-07-중', '',
         '서명은 Apple 인증서 확보 후 적용'),
        ('P18', 'WiFi 로밍 B', 'credential_mode managed', 'BE·provider·mobile',
         '비번 교체 리마인드 + 인가 손님 자동 전파',
         '⬜', '1인', '', '2026-07-중', '',
         'v1 flag — 코드만 완성, UI 비공개'),
        ('P19', 'WiFi 로밍 B', 'units/grant 관리 화면', 'admin·provider·BE',
         '호실·자리 시간제 권한 관리 UI',
         '⬜', '1인', '', '2026-07-중', '',
         'v1 flag — 코드만 완성, UI 비공개'),
        ('P20', '심의 마무리', '앱 버전관리', 'admin·mobile',
         'admin app-versions UI(BE 완성) + mobile OS 최소버전 게이트',
         '⬜', '1인', '', '2026-07-중', '',
         ''),
        ('P21', '심의 마무리', '심의 메타 자산', 'mobile·iOS',
         'PrivacyInfo.xcprivacy + Bundle ID 확정 + Android Photo Picker + 계정삭제 웹 URL',
         '⬜', '1인', '', '2026-07-중', '',
         '심의 reject 방지 필수'),
        ('P22', '회원 QR 운영', '쿠폰·스탬프 회원 QR', 'mobile·provider·BE',
         '회원 QR(URL 토큰) + provider 스캔/코드입력 → 적립·사용 + 친구초대 QR/링크',
         '⬜', '1인', '', '2026-07-초~중', '',
         'P9 이후 병행'),
    ]
    for row in prs:
        ws.append(row)

    # 진척율 수식 — IF(상태)
    for r in range(2, len(prs) + 2):
        status_cell = ws.cell(row=r, column=6).coordinate
        ws.cell(row=r, column=7).value = (
            f'=IF({status_cell}="✅",1,IF({status_cell}="🔄",0.5,'
            f'IF({status_cell}="◑",0.7,IF({status_cell}="🔎",0.9,0))))'
        )
        ws.cell(row=r, column=7).number_format = PCT_FMT
        # 상태 셀 색상
        status = ws.cell(row=r, column=6).value
        fill = {'✅': DONE_FILL, '◑': PARTIAL_FILL, '🔄': ACTIVE_FILL,
                '🔎': ACTIVE_FILL, '⬜': TODO_FILL}.get(status)
        if fill:
            ws.cell(row=r, column=6).fill = fill
            ws.cell(row=r, column=6).alignment = Alignment(horizontal='center', vertical='center')
        # 날짜 컬럼 포맷 + 입력색
        for col in (9, 10, 11):
            cell = ws.cell(row=r, column=col)
            cell.number_format = DATE_FMT
            cell.font = INPUT_FONT
        # 담당 입력색
        ws.cell(row=r, column=8).font = INPUT_FONT

    # 데이터 검증 — 상태 드롭다운
    dv_status = DataValidation(type='list', formula1='"⬜,🔄,🔎,◑,✅"', allow_blank=True)
    dv_status.add(f'F2:F{len(prs)+1}')
    ws.add_data_validation(dv_status)

    apply_table(ws, 1, len(prs) + 1, len(headers))
    widths = [6, 12, 22, 18, 50, 8, 9, 9, 12, 18, 12, 36]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 32

    # ── Sheet: 단계별 일정 ──────────────────────────────────────────────
    ws2 = wb.create_sheet('단계별 일정')
    ws2.append(['단계', '내용', '예상 기간', '누적', '비고'])
    schedule = [
        ('인프라', 'P1~P3', '~4일', '5월 말', '완료'),
        ('Critical 도메인', 'P4~P13 (10 PR)', '~2주', '6월 중순', 'P4~P8 완료, 나머지 진행 예정'),
        ('WiFi 로밍 (B 풀스코프)', 'P14~P19 (6 PR)', '~2.5~3주', '7월 초~중순', 'feature flag로 P18·P19 v1 비공개'),
        ('쿠폰·스탬프 회원 QR', 'P22 (P9 이후 병행)', '~1주', '7월 초~중순', ''),
        ('심의 마무리', 'P20~P21', '~3일', '7월 중순', ''),
        ('Phase 2~4 테스트·시드', '테스트데이터 시드 + 페르소나 검증', '~1.5주', '7월 중순~하순', ''),
        ('Phase 5 제출 준비', '빌드 + 스토어 메타데이터', '며칠', '7월 하순', ''),
        ('출시', '앱스토어/플레이 공개', '—', '7월 하순~8월 초', ''),
    ]
    for row in schedule:
        ws2.append(row)
    apply_table(ws2, 1, len(schedule) + 1, 5)
    for i, w in enumerate([22, 30, 14, 18, 40], 1):
        ws2.column_dimensions[get_column_letter(i)].width = w
    ws2.row_dimensions[1].height = 28

    # ── Sheet: 요약 ────────────────────────────────────────────────────
    ws3 = wb.create_sheet('요약', 0)
    ws3['A1'] = 'PathWave 개발 체크리스트 요약'
    ws3['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
    ws3.merge_cells('A1:C1')

    summary = [
        ('총 PR 수',          "=COUNTA('PR 체크리스트'!A2:A30)"),
        ('완료 (✅)',         "=COUNTIF('PR 체크리스트'!F2:F30,\"✅\")"),
        ('검토중 (🔎)',      "=COUNTIF('PR 체크리스트'!F2:F30,\"🔎\")"),
        ('부분 완료 (◑)',    "=COUNTIF('PR 체크리스트'!F2:F30,\"◑\")"),
        ('진행중 (🔄)',      "=COUNTIF('PR 체크리스트'!F2:F30,\"🔄\")"),
        ('대기 (⬜)',         "=COUNTIF('PR 체크리스트'!F2:F30,\"⬜\")"),
        ('가중 평균 진척율', "=AVERAGE('PR 체크리스트'!G2:G30)"),
        ('업데이트 일자',     today),
        ('목표 출시일',       '2026-07-하순~8월 초'),
    ]
    ws3.cell(row=3, column=1).value = '지표'
    ws3.cell(row=3, column=2).value = '값'
    for c in (1, 2):
        ws3.cell(row=3, column=c).font = HEADER_FONT
        ws3.cell(row=3, column=c).fill = HEADER_FILL
        ws3.cell(row=3, column=c).alignment = Alignment(horizontal='center')
        ws3.cell(row=3, column=c).border = BORDER
    for i, (label, value) in enumerate(summary):
        r = 4 + i
        ws3.cell(row=r, column=1).value = label
        ws3.cell(row=r, column=2).value = value
        for c in (1, 2):
            ws3.cell(row=r, column=c).border = BORDER
            ws3.cell(row=r, column=c).font = Font(name=FONT)
        if label == '가중 평균 진척율':
            ws3.cell(row=r, column=2).number_format = PCT_FMT
            ws3.cell(row=r, column=2).fill = ASSUME_FILL
        if isinstance(value, str) and value.startswith('='):
            ws3.cell(row=r, column=2).font = LINK_FONT
    ws3.column_dimensions['A'].width = 24
    ws3.column_dimensions['B'].width = 32

    # 사용 안내
    ws3.append([])
    ws3.cell(row=ws3.max_row + 1, column=1).value = '사용 방법'
    ws3.cell(row=ws3.max_row, column=1).font = Font(name=FONT, bold=True, color='1F4E78')
    for line in [
        '① "PR 체크리스트" 시트에서 F열(상태) 드롭다운으로 ⬜ → 🔄 → 🔎 → ✅ 갱신',
        '② I/J/K열(시작일·목표일·완료일)을 yyyy-mm-dd 로 입력하면 일정 추적 가능',
        '③ 진척율은 상태에 따라 자동 계산 (⬜=0%, 🔄=50%, ◑=70%, 🔎=90%, ✅=100%)',
        '④ 요약 시트는 PR 체크리스트의 상태를 실시간 집계',
    ]:
        ws3.append([line])
        ws3.cell(row=ws3.max_row, column=1).font = Font(name=FONT, color='505050')

    out = 'docs/exports/pathwave_dev_checklist.xlsx'
    force_workbook_font(wb)
    wb.save(out)
    return out


# ═══════════════════════════════════════════════════════════════════════════
# FILE 2 — 서비스 신청 체크리스트 + 운영비
# ═══════════════════════════════════════════════════════════════════════════
def build_services_costs():
    wb = Workbook()
    wb.remove(wb.active)

    # ── Sheet: 외부 서비스 신청 체크리스트 ───────────────────────────────
    ws = wb.create_sheet('서비스 신청 체크리스트')
    headers = ['우선순위', '카테고리', '서비스', '제공사', '필수/선택',
               '청구 방식', '월 추정 (₩)', '가입 계정',
               '신청 상태', '신청일', '활성일', '환경변수 / 통합 키', '비고']
    ws.append(headers)
    # (pri, cat, name, vendor, req, billing, monthly, account, status, applied, activated, env, note)
    # 우선순위 1=출시 직전 필수(가장 먼저), 2=출시 직후, 3=출시 후 선택
    services = [
        (1, '결제',       '토스페이먼츠',           'Toss Payments',                '필수', '거래 수수료(2.9%+33원)', 0,     'admin@', '대기', '', '', 'TOSS_SECRET_KEY, PG_PROVIDER', '심사 1~2주, 최우선 신청'),
        (1, '스토어',     'Apple Developer',         'Apple',                        '필수', '연 $99 (~₩128,700)',    10725, 'admin@', '대기', '', '', '—',                          '이메일 이관 어려움 → admin@ 필수'),
        (1, '스토어',     'Google Play Console',     'Google',                       '필수', '일회성 $25 (~₩32,500)', 0,     'admin@', '대기', '', '', '—',                          '일회성 등록'),
        (1, '호스팅',     '도메인 (pathwave.co.kr)',  'Cloudflare / 가비아',           '필수', '연 1.5~3만원',           2500,  'admin@', '대기', '', '', '—',                          '한국 법인 정석'),
        (1, '호스팅',     'Cloudflare DNS/Tunnel',    'Cloudflare',                   '필수', '무료',                   0,     'admin@', '대기', '', '', '—',                          'DNS + dev 서버 외부 접근'),
        (1, '호스팅',     '백엔드 서버',              'AWS EC2 / Render / Railway',   '필수', '월 5~15만원',            100000,'admin@', '대기', '', '', '—',                          'Flask + gunicorn'),
        (1, '호스팅',     'PostgreSQL DB',           'AWS RDS / Supabase / Neon',    '필수', '월 정액(서버 포함 가능)', 0,     'admin@', '대기', '', '', 'DATABASE_URL',               '마스터 + read 인덱스'),
        (1, '호스팅',     '프론트 정적 호스팅',       'Vercel / Netlify / CFP',       '필수', '무료 tier',              0,     'admin@', '대기', '', '', '—',                          'admin-web + provider-web'),
        (1, '인증/푸시',  'Firebase Auth + FCM',     'Google',                       '필수', '무료 tier',              0,     'dev@',   '대기', '', '', 'FIREBASE_CREDENTIALS, PUSH_PROVIDER', 'Google/Apple/이메일 인증 + 푸시'),
        (1, '이메일도메인','Google Workspace',        'Google',                       '필수', '월 $7~12/계정',          15600, 'admin@', '대기', '', '', '—',                          'admin/dev/support/info/noreply 5 alias'),

        (2, '소셜로그인', '카카오 로그인',            'Kakao',                        '필수', '무료',                   0,     'info@',  '대기', '', '', 'KAKAO_REST_KEY, KAKAO_NATIVE_APP_KEY', '카카오 검수 필요 (1~2주)'),
        (2, '소셜로그인', '네이버 로그인',            'Naver',                        '필수', '무료',                   0,     'info@',  '대기', '', '', 'NAVER_CLIENT_ID, NAVER_CLIENT_SECRET',  ''),
        (2, '알림톡/SMS', '솔라피 알림톡',            'Solapi',                       '필수', '건당 7~9원',             45000, 'dev@',   '대기', '', '', 'SOLAPI_API_KEY, SOLAPI_API_SECRET',     '템플릿 사전심사 1~2주'),
        (2, '알림톡/SMS', '솔라피 SMS 인증',          'Solapi',                       '필수', '건당 8~15원',            2400,  'dev@',   '대기', '', '', '위 키 공용',                            '회원가입 인증'),
        (2, '이메일',     'SendGrid',                'Twilio',                       '필수', '무료 100통/일',          0,     'dev@',   '대기', '', '', 'EMAIL_PROVIDER, SENDGRID_API_KEY',      '발신: support@/noreply@'),
        (2, '모니터링',   'Sentry',                  'Sentry',                       '필수', '무료 5K/월',             0,     'dev@',   '대기', '', '', 'SENTRY_DSN',                            '백엔드 통합 완료'),
        (2, '지도',       'Google Maps API',         'Google',                       '필수', '월 $200 무료 크레딧',     0,     'dev@',   '대기', '', '', 'GOOGLE_MAPS_API_KEY',                   '카드 등록 필수'),

        (3, '본인인증',   'NICE / KCB / PASS',        '본인인증 사업자',               '선택', '건당 30~80원',           2500,  'admin@', '대기', '', '', '계약 후 키 발급',                       '미성년자 확인용'),
        (3, '번역',       'Google Translate / DeepL', 'Google / DeepL',               '선택(P8b)', '$20/1M chars',     30000, 'dev@',   '대기', '', '', 'GOOGLE_TRANSLATE_API_KEY / DEEPL_API_KEY','채팅 자동번역 USP'),
        (3, '자동화 S2',  'Channeltalk',              'Channel.io',                   '선택', '무료~5만원/월',           0,     'dev@',   '대기', '', '', '—',                                    '출시 후 도입'),
        (3, '자동화 S2',  'ChatGPT API',              'OpenAI',                       '선택', '$0.15~3/M tokens',       0,     'dev@',   '대기', '', '', 'OPENAI_API_KEY',                       '응대/리뷰 응답 자동화'),
        (3, '자동화 S2',  'Make.com',                 'Make',                         '선택', '무료~$9~30/월',           0,     'dev@',   '대기', '', '', '—',                                    '노코드 자동화 허브'),
        (3, '자동화 S2',  'Buffer / Metricool',       'Buffer / Metricool',           '선택', '$6~15/월',               0,     'info@',  '대기', '', '', '—',                                    'SNS 자동 게시'),
        (3, '자동화 S3',  'HubSpot CRM',              'HubSpot',                      '선택', '$20~50/월',              0,     'admin@', '대기', '', '', '—',                                    '데이터 기반 자동화'),
        (3, '자동화 S2',  'Twilio Voice',             'Twilio',                       '선택', '분당 100~500원',         0,     'admin@', '대기', '', '', 'TWILIO_*',                             'AI 음성 통화 (Stage 2)'),
    ]
    for s in services:
        ws.append(s)

    # 월 추정(7열) — 파랑(가정값) + KRW
    for r in range(2, len(services) + 2):
        ws.cell(row=r, column=7).font = INPUT_FONT
        ws.cell(row=r, column=7).number_format = KRW_FMT
        # 신청일/활성일 포맷
        for col in (10, 11):
            ws.cell(row=r, column=col).number_format = DATE_FMT
            ws.cell(row=r, column=col).font = INPUT_FONT
        # 신청 상태 색
        status = ws.cell(row=r, column=9).value
        fill = {'활성': DONE_FILL, '검수중': PARTIAL_FILL, '신청중': ACTIVE_FILL,
                '대기': TODO_FILL, '보류': PARTIAL_FILL}.get(status)
        if fill:
            ws.cell(row=r, column=9).fill = fill
            ws.cell(row=r, column=9).alignment = Alignment(horizontal='center', vertical='center')
        # 우선순위 색상
        pri = ws.cell(row=r, column=1).value
        pri_color = {1: 'FFC7CE', 2: 'FFEB9C', 3: 'F2F2F2'}.get(pri)
        if pri_color:
            ws.cell(row=r, column=1).fill = PatternFill('solid', start_color=pri_color)
            ws.cell(row=r, column=1).alignment = Alignment(horizontal='center', vertical='center')
            ws.cell(row=r, column=1).font = Font(name=FONT, bold=True)

    # 데이터 검증 — 신청 상태 드롭다운
    dv_state = DataValidation(type='list', formula1='"대기,신청중,검수중,활성,보류"', allow_blank=True)
    dv_state.add(f'I2:I{len(services)+1}')
    ws.add_data_validation(dv_state)
    # 우선순위 드롭다운
    dv_pri = DataValidation(type='list', formula1='"1,2,3"', allow_blank=True)
    dv_pri.add(f'A2:A{len(services)+1}')
    ws.add_data_validation(dv_pri)

    apply_table(ws, 1, len(services) + 1, len(headers))
    for i, w in enumerate([8, 14, 26, 22, 11, 24, 14, 12, 12, 12, 12, 38, 28], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 36

    # ── Sheet: 월별 비용 시나리오 ────────────────────────────────────────
    ws2 = wb.create_sheet('월별 비용 시나리오')
    ws2['A1'] = '월별 비용 시나리오 — MAU 규모별'
    ws2['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
    ws2.merge_cells('A1:E1')

    ws2.append([])
    ws2.append(['항목', 'MAU 1K (출시초기)', 'MAU 10K (중간규모)', 'MAU 100K (대규모)', '비고'])
    scen = [
        ('서버 + DB',                100000, 400000, 3500000, '스케일업'),
        ('도메인 (월할)',             2500,   2500,   2500,   '연 3만원 ÷ 12'),
        ('알림톡',                   45000,  450000, 4500000,'5K→50K→500K 건/월'),
        ('SMS + 본인인증',           5000,   50000,  500000, ''),
        ('이메일 (SendGrid)',        0,      15000,  150000, 'tier 초과 시 유료'),
        ('Google Workspace',         15600,  15600,  78000,  '5 alias→5 별도 계정'),
        ('모니터링 (Sentry 등)',     0,      0,      300000, '대규모 유료화'),
        ('Apple Developer (월할)',   10725,  10725,  10725,  '$99/년'),
        ('Firebase / 로그인',        0,      0,      0,      '무료 tier'),
    ]
    start = ws2.max_row + 1
    for row in scen:
        ws2.append(row)
        r = ws2.max_row
        for c in (2, 3, 4):
            ws2.cell(row=r, column=c).number_format = KRW_FMT
            ws2.cell(row=r, column=c).font = INPUT_FONT
    end = ws2.max_row
    ws2.append(['소계 (월 합계)',
                f'=SUM(B{start}:B{end})',
                f'=SUM(C{start}:C{end})',
                f'=SUM(D{start}:D{end})',
                '합계 수식'])
    total_row = ws2.max_row
    for c in (2, 3, 4):
        ws2.cell(row=total_row, column=c).number_format = KRW_FMT
        ws2.cell(row=total_row, column=c).font = Font(name=FONT, bold=True)
        ws2.cell(row=total_row, column=c).fill = ASSUME_FILL
    ws2.cell(row=total_row, column=1).font = Font(name=FONT, bold=True)
    ws2.cell(row=total_row, column=1).fill = ASSUME_FILL

    apply_table(ws2, 3, total_row, 5)
    for i, w in enumerate([28, 22, 22, 22, 36], 1):
        ws2.column_dimensions[get_column_letter(i)].width = w

    # ── 월별 연간 시트 빌더 ────────────────────────────────────────────
    def year_sheet(name, year, months_data, assumptions_note):
        ws = wb.create_sheet(name)
        ws['A1'] = f'{year}년 월별 운영비 추정'
        ws['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
        ws.merge_cells('A1:N1')
        ws['A2'] = f'※ {assumptions_note}'
        ws['A2'].font = Font(name=FONT, italic=True, color='808080')
        ws.merge_cells('A2:N2')

        head = ['항목'] + [f'{m}월' for m in range(1, 13)] + ['연 합계']
        ws.append([])  # 빈 줄
        ws.append(head)
        header_row = ws.max_row

        line_items = [
            '서버 + DB', '도메인 (월할)', '알림톡', 'SMS + 본인인증',
            '이메일 (SendGrid)', 'Google Workspace', '모니터링', 'Firebase / 로그인',
            'Google Maps (무료 크레딧 초과분)', '번역 API (P8b)',
        ]
        for label, monthly in zip(line_items, months_data):
            ws.append([label] + list(monthly))
            r = ws.max_row
            ws.cell(row=r, column=14).value = f'=SUM(B{r}:M{r})'
            for c in range(2, 14):
                ws.cell(row=r, column=c).number_format = KRW_FMT
                ws.cell(row=r, column=c).font = INPUT_FONT
            ws.cell(row=r, column=14).number_format = KRW_FMT
            ws.cell(row=r, column=14).font = Font(name=FONT, bold=True)

        # 1회성
        def append_one_time(label, monthly):
            ws.append([label] + list(monthly))
            r = ws.max_row
            ws.cell(row=r, column=14).value = f'=SUM(B{r}:M{r})'
            for c in range(2, 14):
                ws.cell(row=r, column=c).number_format = KRW_FMT
                ws.cell(row=r, column=c).font = INPUT_FONT
            ws.cell(row=r, column=14).number_format = KRW_FMT
            ws.cell(row=r, column=14).font = Font(name=FONT, bold=True)

        if year == 2026:
            append_one_time('Apple Developer (연회비)', [0]*7 + [128700] + [0]*4)
            append_one_time('Google Play Console (일회성)', [0]*7 + [32500] + [0]*4)
            append_one_time('Mac mini 중고 (선택)', [0]*6 + [800000] + [0]*5)
        else:
            append_one_time('Apple Developer (연회비 갱신)', [0]*7 + [128700] + [0]*4)
            append_one_time('Google Play Console (일회성)', [0]*12)
            append_one_time('Mac mini 중고 (선택)', [0]*12)

        last_item_row = ws.max_row

        # 월 합계
        ws.append(['월 합계'] +
                  [f'=SUM({get_column_letter(c)}{header_row+1}:{get_column_letter(c)}{last_item_row})'
                   for c in range(2, 14)] +
                  [f'=SUM(B{last_item_row+1}:M{last_item_row+1})'])
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
        ws.column_dimensions['A'].width = 32
        for c in range(2, 15):
            ws.column_dimensions[get_column_letter(c)].width = 11
        return total_r

    # 2026년 — 1~7월 출시전(거의 0), 8월 출시, 8~12월 Stage 1
    M2026 = [
        [0,0,0,0,0,0,0,    50000, 100000, 100000, 100000, 100000],
        [0,0,0,0,0,0,0,    2500, 2500, 2500, 2500, 2500],
        [0,0,0,0,0,0,0,    10000, 20000, 30000, 40000, 50000],
        [0,0,0,0,0,0,0,    2000, 3000, 4000, 5000, 5000],
        [0,0,0,0,0,0,0,    0, 0, 0, 0, 0],
        [0,0,0,0,0,0,15600, 15600, 15600, 15600, 15600, 15600],
        [0,0,0,0,0,0,0,    0, 0, 0, 0, 0],
        [0,0,0,0,0,0,0,    0, 0, 0, 0, 0],
        [0,0,0,0,0,0,0,    0, 0, 0, 0, 0],
        [0,0,0,0,0,0,0,    0, 0, 0, 0, 0],
    ]
    total_r_2026 = year_sheet('2026년 월별', 2026, M2026,
        '출시 = 7월 하순~8월 초. 1~7월은 코드 작업 중심. 8월부터 외부 서비스 활성화. MAU 0~1K 가정')

    # 2027년 — 분기별 점진 성장
    M2027 = [
        [100000,100000,100000, 150000,150000,150000, 250000,250000,250000, 400000,400000,400000],
        [2500]*12,
        [50000,60000,70000, 100000,130000,160000, 200000,250000,300000, 350000,400000,450000],
        [5000,6000,7000, 10000,15000,20000, 25000,30000,40000, 45000,50000,50000],
        [0,0,0, 5000,5000,5000, 10000,10000,10000, 15000,15000,15000],
        [15600]*12,
        [0,0,0, 0,0,0, 30000,30000,30000, 50000,50000,50000],
        [0]*9 + [20000,20000,20000],
        [0]*9 + [30000,30000,30000],
        [0,0,0, 20000,30000,40000, 50000,60000,80000, 100000,120000,150000],
    ]
    total_r_2027 = year_sheet('2027년 월별', 2027, M2027,
        '점진 성장 가정 — Q1: MAU 1~2K(Stage 1 후반), Q2~Q3: MAU 3~10K(Stage 2), Q4: MAU 10K+. 자동화 도구는 별도')

    # ── Sheet: 연간 합계 ────────────────────────────────────────────────
    ws_sum = wb.create_sheet('연간 합계', 0)
    ws_sum['A1'] = 'PathWave 운영비 — 연간 합계 (2026·2027)'
    ws_sum['A1'].font = Font(name=FONT, bold=True, size=14, color='1F4E78')
    ws_sum.merge_cells('A1:D1')

    ws_sum.append([])
    ws_sum.append(['연도', '연 합계 (₩)', '월 평균 (₩)', '비고'])
    ws_sum.append(['2026', f"='2026년 월별'!N{total_r_2026}", '=B4/5',
                   '8~12월 (5개월) 실 운영 + 1회성(Apple/Play/Mac mini) 포함'])
    ws_sum.append(['2027', f"='2027년 월별'!N{total_r_2027}", '=B5/12',
                   '12개월 — Stage 1→2 점진 성장 + Apple 갱신'])
    ws_sum.append(['2년 합계', '=SUM(B4:B5)', '—', ''])

    for r in (3, 4, 5, 6):
        for c in (1, 2, 3, 4):
            ws_sum.cell(row=r, column=c).border = BORDER
            ws_sum.cell(row=r, column=c).font = Font(name=FONT)
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
    ws_sum.column_dimensions['D'].width = 56

    ws_sum.append([])
    note_r = ws_sum.max_row + 1
    ws_sum.cell(row=note_r, column=1).value = '주요 가정'
    ws_sum.cell(row=note_r, column=1).font = Font(name=FONT, bold=True, color='1F4E78')
    for n in [
        '· 환율: USD 1 = ₩1,300 (변동 시 가정 갱신)',
        '· MAU 성장: 2026 8~12월 0~1K → 2027 Q4까지 10K+ (보수적 추정)',
        '· 토스페이먼츠 수수료(2.9%+33원)는 결제 발생 시 매출 차감 — 운영비에 미포함',
        '· Mac mini 옵션 80만원 — 2026년 7월(출시 직전), 자본 여유 시',
        '· 자동화 도구(Stage 2~3 — Channeltalk/ChatGPT/Make/Buffer 등)는 별도 — 도입 시 추가',
        '· 모든 외부 서비스 키는 법인카드 발급 후 법인 명의로 가입',
        '· 신청 체크리스트의 신청 상태가 "활성"으로 바뀐 항목만 실제 비용 발생',
    ]:
        ws_sum.append([n])
        ws_sum.cell(row=ws_sum.max_row, column=1).font = Font(name=FONT, color='505050')

    # 사용 안내
    ws_sum.append([])
    ws_sum.cell(row=ws_sum.max_row + 1, column=1).value = '사용 방법'
    ws_sum.cell(row=ws_sum.max_row, column=1).font = Font(name=FONT, bold=True, color='1F4E78')
    for line in [
        '① "서비스 신청 체크리스트" 시트의 I열(신청 상태)을 대기→신청중→검수중→활성 으로 갱신',
        '② J/K열(신청일·활성일)을 입력해 신청 진행을 추적',
        '③ 우선순위 1(빨강) → 2(노랑) → 3(회색) 순으로 신청 진행 권장',
        '④ "월별 비용 시나리오" / "2026년·2027년 월별" / "연간 합계" 시트로 비용 예측',
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
