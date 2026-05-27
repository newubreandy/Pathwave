"""PathWave 과업지시서 (전체 신규 개발) → MS Word(.docx) 생성.

실행:
    cd /Users/m5pro16/Desktop/pathwave
    ./venv/bin/python docs/vendor/build_docx.py

산출물:
    docs/vendor/PathWave_과업지시서_2026-05-03.docx
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pathlib import Path


# ── 색상 ──────────────────────────────────────────────────────────────────────
PURPLE      = RGBColor(0x4A, 0x23, 0xBF)
DARK_PURPLE = RGBColor(0x33, 0x18, 0x99)
GREY        = RGBColor(0x66, 0x66, 0x66)
DARK        = RGBColor(0x1A, 0x1A, 0x1A)
RED         = RGBColor(0xCC, 0x00, 0x00)   # ⚠️ 위험/주의 항목
DARK_RED    = RGBColor(0x99, 0x00, 0x00)
LIGHT_BG    = "F4F0FF"
RED_BG      = "FFE5E5"


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────
def set_cell_bg(cell, hex_color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tc_pr.append(shd)


def set_korean_font(run, size=10, bold=False, color=None):
    run.font.name = 'Malgun Gothic'
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), '맑은 고딕')
    rFonts.set(qn('w:ascii'), 'Malgun Gothic')
    rFonts.set(qn('w:hAnsi'), 'Malgun Gothic')
    run.font.size = Pt(size)
    run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def add_heading(doc, text, level=1, color=None):
    p = doc.add_paragraph()
    if level == 0:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        set_korean_font(run, size=28, bold=True, color=color or PURPLE)
    elif level == 1:
        run = p.add_run(text)
        set_korean_font(run, size=18, bold=True, color=color or PURPLE)
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(8)
    elif level == 2:
        run = p.add_run(text)
        set_korean_font(run, size=14, bold=True, color=color or DARK_PURPLE)
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
    elif level == 3:
        run = p.add_run(text)
        set_korean_font(run, size=12, bold=True, color=color or DARK)
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
    return p


def add_para(doc, text, size=10, bold=False, color=None, indent=None):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    run = p.add_run(text)
    set_korean_font(run, size=size, bold=bold, color=color)
    return p


def add_red_para(doc, text, size=10, indent=0.5):
    """⚠️ 빨간색 경고 문단."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(indent)
    run = p.add_run('⚠ ')
    set_korean_font(run, size=size, bold=True, color=RED)
    run = p.add_run(text)
    set_korean_font(run, size=size, color=RED)
    return p


def add_bullet(doc, text, size=10, indent=0.5):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent = Cm(indent)
    run = p.add_run(text)
    set_korean_font(run, size=size)
    return p


def add_bullet_with_red(doc, normal_text, red_tail, size=10, indent=0.5):
    """일반 텍스트 + 빨간색 꼬리표 (예: '… [위험: iOS 제약]')."""
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent = Cm(indent)
    run = p.add_run(normal_text + ' ')
    set_korean_font(run, size=size)
    run = p.add_run(red_tail)
    set_korean_font(run, size=size, bold=True, color=RED)
    return p


def add_checklist(doc, items, size=10):
    for item in items:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.5)
        run = p.add_run('☐  ' + item)
        set_korean_font(run, size=size)


def add_numbered(doc, text, size=10):
    p = doc.add_paragraph(style='List Number')
    run = p.add_run(text)
    set_korean_font(run, size=size)


def add_table(doc, headers, rows, col_widths=None, header_bg=LIGHT_BG, font_size=10,
              red_rows=None):
    """
    rows의 일부 행을 빨간색으로 강조하려면 red_rows=[행번호…] (0-based, 본문 기준).
    또는 셀 단위로 빨갛게 하려면 row_data 안에 ('text', 'RED')처럼 튜플 사용.
    """
    red_rows = red_rows or []
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    if col_widths:
        for i, w in enumerate(col_widths):
            for cell in table.columns[i].cells:
                cell.width = Cm(w)

    # 헤더
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_bg(cell, header_bg)
        cell.text = ''
        p = cell.paragraphs[0]
        run = p.add_run(h)
        set_korean_font(run, size=font_size, bold=True, color=DARK_PURPLE)

    # 본문
    for r, row_data in enumerate(rows):
        row = table.rows[r + 1]
        is_red_row = r in red_rows
        for i, val in enumerate(row_data):
            cell = row.cells[i]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP

            # 셀 단위 색상: ('text', 'RED') 튜플 처리
            text = val
            cell_red = is_red_row
            if isinstance(val, tuple) and len(val) == 2 and val[1] == 'RED':
                text = val[0]
                cell_red = True

            cell.text = ''
            p = cell.paragraphs[0]
            run = p.add_run(str(text))
            color = RED if cell_red else None
            set_korean_font(run, size=font_size, color=color, bold=cell_red)

            if is_red_row:
                set_cell_bg(cell, RED_BG)
    return table


def add_note_box(doc, text, color=RGBColor(0x66, 0x46, 0x00), bg="FFFBE6", icon='💡  '):
    table = doc.add_table(rows=1, cols=1)
    cell = table.rows[0].cells[0]
    set_cell_bg(cell, bg)
    cell.text = ''
    p = cell.paragraphs[0]
    run = p.add_run(icon + text)
    set_korean_font(run, size=10, color=color)
    return table


def add_red_box(doc, text):
    """빨간색 경고 박스 (강조)."""
    return add_note_box(doc, text, color=DARK_RED, bg=RED_BG, icon='⚠ 주의: ')


def add_page_break(doc):
    doc.add_page_break()


# ═══════════════════════════════════════════════════════════════════════════════
#  문서 시작
# ═══════════════════════════════════════════════════════════════════════════════
doc = Document()

