# PathWave — PROJECT_CONTEXT

> **이 파일의 목적**
> 새 대화 세션에서 컨텍스트를 빠르게 복원하기 위한 단일 진실 소스(SSoT).
> 한 줄만 던지면 됩니다 → "PROJECT_CONTEXT.md 읽고 이어서 다음 단계 진행해줘"
>
> **업데이트 규칙:** 각 PR 머지 시 4번(진행 현황) + 관련 섹션을 같은 PR에서 함께 수정.
> main 브랜치가 항상 "현재 상태의 진실"이 되도록 유지.

---

## 1. 한 줄 소개

**PathWave** = BLE 비콘(FSC-BP108B) 기반 매장 통합 SaaS.
앱 사용자가 매장에 들어오면 자동으로 ① WiFi 자동 연결 ② 스탬프 적립 ③ 쿠폰 발급이 트리거되고, 사장님은 시설/직원/스탬프/쿠폰/리포트를 관리, PathWave 운영자는 비콘 입고와 가입 승인을 처리합니다.

- **개발자:** 1인 초보 개발자 (개인사업자)
- **목표 런칭:** 2026년 5월 (법인 등록 후)
- **현재 단계:** 백엔드 27 PR 머지 완료, Flutter 앱 + Provider Web 진행 중

---

## 2. 기술 스택

| 영역 | 기술 |
|---|---|
| **백엔드** | Python 3, Flask + Blueprint (13 모듈), SQLite + 멱등 마이그레이션 |
| **인증** | bcrypt + JWT (sub_type, role, kind 클레임) |
| **암호화** | AES-256-GCM (WiFi 비밀번호) |
| **모바일 앱 (User)** | Flutter (`mobile/`) — Phase 3 진행 중 |
| **사장님/직원 포털** | React + Vite (`provider-web/`) — UI 진행 중 |
| **Super Admin 웹** | React + Vite (`admin-web/`) — PR #36 베이스라인 완료, 후속 PR 에서 페이지별 구현 |
| **외부 연동** | Stub ↔ Real 스위치: PG / FCM / Google Translate / SMTP |
| **실시간** | SSE (chat 폴링 푸시) |

---

## 3. 4개 페르소나 & 권한

| 페르소나 | sub_type | 가입/로그인 | 핵심 권한 |
|---|---|---|---|
| **익명 (Anonymous)** | 없음 | — | 시설 검색 / 공개 정보 조회만 |
| **앱 사용자 (User)** | `user` | 이메일+코드 OR 소셜(Firebase) | BLE 핸드셰이크, 스탬프 적립, 쿠폰 사용, 채팅 |
| **시설측 (Facility)** | `facility`(owner/admin) `staff` | 사업자번호+이메일 (운영자 승인 후) / 초대 수락 | 시설 CRUD, 스탬프/쿠폰 발급, 푸시, 리포트 |
| **PathWave 운영자 (Super Admin)** | `super_admin` | ENV 부트스트랩 + 추후 추가 | 비콘 입고, 사장 가입 승인, 결제/정산, 시스템 공지 |

> **권한 데코레이터** (routes/auth.py):
> `require_auth(sub_type=...)`, `require_facility_actor(roles=...)`, `require_super_admin(roles=...)`
> 잘못된 sub_type 토큰 → 401 (강제 격리)

---

## 4. 진행 현황 — PR 체크리스트

### ✅ 머지 완료 (#1 ~ #27)

