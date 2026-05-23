# PathWave Phase 1 실행 계획 — PR 묶음 · 순서 · 일정

- 문서 버전: 2026-05-21
- 성격: **Phase 1 단일 실행 추적 문서** — PR 진행에 따라 상태(§6) 갱신
- 상위 문서: `docs/pathwave_launch_master_plan_2026-05-20.md` (마스터 플랜)
- 입력 문서: `docs/pathwave_phase0_gap_list_2026-05-21.md` (전수 감사 갭 리스트)
- 회사: 주식회사 트리거소프트

---

## 1. 목적

Phase 0 전수 감사가 산출한 **출시 차단 Critical 14건(C1~C14) + High** 을
**PR 단위 작업 22개**로 묶고, 실행 순서·작업량·일정을 확정한다.

작업 원칙(마스터플랜 §4 품질 기준 강제):
- 한 도메인 = 3콘솔(mobile·provider-web·admin-web) + 백엔드 연계 1 PR. piecemeal 금지.
- 디자인 시스템 강제 / Apple HIG·Material 3 / 심의 가이드 디테일 / 유사서비스 벤치마크 선행.
- "완료" 전 시나리오 테스트 — 사용자 관점 + 심의 심사관 관점 → 결과 보고.

---

## 2. Phase 0 갭 리스트 코드 검증 — 정정 5건

갭 리스트를 실제 코드로 재확인한 결과 5건이 사실과 달랐다 (3건은 작업량 축소).

| # | 갭 리스트 원문 | 코드 확인 결과 | 영향 |
|---|---|---|---|
| C9 | mobile settings `localhost:8080` 하드코딩 | `ApiConfig.baseUrl`(dart-define 교체 가능) — 하드코딩 아님. 진짜 문제 = settings가 API URL·개발안내문을 사용자에게 노출 + 앱 버전 `'1.0.0+1'` 하드코드 | C9 유효, 설명 정밀화 |
| C11 | admin 앱 버전관리 화면 전무 | 백엔드 `routes/version.py` 완성(`GET/PUT /api/admin/app-versions`, `app_versions` 테이블). 누락은 admin-web UI 뿐 | 🟢 축소 |
| W8 | i18n 실연동 필요 | 백엔드 i18n API(`translations` 테이블, DeepL/Google, admin CRUD) + admin-web i18n 모두 완성. 남은 건 mobile i18n + 번역 콘텐츠 + 채팅 번역 연결 | 🟢 축소 |
| C10 | admin WiFi 등록 화면 없음 | 사실. 백엔드 `/api/beacon/wifi`(점주용)는 존재. 슈퍼어드민 감독용 라우트 신규 필요 | 범위 명확화 |
| High | provider `/forgot-password` 라우트 부재 | ✅ P4 해결 — 갭리스트 오기(파일 없었음). BE 시설 재설정 API 2개 + `ForgotPassword` 페이지·라우트 정식 구현 | — |

---

## 3. WiFi 로밍 v1 스코프 결정 — B(풀 스코프) 채택

2026-05-21 사용자 확정. 선택지 A(구조 완비+단일매장) / B(풀 스코프) / C(최소) 중 **B**.

**결정 근거:**
- Apple Developer 계정·인증서는 A·B 무관하게 앱스토어 출시에 어차피 필요 → B의 추가 외부 블로커 아님.
- 로밍 설계 문서 §9 A.12 = ".mobileconfig 생성 로직은 지금, 서명만 인증서 후" → B 코드를 지금 다 짓고 마지막 서명만 인증서 후 적용 = 설계와 일치.
- **feature flag 전략**: 고급 기능(units/grant 관리 화면, `managed` 모드)은 코드는 구현하되
  provider-web UI에 노출하지 않음 → 심의 심사관에게 안 보임 = 심의 리스크 0.
  정부과제용 내부 구현 완료 상태 확보, 2차에서 flag만 켜면 공개.

**비용:** 개발 +1~2주 (feature flag도 코드 작성 시간은 동일). 사용자가 외부 행정 압축으로 상쇄.