for section in doc.sections:
    section.left_margin   = Cm(2.2)
    section.right_margin  = Cm(2.2)
    section.top_margin    = Cm(2.0)
    section.bottom_margin = Cm(2.0)

style = doc.styles['Normal']
style.font.name = 'Malgun Gothic'
style.font.size = Pt(10)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '맑은 고딕')


# ── 표지 ────────────────────────────────────────────────────────────────────
for _ in range(4):
    doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('PathWave')
set_korean_font(run, size=36, bold=True, color=PURPLE)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('외주 과업지시서')
set_korean_font(run, size=22, bold=True, color=DARK_PURPLE)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('Statement of Work — Full New Build')
set_korean_font(run, size=14, color=GREY)

for _ in range(4):
    doc.add_paragraph()

cover_table = doc.add_table(rows=6, cols=2)
cover_table.alignment = WD_TABLE_ALIGNMENT.CENTER
cover_info = [
    ('발주처',     '(개인사업자, 법인 전환 예정 — 2026년 5월)'),
    ('프로젝트명', 'PathWave (BLE 비콘 기반 매장 통합 SaaS)'),
    ('과업 성격',  '전체 시스템 신규 개발 (백엔드 + 클라이언트 3종 + 인프라)'),
    ('문서 작성일', '2026-05-03'),
    ('문서 버전',  'v2.0 (전체 신규 개발판)'),
    ('대상 외주사', '___________________________________'),
]
for r, (k, v) in enumerate(cover_info):
    row = cover_table.rows[r]
    row.cells[0].width = Cm(4)
    row.cells[1].width = Cm(11)
    set_cell_bg(row.cells[0], "F7F5FF")
    row.cells[0].text = ''
    p = row.cells[0].paragraphs[0]
    run = p.add_run(k)
    set_korean_font(run, size=11, bold=True, color=DARK_PURPLE)
    row.cells[1].text = ''
    p = row.cells[1].paragraphs[0]
    run = p.add_run(v)
    set_korean_font(run, size=11)

add_page_break(doc)


# ── 목차 ────────────────────────────────────────────────────────────────────
add_heading(doc, '📑 목차', level=1)
for item in [
    '1. 프로젝트 개요',
    '2. 시스템 구성 및 페르소나',
    '3. 기술 위험 및 제약 사항 ⚠ (반드시 검토)',
    '4. 과업 범위 (Work Packages 5개)',
    '5. 기능 요구사항 (페르소나별)',
    '6. 비기능 요구사항',
    '7. 발주처 제공 자료',
    '8. 일정 및 마일스톤',
    '9. 산출물 및 검수 기준',
    '10. 견적 양식',
    '11. 일반 조건',
]:
    add_para(doc, item, size=11, indent=0.5)

add_page_break(doc)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. 프로젝트 개요
# ═══════════════════════════════════════════════════════════════════════════════
add_heading(doc, '1. 프로젝트 개요', level=1)

add_heading(doc, '1.1 서비스 정의', level=2)
add_para(doc,
    'PathWave는 매장에 설치된 BLE 비콘(FSC-BP108B)을 통해 사용자 앱이 자동으로 '
    '① WiFi 연결 (한 번 동의 후), ② 스탬프 적립, ③ 쿠폰 발급을 트리거하는 매장 SaaS 플랫폼이다. '
    '본 외주는 백엔드, 시설관리자 웹, 사용자 모바일 앱, 운영자 웹 콘솔, 인프라까지 '
    '전체 시스템을 신규 개발하는 것을 목적으로 한다.'
)

add_heading(doc, '1.2 비즈니스 일정', level=2)
add_bullet(doc, '2026년 5월 — 법인 등록 및 정식 런칭 목표')
add_bullet_with_red(doc,
    '결제(PG)·푸시(APNs)·소셜로그인 등 외부 연동의 실 키 발급은 발주처 법인 등록 이후 가능',
    '[일정 영향]')
add_bullet(doc, '본 과업은 런칭 직전까지 전체 시스템 완성 및 베타 검증을 목표로 함')

add_heading(doc, '1.3 본 과업의 정의', level=2)
add_para(doc,
    '발주처는 본 과업을 통해 PathWave 서비스를 운영하기 위한 모든 소프트웨어 자산을 인수받는다. '
    '외주사는 백엔드 API 설계·구현, 데이터베이스 설계, 클라이언트 3종(반응형 웹 2개 + 모바일 앱), '
    '인프라/배포/모니터링까지 일관된 책임을 진다.'
)

add_red_box(doc,
    '본 문서는 "전체 신규 개발"을 전제로 작성되었다. 발주처가 보유한 참조 구현(reference implementation)은 '
    '7장에서 옵션으로 제공되며, 외주사는 이를 참고하거나 무시할 수 있다. 단, 본 문서의 기능 요구사항을 '
    '최종 산출물이 만족해야 한다.'
)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. 시스템 구성 및 페르소나
# ═══════════════════════════════════════════════════════════════════════════════
add_heading(doc, '2. 시스템 구성 및 페르소나', level=1)

add_heading(doc, '2.1 시스템 구성', level=2)
add_table(doc,
    headers=['구성요소', '플랫폼', '대상 사용자'],
    rows=[
        ('① 백엔드 API 서버',          'REST API + SSE',            '모든 클라이언트'),
        ('② 시설관리자 반응형 웹',     'PC + 모바일 (반응형)',       '매장 사장님 / 직원'),
        ('③ 사용자 모바일 앱',         'iOS + Android (Flutter 권장)', '일반 사용자'),
        ('④ Super Admin 웹 콘솔',      'PC 우선',                    'PathWave 운영자'),
        ('⑤ 인프라 / 배포 / 모니터링', 'AWS·GCP·NCP 등 협의',        '운영팀'),
    ],
    col_widths=[5, 6, 5],
)

