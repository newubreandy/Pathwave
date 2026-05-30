# PathWave — 심사관 안내 (Apple App Review / Google Play)

> 본 문서는 App Store Connect / Play Console **"App Review Information"** 칸에 그대로 붙여넣기 위해 작성되었습니다.
> 심사 빌드 제출 직전에 콘솔에서 입력 + 영문 버전(아래 §EN)도 함께 제출하세요.

## 한국어 (KR)

### 데모 계정

| 역할 | 이메일 | 비밀번호 |
|---|---|---|
| 일반 사용자 (앱) | `demo-user@pathwave.app` | `Demo2026!` |
| 매장 점주 (웹) | `demo-provider@pathwave.app` | `Demo2026!` |
| 운영자 (참고) | 심사 미사용 — 운영자 전용 웹 |

⚠️ 실제 키 발급 후 위 계정을 사전에 시드 + 1매장(데모 시설) 사전 세팅하여 BLE 비콘 없이도 핵심 기능 점검이 가능하도록 합니다.

### 핵심 기능 도달 경로 (BLE 비콘 없이도 검증 가능)

1. **회원가입 / 로그인** — 이메일 코드 + 비밀번호. 14세 미만은 가입 거부됨.
2. **소셜 로그인** — Kakao / Google / Apple / Naver. 데모 빌드에 각 키 주입됨.
3. **데모 매장 진입** — 홈에서 "데모 시설" 카드 클릭. (실 BLE 비콘 없이 매장 정보·메뉴·채팅 도달 가능)
4. **매장 채팅** — 매장에 메시지 작성 → 자동 번역(한국어↔영어 등) → 데모 매장 응답.
5. **스탬프 / 쿠폰** — 데모 매장 화면에서 스탬프 적립 / 쿠폰 받기·사용 시연 가능.
6. **계정 삭제** — 설정 > 계정 관리 > 계정 삭제. 본인 비밀번호 입력 후 즉시 비활성화.

### BLE 비콘 의존 기능 (심사 시 미시연)

- 매장 자동 인식 / 자동 WiFi 연결 / 자동 스탬프 적립은 **실 BLE 비콘(FSC-BP108B)** 근처에서 동작합니다.
- 심사관에게 위 데모 매장 카드 클릭 경로를 안내해 비콘 없이도 매장 기능을 검증할 수 있게 합니다.

### 권한 사용 안내

| 권한 | 사용 시점 | 백그라운드 |
|---|---|---|
| 위치 (WhenInUse) | 매장 자동 감지 시 (앱 사용 중에만) | 사용 안 함 |
| Bluetooth | BLE 비콘 감지 | 사용 안 함 |
| 카메라 | 프로필 사진 / QR 스캔 | — |
| 사진 라이브러리 | 프로필 사진 / 매장 사진 선택 (Photo Picker 사용) | — |
| Local Network | 매장 WiFi 자동 연결 | — |
| 알림 | 푸시 알림 | — |

### 정책 / 동의 / 모더레이션

- 가입 시 필수 동의: 만 14세 이상 / 위치 정보 / 이용약관 / 개인정보처리방침
- UGC(채팅): 우측 상단 ⋮ 메뉴에서 **신고 / 차단** 가능. 신고된 콘텐츠는 운영자 검토 후 조치.
- 만 14세 미만 가입 거부. 14~18세는 보호자 초대 코드 필수.
- 계정 삭제: 앱 내 즉시 가능 + 앱 외 공개 URL `/legal/account-deletion.html`.

### 공개 법적 페이지

- 개인정보처리방침: `https://(도메인)/legal/privacy-policy.html`
- 이용약관: `https://(도메인)/legal/terms-of-service.html`
- 환불 정책: `https://(도메인)/legal/refund-policy.html`
- 청소년 보호 정책: `https://(도메인)/legal/youth-protection.html`
- 쿠키 정책: `https://(도메인)/legal/cookie-policy.html`
- 계정 삭제: `https://(도메인)/legal/account-deletion.html`

### 결제 / IAP

- iOS 앱 내에서는 **디지털 재화/구독 판매 없음**(Apple 3.1 IAP 비적용).
- 점주 구독료(B2B SaaS)는 별도 웹 콘솔(provider-web)에서 외부 PG(토스/제로페이) 결제.
- 사용자 매장 결제(제로페이)는 실물 매장 결제(외부 PG 허용 범위).

### 문의

- 심사 관련: `review@pathwave.app`
- 개인정보 보호책임자: `privacy@pathwave.app`

---

## English (EN)

### Test Accounts

| Role | Email | Password |
|---|---|---|
| End user (app) | `demo-user@pathwave.app` | `Demo2026!` |
| Store owner (web) | `demo-provider@pathwave.app` | `Demo2026!` |

### How to verify core features without a physical BLE beacon

1. **Sign up / log in** — email code + password. Users under 14 are rejected.
2. **Social login** — Kakao / Google / Apple / Naver. Keys are injected in the demo build.
3. **Enter the Demo Store** — tap the "Demo Store" card on Home. Core features (info, menu, chat) are reachable without a beacon.
4. **In-store chat** — write a message → automatic translation (Korean ↔ English etc.) → demo store reply.
5. **Stamps / coupons** — earn a stamp or claim/redeem a coupon from the demo store view.
6. **Account deletion** — Settings > Account > Delete Account. Confirm with password → soft delete.

### Beacon-dependent features (not demonstrable in review)

- Automatic store detection, automatic Wi-Fi connection, and automatic stamp credit run with a physical **FSC-BP108B BLE beacon**. The demo-store entry path above lets reviewers verify all store-side features without a beacon.

### Permissions

| Permission | When | Background |
|---|---|---|
| Location (WhenInUse) | Automatic store detection (foreground only) | No |
| Bluetooth | BLE beacon detection | No |
| Camera | Profile photo / QR scan | — |
| Photo Library | Profile photo / store photo (Photo Picker) | — |
| Local Network | Store Wi-Fi auto-connect | — |
| Notifications | Push notifications | — |

### Policies / Consent / Moderation

- Required consents at sign-up: age 14+, location, ToS, Privacy Policy.
- UGC (chat): a "Report / Block" menu is available on every chat (top-right ⋮).
- Users under 14 are denied. Users 14–18 require a guardian invite code.
- Account deletion: in-app instantly + public web URL `/legal/account-deletion.html`.

### Public Legal Pages

(Same Korean list — replace path with your production domain)

### Payment / IAP

- The iOS app does **not** sell digital goods or subscriptions in-app (Apple 3.1 IAP does not apply).
- Store-owner subscriptions (B2B SaaS) are paid via a separate web console (provider-web) using external PGs (Toss / ZeroPay).
- End-user payments at physical stores (ZeroPay) are for real-world goods/services (external PG allowed).

### Contact

- Review: `review@pathwave.app`
- Privacy officer: `privacy@pathwave.app`
