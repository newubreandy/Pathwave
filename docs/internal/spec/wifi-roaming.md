# spec/wifi-roaming.md — 무중단 WiFi 로밍 (방식 C 비콘 주도)

> **트랙**: 실제 개발 (`docs/internal/`) · 정교·상세
> **버전**: v0.1 (2026-05-26)
> **창업지원단 자료** : (별첨 2 비콘 프로토콜에 간단히 언급, 본 문서는 비공개)
> **관련 메모리**: `project_core_wifi_roaming.md` (USP 정의), `project_beacon_spec.md`

---

## 1. ⭐ PathWave 의 본질

> **"신호강도 기반 무중단 WiFi 핸드오프 — 리조트 1회 인증 후 이동해도 안 끊김"**
> — 사용자 직접 정의 (2026-05-20)

다른 LBS/광고 플랫폼이 못하는 빈 시장 = **이동 중 끊김 없는 자동 인증**.

## 2. 일반 WiFi 의 한계

```
방 A (SSID: hotel-floor1)              방 B (SSID: hotel-floor2)
   ↓ 사용자 이동                          ↓
[자동 끊김 → 새 SSID 비밀번호 재입력 → 인증 → 다시 연결]
   = 30~60초 끊김
   = 채팅·영상 끊김, 알림 누락
```

리조트·대형 카페·공항 등에서 **AP 가 여러 개**일 때 발생. SSID 가 같아도 비밀번호가 다르면 끊김. BSSID 가 달라도 802.11r/k/v (Fast Transition) 미지원 AP 면 끊김.

## 3. 방식 비교 (사용자 직접 검토 후 C 확정)

| 방식 | 설명 | 장점 | 단점 | 채택 |
|---|---|---|---|---|
| A. 802.11r/k/v | 표준 Fast BSS Transition | OS 자동 처리 | AP 모두 지원 필요 (현실 X) | ❌ |
| B. WPA3-Enterprise + RADIUS | EAP 인증서 + RADIUS | 보안 강력 | 도입 비용·운영 부담 | ❌ |
| **C. 비콘 주도 다건 인증** | **비콘이 다음 SSID 푸시 + 앱이 .mobileconfig/WiFiConfig 사전 다건 설치** | **AP 변경 불필요, OS 표준 API** | 비콘 + 앱 구현 필요 | ✅ |
| D. 데이터 폴백 (LTE 우선) | 끊기면 LTE 로 전환 | 간단 | WiFi 본질 무시 | ❌ |

**선택 C 의 핵심**: AP 측은 손대지 않고, **앱이 미리 모든 SSID 의 자격증명을 OS 에 등록** 해두면 OS 가 자동 전환.

## 4. 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                       Backend                                │
│  - beacons (role: entry / corridor / room)                   │
│  - beacon_wifi (priority ASC)                                │
│  - wifi_profiles (scope: facility/unit, credential_mode)     │
│  - wifi_access_grant (target_type, valid_until)              │
└──────────────────────────────┬──────────────────────────────┘
                               │ handshake 응답
                               │  wifis: [
                               │    {ssid, password, priority: 0},
                               │    {ssid, password, priority: 1},
                               │    ...
                               │  ]
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Mobile (Flutter)                          │
│                                                              │
│  1. BLE 스캔 → 비콘 인식                                       │
│  2. handshake 호출 → wifis[] 수신                              │
│  3. iOS: .mobileconfig 1개에 wifi profile N 개 묶어서 설치       │
│     Android: WifiNetworkSuggestion 다건 등록                  │
│  4. OS WiFi 매니저가 신호 강도 따라 자동 전환                       │
│  5. 사용자 이동 시 OS 가 자동 핸드오프 (0초)                        │
└──────────────────────────────────────────────────────────────┘
```

## 5. iOS — `.mobileconfig` 다건 설치

### 5.1 구조

```xml
<plist version="1.0">
<dict>
  <key>PayloadContent</key>
  <array>
    <!-- WiFi profile #1 -->
    <dict>
      <key>PayloadType</key><string>com.apple.wifi.managed</string>
      <key>PayloadIdentifier</key><string>com.pathwave.wifi.cafe.5g</string>
      <key>SSID_STR</key><string>PathWave-Cafe-5G</string>
      <key>Password</key><string>...</string>
      <key>EncryptionType</key><string>WPA2</string>
      <key>AutoJoin</key><true/>
      <key>Priority</key><integer>1</integer>
    </dict>
    <!-- WiFi profile #2 -->
    <dict>
      <key>SSID_STR</key><string>PathWave-Cafe-2.4G</string>
      ...
      <key>Priority</key><integer>2</integer>
    </dict>
    <!-- ... up to N -->
  </array>
  <key>PayloadDisplayName</key><string>PathWave 자동 WiFi</string>
  <key>PayloadUUID</key><string>{생성된 UUID}</string>
