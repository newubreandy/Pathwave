# spec/data-architecture.md — 데이터 아키텍처

> **트랙**: 실제 개발 (`docs/internal/`) · 정교·상세
> **버전**: v0.1 (2026-05-26)
> **참조**: `architecture.md` §2, 메모리 `project_state_2026_05_06_provider_dark.md` (데이터 아키텍처 원칙)

---

## 1. 핵심 원칙 (사용자 직접 정의)

> **마스터 DB 는 슈퍼어드민만 보유. provider/mobile 은 read 인덱스(배치 delta sync) 만 접근. 환경/보안 완전 분리.**

이유:
- 사용자/매장 데이터 유출 위험 최소화 (provider 가 master 에 직접 쓰기 권한 보유 시 사고 영향 큼).
- provider/mobile 콘솔의 DB 사고가 마스터에 전파되지 않도록 격리.
- 슈퍼어드민이 정정/감사 전권 보유 (단일 진실).

## 2. 현재 상태 (2026-05-26)

⚠️ **원칙 vs 구현 갭** — 현재는 단일 마스터 DB 직접 접근 구조. read 인덱스 분리는 출시 후 Phase 2 로드맵.

| 항목 | 원칙 (목표) | 현재 구현 | 상태 |
|---|---|---|---|
| 마스터 DB 위치 | 슈퍼어드민 전용 서버 | 단일 `pathwave.db` (SQLite) | ⚠️ 단일 |
| provider read 인덱스 | 배치 delta sync 별도 DB | 마스터에 직접 read/write | ⚠️ 미분리 |
| mobile read 인덱스 | 배치 delta sync 별도 DB | 마스터에 직접 read | ⚠️ 미분리 |
| 환경 분리 | dev / staging / prod 3 단계 | dev (로컬) 만 | ⏳ 출시 직전 |
| 보안 격리 | 콘솔별 별도 자격증명 | 단일 JWT secret | ⏳ Phase 2 |

→ 출시 시점에 최소한 **prod / staging 환경 분리** 와 **콘솔별 API 토큰 분리** 는 적용해야 함.
→ read 인덱스 물리 분리는 매출 발생 후 클라우드 이전 시점.

## 3. 마스터 DB 현황 (`pathwave.db`)

- **엔진**: SQLite 3
- **위치**: `/Users/m5pro16/Desktop/pathwave/pathwave.db` (로컬 dev)
- **크기**: ~870 KB (2026-05-26 기준, 테스트 데이터 포함)
- **테이블 수**: 55
- **마이그레이션**: `models/database.py` 의 `init_db()` 가 idempotent schema 생성

### 3.1 테이블 도메인 분류 (55 개)

| 도메인 | 테이블 | 용도 |
|---|---|---|
| **인증/사용자** (8) | `users`, `phone_verifications`, `email_codes`, `consents`, `devices`, `push_tokens`, `notification_preferences`, `notification_blocklist` | 회원·기기·동의·푸시 |
| **시설(매장)** (6) | `facilities`, `facility_accounts`, `facility_images`, `facility_menu_items`, `facility_menu_uploads`, `facility_translations` | 1계정=1매장 + 다국어 |
| **비콘 / WiFi** (5) | `beacons`, `beacon_battery_history`, `beacon_wifi`, `wifi_profiles`, `wifi_access_grant`, `user_wifi_logs` | BLE 자산 + WiFi 토큰/로그 |
| **스탬프 / 쿠폰 / 즐겨찾기** (5) | `stamps`, `stamp_policies`, `coupons`, `user_favorites`, `store_categories` | 마케팅 + 카테고리 마스터 |
| **결제 / 정산 / 구독** (3) | `payments`, `billing_keys`, `service_subscriptions` | 토스 빌링키 + 정기결제 |
| **채팅 / 신고 / 차단** (6) | `chat_rooms`, `chat_messages`, `chat_message_translations`, `chat_blocks`, `abuse_reports`, `block` | 1:1 채팅 + 다국어 자동번역 + 신고 |
| **알림 / 공지** (5) | `notifications`, `notification_recipients`, `notification_quota`, `announcements`, `announcement_reads` | 푸시·인앱 알림 + 쿼터 |
| **고객지원** (5) | `support_tickets`, `support_messages`, `support_message_translations`, `support_categories`, `faqs` | 1:1 문의 + 다국어 |
| **직원 / 초대** (3) | `staff_accounts`, `staff_invitations`, `invitations` | 매장 직원 |
| **i18n** (2) | `translations`, `units` | 23개 언어 + 단위 |
| **약관 / 정책 / 회사 정보** (3) | `policies`, `company_info`, `app_versions` | 약관 버전·법인정보·앱강제업데이트 |
| **관리자 / AI 로그** (3) | `super_admin_accounts`, `admin_alert_dismissals`, `ai_usage_logs` | 슈퍼어드민 + AI 사용량 |
| **시스템** (1) | `sqlite_sequence` | SQLite 내부 |