add_heading(doc, '2.2 4개 페르소나', level=2)
add_table(doc,
    headers=['페르소나', '주요 행위', '접근 채널'],
    rows=[
        ('익명 사용자', '매장 검색, 공개 정보 조회', '모바일 앱 / 웹'),
        ('일반 사용자 (User)', '매장 방문 → 자동 WiFi/스탬프, 쿠폰 사용, 채팅', '모바일 앱 (iOS/Android)'),
        ('시설 사장님/직원 (Facility)', '매장 관리, 비콘 클레임, 스탬프·쿠폰 발급, 직원 관리, 푸시', '반응형 웹 (PC + 모바일)'),
        ('PathWave 운영자 (Super Admin)', '비콘 입고·할당, 사장 가입 승인, 결제·정산 관리, 시스템 공지', '웹 (PC 우선)'),
    ],
    col_widths=[4, 8, 4],
)

add_heading(doc, '2.3 핵심 흐름 (한눈에)', level=2)
add_para(doc, '운영자 → 비콘 입고 → 사장 가입 승인 → 사장이 시설/비콘 등록 → '
              '사용자가 매장 방문 → BLE 핸드셰이크 → WiFi/스탬프/쿠폰 자동 처리 → 푸시 알림 → 매장 직원이 쿠폰 사용 처리.')


# ═══════════════════════════════════════════════════════════════════════════════
# 3. 기술 위험 및 제약 사항 ⚠ ── 빨간색 강조
# ═══════════════════════════════════════════════════════════════════════════════
add_page_break(doc)
add_heading(doc, '3. 기술 위험 및 제약 사항 ⚠', level=1, color=RED)
add_red_box(doc,
    '본 장은 외주사가 견적 산정 및 일정 수립 전 반드시 검토해야 할 항목이다. '
    '아래 항목은 OS·외부 서비스·법규에 의한 제약이며, 본 문서의 다른 어떤 기능 요구사항보다 우선한다. '
    '항목 누락으로 인한 일정/비용 상승은 외주사 책임으로 한정되지 않는다.'
)

# 3.1 OS/플랫폼 제약
add_heading(doc, '3.1 OS / 플랫폼 제약', level=2, color=DARK_RED)
add_table(doc,
    headers=['항목', '제약 내용'],
    rows=[
        ('iOS / Android WiFi 자동 연결',
         '⚠ "완전 자동" 불가. iOS는 NEHotspotConfiguration이 첫 연결 시 사용자 동의 프롬프트 필수, '
         'Android 10+는 WifiNetworkSuggestion API로 알림 표시 후 사용자 승인 필요. '
         '"한 번 동의 후 자동 재연결"이 정확한 표현.'),
        ('iOS Background BLE 스캔',
         '⚠ 일반 BLE 스캔은 백그라운드에서 큰 제약. 비콘 영역 모니터링은 iBeacon/CoreLocation 영역 모니터링으로 '
         '대체 필수. Background Modes 권한(Bluetooth Central / Location updates) 필수.'),
        ('Android 12+ BLE 권한',
         '⚠ BLUETOOTH_SCAN, BLUETOOTH_CONNECT 런타임 권한 추가. neverForLocation 플래그 처리 필요.'),
        ('Android 13+ 알림 권한',
         '⚠ POST_NOTIFICATIONS 런타임 권한 사용자 동의 필수.'),
        ('iOS 14+ 추적 투명성 (ATT)',
         '⚠ 광고 식별자 수집 시 권한 프롬프트 필요. PathWave는 광고 사용 없으면 적용 안 됨.'),
    ],
    col_widths=[5, 11],
    red_rows=[0, 1, 2, 3, 4],
)

# 3.2 외부 서비스 의존
add_heading(doc, '3.2 외부 서비스 의존 (발주처 책임)', level=2, color=DARK_RED)
add_table(doc,
    headers=['외부 서비스', '주의 사항'],
    rows=[
        ('카카오 / 네이버 소셜 로그인',
         '⚠ Firebase Authentication이 직접 지원 안 함. 카카오·네이버 SDK로 로그인 → '
         '백엔드에서 Firebase Custom Token 발급 → Firebase로 이중 인증 흐름 필요. '
         '클라이언트·서버 양쪽 모두 추가 작업 발생.'),
        ('PG 결제 연동 (토스페이먼츠 권장)',
         '⚠ 사업자 심사 후 실 키 발급. 법인 미등록 단계에서는 sandbox만 가능. '
         'PCI-DSS 준수: 카드 정보 직접 저장 절대 금지, PG 토큰화 필수.'),
        ('FCM (Firebase Cloud Messaging)',
         '⚠ iOS 푸시는 APNs 인증서/키 발급 필수. Apple Developer Program 가입(연 $99) 발주처 책임. '
         'Firebase 프로젝트 생성 및 권한 부여 발주처 책임.'),
        ('Google Translate API',
         '⚠ 유료. 번역 캐싱 전략 필수 (DB에 lang_code별 저장).'),
        ('BLE 비콘 FSC-BP108B',
         '⚠ 펌웨어 사양서 발주처가 사전 제공. UUID/Major/Minor 체계, 핸드셰이크 프로토콜, '
         '실물 비콘 1~3개 대여. 비콘 제조사와의 추가 인터페이스가 필요한 경우 발주처가 협의 주관.'),
    ],
    col_widths=[5, 11],
    red_rows=[0, 1, 2, 3, 4],
)