</dict>
</plist>
```

### 5.2 설치 절차
1. 백엔드 또는 mobile 앱이 위 plist 동적 생성
2. iOS Safari 로 다운로드 → "프로파일 다운로드됨" 알림
3. 설정 앱 → 프로파일 → 신뢰
4. 등록된 N 개 WiFi 가 모두 AutoJoin 활성화됨

### 5.3 제약
- App Store 정책 — `.mobileconfig` 강제 설치 금지. 사용자 동의 후 다운로드만.
- 앱 내 자동 설치는 MDM (Mobile Device Management) 필요. 본 단계에서는 사용자가 직접 설치.
- "프로파일 신뢰" 단계 UI 가이드 필요 (스토어 심사 reject 사유 될 수 있음 — 명확한 안내 화면 추가).

### 5.4 갱신 / 회수
- 비밀번호 변경 시 → 새 mobileconfig 재배포 + 사용자가 재신뢰
- 매장 탈퇴 시 → mobileconfig 삭제 안내 (앱에서 자동 삭제 API 없음)

## 6. Android — `WifiNetworkSuggestion` 다건 등록

### 6.1 코드 패턴 (Flutter / Kotlin)

```kotlin
val suggestions = listOf(
  WifiNetworkSuggestion.Builder()
    .setSsid("PathWave-Cafe-5G")
    .setWpa2Passphrase("...")
    .setIsAppInteractionRequired(false)
    .setPriority(1)
    .build(),
  WifiNetworkSuggestion.Builder()
    .setSsid("PathWave-Cafe-2.4G")
    .setWpa2Passphrase("...")
    .setPriority(2)
    .build(),
)
val status = wifiManager.addNetworkSuggestions(suggestions)
// STATUS_NETWORK_SUGGESTIONS_SUCCESS 확인
```

### 6.2 OS 버전별 호환

| Android | 지원 | 비고 |
|---|---|---|
| 10 (API 29) | ✅ | `addNetworkSuggestions` 도입 |
| 11 (API 30) | ✅ | 다건 제한 풀림 |
| 12+ | ✅ | + WPA3 지원 |
| < 10 | ❌ | 본 단계 미지원 (앱 minSdk 검토) |

### 6.3 사용자 UX
- 최초 등록 시 OS 알림 — "PathWave 가 WiFi 를 제안합니다. 허용하시겠습니까?"
- 허용 후 자동 연결.

### 6.4 제약
- 백그라운드 자동 등록 불가 (Android 11+) → 앱이 포그라운드일 때만.
- 사용자가 OS 설정에서 개별 SSID 비활성화 가능.

## 7. 무중단 핸드오프 시나리오 (리조트)

```
┌──────────────────────────────────────────────────────────────┐
│ 리조트 입구 (비콘 role='entry')                                │
│   ↓ BLE 인식 + handshake                                       │
│   ↓ wifis[] = [
│       {ssid: 'pathwave-resort-lobby',  priority: 0},
│       {ssid: 'pathwave-resort-floor1', priority: 1},
│       {ssid: 'pathwave-resort-floor2', priority: 2},
│       {ssid: 'pathwave-resort-spa',    priority: 3},
│       {ssid: 'pathwave-resort-pool',   priority: 4},
│       ...
│     ]
│   ↓ 앱이 mobileconfig (iOS) / suggestion (Android) 다건 등록
│   ↓ 로비 SSID 자동 연결
├──────────────────────────────────────────────────────────────┤
│ 사용자 → 1층 객실 이동                                         │
│   ↓ 로비 SSID 신호 약화 (-90 dBm)                              │
│   ↓ floor1 SSID 신호 강화 (-50 dBm)                            │
│   ↓ OS 자동 핸드오프 (앱 개입 X, 0초 끊김)                       │
├──────────────────────────────────────────────────────────────┤
│ 사용자 → 스파 이동                                             │
│   ↓ 동일 패턴 — spa SSID 로 자동 전환                            │
└──────────────────────────────────────────────────────────────┘
```

**핵심**: 한 번 handshake → N 개 자격증명 사전 등록 → 이후 OS 가 알아서 전환. 앱은 BLE 스캔만 백그라운드로 유지.

## 8. Phase 1 B 스코프 (사용자 확정)

> **Phase 1 = B 풀 스코프 (P14~P19), units/grant·managed 는 feature flag 로 v1 비공개**
> — 메모리 `project_core_wifi_roaming.md`

| PR | 내용 | 상태 |
|---|---|---|
| P14 | beacon handshake + AES-GCM | ✅ |
| P15 | `wifis[]` multi-SSID 응답 | ✅ |
| P16-a | provider unit / unit grant CRUD (백엔드) | ✅ |
| **P16-b** | **mobile BLE 무중단 핸드오프 — .mobileconfig 생성·설치 UI** | ⏳ **비콘 도착 후** |
| P17 | priority 기반 핸드오프 검증 (시뮬레이터) | ⏳ |
| P18 | 마지막 wifi_profile (fallback) 정책 | ⏳ |
| P19 | rate limit + audit log | ⏳ |

### 8.1 Feature flag (v1 비공개)
- `units` (방/구역 단위 grant) — DB 스키마는 있으나 UI 미노출
- `wifi_access_grant.target_type = 'user'` (개별 자격증명) — `credential_mode='individual'` UI 미노출
- v1 = 매장 단위 단일 자격증명 (`credential_mode='shared'`) 만

이유: 1차 출시 복잡성 최소화. 대형 리조트는 v2.

## 9. 측정 지표 (KPI)

| 지표 | 목표 (Phase 1) | 측정 방법 |
|---|---|---|
| 핸드셰이크 응답 시간 | ≤ 500ms (p95) | 백엔드 로그 |
| BLE 인식 → WiFi 연결 완료 | ≤ 3초 (평균) | mobile 자체 측정 |
| 핸드오프 끊김 시간 | ≤ 1초 (체감 0) | mobile WiFi 상태 모니터 |
| 핸드오프 성공률 | ≥ 95% | (성공 수) / (시도 수) |
| 최초 인증 후 재방문 시 자동 연결 성공률 | ≥ 99% | mobile 측정 |

⚠️ 실제 측정값은 Phase 1 P17 검증 이후 갱신.

## 10. 테스트 계획 — 비콘 통합 리허설 (월요일)

> 메모리 `project_next_week_sprint.md` 의 월요일 비콘 리허설.

### 시나리오 1: 단일 매장 단일 SSID
- 비콘 1개 + WiFi AP 1개
- 인식 → handshake → 연결 → 스탬프 적립
- ✅ 통과 기준

### 시나리오 2: 단일 매장 다중 SSID (2.4G + 5G)
- 비콘 1개 + WiFi AP 2개 (동일 비밀번호)
- handshake `wifis[]` 응답에 2개 반환
- mobileconfig/suggestion 둘 다 등록
- 사용자 이동 시뮬레이션 → OS 자동 핸드오프 확인

### 시나리오 3: 리조트 모의 (다중 비콘 + 다중 SSID)
- 비콘 3개 + WiFi AP 3개 (서로 다른 SSID)
- entry 비콘 인식 → 3개 SSID 한꺼번에 등록
- 비콘 → 비콘 이동 시 SSID 전환 확인
- 끊김 시간 측정

### 시나리오 4: 이상 케이스
- 비콘 inactive 상태 → 403
- 미등록 UUID → 404
- handshake 응답 후 mobileconfig 신뢰 거부 → 사용자 안내 UI
- Android suggestion 거부 → 재시도 UI

## 11. 보안 / 프라이버시

- **WiFi 비밀번호는 OS 키체인에 저장** — 앱이 직접 보관 X.
- **mobileconfig 안의 비밀번호는 평문** — HTTPS 다운로드 강제 + 설치 후 OS 가 암호화 저장.
- **사용자가 매장 탈퇴 시** — mobile 앱에서 등록한 suggestion 자동 회수 (Android `removeNetworkSuggestions`). iOS 는 사용자가 설정 앱에서 프로파일 삭제 안내.
- **WiFi 사용 로그** (`user_wifi_logs`) 는 사용자가 본인 데이터 다운로드 / 삭제 가능 (GDPR / 개인정보보호법).

## 12. 위험 / 미해결 사항

- [ ] iOS `.mobileconfig` 사용자 신뢰 단계 — UX 마찰. 대안 검토 (앱 내 안내 영상).
- [ ] Android 12+ 백그라운드 BLE 스캔 제약 — Phase 2 에서 Foreground Service + 알림 표시 검토.
- [ ] WiFi 비밀번호 평문 응답 vs grant 토큰 발급 — Phase 2 결정 시점.
- [ ] 802.11r/k/v 미지원 AP 에서 BSSID 다를 시 OS 가 항상 가장 강한 SSID 잡지 않는 경우 — 사용자 경험 측정 필요.
- [ ] `feature flag` 토글 메커니즘 (백엔드 → mobile 동적 푸시?).

## 13. 향후 (v2 이후)

- **MDM 통합** — 호텔/리조트 사업자가 객실 단위 mobileconfig 자동 푸시
- **WPA3-Enterprise** — 대형 사업자 대상 RADIUS 인증
- **사전 다운로드 / 오프라인 캐시** — 비콘 인식 전에 mobileconfig 미리 발급
- **다국적 사업자** — `country` 컬럼 활용한 regulatory 자동 적용
