# spec/store-review-compliance.md — Apple HIG + Material 3 + 심의 컴플라이언스

> **트랙**: 실제 개발 · 정교·상세 · v0.1 (2026-05-26)
> **메모리**: `project_store_review_audit.md`, `project_ui_legal_compliance.md`, `project_pre_launch_checklist.md`
> **목적**: 출시 직전 reject 방지. 심사 통과 후 운영 컴플라이언스 유지.

---

## 1. 전체 체크리스트 (출시 전 필수)

| 영역 | 항목 | 상태 |
|---|---|---|
| iOS | PrivacyInfo.xcprivacy (Required Reasons API) | ✅ PR #194 머지 |
| iOS | Sign in with Apple (소셜 로그인 있을 시) | ⏳ 본 단계 OOS (소셜 X) |
| iOS | App Tracking Transparency (광고 ID) | ⚠️ 광고 SDK 없으므로 미해당 |
| iOS | 계정 삭제 가이드라인 5.1.1(v) | ⏳ 웹 URL 필요 |
| Android | Photo Picker (Android 13+) | ✅ PR #195 머지 |
| Android | Data Safety (Play Console) | ⏳ 출시 직전 |
| Android | Foreground Service (BLE 백그라운드) | ⏳ Phase 2 |
| 공통 | 청소년 보호 정책 페이지 | ✅ PR #195 머지 |
| 공통 | 쿠키 정책 페이지 | ✅ PR #195 머지 |
| 공통 | 약관 다국어 (ko / en 최소) | ✅ |
| 공통 | 신고/차단 UI (User Generated Content) | ⏳ pre-launch-store-review-h1 PR |
| 공통 | 부적절 컨텐츠 신고 24h 내 대응 약속 | ⏳ 약관 명시 |

---

## 2. iOS — Apple HIG + 심사 가이드라인

### 2.1 Privacy Manifest (PR #194)
`mobile/ios/Runner/PrivacyInfo.xcprivacy` 등록 완료.
- **Required Reasons API** 명시:
  - `NSPrivacyAccessedAPICategoryUserDefaults` (사용자 설정 저장)
  - `NSPrivacyAccessedAPICategoryFileTimestamp` (파일 시각)
  - `NSPrivacyAccessedAPICategorySystemBootTime` (BLE 스캔 timing)
- **Data Types**: 이메일 / 위치 (정확) / 디바이스 ID / 사용 로그
- **Collection Purpose**: App Functionality / Analytics

### 2.2 권한 사용 사유 (`Info.plist`)
| 권한 | Key | 한국어 사유 |
|---|---|---|
| 위치 (사용 중) | `NSLocationWhenInUseUsageDescription` | "주변 매장의 WiFi 자동 연결을 위해 위치 권한이 필요합니다." |
| 블루투스 | `NSBluetoothAlwaysUsageDescription` | "비콘 인식을 통한 WiFi 자동 연결에 사용됩니다." |
| 카메라 | `NSCameraUsageDescription` | "프로필 사진 등록 및 채팅 사진 전송에 사용됩니다." |
| 사진 | `NSPhotoLibraryUsageDescription` | "채팅 사진 첨부에 사용됩니다." |
| 푸시 | (NSUserNotificationsUsageDescription 자동) | "쿠폰, 스탬프, 채팅 알림 수신에 사용됩니다." |

⚠️ 한국어 + 영어 모두 명시 필요.

### 2.3 Apple HIG 체크리스트
| 항목 | 적용 |
|---|---|
| 다크모드 | ✅ 3 콘솔 모두 다크 (mobile / provider / admin) |
| Dynamic Type (글자 크기) | ⏳ 검증 필요 |
| 햅틱 | ⏳ 결제·스탬프 적립 시 추가 |
| VoiceOver (a11y) | ⏳ 필수 화면 검증 |
| Safe Area (notch / Dynamic Island) | ✅ PR `c1b-safearea-coverage` |
| iPad 지원 | ⏳ Phase 2 (Phase 1 = iPhone only 등록 가능) |
| 가로 모드 | ⏳ 결정 필요 (포트레이트만 lock?) |
| 키보드 자동 dismiss | ⏳ 검증 |
| 진동/사운드 권한 | ✅ 푸시 권한과 통합 |

### 2.4 심사 reject 빈도 상위
1. **Privacy Manifest 누락** — ✅ 해결
2. **계정 삭제 in-app** — ⏳ "회원탈퇴" 버튼 + 웹 URL 둘 다
3. **데모 계정 누락** — ⏳ provider 시연용 계정 발급 + 심사 메모 작성
4. **로그인 필수 화면 안내 부족** — ⏳ "게스트로 둘러보기" 가 일부 화면 노출
5. **결제 가이드라인 3.1.1** — 디지털 컨텐츠 구매는 IAP 필요. 우리는 provider 구독만 → 외부결제 가능 (해당 안 됨)