| # | 제목 | 영역 |
|---|---|---|
| 1~9 | 보안/SRS 기반 정비 | auth, validation |
| 10 | 시설(Facility) CRUD | store |
| 11 | 시설 검색 / 자동완성 | search |
| 12 | 시설 이미지 업로드 | store |
| 13 | 시설 전화/영업시간 | store |
| 14 | 다국어 번역 (Stub/Google) | facility/translations |
| 15 | 직원(Staff) 시스템 + 초대 | staff |
| 16 | 스탬프 발급/사용 | stamp |
| 17 | 쿠폰 발급/리딤 | coupon |
| 18 | BLE 자동 스탬프 흐름 | beacon → stamp |
| 19 | 자동 쿠폰 보상 트리거 | stamp → coupon |
| 20 | 알림(Notification) DB | notification |
| 21 | 푸시(FCM/Stub) | push |
| 22 | 1:1 채팅 (SSE) | chat |
| 23 | 매출/리포트 | report, billing |
| **24** | **Super Admin 인증 (login/me/refresh)** | admin |
| **25** | **비콘 인벤토리 + claim-beacon** | admin, beacon, store |
| **26** | **사장 가입 승인 흐름 (verified=0 → admin verify)** | admin, facility |
| **27** | **대시보드 stats + 전체 결제/구독 관리** | admin |
| **28** | **PROJECT_CONTEXT.md 신설** | docs |
| **29** | **와이파이 초대 + 회원 폐쇄형 가입** | invitation, auth |
| **30** | **Provider Web 베이스라인 (16페이지) + 인증 API 연동** | provider-web |
| **31** | **Provider Web — 매장/스탬프/쿠폰 도메인 API 연동** | provider-web/services |
| **32** | **Provider Web — 직원/와이파이/푸시/채팅 API 연동** | provider-web/services |
| **33** | **시스템 공지 (Super Admin → 사장/사용자) 백엔드** | announcement, admin |
| **34** | **비콘 배터리 모니터링 백엔드** | beacon, admin |
| **35** | **🔒 보안 블로커 — SECRET_KEY/AES_KEY ENV 강제 + CORS 화이트리스트 + rate-limit** | app, auth, facility, staff, admin, beacon |
| **36** | **🛡️ Super Admin Web UI 베이스라인 (Vite + React 19) — Login + 대시보드 + 4 placeholder** | admin-web/ (신규 폴더) |
| **37** | **🔌 Admin Web — Beacons 인벤토리 + Approvals + 통계 키 매칭 수정** | admin-web/pages/Beacons, Approvals + Modal |
| **38** | **🔋 Admin Web — Battery 모니터링 + 시스템 공지 CRUD + 실제 푸시 발송 통합** | admin-web/pages/Battery, Announcements + announcement.py push_to_users |
| **39** | **💳 Admin Web — 결제·구독 관리 + 환불 (Payments 페이지 신설)** | admin-web/pages/Payments (탭 2개) |
| **40** | **📱 Mobile App — 컴파일 가능한 골격 + 인증 동선 + 14개 화면 (실+stub)** | mobile/lib/screens (14) + api_client + ApiConfig |
| **41** | **🚀 운영 전환 — PG/Email provider 추상화 + gunicorn/Procfile + Sentry** | models/payment_provider.py, models/email_provider.py, wsgi.py, gunicorn.conf.py, Procfile |
| **42** | **📱 Mobile API services — 6개 도메인 dart 모듈 + SSE 스트림 + Push 토큰 등록** | mobile/lib/services/{store,stamp,coupon,notification,chat,push}_service.dart |
| **43** | **🎫 Mobile — Stamps + Coupons + Notifications 실 구현** | screens/mypage/{stamps,coupons}.dart, screens/notifications/notifications.dart, widgets/empty_state.dart |
| **44** | **🔎 Mobile — 시설 검색 (위치 기반) + 시설 상세** | screens/search/search_screen.dart, screens/facility/facility_screen.dart |
| **45** | **🔐 회원가입 동의 시스템 — 9개 항목 + DB + 정책 본문 (트리거소프트)** | consents 테이블, models/consent.py, routes/policy.py, static/policies/*.ko.md (9), mobile/screens/auth/consent_screen.dart, provider-web/components/ConsentSection |
| **46** | **📝 약관/정책 변경 관리 — DB 버전링 + MDXEditor + 이메일 공지 + 이전 버전 보기** | policies 테이블, models/policy_store.py, routes/policy.py 확장, admin-web/pages/Policies, admin-web/components/PolicyEditor, mobile + provider-web 버전 드롭다운 |
| **47** | **🔞 연령 분류 + 부모 초대 + 미성년자 시설 제한** | users.{birth_year,age_group,parent_invitation_id} + facilities.adult_only + invitations.{is_minor_invite,inviter_liability_accepted_at} + 부모 초대 라우트 + 핸드셰이크/검색 자동 필터 + 모바일 5단계 가입 + 자녀 초대 화면 |
| **48** | **💬 Mobile — 채팅 목록 + 상세 (SSE 실시간)** | screens/chat/{chat_list,chat_detail}_screen.dart, ChatService SSE 스트림 통합 + 메시지 입력 + 낙관적 UI |

**누적 통계:** 48 PR · 17 blueprint · ~117 API endpoint · 29 DB 테이블 · 백엔드 ~7,400 LOC + admin-web 9페이지 + mobile 17화면 + provider-web

### ⬜ 후보 (다음 작업)

| # | 제목 | 메모 |
|---|---|---|
| 49 | **Mobile — WiFi 자동 가입 native plugin** | Android SuggestNetwork + iOS NEHotspotConfiguration |
| 50 | **APNs Push Provider (iOS native)** | models/push.py |
| 51 | **PostgreSQL 이전** | 10K 동시접속 SRS 요건 |

---

## 5. API 엔드포인트 지도 (13 Blueprint)

| Blueprint | Prefix | 주요 엔드포인트 |
|---|---|---|
| `auth_bp` | `/api/auth` | send-code, verify-code, register, login, refresh, social-login (Firebase) |
| `facility_bp` | `/api/facility` | send-code, verify-code, register, login, me (사장 가입/로그인) |
| `staff_bp` | `/api/staff` | invite, accept, login, list (직원 관리) |
| `store_bp` | `/api/facilities` | CRUD, images, hours, translate, claim-beacon |
| `search_bp` | `/api/search` | facilities (검색 + 자동완성) |
| `beacon_bp` | `/api/beacon` | handshake (사용자), register (super_admin only), nearby, `<id>/battery` 보고 |
| `stamp_bp` | `/api/stamps` | issue, list, redeem, auto (BLE 트리거) |
| `coupon_bp` | `/api/coupons` | issue, list, redeem, auto (스탬프 보상) |
| `notification_bp` | `/api/notifications` | list, mark-read, settings |
| `push_bp` | `/api/push` | register-token, send (Stub/FCM) |
| `chat_bp` | `/api/chat` | rooms, messages, sse-stream |
| `billing_bp` | `/api/billing` | charge (sim PG), invoices, subscription |
| `report_bp` | `/api/reports` | sales, stamps, coupons (집계) |
| `admin_bp` | `/api/admin` | login, beacons (import/list/assign), facility-accounts (verify/suspend), stats/overview, payments (refund), subscriptions |
| `invitation_bp` | `/api/invitations` | POST 발급, GET 목록, GET `<code>` 검증 (회원 폐쇄형 가입) |
| `announcement_bp` | `/api/admin/announcements`, `/api/announcements` | 운영자 공지 CRUD + 사용자 측 audience 필터 + 읽음 처리 |

---

## 6. DB 테이블 23개 요약

**계정/인증 + 초대 (6)** — `users`, `facility_accounts`, `staff_accounts`, `super_admin_accounts`, `email_codes`, `invitations`
**비콘/시설 (5)** — `beacons`, `facilities`, `facility_images`, `facility_hours`, `facility_translations`
**스탬프/쿠폰 (4)** — `stamp_cards`, `stamps`, `coupons`, `coupon_redemptions`
**알림/푸시/채팅 (5)** — `notifications`, `notification_settings`, `push_tokens`, `chat_rooms`, `chat_messages`
**결제/구독 (3)** — `payments`, `subscriptions`, `invoices`
**리포트 (1)** — `sales_daily`

**마이그레이션 패턴:** [models/database.py](models/database.py) — `_add_column_if_missing(db, table, col, ddl)` + `_bootstrap_super_admin()` (ENV 기반).

---

## 7. 핵심 흐름 시나리오 (재검증용)

```
[Super Admin]
 1. /api/admin/beacons/import (CSV 또는 SN 배열) → status='inventory'
 2. 사장 가입 신청 들어오면 /api/admin/facility-accounts/<id>/verify

[사장 (Facility owner)]
 3. /api/facility/register (verified=0, status='pending')
 4. 운영자 승인 후 /api/facility/login → 토큰 발급
 5. /api/facilities (시설 생성) → /api/facilities/<fid>/claim-beacon (SN 입력 → 비콘 할당)

[앱 사용자 (User)]
 6. BLE로 비콘 감지 → /api/beacon/handshake (uuid+major+minor)
 7. 응답: WiFi SSID/password (AES 복호화) + 자동 스탬프 1개 적립
 8. N개 누적 시 자동 쿠폰 발급 → 푸시 알림
 9. 매장 방문 시 직원이 /api/coupons/redeem 으로 사용 처리
```

---

## 8. 환경 변수 & 프로바이더 스위치

| 변수 | Stub (개발) | Real (운영) |
|---|---|---|
| `PATHWAVE_ENV` | `development` (기본) | `production` (필수 — ENV 검증 발동) |
| `PG_PROVIDER` | `sim` (sim-prefix 토큰) | `toss` (Toss Payments) |
| `TOSS_SECRET_KEY` | — | `test_sk_xxxxx` 또는 `live_sk_xxxxx` |
| `EMAIL_PROVIDER` | `console` (stdout) | `smtp` / `ses` / `sendgrid` |
| `SENDGRID_API_KEY` | — | `SG.xxxxx` (sendgrid 시) |
| `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | — | SES 사용 시 (boto3) |
| `EMAIL_FROM` | — | 발신 주소 (모든 provider 공통) |
| `PUSH_PROVIDER` | `stub` (로그만) | `fcm` (Firebase Service Account JSON) |
| `TRANSLATION_PROVIDER` | `stub` ([ko]→[en] 더미) | `google` (API key) |
| `SECRET_KEY` | (개발 기본값 허용) | **운영: 필수, dev 기본값 금지** |
| `PATHWAVE_AES_KEY` | (없으면 SECRET_KEY 파생) | **운영: 32바이트 base64 필수** |
| `CORS_ORIGINS` | (없으면 전체 허용) | **운영: 콤마 구분 화이트리스트 필수** |
| `SENTRY_DSN` | (미설정 → no-op) | Sentry 운영 DSN |
| `SUPER_ADMIN_BOOTSTRAP_EMAIL` | — | 첫 super admin 자동 생성용 |

> **PR #35 보안 블로커:** `PATHWAVE_ENV=production` 일 때 `SECRET_KEY`/`PATHWAVE_AES_KEY`/`CORS_ORIGINS` 누락 시 부팅 단계에서 `RuntimeError` 발생.
> Rate-limit: `/api/auth/send-code` (5/분), `/api/*/login` (10/분), `/api/beacon/handshake` (60/분).

> Firebase credentials, `google-services.json`, `GoogleService-Info.plist`은 `.gitignore` 처리됨 (커밋 금지).

---

## 9. 로컬 실행 / 테스트

```bash
# 백엔드 (개발)
cd /Users/m5pro16/Desktop/pathwave
python3 app.py            # http://localhost:8080