**테스트 환경 (확정):** 호텔 다중 WiFi 로밍 실기기 테스트는 **원광대학교 건물(다중 AP 보유)**을
테스트장으로 사용 — 각 AP를 PathWave에 units(호실)로 등록 + 비콘 9개 배치 → 호실별 다른
SSID + 이동 시 무중단 시나리오를 실기기로 walk-through 검증.
→ v1 = 단일 매장 + 호텔 시나리오 **모두 실기기 검증**.
단 테스트 AP는 SSID·비밀번호를 아는 `static` 방식이어야 함 (eduroam 등 WPA2-Enterprise는
`radius` 모드 = 2차라 v1 테스트 불가).

---

## 4. PR 묶음 — 22개

순서: 🔧 인프라 → 🔴 Critical 도메인 → 📡 WiFi 로밍 → 🎟️ 쿠폰·스탬프 회원 QR → 📋 심의 마무리.

### 🔧 인프라 (개별 화면 수정 전 기반)

| PR | 도메인 | 콘솔 | 내용 | 갭 |
|---|---|---|---|---|
| P1 | mobile 디자인 기반 | mobile | 테마 단일화(`AppTheme`+`NeuTheme`→1) + Noto Sans 폰트 번들(CJK/태국어) + `neu/` 위젯 통합 + `Pw*` 4종 추가(Radio·Checkbox·Dropdown·Chip) | High×4 |
| P2 | mobile i18n | mobile·BE | DB 기반 `I18nService` 정합(ARB 아님) + supportedLocales 12개 단일화 + 전 화면·공용위젯 하드코딩 한글 `t(키, defaultValue:)` 일괄 전환 + `translations` ko 시드 347개(코드 추출, 203→550) + DeepL 일괄번역 스크립트 준비 | High |
| P3 | 웹 디자인 시스템 강제 | provider·admin | 네이티브 `alert/confirm` 33곳(provider 16+admin 17)→`useDialog()` 비동기 공용 모달(콘솔별 기존 ConfirmModal/Modal 재사용, danger 변형 추가) / 색 토큰 정합(provider-web 구 보라 #8B5CF6 잔존 2곳→녹색 토큰) | High×3 |

### 🔴 Critical 도메인 (C1~C14)

| PR | 도메인 | 콘솔 | 내용 | 갭 |
|---|---|---|---|---|
| P4 | 인증 우회 제거 | provider·admin·BE | provider `DEV_AUTO_LOGIN`·`Login` 자동토큰·`Signup` 게스트를 `import.meta.env.DEV` 게이트(출시 빌드 차단) + 실 로그인폼 복구 / admin 은 이미 정합(DevPreviewBar=`VITE_PREVIEW_MODE`) / `/forgot-password` 정식 구현 — BE `POST /api/facility/forgot-password`·`reset-password` 신규 + provider `ForgotPassword` 페이지·라우트 | C1·C2·C3 |
| P5 | 매장·회사정보 실연동 | provider | StoreInfo 하드코딩('패스트파이브'·'02-1234-5678') 제거 + `StoreService` 실연동(list/update/비콘 fid) + Settings 푸터 → `PwFooter`(트리거소프트 법인정보) + dead code Facilities 삭제. ※쿠폰·알림·직원 등의 '호텔H' mock 은 각 도메인 PR(P7/P9/P10/P11) 소관 | C7·C4 |
| P6 | OCR 허위 제거 | provider | `WifiSettings`·`ServiceRequest` `runOcrMock` 제거 → 정직한 수동입력 UI | C5 |
| P7 | 결제·구독 실연동 | provider·admin | 카드 평문저장 제거(서버 토큰화) + PG 시뮬 정리 + `Subscriptions` 실연동 + 결제/서비스신청 중복흐름 통합 + admin Payments 정합 | C6·C4 |
| P8 | 채팅 도메인 | mobile·provider·admin·BE | ✅ provider `CustomerChat` 실연동(`ChatService`) + admin `ChatMonitor` 실연동(BE `GET /api/chat/reports` 신규) + mobile SSE 끊김 복구(지수 backoff 재연결). ⏸ **채팅 번역 연결 = P8b 분리** — `chat_messages` 번역 캐시 스키마 + 뷰어별 언어 설계 + Google/DeepL 키(출시 2단계) 필요 | C4·C12·W8 |
| P9 | 쿠폰·스탬프 실연동 | mobile·provider | provider `Coupons`·`Stamps` mock→실연동 + mobile 쿠폰 사용 silent error 수정(피드백·목록갱신). 캐셔 게이트는 P22 | C4·High |
| P10 | 알림 도메인 | mobile·provider·admin | provider `Notifications` 실연동 + mobile 알림 라우팅 구현 + 알림 탭 보강 | C4·High |
| P11 | 대시보드·직원 | provider·admin·BE | provider `Dashboard`·`StaffManagement` 실연동 + admin Dashboard 가짜데이터 제거 + `StaffMonitor`·`CouponStats` placeholder 해소 | C4·C12 |
| P12 | mobile 심의 직격 화면 | mobile·BE | consent placeholder 노출 제거 + 동의 로드 실패 dead-end 복구 + settings dev정보 노출 제거 + 앱 버전 동적화 | C8·C9 |
| P13 | 약관 3종 | mobile·provider·admin·BE | 환불·청소년보호·쿠키 정책 — BE policy KIND 추가 + admin Policies + mobile/provider 노출 + `policy_view` 언어 정합(`?lang=ko` 제거) | C14·High |

### 📡 WiFi 로밍 (W1 — B 스코프, C10·C13 포함)

| PR | 도메인 | 콘솔 | 내용 | v1 노출 | 갭 |
|---|---|---|---|---|---|
| P14 | WiFi 데이터 모델 재설계 | BE | `wifi_profiles` 확장 + `beacon_wifi`·`units`·`wifi_access_grant`·`devices` 신규 + `beacons.role`(wifi/cashier) 추가 (확장 필드 전부 선반영) | — | W1 기반 |
| P15 | WiFi 등록·연동 | provider·admin·BE | handshake 묶음 반환(`LIMIT 1` 제거) + 슈퍼어드민 WiFi 등록화면 + provider `WifiSettings` 실연동 + `credential_mode static` + 비콘 role 설정 UI(admin `Beacons`·provider claim, wifi/cashier) | ✅ 공개 | C10·C13·C4 |
| P16 | mobile WiFi 클라이언트 | mobile | 비콘→WiFi 묶음 fetch·캐시 + BSSID 검증 + "WiFi 변경됨" 흐름 + 손님 자동/승인 설정 + home 진입점 보강 | ✅ 공개 | High·W1 |
| P17 | `.mobileconfig` 다건 설치 | BE·mobile·iOS | `.mobileconfig` 생성·다건 설치 흐름 (서명은 인증서 도착 후 적용) | ✅ 공개 | W1 |
| P18 | `credential_mode managed` | BE·provider·mobile | 비번 교체 리마인드 + 인가 손님 자동 전파 (알림 연동) | 🔒 flag | W1 |
| P19 | units/grant 관리 화면 | admin·provider·BE | 호실·자리 시간제 권한 관리 UI | 🔒 flag | W1 |

### 📋 심의·버전 마무리

| PR | 도메인 | 콘솔 | 내용 | 갭 |
|---|---|---|---|---|
| P20 | 앱 버전관리 | admin·mobile | admin `app-versions` UI(BE 이미 완성) + mobile OS 최소버전 게이트 | C11·W5 |
| P21 | 심의 메타 자산 | mobile·iOS | `PrivacyInfo.xcprivacy` + Bundle ID 확정 + Android Photo Picker + 계정삭제 웹 URL | W2 |

### 🎟️ 쿠폰·스탬프 회원 QR 운영 (2026-05-21 재설계 — P9 이후 실행)

| PR | 도메인 | 콘솔 | 내용 | v1 노출 |
|---|---|---|---|---|
| P22 | 쿠폰·스탬프 회원 QR 운영 | mobile·provider·BE | mobile 마이페이지 **회원 QR**(URL 토큰 인코딩, 수동 새로고침) + provider-web QR 스캔·코드입력 → 스탬프 적립/쿠폰 사용 화면 + 스탬프 적립 모드(`auto` 방문자동 / `staff` 점주수동) 매장 선택 + 쿠폰함 쿠폰 회수 보호(점주 삭제 불가, 사용·만료만) + **친구초대** QR/링크(기존 `invitations` API·`channel=qr` 활용, `invited_via_code` 가입추적) + 초대보상 구조 hook(스키마만) | ✅ 공개 |

**결정 배경 (2026-05-21 사용자 확정):**
- 현재 코드는 점주가 손님을 식별·조회·적립할 방법이 전무(`users` 테이블에 이름·전화번호도
  없음). 유일 동작 경로 = BLE 방문 자동적립. → 점주 수동적립용 **회원 식별 다리**를 신규 구축.
- **통합 QR 1개** — 손님 마이페이지에 회원 QR 1개. 점주가 provider-web으로 스캔 →
  스탬프/쿠폰, 친구가 일반 카메라로 찍으면 → 초대 랜딩. 스캔 주체로 분기.
- **수동 새로고침** — 결제가 아니므로 네이버페이식 단기 자동회전은 v1 미적용. 사용자가
  필요 시 직접 새로고침해 이전 QR 무효화. 토큰 구조는 결제 연계(2차) 시 단기회전으로
  강화 가능하게 설계(확장성).
- **친구초대 보상** — v1은 구조(hook)만. 실제 보상 종류·예산·매장 정산·비용지급·세무는
  2차 슈퍼어드민에서 결정.
- 폐기: 이전 "캐셔 게이트 + 점주 실시간 승인/거절" 모델(거절은 단방향 흐름에 무의미).

**2차 이후:** 키오스크/POS·네이버·카카오·편의점 등 현장결제 코드스캔 인프라와 연계해
설정 금액·조건 도달 시 자동 적립/쿠폰발행. 회원 QR 단기 자동회전. 친구초대 보상 지급·정산.

**의존성:** P3 → P11(ConfirmModal 선행) · P4 → P5~P11(실 인증 후 테스트) ·
P9 → P22(쿠폰·스탬프 실연동 후) · P14 → P15~P19 · P13 BE → mobile/provider 노출.

---

## 5. Critical 14건 매핑 검증

| 갭 | PR | 갭 | PR |
|---|---|---|---|
| C1·C2·C3 인증 우회 | P4 | C8 consent placeholder | P12 |
| C4 mock 데이터 | P5·P7·P8·P9·P10·P11·P15 | C9 settings dev 노출 | P12 |
| C5 OCR 허위 ✅ | P6 | C10 WiFi 등록화면 | P15 |
| C6 PG 평문 저장 ✅ | P7 | C11 앱 버전관리 | P20 |
| C7 구 회사정보 | P5 | C12 placeholder/dead 페이지 | P8·P11 |
| C13 WiFi password 빈값 | P15 | C14 약관 3종 | P13 |

→ C1~C14 전건 매핑 완료. High 항목은 도메인 PR에 흡수(테마/폰트→P1, i18n→P2, 디자인→P1·P3, ConfirmModal→P3, coupons silent→P9, 알림 라우팅→P10, forgot-pw→P4, policy lang→P13, home 빈약→P16).

---

## 6. 진행 상태

⬜ 대기 · 🔄 진행중 · 🔎 검토 · ✅ 완료

| PR | 상태 | PR | 상태 | PR | 상태 |
|---|---|---|---|---|---|
| P1 | ✅ | P8 | ◑ (번역=P8b) | P15 | ⬜ |
| P2 | ✅ | P9 | ✅ | P16 | ⬜ |
| P3 | ✅ | P10 | ⬜ | P17 | ⬜ |
| P4 | ✅ | P11 | ⬜ | P18 | ⬜ |
| P5 | ✅ | P12 | ⬜ | P19 | ⬜ |
| P6 | ✅ | P13 | ⬜ | P20 | ⬜ |
| P7 | ✅ | P14 | ⬜ | P21 | ⬜ |
| P22 | ⬜ |  |  |  |  |

---

## 7. 일정 재추정

| 단계 | 내용 | 기간 | 누적 |
|---|---|---|---|
| 인프라 | P1~P3 | ~4일 | 5월 말 |
| Critical 도메인 | P4~P13 (10 PR) | ~2주 | 6월 중순 |
| WiFi 로밍 (B) | P14~P19 (6 PR) | ~2.5~3주 | 7월 초~중순 |
| 쿠폰·스탬프 회원 QR | P22 (P9 이후·병행) | ~1주 | 7월 초~중순 |
| 심의 마무리 | P20~P21 | ~3일 | 7월 중순 |
| Phase 2~4 | 테스트데이터 시드(W7)·페르소나 검증·수정 | ~1.5주 | 7월 중순~하순 |
| Phase 5 | 제출 준비(빌드·메타데이터) | 며칠 | 7월 하순 |

- **코드 완료: 7월 초~중순** / **심의 제출: 7월 중순** / **출시: 7월 하순~8월 초**
- 외부 병목(병행): 사업자등록 5/22~26 → 통신판매업·위치기반서비스 신고 → 토스 PG 심사 1~2주.
  사용자가 외부 행정을 압축 처리하면 코드 +1~2주가 외부 critical path와 겹쳐 흡수 → 7월 하순 가능.
- A 스코프 대비 +1~2주 (WiFi 로밍 B 채택분).

---

## 8. 외부 의존 — 원광대학교 테스트 환경 요청 체크리스트

호텔/리조트 다중 WiFi 로밍 실기기 테스트(§3)를 위해 **원광대학교 창업지원단**에
사전 확인·요청할 항목.

| # | 요청 항목 | 목적 |
|---|---|---|
| 1 | 테스트용 건물 내 와이파이 SSID(이름) + 비밀번호 | WiFi 프로필 등록 |
| 2 | 해당 와이파이 접속 방식 — 공용 비번형 vs 학교계정 로그인형 | static(가능) / enterprise(v1 불가) 판별 |
| 3 | 건물 내 AP(공유기) 층별 개수·대략 위치 | units(호실) 매핑 설계 |
| 4 | 비콘 9개 임시 부착 + 테스트 기간 출입 허가 | 실기기 walk-through |

**보낼 질문 초안 (비전문가도 이해 가능하게):**

> 안녕하세요. PathWave 와이파이 서비스 실증 테스트 관련 문의드립니다.
>
> 1. 테스트로 사용할 수 있는 건물 내 와이파이의 **이름(SSID)과 비밀번호**를 알려주실 수 있을까요?
> 2. 그 와이파이는 다음 중 어느 방식인가요?
>    - (A) 와이파이 이름·비밀번호 하나로 누구나 접속 (카페 와이파이 방식)
>    - (B) 각자 본인 학교 아이디·비밀번호로 로그인해 접속 (eduroam 방식)
>
>    → 저희 테스트에는 **(A) 방식**이 필요합니다. (B)만 있다면 테스트 전용으로 (A) 방식을 별도로 열어주실 수 있는지요?
> 3. 테스트 건물에 와이파이 공유기(AP)가 층별로 몇 개쯤, 어디에 있는지 대략 알 수 있을까요?
> 4. 테스트 기간 동안 건물 내 벽·천장에 소형 비콘(BLE 센서 9개)을 임시로 부착하고 출입하며 측정해도 괜찮을까요?

**비콘 9개 배정:** 단일매장 6개(WiFi 존 5 + 캐셔 역할 1) + 호텔 호실 3개.
캐셔 비콘 = 별도 추가가 아니라 6개 중 1개를 role=cashier·좁은 RSSI로 지정.

## 9. 다음 단계

1. P1(mobile 디자인 기반)부터 순서대로 착수.
2. 각 PR = 마스터플랜 §4 품질 기준 7개 강제 + 시나리오 테스트 후 완료 보고.
3. PR 완료 시 본 문서 §6 상태 갱신 + 마스터플랜 §6 워크스트림 갱신.