### 2.5 출시 메타데이터
- **App Name**: PathWave
- **Subtitle**: "BLE 비콘으로 자동 WiFi 연결" (30 chars 이하)
- **카테고리**: Travel (primary), Utilities (secondary)
- **연령**: 4+ (UGC 신고 시스템 있으므로 17+ 필요 가능 — 검토)
- **스크린샷**: 6.7" / 6.1" / 5.5" iPhone + 12.9" iPad (선택)

---

## 3. Android — Material 3 + Play Console

### 3.1 Photo Picker (PR #195)
Android 13+ (API 33+) 의 `ActivityResultContracts.PickVisualMedia` 사용.
- 권한 요청 없이 사용자가 선택한 사진만 접근.
- 이전 `READ_MEDIA_IMAGES` 권한 제거.

### 3.2 권한 (`AndroidManifest.xml`)
| 권한 | 용도 | minSdk 정책 |
|---|---|---|
| `BLUETOOTH_SCAN` | 비콘 스캔 (API 31+) | + `neverForLocation` 플래그 |
| `BLUETOOTH_CONNECT` | 비콘 연결 (API 31+) | |
| `ACCESS_FINE_LOCATION` | BLE 스캔 (API ≤30) + WiFi 정보 | API 31+ 면 BLE 만으로 가능 |
| `CHANGE_WIFI_STATE` | WiFi 자동 연결 | |
| `INTERNET` | 백엔드 통신 | |
| `POST_NOTIFICATIONS` | 푸시 (Android 13+) | runtime |

### 3.3 Material 3 체크리스트
| 항목 | 적용 |
|---|---|
| Dynamic Color (Wallpaper-based) | ⏳ Phase 2 (브랜드 색 우선) |
| Edge-to-Edge | ⏳ 검증 (status bar / nav bar 투명) |
| Predictive Back Gesture | ⏳ Android 14+ 검증 |
| Theme: Light / Dark | ✅ 다크 적용 |
| 권한 rationale | ✅ PR `permission-rationale` |
| Splash Screen API (12+) | ⏳ 검증 |
| Adaptive Icon | ⏳ 검증 |

### 3.4 Data Safety (Play Console)
출시 전 등록 필수.

| 데이터 카테고리 | 수집 | 공유 | 목적 |
|---|---|---|---|
| 개인 정보 (이메일) | ✅ | ❌ | 계정 식별 |
| 위치 (정확) | ✅ | ❌ | 매장 검색·WiFi 자동연결 |
| 디바이스 ID | ✅ | ❌ | 푸시 알림 |
| 사용 로그 | ✅ | ❌ | 서비스 개선 |
| 사진 (사용자 제공) | ✅ | ❌ | 프로필·채팅 |
| 채팅 메시지 | ✅ | ❌ | 매장-사용자 소통 |

**보안**:
- 전송 중 암호화 ✅ (HTTPS)
- 사용자 데이터 삭제 요청 ✅ (계정 삭제 시 자동)

### 3.5 출시 메타데이터
- **앱 이름**: PathWave
- **짧은 설명**: "BLE 비콘으로 자동 WiFi 연결" (80 chars)
- **자세한 설명**: 한국어 + 영어 (4,000 chars)
- **카테고리**: 여행 및 지역정보
- **콘텐츠 등급**: 3+ (UGC 시 12+ 검토)

---

## 4. 공통 — 법적 컴플라이언스 (한국)

### 4.1 약관 / 정책 (필수)
| 약관 | 위치 | 다국어 | 비고 |
|---|---|---|---|
| 이용약관 | `policies` (kind='terms') | ⏳ ko/en | 사용자용 / provider용 분리 |
| 개인정보처리방침 | `policies` (kind='privacy') | ⏳ ko/en | |
| 위치기반서비스 이용약관 | `policies` (kind='location') | ⏳ ko/en | LBS 사업자 필수 |
| 마케팅 수신 동의 | `policies` (kind='marketing') | ✅ ko | 선택 |
| 청소년 보호 정책 | 웹 페이지 | ✅ ko | PR #195 |
| 쿠키 정책 | 웹 페이지 | ✅ ko | PR #195 |

### 4.2 동의 수집 (`consents` 테이블)
- 가입 시 필수 약관 동의 → `accepted=1`, `accepted_at`, `version`, `ip`, `user_agent` 기록
- 약관 개정 시 → 재동의 (백엔드: `policies.version` 갱신, mobile/web: 모달 표시)

### 4.3 사용자 권리 (개인정보보호법 + GDPR 대응)
- 열람: 마이페이지 → "내 정보 다운로드" (JSON 또는 CSV 발급)
- 수정: 마이페이지 → 프로필 편집
- 삭제: 마이페이지 → "회원탈퇴" (즉시 처리 + 30일 보관 후 완전 삭제)
- 처리 정지: 약관 동의 철회 (서비스 사용 불가)
- 이전: 데이터 다운로드 후 본인이 이전