# 3.3 보안 / 규제
add_heading(doc, '3.3 보안 및 규제', level=2, color=DARK_RED)
add_table(doc,
    headers=['항목', '주의 사항'],
    rows=[
        ('개인정보보호법 / 정보통신망법',
         '⚠ 가입·로그인·결제 화면의 개인정보 처리방침 노출 필수. 만 14세 미만 가입 제한. '
         '파기·이용 정지 요청 처리 절차.'),
        ('WiFi 비밀번호 저장',
         '⚠ DB 저장 시 AES-256-GCM 등 강암호화 필수. 클라이언트에 평문 노출 시점은 '
         'BLE 핸드셰이크 응답 시 HTTPS 위에서만 허용. 로그/덤프에 평문 출력 금지.'),
        ('JWT 토큰 관리',
         '⚠ 클라이언트는 secure storage에 저장 (iOS Keychain / Android EncryptedSharedPreferences). '
         '리프레시 토큰 회전(rotation) 권장.'),
        ('ISMS-P 인증',
         '⚠ 운영 단계에서 신청 가능. 본 외주 범위에서는 인증 준수 가능한 설계 (감사로그, 접근통제) 적용.'),
    ],
    col_widths=[5, 11],
    red_rows=[0, 1, 2, 3],
)

# 3.4 운영
add_heading(doc, '3.4 운영 / 스케일', level=2, color=DARK_RED)
add_table(doc,
    headers=['항목', '주의 사항'],
    rows=[
        ('DB 마이그레이션',
         '⚠ 개발은 SQLite, 운영은 PostgreSQL 14+ 권장. SQL 호환성 확보 (RAW 쿼리에 SQLite 전용 함수 사용 금지).'),
        ('런칭 일정',
         '⚠ 발주처 법인 등록(2026-05) 이전엔 PG 실 결제, APNs 인증서, 카카오 비즈 SDK 등 '
         '일부 외부 자원 미발급. 베타 단계까지 실 결제 검증 불가.'),
        ('한국어 외 다국어',
         '⚠ ko 기본, en/ja/zh는 자동 번역 캐시. 정식 번역 검수는 외주 범위 외.'),
    ],
    col_widths=[5, 11],
    red_rows=[0, 1, 2],
)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. 과업 범위 (5 WPs)
# ═══════════════════════════════════════════════════════════════════════════════
add_page_break(doc)
add_heading(doc, '4. 과업 범위 (Work Packages)', level=1)

# WP1 백엔드
add_heading(doc, '📦 WP1 — 백엔드 시스템 (REST API + DB)', level=2)

add_heading(doc, '4.1.1 범위', level=3)
add_para(doc,
    '4개 페르소나가 사용하는 모든 API 및 데이터 모델을 신규 설계·구현한다. '
    '인증, 비콘 핸드셰이크, 스탬프/쿠폰, 채팅(SSE), 결제, 푸시 발송 등 핵심 도메인을 포함한다.'
)

add_heading(doc, '4.1.2 기술 권장 스택', level=3)
add_bullet(doc, '언어: Python 3.12 / Node.js 20 / Go 1.22 등 (외주사 제안 — 발주처 협의)')
add_bullet(doc, 'API: REST 또는 GraphQL (REST 권장)')
add_bullet(doc, 'DB: 개발 SQLite → 운영 PostgreSQL 14+')
add_bullet(doc, '인증: JWT (access + refresh, 토큰 회전)')
add_bullet(doc, '실시간: SSE (Server-Sent Events) — 채팅 메시지 push')
add_bullet(doc, '암호화: bcrypt(비밀번호), AES-256-GCM(WiFi 비밀번호)')
add_bullet_with_red(doc,
    '소셜 로그인: Firebase Authentication 기반 + 카카오/네이버 Custom Token 변환',
    '[제약: 3.2 참조]')

add_heading(doc, '4.1.3 핵심 기능 영역 (13개 도메인)', level=3)
add_table(doc,
    headers=['도메인', '주요 엔드포인트 (예시)'],
    rows=[
        ('일반 인증',          'send-code / verify-code / register / login / refresh / social-login'),
        ('시설 가입(사장)',     'send-code / verify-code / register / login / me'),
        ('직원',                'invite / accept / login / list'),
        ('시설(매장) 관리',     'CRUD / 이미지 다중 업로드 / 영업시간 / 다국어 / claim-beacon'),
        ('검색',                'facilities (자동완성, 카테고리, 위치 필터)'),
        ('비콘',                'handshake / register(super_admin) / nearby / inventory'),
        ('스탬프',              'issue / list / redeem / auto(BLE 트리거)'),
        ('쿠폰',                'issue / list / redeem / auto(스탬프 보상)'),
        ('알림',                'list / mark-read / settings'),
        ('푸시',                'register-token / send (FCM 추상화)'),
        ('채팅',                'rooms / messages / sse-stream'),
        ('결제 / 구독',         'charge (PG 추상화) / invoices / subscription'),
        ('리포트',              'sales / stamps / coupons (집계)'),
        ('운영자',              'login / beacons (import/list/assign) / facility-accounts (verify/suspend) / stats / payments / subscriptions'),
    ],
    col_widths=[4, 12],
)

add_heading(doc, '4.1.4 데이터 모델 (테이블 23종 권장)', level=3)
add_para(doc,
    '계정/인증 5종 (users, facility_accounts, staff_accounts, super_admin_accounts, email_codes), '
    '비콘/시설 5종, 스탬프/쿠폰 4종, 알림/푸시/채팅 5종, 결제/구독 3종, 리포트 1종. '
    '세부 스키마는 7장의 발주처 제공 자료(스키마 정의서) 참조.'
)