총 55 (도메인 합계와 동일).

### 3.2 핵심 테이블 — 비콘 / WiFi (Phase 1 USP)

```
beacons (마스터 자산)
  ├ id, uuid, major, minor
  ├ facility_id (FK → facilities)
  ├ status (inventory / active / inactive / lost)
  ├ battery_level, last_seen_at
  └ created_at, updated_at

beacon_wifi (비콘 ↔ SSID 매핑)
  ├ beacon_id (FK)
  └ wifi_profile_id (FK → wifi_profiles)

wifi_profiles (SSID + 인증 정보)
  ├ id, ssid, security_type
  ├ facility_id (FK)
  └ (인증 토큰 발급 기준)

wifi_access_grant (사용자별 발급 토큰)
  ├ user_id, beacon_id, wifi_profile_id
  ├ token, issued_at, expires_at
  └ (Phase B 무중단 핸드오프 시 다건 발급)

user_wifi_logs (감사용)
  └ user_id, beacon_id, action, timestamp
```

자세히: [`beacon-protocol.md`](beacon-protocol.md), [`wifi-roaming.md`](wifi-roaming.md)

### 3.3 i18n 핵심 — `translations` 테이블

```
translations
  ├ key (예: 'common.login', 'mobile.beacon.connecting')
  ├ lang (ko, en, zh-CN, ja, zh-TW, vi, th, tl, id, ms ...)
  ├ value
  ├ source ('manual' / 'deepl' / 'imported')
  └ updated_at

UNIQUE(key, lang)
```

- API: `GET /api/i18n/{lang}` → 모든 key:value 페이로드
- DeepL 1회 번역 후 캐시 (비용 최소화)
- 자세히: [`i18n-strategy.md`](i18n-strategy.md)

## 4. 백엔드 라우트 (`routes/`) — 30+ 블루프린트

| 모듈 | 엔드포인트 prefix | 용도 |
|---|---|---|
| `auth.py` | `/api/auth/*` | JWT 로그인·가입·forgot-password |
| `users.py` (`users/` 추정) | `/api/users/*` | 사용자 프로필 |
| `facility.py` | `/api/facilities/*` + admin | 매장 등록·수정·승인 |
| `beacon.py` | `/api/beacons/*` + admin | 비콘 자산 + claim + 핸드셰이크 |
| `wifi` (beacon.py 내) | `/api/wifi/*` | WiFi 인증 토큰 발급 |
| `categories.py` | `/api/categories` (공개) + `/api/admin/categories` | 카테고리 마스터 |
| `coupon.py` | `/api/coupons/*` | 쿠폰 (P2 가능) |
| `stamp.py` | `/api/stamps/*` | 스탬프 적립 |
| `chat.py` | `/api/chat/*` | 1:1 채팅 + 자동번역 |
| `notification.py` + `push.py` | `/api/notifications/*` | 인앱 + FCM |
| `notification_preferences.py` | `/api/notification-preferences/*` | 알림 분리 설정 |
| `support.py` | `/api/support/*` | 1:1 문의 + FAQ |
| `report.py` + `abuse_report.py` + `block.py` | `/api/reports/*` | 신고·차단 |
| `policy.py` | `/api/policies/*` | 약관 버전 관리 |
| `company_info.py` | `/api/company-info` | 법인 정보 footer |
| `i18n.py` | `/api/i18n/{lang}` | 다국어 페이로드 |
| `payment` (billing.py) | `/api/payments/*` + 빌링키 | 토스페이먼츠 |
| `staff.py` + `invitation.py` | `/api/staff/*` | 매장 직원 + 초대 |
| `social_kakao.py` + `social_naver.py` | `/api/auth/social/*` | 소셜 로그인 (본 단계 OOS) |
| `version.py` | `/api/version` | 앱 강제 업데이트 |
| `admin.py` | `/api/admin/*` | 슈퍼어드민 전용 |
| `search.py` | `/api/search/*` | 매장 검색 |
| `announcement.py` | `/api/announcements/*` | 공지 |
| `favorite.py` | `/api/favorites/*` | 즐겨찾기 |
| `menu.py` | `/api/menu/*` | 메뉴 자동 번역 |
| `faq.py` | `/api/faqs/*` | FAQ DB |