### 4.4 푸터 필수 요소 (footer 위젯)
메모리 `project_ui_legal_compliance.md`:
- 사업자등록번호
- 통신판매업 신고번호
- 위치기반서비스사업자 신고번호
- 법인 주소 / 대표자
- 고객센터 연락처 / 운영시간
- 약관 / 개인정보처리방침 / 위치기반 약관 링크

### 4.5 화면별 필수 안내 매트릭스
메모리 `project_ui_legal_compliance.md` 참조.
- 위치 권한 요청 화면 → LBS 약관 동의 동시
- 결제 화면 → 영수증 수신 동의
- 채팅 화면 → 신고/차단 UI 명시

---

## 5. UGC (User Generated Content) — 신고·차단 (필수)

스토어 가이드라인 (Apple 1.2 / Google UGC) 요구사항:
1. ✅ 부적절 컨텐츠 신고 기능
2. ✅ 사용자 차단 기능
3. ✅ 24시간 내 신고 처리 약속
4. ⏳ 운영자 처리 결과 사용자에게 통지

### 5.1 신고 (`abuse_report` + `routes/report.py`)
- 채팅 메시지 신고 → admin alert
- 사유: 욕설 / 사기 / 음란 / 기타
- 신고 후 메시지 자동 hide (조회 가능, 본문 마스킹)

### 5.2 차단 (`chat_blocks` + `block.py`)
- 사용자가 사장 / 사장이 사용자 차단 가능
- 차단 시: 채팅 이력 양쪽 모두 숨김, 신규 메시지 차단

### 5.3 운영자 처리 (admin 채팅 admin 패널)
- 신고 큐 표시
- 처리 결과 (경고 / 정지 / 무시) 기록
- 사용자에게 결과 알림 (Phase 2)

---

## 6. 출시 전 reject 방지 audit (메모리 기반)

### 6.1 HIGH (해결됨 또는 진행 중)
- ✅ iOS Privacy Manifest (PR #194)
- ✅ 채팅 신고·차단 UI (pre-launch-store-review-h1 PR)
- ⏳ 계정 삭제 웹 URL

### 6.2 MEDIUM (출시 직전 적용)
- ⏳ 환불 정책 문서
- ⏳ 청소년 정책 / 쿠키 정책 (✅ PR #195)
- ⏳ Data Safety 등록
- ⏳ Apple Privacy Nutrition Label
- ⏳ 데모 계정 + 심사 메모

### 6.3 LOW (Phase 2)
- 백그라운드 위치 (v1 미포함 권장)
- iPad 최적화
- Wear OS / watchOS 지원

---

## 7. 심사 메모 작성 (Apple Connect / Play Console)

### 7.1 데모 계정
| 콘솔 | 계정 | 비고 |
|---|---|---|
| 사용자 (mobile) | demo-user@pathwave.kr / DemoUser2026! | 비콘 없이도 일부 화면 확인 |
| provider (web) | demo-sp@pathwave.kr / DemoSP2026! | 매장 등록 완료 상태 |
| admin | (제공 X) | 심사관 요청 시만 별도 제공 |

### 7.2 BLE 시연 (심사관에게 안내)
- 실 비콘 없으면 일부 기능 시연 불가
- 영상 첨부 (앱 미리보기 영상) 또는 admin 의 "비콘 시뮬레이션" 토글
- Apple: TestFlight 외부 테스터 등록 추천

---

## 8. 운영 컴플라이언스 (출시 후 유지)

- 약관 개정 → 사전 30일 통지 + 재동의
- 개인정보 유출 사고 → 24시간 내 KISA 신고
- 어린이 대상 X (만 14세 미만 가입 차단 — 회원가입 시 검증)
- 영업비밀 / 영업양도 시 별도 처리

---

## 9. 현재 갭 / TODO

- [ ] 계정 삭제 웹 URL 페이지 (Apple 필수)
- [ ] iOS Info.plist 권한 사유 한국어 + 영어 완전 작성
- [ ] Data Safety 등록 (Play Console)
- [ ] Apple Privacy Nutrition Label 등록
- [ ] 데모 계정 발급 (mobile + provider) + 심사 메모
- [ ] BLE 시뮬레이션 토글 (admin)
- [ ] 약관 ko + en 작성 완료 (위치기반 약관 포함)
- [ ] 어린이 만 14세 미만 가입 차단 검증
- [ ] 한국 LBS 사업자 신고 (사업자등록 후)
- [ ] 사고 대응 매뉴얼 (1인 회사)

## 10. 관련 PR / 메모리

- PR #194 iOS Privacy Manifest
- PR #195 Photo Picker + 청소년·쿠키 정책
- pre-launch-store-review-h1 (채팅 신고·차단)
- 메모리 `project_store_review_audit.md` (전체 audit 결과)
- 메모리 `project_ui_legal_compliance.md` (UI 가이드 + 푸터 + 화면별 매트릭스)
- 메모리 `project_pre_launch_checklist.md` (4영역 정의)