add_heading(doc, '4.1.5 작업 항목 (Checklist)', level=3)
add_checklist(doc, [
    '도메인별 API 설계 + OpenAPI 명세 산출',
    'DB 스키마 설계 + 마이그레이션 도구 (Alembic 등) 구성',
    '4개 페르소나(sub_type) 권한 분리 + 데코레이터 또는 미들웨어',
    '이메일 인증, 비밀번호 강도 검증, 휴대폰 OTP(선택)',
    'BLE 핸드셰이크: 비콘 UUID/Major/Minor 검증 → WiFi 정보 + 자동 스탬프 응답',
    'AES-256-GCM 키 관리(KMS 또는 환경변수 + 회전)',
    'SSE 채팅 + 푸시 알림 통합',
    'PG 추상화 (sandbox 우선, 운영 시 토스페이먼츠 등으로 swap)',
    'FCM 추상화 (stub 모드 + 실제 모드 스위치)',
    '구글 번역 추상화 (캐싱 포함)',
    '관리자 감사 로그 (audit log)',
    'API 단위 테스트 + 통합 테스트 (커버리지 70% 이상 목표)',
    'CORS, 레이트 리밋, IP 차단 등 보안 헤더',
])

# WP2 시설관리자 웹
add_page_break(doc)
add_heading(doc, '📦 WP2 — 시설관리자 반응형 웹', level=2)

add_heading(doc, '4.2.1 범위', level=3)
add_para(doc,
    '시설 사장님/직원이 PC와 모바일 모두에서 사용 가능한 반응형 웹을 신규 개발한다. '
    'React + Vite 권장. 디자인 시스템은 발주처 제공.'
)

add_heading(doc, '4.2.2 화면 목록 (16종)', level=3)
add_table(doc,
    headers=['분류', '화면', '주요 기능'],
    rows=[
        ('인증', '로그인 / 회원가입', '8필드 사장 가입 (상호/사업자번호/이메일/비밀번호/담당자×3) + 로그인'),
        ('대시보드', '대시보드 / 알림센터', 'KPI 카드, 차트, 알림 목록'),
        ('매장', '매장 목록 / 상세 / WiFi 설정', '다매장 CRUD, 이미지·영업시간·다국어, WiFi SSID/암호'),
        ('스탬프', '스탬프 카드 / 발급 폼', '카드 디자인, 적립 내역, 보상 조건'),
        ('쿠폰', '쿠폰 목록 / 발급 폼', '할인율, 만료일, 사용 조건'),
        ('직원', '직원 관리', '이메일 초대, 권한 부여, 비활성화'),
        ('고객', '고객 프로필', '방문 이력, 스탬프/쿠폰 보유 현황'),
        ('채팅', '고객 1:1 채팅', 'SSE 실시간 메시지'),
        ('결제', '결제·구독 관리', '구독 플랜, 결제 내역, 정산'),
        ('설정', '계정/알림/테마 설정', ''),
    ],
    col_widths=[2.5, 4, 9.5],
)

add_heading(doc, '4.2.3 기술 권장 스택', level=3)
add_bullet(doc, 'React 19, Vite 8, React Router 7')
add_bullet(doc, 'i18next (한·영·일·중)')
add_bullet(doc, 'Recharts (차트), react-leaflet (지도)')
add_bullet(doc, '상태관리: Zustand 또는 Redux Toolkit')
add_bullet(doc, 'API 통신: fetch/axios + 토큰 갱신 인터셉터')

add_heading(doc, '4.2.4 작업 항목', level=3)
add_checklist(doc, [
    '디자인 가이드 기반 16개 화면 UI 구현',
    'PC / 태블릿 / 모바일 반응형',
    'JWT 저장 + 라우터 가드 + 토큰 갱신',
    '백엔드 API 통합 (모든 화면)',
    '이미지 업로드 (multipart/form-data)',
    'SSE 채팅 실시간 수신',
    '다국어 i18n',
    '에러/로딩/빈 상태 UI 일관성',
    '404/401/403/500 페이지',
    '접근성 기본 준수 (라벨, 포커스, 키보드)',
    '빌드 산출물 + 환경변수(API_BASE) 분리',
])

# WP3 모바일 앱
add_page_break(doc)
add_heading(doc, '📦 WP3 — 사용자 모바일 앱 (Flutter)', level=2)

add_heading(doc, '4.3.1 범위', level=3)
add_para(doc,
    'iOS와 Android에서 동작하는 사용자 앱을 신규 개발한다. Flutter 단일 코드베이스 권장. '
    'BLE 비콘 자동 인식, 자동 WiFi 연결, 푸시, 소셜 로그인을 포함한다.'
)

add_heading(doc, '4.3.2 화면 목록 (12종)', level=3)
add_table(doc,
    headers=['분류', '화면', '주요 기능'],
    rows=[
        ('스플래시', 'Splash', '앱 시작 + 토큰 검증'),
        ('인증', '로그인 / 회원가입 / 비밀번호 찾기',
            '이메일 + 소셜(Google/Apple/카카오/네이버)'),
        ('홈', '메인 탭 / 홈', '주변 매장 추천, 최근 방문'),
        ('주변', '주변 매장 (지도 + 리스트)', '지도, 비콘 감지, 매장 카드'),
        ('매장', '매장 상세', '스탬프 카드, 쿠폰, 채팅 진입'),
        ('WiFi', 'WiFi 자동 연결', 'BLE 핸드셰이크 → 한 번 동의 후 자동 재연결'),
        ('마이페이지', '내 정보 / 스탬프 / 쿠폰', '보유 스탬프, 발급된 쿠폰'),
        ('채팅', '채팅 목록 / 상세', 'SSE 또는 폴링 기반'),
        ('알림', '알림 목록', '푸시 수신 이력'),
        ('설정', '알림/언어/약관/로그아웃', ''),
    ],
    col_widths=[3, 5, 8],
)

add_heading(doc, '4.3.3 기술 권장 스택', level=3)
add_bullet(doc, 'Flutter 3.x, Dart 3.x')
add_bullet(doc, 'flutter_blue_plus (BLE), flutter_secure_storage (토큰), dio (HTTP)')
add_bullet(doc, '상태관리: Riverpod 또는 Provider')
add_bullet(doc, 'firebase_core, firebase_auth, firebase_messaging')