# 백엔드 (운영) — gunicorn + WSGI
gunicorn -c gunicorn.conf.py wsgi:app

# Flutter 앱 (Phase 3 진행 중)
cd mobile && flutter run

# Provider Web (사장/직원 포털, UI 빌드 진행 중)
cd provider-web && npm run dev      # http://localhost:5173

# Admin Web (운영자 콘솔, PR #36 베이스라인)
cd admin-web && npm install && npm run dev   # http://localhost:5174
```

각 PR 머지 직전에 수행한 시나리오 테스트는 해당 PR description의 **"Test Plan"** 섹션에 체크리스트 형식으로 보존되어 있음 (GitHub PR 페이지에서 영구 조회 가능).

---

## 10. 다음 작업 후보 (사용자 선택)

1. **PR #28 — 시스템 공지**: super_admin → 사장/사용자 일괄 공지 + 푸시
2. **PR #29 — Provider Web UI**: 사장님/직원 React 페이지 본격 빌드
3. **PR #30 — Super Admin Web UI**: 운영자 콘솔 (비콘 입고, 가입 승인, 결제 관리)
4. **서버 배포 + 리얼 키 검증**: PG / FCM / Google Translate 실 연동 후 시나리오 재검증

---

## 11. 업데이트 규칙

- 각 PR을 머지할 때 **그 PR 안에서** 본 파일도 같이 수정 (4번 체크리스트 + 영향 받은 섹션).
- 새 blueprint/테이블/엔드포인트가 생기면 5/6번에 반드시 추가.
- 환경 변수 추가 시 8번에 반영.
- 데스크탑 로컬 폴더 (`/Users/m5pro16/Desktop/pathwave`)는 `git pull origin main`으로 동기화 가능.

---

**마지막 업데이트:** 2026-05-05 (PR #48 — Mobile 채팅 목록 + 상세 SSE 실시간)
