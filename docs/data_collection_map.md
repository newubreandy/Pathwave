# PathWave 데이터 수집 맵 (Apple App Privacy + Google Data Safety 정답지)

> 콘솔 폼 작성용 정답지. xcprivacy 본문과 정렬되어 있음.
> 작성 근거: `mobile/ios/Runner/PrivacyInfo.xcprivacy`, `models/consent.py`, `routes/auth.py`, `routes/checkin.py` 등 코드 검증.

## 1. 수집 항목 × 목적 매트릭스 (콘솔 폼 직접 입력용)

| 데이터 종류 | 수집함? | 목적 (Apple 라벨) | 사용자 식별 연결 | 추적 사용 |
|---|---|---|---|---|
| 이메일 주소 | ✅ | App Functionality / 계정 식별 | Linked | No |
| 비밀번호(해시) | ✅ | App Functionality / 인증 | Linked | No |
| 이름 (선택) | ✅ | App Functionality / 프로필 | Linked | No |
| 전화번호 (점주) | ✅ | App Functionality / 매장 운영 | Linked | No |
| 출생연도 | ✅ | App Functionality / 연령 확인(만 14세 차단) | Linked | No |
| 정확한 위치 | ✅ | App Functionality / BLE 비콘 핸드셰이크 (WhenInUse) | Linked | No |
| 대략적 위치 | ✅ | App Functionality / 주변 매장 안내 | Linked | No |
| 사진 (선택) | ✅ | App Functionality / 프로필·매장 사진 | Linked | No |
| 디바이스 ID | ✅ | App Functionality / 푸시 토큰 (FCM) | Linked | No |
| 사용자 ID (앱 내) | ✅ | App Functionality / 계정 식별 | Linked | No |
| 결제 정보 | ✅ | App Functionality + Personalization / 구독 결제 | Linked | No |
| 1:1 매장 채팅 콘텐츠 | ✅ | App Functionality / 매장 응대 | Linked | No |
| 광고 ID (IDFA / GAID) | ❌ | — | — | — |
| 위치 기록(과거) | ❌ | — | — | — |
| 연락처 | ❌ | — | — | — |
| 검색 기록 | ❌ | — | — | — |
| 사용 데이터 (앱 내 인터랙션) | ❌ | — | — | — |
| 진단 데이터 (크래시) | ❌ (M4 후 추가 예정) | App Functionality / 운영 안정성 | Unlinked | No |
| 금융 정보(은행계좌·카드번호) | ❌ | (PG사 직접 처리, 우리 서버 미저장) | — | — |
| 건강·피트니스 | ❌ | — | — | — |
| 민감 정보 (인종·종교·정치 등) | ❌ | — | — | — |

→ **핵심 강점**: 광고 ID 미수집 + 추적 0건. Apple "App Tracking Transparency" 프롬프트 불필요. Google Data Safety "광고/마케팅 ID 수집 안 함" 명시.

## 2. 데이터 보존 기간 (개인정보처리방침 §3 과 동일)

| 항목 | 기간 | 근거 |
|---|---|---|
| 계약·청약철회·대금결제·재화공급 기록 | 5년 | 전자상거래법 |
| 소비자 불만·분쟁 처리 기록 | 3년 | 전자상거래법 |
| 표시·광고 기록 | 6개월 | 전자상거래법 |
| 로그인(접속) 기록 | 3개월 | 통신비밀보호법 |
| 부정이용·신고 처리 기록 | 6개월 | 정보통신망법 |
| 회원 탈퇴 후 채팅 본인 발신분 | 30일 후 익명화 + 30일 grace → 영구 삭제 | — |

## 3. 데이터 위탁 처리 (Google Data Safety "Shared with third parties")

| 수탁자 | 데이터 | 목적 |
|---|---|---|
| 결제대행(PG) — 토스페이먼츠 | 결제 정보(빌링키·승인번호 등, **카드번호는 수탁자가 직접 보관**) | 결제·정산·환불 |
| 클라우드 인프라 | 위 항목 전체 | 데이터 보관·서버 운영 |
| 이메일·SMS·푸시 | 이메일 / 푸시 토큰 / SMS | 인증 코드 · 알림 발송 |
| 기계 번역 (DeepL / Google) | 채팅·콘텐츠 텍스트 | 자동 번역 |
| Firebase (Google) | 푸시 토큰 / Auth ID 토큰 (검증만) | FCM 푸시 · 소셜 로그인 |

## 4. 보안 조치 (콘솔 폼 "Data is encrypted in transit" 등)

- 전송 구간: HTTPS / TLS 강제 (개발 클리어텍스트 허용 X)
- 저장 암호화:
  - 비밀번호: bcrypt 단방향 해시 (`routes/auth.py`, `routes/facility.py`)
  - WiFi 비밀번호: AES-256-GCM (`models/crypto.py` + `routes/beacon.py:364` + 신청 유닛 `wifi_password_enc`)
  - PG 빌링키(`billing_keys.pg_key`): AES-256-GCM (#230)
- 사용자 본인 데이터 열람·정정·삭제·반출 요청 가능 (인앱 설정 + privacy@pathwave.app).

## 5. 만 14세 미만 / 가족 정책

- 만 14세 미만 가입 거부 (`routes/auth.py:347` `classify_age`).
- 만 14~18세는 보호자 초대 코드 필수 (`routes/auth.py:369`).
- 광고 노출 0건 / 광고 ID 미수집 → Google Play Families 정책 충돌 없음(가족 카테고리 신청 시).

## 6. iOS Privacy Manifest (xcprivacy) Required-Reason API

```
NSPrivacyAccessedAPIType: UserDefaults     — 사용자 설정 저장
NSPrivacyAccessedAPIType: FileTimestamp    — 파일 메타데이터 조회
NSPrivacyAccessedAPIType: DiskSpace        — 디스크 용량 점검
NSPrivacyAccessedAPIType: SystemBootTime   — 앱 진단(세션 식별)
```

(파일: `mobile/ios/Runner/PrivacyInfo.xcprivacy`, `plutil -lint` OK)

---

## 콘솔 작성 시 주의

- Apple App Privacy: 데이터 항목 추가 시 **각각 별도 "Used for" 라벨 + "Linked to user" 여부 + "Used for tracking" 여부** 3가지 모두 선택.
- Google Data Safety: 위 매트릭스의 ❌ 항목은 명시적으로 "수집 안 함" 선택 → 강점 어필.
- 회원 탈퇴 후 30일 grace 정책 → "Data deletion request" 섹션에 명시.