add_heading(doc, '4.3.4 작업 항목', level=3)
add_checklist(doc, [
    '디자인 가이드 기반 12종 화면 UI 구현',
    'Firebase Auth로 Google/Apple 로그인',
    '카카오/네이버 SDK 통합 → 백엔드 Custom Token 변환',
    'flutter_blue_plus로 비콘 스캔 + 핸드셰이크 (FSC-BP108B)',
    'iOS: CoreLocation 영역 모니터링으로 백그라운드 비콘 감지 보강',
    'BLE 핸드셰이크 응답 → WiFi 자동 연결 (NEHotspotConfiguration / WifiNetworkSuggestion)',
    'FCM 등록 + 수신 + 딥링크 처리',
    'SSE 또는 폴링 기반 채팅 메시지 실시간 수신',
    '토큰 갱신 인터셉터 + 401 자동 재인증',
    '오프라인 캐시 (스탬프/쿠폰 마지막 조회)',
    'iOS Info.plist, Android Manifest 권한 (BLE/위치/알림/카메라)',
    'TestFlight + Internal Test 빌드 산출물',
    '스토어 메타데이터 (아이콘/스플래시/스크린샷)',
])

# WP4 Super Admin
add_page_break(doc)
add_heading(doc, '📦 WP4 — Super Admin 웹 콘솔', level=2)

add_heading(doc, '4.4.1 범위', level=3)
add_para(doc,
    'PathWave 운영자가 사용하는 관리자 콘솔. PC 우선, 태블릿까지 지원. '
    'WP2와 동일 스택(React+Vite) 권장하여 컴포넌트 재사용.'
)

add_heading(doc, '4.4.2 화면 목록 (최소 6종)', level=3)
add_table(doc,
    headers=['화면', '주요 기능'],
    rows=[
        ('운영자 로그인', 'sub_type=super_admin JWT 검증, 2FA 권장'),
        ('대시보드', '전체 통계 (회원/매장/매출/비콘 현황) + 차트'),
        ('비콘 관리', 'CSV 일괄 입고, inventory→active/lost, 매장 할당'),
        ('사장 가입 승인', 'pending 목록, 사업자등록증 이미지 뷰어, verify/suspend/reactivate'),
        ('결제·정산 관리', '전체 결제 내역, 환불, 구독 플랜'),
        ('시스템 공지', '전체 사용자/사장 대상 공지 + 푸시 일괄 발송'),
    ],
    col_widths=[4, 12],
)

add_heading(doc, '4.4.3 작업 항목', level=3)
add_checklist(doc, [
    '운영자 가드 (잘못된 sub_type 401)',
    '비콘 CSV 업로드 (드래그 앤 드롭)',
    '사업자등록증 이미지 뷰어 + 확대',
    '결제 환불 확인 모달 + 사유 입력',
    '시스템 공지 작성 + 미리보기 + 발송 예약',
    '감사 로그 보기 (운영자 행위 추적)',
])

# WP5 인프라
add_page_break(doc)
add_heading(doc, '📦 WP5 — 인프라 / 배포 / 모니터링', level=2)

add_heading(doc, '4.5.1 범위', level=3)
add_para(doc,
    '백엔드 + 정적 웹 + 모바일 앱 빌드 산출물의 운영 환경 구성을 포함한다. '
    '클라우드 사업자는 발주처와 협의(AWS/GCP/NCP).'
)

add_heading(doc, '4.5.2 작업 항목', level=3)
add_checklist(doc, [
    '운영/스테이징 환경 분리 (URL, DB, 시크릿)',
    'CI/CD 파이프라인 (GitHub Actions 등)',
    '백엔드 컨테이너화 (Docker) + 자동 배포',
    '웹 정적 호스팅 (S3+CloudFront 또는 동등)',
    '모바일 앱 스토어 등록 가이드 (실제 등록은 발주처)',
    '도메인 + HTTPS 인증서 (Let\'s Encrypt 또는 ACM)',
    '백엔드 로그 수집 (CloudWatch / Stackdriver 등)',
    'APM 또는 Sentry 도입',
    '주간 자동 백업 (DB / S3)',
    '런북 (장애 대응 매뉴얼) 작성',
])


# ═══════════════════════════════════════════════════════════════════════════════
# 5. 기능 요구사항 (페르소나별)
# ═══════════════════════════════════════════════════════════════════════════════
add_page_break(doc)
add_heading(doc, '5. 기능 요구사항 (페르소나별)', level=1)

add_heading(doc, '5.1 일반 사용자 (User)', level=2)
for item in [
    '회원가입 / 로그인 (이메일·비밀번호)',
    '소셜 로그인 (Google, Apple, 카카오, 네이버) — 카카오/네이버는 Custom Token 변환',
    '주변 매장 검색 (지도 + 리스트)',
    'BLE 비콘 감지 → 매장 진입 자동 인식',
    'WiFi 자동 연결 (한 번 동의 후 재연결)',
    '스탬프 자동 적립',
    '쿠폰 자동 발급 (스탬프 N개 누적 시)',
    '쿠폰 사용 (직원 스캔 또는 코드 입력)',
    '매장과 1:1 채팅',
    '푸시 알림 수신',
    '계정 설정 / 알림 설정 / 회원 탈퇴',
]:
    add_bullet(doc, item)

add_heading(doc, '5.2 시설 사장님/직원 (Facility)', level=2)
for item in [
    '8필드 사장 가입 + 운영자 승인 대기',
    '로그인 후 시설 등록 + 비콘 SN 클레임',
    '매장 정보 관리 (이름/주소/영업시간/이미지/다국어)',
    'WiFi SSID/암호 설정 (서버측 AES 암호화)',
    '스탬프 카드 디자인 / 발급 / 적립 내역',
    '쿠폰 발급 / 사용 처리',
    '직원 초대 + 권한 부여',
    '고객 채팅 응대 (SSE)',
    '매출/스탬프/쿠폰 리포트',
    '결제·구독 관리',
    '직원·사장 권한 분리',
]:
    add_bullet(doc, item)