총 ≥30 블루프린트.

### 4.1 권한 데코레이터 (`routes/auth.py`)

- `@require_login()` — 일반 사용자 JWT 검증
- `@require_facility_owner()` — provider (1계정=1매장)
- `@require_super_admin()` — 슈퍼어드민
- `@require_staff()` — 매장 직원

모든 admin 엔드포인트는 `@require_super_admin()` 강제.

## 5. 데이터 격리 로드맵

### Phase 1 (현재 — 출시 전)
- 단일 SQLite `pathwave.db`
- 권한 분리 = 데코레이터 + JWT role
- ⚠️ 같은 process / 같은 file → DB 사고 영향 큼

### Phase 2 (출시 직후 — 클라우드 이전)
- **단일 DB 유지 + 환경 3 분리** (dev / staging / prod)
- Postgres / Supabase 이전 검토 (SQLite 성능 한계 시)
- **콘솔별 API 토큰 분리** (JWT secret 3개 — mobile / provider / admin)

### Phase 3 (매출 발생 후 — MAU 1만+)
- **read 인덱스 물리 분리**
  - 마스터 (writer) = 슈퍼어드민 전용
  - mobile read replica = 사용자 조회 전용
  - provider read replica = SP 조회 전용
  - 배치 delta sync (5분~15분 주기)
- **이벤트 큐** (Kafka / SQS) — write 이벤트 전파
- **콘솔별 별도 자격증명 + IP allowlist**

## 6. 백업 / 감사 / 정정

### 6.1 백업
- 현재: 수동 `cp pathwave.db pathwave.db.bak`
- Phase 2: Litestream / 정기 클라우드 백업 (1시간 주기 + 일간 스냅샷)
- Phase 3: read replica + WAL 백업

### 6.2 감사 로그
- `user_wifi_logs`, `ai_usage_logs` 등 일부 감사 테이블 존재
- ⚠️ 통합 audit log 테이블 없음 — Phase 2 신설 필요 (`audit_logs`)
- 추적 대상: admin 의 매장 승인·정산 처리·계정 정지·약관 수정 등

### 6.3 정정 (사용자 데이터 수정)
- 슈퍼어드민만 가능
- 모든 정정은 audit log 에 기록 (Phase 2)

## 7. 보안 고려사항

| 항목 | 현재 | 출시 전 필수 |
|---|---|---|
| JWT secret | 단일 (`.env`) | 콘솔별 분리 + 정기 rotation |
| DB 파일 권한 | `0644` | `0600` + 비루트 계정 |
| HTTPS | 로컬 http | Cloudflare Tunnel 또는 정식 인증서 |
| Rate limit | 없음 | Flask-Limiter (auth / chat / search) |
| 비밀번호 해시 | bcrypt | 유지 |
| 개인정보 암호화 | 평문 | 출시 전 결제수단·전화번호 암호화 |
| Personal Identifiable Information 노출 | 일부 API | 슈퍼어드민 외 마스킹 |

## 8. 관련 PR / 문서

- 출시 마스터 플랜: `docs/pathwave_launch_master_plan_2026-05-20.md`
- Phase 1 계획: `docs/pathwave_phase1_plan_2026-05-21.md`
- 슈퍼어드민 작업 체크리스트: 메모리 `project_state_2026_05_06_provider_dark.md`
- 1계정 1매장 정책: 메모리 `project_account_store_policy.md`

## 9. TODO

- [ ] `audit_logs` 테이블 스키마 정의 (Phase 2)
- [ ] read replica delta sync 알고리즘 결정 (Phase 3)
- [ ] 콘솔별 JWT secret rotation 자동화 (Phase 2)
- [ ] 결제수단·전화번호 암호화 (출시 전 필수)
- [ ] Litestream 또는 동등 백업 도구 평가 (출시 직전)
