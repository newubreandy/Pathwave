# PathWave 변경 이력

## v1.0.0-rc1 — 2026-05-29

출시 후보 1차. 비콘 프로비저닝 워크플로우 완성 + 앱스토어 심사 코드 처리 완료 + 출시 운영 문서 정비.

### 🆕 신규 기능 — 비콘 프로비저닝 (P-A ~ P-D)

점주가 신청한 설치위치·WiFi 가 슈퍼어드민 매칭·발송·점주 설치완료 라이프사이클로 흐름.

- **P-A** (#236) — 점주 서비스 신청 저장. `service_requests` + `service_request_units` 테이블. WiFi 비번 AES-256-GCM 암호화 저장. `POST /api/service-requests`.
- **P-B** (#237) — 슈퍼어드민 신청 관리 + 인벤토리 비콘 매칭. `POST /api/admin/service-request-units/<uid>/match` (할당·활성·major/minor·설치위치·WiFi 프로필 자동 연결).
- **P-C** (#238) — 라벨(스티커) 인쇄. 매칭된 비콘별 설치위치 라벨 1장씩 출력. `@page size 40×25mm` print CSS + 새 창 격리. 크기 admin 설정값.
- **P-D** (#239) — 상태 추적. `matched → shipped (어드민 발송) → installed (점주 설치완료)` 전이. 가드(매칭 전 발송 차단).
- (#234) provider-web 비콘 claim UI mock→실연동.
- (#235) 점주 매장정보 화면 = 비콘 목록 읽기 전용 (할당은 슈퍼어드민 주도).

### 🆕 신규 기능 — 결제

- (#225) 제로페이 B — provider 구독료 결제 (점주→PathWave). feature flag 토글.
- (#226) 제로페이 A-1 — 사용자→매장 결제 (회원 QR 스캔). v1 mock placeholder.
- (#227) 회원 QR verify 의 `users.status` 컬럼 참조 버그 수정 (`deleted_at` 기준).

### 🆕 신규 기능 — 인증·계정

- (#230) 점주 비밀번호 재설정 (`/api/facility/forgot-password`, `/reset-password`) + provider-web ForgotPassword 페이지.
- (#230) 빌링키(pg_key) AES-256-GCM 암호화 저장. 레거시 평문 데이터 fallback.

### 🆕 신규 기능 — 정책·법적 페이지

- (#233) 공개 개인정보처리방침 + 이용약관 정적 페이지 (한국어+영어). Apple/Google 제출 필수 URL.
- (#245) 동의 마이크로항목 7종 영문 시드 (`age14`/`camera`/`location`/`marketing`/`push`/`storage`/`third_party`).

### 🛡️ 앱스토어 심사 준비 (R1 ~ R7 코드 7건)

- (#240) **R1·R3·R4·R5·R6 묶음**:
  - R1 앱 표시 이름 `pathwave_app` → **"PathWave"** (iOS CFBundleName/DisplayName + Android android:label)
  - R3 iOS `LSApplicationQueriesSchemes` 추가 (카카오·네이버 6종 scheme)
  - R4 Android `<queries>` 에 `com.kakao.talk` + `com.nhn.android.search` package
  - R5 iOS `ITSAppUsesNonExemptEncryption = false` (수출규제 영구 해소)
  - R6 iOS deployment target 13.0 → 15.0 (Podfile 일치)
- (#241) **R2 Bundle ID 통일** → `com.triggersoft.pathwave` (iOS·Android·Kotlin 패키지 디렉토리 이동 포함). `docs/launch_bundle_id_console_steps.md` 가이드 동봉.
- (#242) **R7 WifiSettings mock 제거** + 실 백엔드 매핑 (`service_requests` + 비콘 조합).

### 📚 출시 운영 문서 (M1·M2·M3·M4·M5)

- (#243) 4종 정답지/원문 문서:
  - `docs/data_collection_map.md` (M1) — Apple App Privacy + Google Data Safety 폼
  - `docs/reviewer_guide.md` (M2) — 심사관 안내 한국어+영어
  - `docs/store_listing_content.md` (M3) — 앱 이름·부제·키워드·4000자 설명 한국어+영어
  - `docs/launch_build_commands.md` (M5) — iOS/Android/백엔드/웹 빌드 명령 + dart-define + 체크리스트
- (#244) **M4 Sentry** 3 클라이언트 신규 설치 (mobile `sentry_flutter`, provider-web/admin-web `@sentry/react`). 백엔드는 기존 완비. DSN 미주입 시 자동 no-op.
- 출시 심의 시뮬레이션 리포트: `docs/store_review_simulation_2026-05-29.md`.

### 🧪 검증

- 비콘 프로비저닝 end-to-end: 신청 → 매칭(major/minor/설치위치/WiFi연결) → 발송 → 설치완료, 가드 포함 전부 통과.
- 점주 forgot/reset, pg_key 암호화 라운드트립, 라벨 인쇄 새 창 격리 등 개별 검증.
- 심사 시뮬레이션: HIGH 0건, MEDIUM 코드 0건(R1~R7 전부 해소), 잔여는 콘솔/실물.

### ⚠️ 출시 직전 필수 — 사용자 콘솔 작업 (코드 외)

1. R2 후속 — Firebase / Apple Portal / Kakao / Naver / Play Console 에 새 Bundle ID 등록 + 새 `GoogleService-Info.plist` · `google-services.json` 교체. (가이드: `docs/launch_bundle_id_console_steps.md`)
2. R3 후속 — Info.plist `CFBundleURLTypes` 에 `kakao{NATIVE_APP_KEY}` 추가 (실 키 확보 후).
3. Sentry — 프로젝트 4개(backend / mobile-ios / mobile-android / web) 생성 → DSN 받아 빌드/배포 env 에 주입.
4. M3 스크린샷 디자인 (사용자/외주).
5. 운영 DB 에 `scripts/seed_consent_micro_en.py` 1회 실행.
6. 운영 env — `.env.example` 참고해 실 값 주입.

### 🔧 인프라

- 백엔드 `.env.example` 작성.
- 운영 env 검증 (`app.py:_validate_production_env`) — 누락 시 부팅 차단.

---

## v0.x — 이전 작업 (요약)

P1 ~ P22 + Phase A~K, store review pre-launch audit, BLE 비콘 데이터모델, mobile i18n 인프라, 채팅 자동번역(P8b), Privacy Manifest 등 다수. 상세는 `docs/pathwave_phase1_plan_2026-05-21.md` 참고.