add_heading(doc, '5.3 PathWave 운영자 (Super Admin)', level=2)
for item in [
    '운영자 로그인',
    '비콘 CSV 일괄 입고 → 인벤토리 관리',
    '사장 가입 승인 (사업자등록증 검토)',
    '계정 정지 / 재활성화',
    '전체 결제 내역 / 환불 / 구독 플랜',
    '시스템 공지 (전체/매장/사용자)',
    '감사 로그 / 통계',
]:
    add_bullet(doc, item)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. 비기능 요구사항
# ═══════════════════════════════════════════════════════════════════════════════
add_heading(doc, '6. 비기능 요구사항', level=1)

add_table(doc,
    headers=['구분', '요구사항'],
    rows=[
        ('성능 (웹)', '첫 페인트 2초 이내 (4G), 라이트하우스 Performance 80점 이상'),
        ('성능 (앱)', '콜드 스타트 3초 이내, 핫 스타트 1초 이내'),
        ('성능 (API)', '핵심 엔드포인트 P95 응답 500ms 이내'),
        ('보안', 'OWASP Top 10 준수, JWT 안전 저장, HTTPS 강제, 레이트 리밋'),
        ('호환성', '웹: Chrome/Safari 최신 2버전 / iOS 15+ / Android 9+'),
        ('접근성', 'WCAG 2.1 AA 기본 준수 (색 대비, 키보드, 라벨)'),
        ('국제화', '한국어 기본, 영·일·중 자동 번역 (캐싱)'),
        ('가용성', '99.5% 이상 (계획 다운타임 제외)'),
        ('확장성', '동시 접속 1만, DB 50GB까지 무중단 운영'),
    ],
    col_widths=[3, 13],
)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. 발주처 제공 자료
# ═══════════════════════════════════════════════════════════════════════════════
add_page_break(doc)
add_heading(doc, '7. 발주처 제공 자료', level=1)

add_heading(doc, '7.1 필수 제공 자료', level=2)
for item in [
    'SRS (Software Requirements Specification) 문서',
    'API 명세 초안 또는 도메인 흐름도',
    'DB 스키마 정의서 (테이블 23종)',
    'UI 디자인 산출물 (Figma 또는 PNG export)',
    'BLE 비콘 FSC-BP108B 펌웨어 사양서 + 핸드셰이크 프로토콜',
    'BLE 비콘 실물 1~3개 대여',
    'Firebase 프로젝트(Auth/FCM/Storage) 접근 권한',
    '브랜드 가이드 (로고, 컬러, 폰트)',
    '약관/개인정보처리방침 텍스트',
]:
    add_bullet(doc, item)

add_heading(doc, '7.2 선택 제공 자료 (참조 구현)', level=2)
add_para(doc,
    '발주처는 본 과업과 별개로 자체 개발한 참조 구현(reference implementation)을 보유하고 있다. '
    '외주사는 이를 GitHub repository로 열람할 수 있으며, 코드 재사용·아이디어 참고·기능 검증용으로 활용 가능하다. '
    '단, 본 과업의 산출물은 외주사 자체 책임 하에 신규 개발된 것으로 간주한다.'
)
add_red_box(doc,
    '참조 구현은 검증되지 않은 프로토타입이며, 본 외주의 품질·성능 기준을 보장하지 않는다. '
    '외주사가 참조 구현의 결함을 그대로 산출물에 가져오는 것은 외주사 책임이다.'
)


# ═══════════════════════════════════════════════════════════════════════════════
# 8. 일정
# ═══════════════════════════════════════════════════════════════════════════════
add_heading(doc, '8. 일정 및 마일스톤', level=1)

add_table(doc,
    headers=['단계', '내용', '기간(권장)'],
    rows=[
        ('M0 — 킥오프', '발주처-외주사 계약, 자료 인수, 아키텍처 합의', '2주'),
        ('M1 — 백엔드 코어', 'WP1 인증/시설/비콘/스탬프/쿠폰', '6~8주'),
        ('M2 — 백엔드 확장', 'WP1 알림/푸시/채팅/결제/리포트/운영자', '4~5주'),
        ('M3 — 시설관리자 웹', 'WP2 16화면 + API 연동', '6~8주'),
        ('M4 — 사용자 모바일 앱', 'WP3 12화면 + BLE/푸시/소셜', '8~10주'),
        ('M5 — Super Admin', 'WP4 6화면', '3~4주'),
        ('M6 — 인프라', 'WP5 운영/스테이징 + CI/CD + 모니터링', '2~3주'),
        ('M7 — 통합 검수 / 베타', '전체 시나리오 검증, 결함 수정', '3~4주'),
        ('총 예상 (병렬 진행 시)', '—', '약 4~6개월'),
    ],
    col_widths=[5, 8, 3],
)

add_red_box(doc,
    '발주처 법인 등록(2026-05) 이전엔 PG 실 결제·APNs 인증서·카카오 비즈 SDK 등 외부 자원 미발급. '
    '베타까지는 sandbox/stub 모드로 진행되며, 정식 런칭 직전 1~2주에 실 키 교체 일정 확보 필요.'
)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. 산출물 / 검수
# ═══════════════════════════════════════════════════════════════════════════════
add_heading(doc, '9. 산출물 및 검수 기준', level=1)

add_heading(doc, '9.1 최종 산출물', level=2)
for item in [
    '백엔드 소스 코드 + Dockerfile + docker-compose.yml',
    '시설관리자 웹 / Super Admin 웹 빌드 산출물 (정적 호스팅 가능)',
    'iOS .ipa (TestFlight 등록) + Android .aab',
    'OpenAPI 명세서 (Swagger UI 호스팅 포함)',
    'DB 스키마 마이그레이션 스크립트 (Alembic 등)',
    '운영자 매뉴얼 (PDF 또는 Markdown)',
    '설치/배포 가이드',
    '런북 (장애 대응)',
    '테스트 리포트 + 커버리지 리포트',
    'CHANGELOG',
]:
    add_bullet(doc, item)

