# PathWave Phase 0 전수 감사 — 갭 리스트

- 문서 버전: 2026-05-21
- 감사 범위: mobile(24화면) · provider-web(22페이지) · admin-web(17페이지) + 백엔드 연계
- 점검 기준: 디자인 시스템 / Apple HIG·Material 3 / 심의 가이드 / 누락 기능 / 마스터플랜 W1~W8

---

## 1. 요약 — 6대 공통 테마

"소소한 누락"이 아니라 **구조적 공통 문제 6가지**가 드러났다:

1. **mock 데이터 / 실 API 미연동** — 특히 provider-web은 거의 전 페이지가 mock UI.
   서비스 레이어(ChatService·StampService 등)는 완비됐는데 화면이 호출하지 않음.
2. **인증 우회** — provider-web `DEV_AUTO_LOGIN=true` + Login 자동 우회 + Signup 게스트
   fake 토큰, admin-web DevPreviewBar. 출시 빌드 노출 시 보안·심의 차단.
3. **i18n 광범위 미적용** — 3콘솔 모두. mobile 13화면 하드코딩 + ARB 0개 + 폰트 미번들.
4. **디자인 시스템 불일치** — 공용 컴포넌트 vs 자체 CSS 혼재, 네이티브 alert/confirm 다수,
   구 팔레트(보라/파랑) 잔존, mobile 테마 이중화.
5. **핵심 화면 부재** — 슈퍼어드민 WiFi 등록(W1), 앱 버전관리(W5), placeholder/dead 페이지 다수.
6. **심의 직격 리스크** — 정책 placeholder 노출, localhost URL 노출, OCR 허위 표기,
   PG 카드정보 평문 저장, 구 회사정보.

**콘솔별 한 줄 평:**
- **mobile** — 실 연동은 상대적으로 많이 됨. 단 i18n·테마·폰트 인프라 3종 미비 + 화면 갭 다수.
- **provider-web** — 시각 디자인은 됐으나 **기능 대부분이 mock 프로토타입.** 실 API 연동 +
  인증 복구가 가장 큰 작업.
- **admin-web** — 핵심 기능은 동작. 단 placeholder 페이지 3개 + 디자인 토큰 색상 오류.

---

## 2. 🔴 출시 차단 — Critical (심의 신청 전 반드시 해결)

| # | 갭 | 콘솔 | 상태 |
|---|---|---|---|
| C1 | 인증 우회 — `DEV_AUTO_LOGIN=true`, Login.jsx 자동 mock 토큰, 로그인 폼 미렌더 | provider-web | ⬜ |
| C2 | 게스트 우회 — Signup `enterAsGuest()` fake 토큰 | provider-web | ⬜ |
| C3 | DevPreviewBar 인증 우회 (preview 모드) — 출시 빌드 환경변수 차단 검증 | admin-web | ⬜ |
| C4 | 거의 전 페이지 mock 데이터 — 실 API 미연동 (Dashboard·StoreInfo·WifiSettings·CustomerChat·Coupons·Payment·Stamps·Notifications·StaffManagement) | provider-web | ⬜ |
| C5 | OCR "자동 인식" 허위 — 랜덤값 생성하면서 "사진에서 자동 입력" 안내 (WifiSettings·ServiceRequest) | provider-web | ⬜ |
| C6 | PG 결제 시뮬레이션 + 카드번호·CVC localStorage 평문 저장 | provider-web | ⬜ |
| C7 | 구 회사정보 하드코딩 — "시원컴퍼니/메헌로/02-1234-5678" (법인은 트리거소프트), 자체 푸터 ≠ PwFooter | provider-web | ⬜ |
| C8 | consent 화면 — "정책 본문이 아직 등록되지 않았습니다 (placeholder)" 사용자 노출 + 동의 로드 실패 시 가입 dead-end | mobile | ⬜ |
| C9 | settings 화면 — `localhost:8080` API URL + dart-define 개발 안내 노출, 앱 버전 하드코드 | mobile | ⬜ |
| C10 | 슈퍼어드민 **WiFi 등록·관리 화면 전무** (마스터플랜 W1 핵심) | admin-web | ⬜ |
| C11 | **앱 버전관리 화면 전무** — OS별 강제 업데이트 설정 불가 (W5) | admin-web | ⬜ |
| C12 | placeholder/dead 페이지 — ChatMonitor·StaffMonitor·CouponStats(admin), /dashboard/report·MemberProfile·Facilities(provider) | admin·provider | ⬜ |
| C13 | wifi_connect — WiFi password 항상 빈값 전송, 보안 WiFi 매장 연결 실패 (핵심 가치 손상) | mobile | ⬜ |
| C14 | 약관 3종 누락 — 환불정책·청소년보호정책·쿠키정책 (심사 필수 문서) | admin-web | ⬜ |

---

## 3. 🟠 High — 구조·광범위 (Phase 1에서 인프라 먼저)

- **mobile 테마 이중화** — `AppTheme` vs `NeuTheme` 색상 토큰 분열 → 화면 간 톤 불일치. 단일화 필요.
- **mobile Noto Sans 폰트 미번들** — pubspec `fonts:` 섹션 없음 → CJK/태국어 글리프 깨짐 위험.
- **i18n 인프라 미완** — ARB 0개, 13개 화면 `t()` 미사용, supportedLocales 3중 불일치(7/23/10).
- **디자인 시스템 강제** — 공용 컴포넌트 미사용 페이지 다수, 네이티브 `alert/confirm` 약 18곳,
  provider-web 구 보라(#8B5CF6) 잔존 정리. (2026-05-21 정정: admin `--accent` #2563EB 파랑은
  정책상 정상 — 색 정책 = mobile 보라 / provider 녹색 / admin 블루.)
- **provider ConfirmModal prop 불일치** — StaffManagement·MemberProfile이 `desc/isOpen` 대신
  `message` 전달 → 모달이 아예 안 뜸 (직원 비활성화/삭제 작동 불능).
- **mobile home 화면 빈약** — 홈 탭 BLE 카드 1개뿐, 알림 탭은 버튼 1개. 진입점 부재.
- **mobile 알림 라우팅 미구현** — 알림 탭해도 해당 화면 미이동 (`// TODO: kind 별 라우팅`).
- **mobile coupons 쿠폰 사용 silent** — 에러 삼킴, 성공/실패 피드백·목록갱신 없음.
- **provider 결제/서비스신청 흐름 중복** — ServiceRequest vs PaymentManagement.ServiceApplyFlow 2곳.
- **provider /forgot-password 라우트 부재** — 비밀번호 찾기 흐름 전무.
- **mobile policy_view `?lang=ko` 하드코드** — 외국인도 약관이 한국어 (법적 동의 유효성 문제).

---

## 4. 콘솔별 상세

### 4.1 mobile (24화면)
- 횡단: 테마 이중화 / i18n 미적용 13화면 / 폰트 미번들 / supportedLocales 불일치.
- consent: placeholder 노출 + 에러 dead-end. settings: localhost URL·버전 하드코드·하드코드 FAQ.
- home: 빈약. wifi_connect: password 빈값. coupons: silent 사용. notifications: 라우팅 TODO.
- splash: 라우팅 실패 시 dead-end. chat_detail: SSE 끊김 무복구, 채팅 번역 미연결.
- 입력 검증 부실(register·forgot·login), 비밀번호 표시 토글 부재, 자작 체크박스/라디오 반복.
- Pw* 세트 누락(라디오·체크박스·드롭다운·칩) → 화면마다 raw 재구현.

### 4.2 provider-web (22페이지)
- C1·C2 인증 우회. C4 전 페이지 mock. C5 OCR 허위. C6 PG 평문. C7 구 회사정보.
- Login 폼 미렌더. Dashboard·StoreInfo·WifiSettings·CustomerChat·Coupons·Payment·Stamps·
  Notifications·StaffManagement·Subscriptions 전부 mock.
- CustomerChat: DUMMY_CHATS, ChatService 미호출, 차단 로컬 상태만.
- ConfirmModal prop 불일치(StaffManagement·MemberProfile). /dashboard/report 빈 화면.
- dead page: MemberProfile·Facilities(라우트 미연결), Subscriptions(메뉴 없음).
- 네이티브 alert/confirm 18곳, 구 보라/파랑 잔존, console.log 7건, App.css 보일러플레이트 잔존.

### 4.3 admin-web (17페이지)
- C3 DevPreviewBar. C10 WiFi 화면 없음. C11 앱 버전관리 없음. C14 약관 3종 누락.
- ChatMonitor·StaffMonitor·CouponStats — 백엔드 미연동 placeholder.
- Dashboard 가짜 데이터(랜덤 스파크라인·하드코드 수치·미작동 기간 필터).
- `--accent` #2563EB 파랑 = 정책 정상(슈퍼어드민=블루, 2026-05-21 정정). 네이티브 confirm/alert 5페이지. i18n 미적용 8/17.
- 페이지네이션 전반 부재. 사이드바 검색창 미작동.
- ✅ 양호: AbuseReports, Battery, CompanyInfo, Faq, Policies(3종 누락 제외), Payments(시뮬 한정).

---

## 5. 다음 단계

1. 본 갭 리스트를 **Phase 1 작업 단위(PR 단위)** 로 묶는다.
2. 인프라 우선 — mobile 테마/폰트/i18n, 디자인 시스템 강제는 개별 화면 수정 전에.
3. Critical(C1~C14) 먼저, 그다음 High, Medium.
4. 작업량 재산정 → 마스터플랜 §6 워크스트림 + 심의 일정 갱신.

> 원본 상세: 콘솔별 전수 감사 3건의 전체 보고는 본 문서로 집약함. Low 등급 항목 다수는
> 디자인 토큰화·상대시간 포맷·페이지네이션 등으로, Phase 1 화면 작업 시 일괄 처리.