add_heading(doc, '9.2 검수 기준', level=2)
add_table(doc,
    headers=['구분', '기준'],
    rows=[
        ('기능', '본 과업지시서의 모든 체크리스트 항목 충족'),
        ('품질', '주요 시나리오 무결점 (회원가입/BLE 핸드셰이크/스탬프/쿠폰/결제/푸시)'),
        ('성능', '6장 비기능 요구사항 충족'),
        ('보안', 'OWASP Top 10 점검 통과, 정적 분석 도구 통과'),
        ('호환성', '6장 명시 버전'),
        ('인수 후', '주요 결함 30일 이내 1회 무상 보수'),
    ],
    col_widths=[3, 13],
)


# ═══════════════════════════════════════════════════════════════════════════════
# 10. 견적 양식
# ═══════════════════════════════════════════════════════════════════════════════
add_page_break(doc)
add_heading(doc, '10. 견적 양식', level=1)

add_table(doc,
    headers=['항목', '인력 (M/M)', '기간', '견적 (VAT 별도)'],
    rows=[
        ('WP1 — 백엔드 시스템', '　', '　주', '　원'),
        ('WP2 — 시설관리자 웹', '　', '　주', '　원'),
        ('WP3 — 사용자 모바일 앱', '　', '　주', '　원'),
        ('WP4 — Super Admin 웹', '　', '　주', '　원'),
        ('WP5 — 인프라/배포/모니터링', '　', '　주', '　원'),
        ('통합 검수 / 베타 지원', '　', '　주', '　원'),
        ('합계', '—', '—', '　원'),
    ],
    col_widths=[6, 3, 3, 4],
)

add_heading(doc, '10.1 지급 조건 (협의)', level=2)
add_bullet(doc, '계약금: 25% (계약 체결 시)')
add_bullet(doc, '1차 중도금: 25% (M1+M2 백엔드 코어 완료 시)')
add_bullet(doc, '2차 중도금: 25% (M3+M4 클라이언트 핵심 완료 시)')
add_bullet(doc, '잔금: 25% (M7 최종 검수 완료 시)')

add_red_box(doc,
    '카카오/네이버 소셜 로그인, BLE 자동 WiFi 연결, PG 연동 등 3장에서 명시한 외부 의존·제약 항목은 '
    '견적 산정 시 별도 라인 또는 가산 사유로 명시 권장.'
)


# ═══════════════════════════════════════════════════════════════════════════════
# 11. 일반 조건
# ═══════════════════════════════════════════════════════════════════════════════
add_heading(doc, '11. 일반 조건', level=1)
for item in [
    '지적재산권: 산출물(소스 코드 포함)의 모든 권리는 발주처에 귀속한다.',
    '기밀 유지: 외주사는 본 프로젝트 진행 중 알게 된 모든 정보를 제3자에 유출하지 않는다 (NDA 별도 체결).',
    '오픈소스 라이선스: 외주사는 사용한 OSS 목록과 라이선스를 산출물에 포함한다. GPL 등 강한 카피레프트 라이선스는 사용 금지.',
    '하자 보수: 인수 후 30일 내 발견된 주요 결함은 무상 보수한다.',
    '변경 관리: 과업 범위 변경은 서면 합의 후 적용하며, 영향도에 따라 비용/기간을 재산정한다.',
    '커뮤니케이션: 주요 의사결정은 이메일 또는 GitHub Issue로 기록을 남긴다.',
    '버전 관리: GitHub 발주처 리포지토리 사용. 모든 변경은 PR을 통해 제출.',
    '리스크 공유: 3장의 위험 항목 중 발주처 책임 영역(외부 키 발급 등)의 지연은 외주사 일정에 비례 반영한다.',
]:
    add_numbered(doc, item)


# ── 서명란 ──────────────────────────────────────────────────────────────────
for _ in range(3):
    doc.add_paragraph()

sig_table = doc.add_table(rows=1, cols=2)
sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER

left = sig_table.rows[0].cells[0]
left.text = ''
p = left.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('발주처\n')
set_korean_font(run, size=12, bold=True, color=DARK_PURPLE)
run = p.add_run('PathWave (개인사업자/법인)\n\n\n')
set_korean_font(run, size=10)
run = p.add_run('대표: ___________________ (인)\n\n')
set_korean_font(run, size=10)
run = p.add_run('날짜: 2026년 ___월 ___일')
set_korean_font(run, size=10)

right = sig_table.rows[0].cells[1]
right.text = ''
p = right.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('외주사\n')
set_korean_font(run, size=12, bold=True, color=DARK_PURPLE)
run = p.add_run('회사명: ___________________________\n\n\n')
set_korean_font(run, size=10)
run = p.add_run('대표: ___________________ (인)\n\n')
set_korean_font(run, size=10)
run = p.add_run('날짜: 2026년 ___월 ___일')
set_korean_font(run, size=10)


# ── 푸터 ────────────────────────────────────────────────────────────────────
for _ in range(2):
    doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('— PathWave Statement of Work v2.0 (Full New Build) — 본 문서는 외주 산출물 평가 및 계약의 근거 자료로 사용됩니다 —')
set_korean_font(run, size=9, color=GREY)


# ── 저장 ────────────────────────────────────────────────────────────────────
out_path = Path('/Users/m5pro16/Desktop/pathwave/docs/vendor/PathWave_과업지시서_2026-05-03.docx')
doc.save(out_path)
print(f'✅ 저장 완료: {out_path}')
print(f'   크기: {out_path.stat().st_size:,} bytes')
