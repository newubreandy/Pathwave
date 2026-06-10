# PathWave — 3 콘솔 상세 기능정의서 + 인프라/환경 상세

> **버전**: v1.0 (2026-06-05)
> **참조**: 종합본 = `pathwave_feature_spec_2026-06-05.md`
> **출처**: 본 문서는 실제 구현된 코드(routes/, screens/, pages/, database.py, .env.example)에서 직접 추출됨. 추론 없음.

---

## 1. mobile (사용자 앱) — Flutter

`lib/screens/` 9 디렉토리. 모든 화면은 `PwAppBar` + `SeasonalBackground` 위에 글래스 카드 구조 (디자인 가이드).

### 1-1. auth/ (인증)

| 화면 | 파일 | 기능 |
|---|---|---|
| 로그인 | `login_screen.dart` | 이메일+비밀번호, SNS 5종 (Google/Apple/Facebook/Kakao/Naver), 비번 찾기, 회원가입, "로그인 없이 둘러보기" |
| 회원가입 | `register_screen.dart` | 단계형 (방법 선택 → 이메일 인증 → 정책 동의 → 프로필 → 완료) |
| 비밀번호 찾기 | `forgot_password_screen.dart` | 이메일 입력 → 인증 코드 → 새 비밀번호 |
| 정책 동의 | `consent_screen.dart` | 가입 마지막 단계, 필수+선택 항목 |

### 1-2. home/ (홈 탭)

| 화면 | 파일 | 기능 |
|---|---|---|
| 홈 (탭 컨테이너) | `home_screen.dart` | 4 탭: 홈 / 검색 / 마이 / 알림. BLE 스캔 상태, "비콘 미감지", WiFi 발견 배너 |
| WiFi 자동 연결 | `wifi_connect_screen.dart` | 비콘 감지 시 자동 진입. mobileconfig 설치 안내 |

### 1-3. search/ (검색 탭)

| 화면 | 파일 | 기능 |
|---|---|---|
| 매장 검색 | `search_screen.dart` | 키워드/주소/거리(geolocator) 정렬, 즐겨찾기 토글 |

### 1-4. facility/ (매장 상세)

| 화면 | 파일 | 기능 |
|---|---|---|
| 매장 상세 | `facility_screen.dart` | 이미지 슬라이드, 메뉴(번역), 정보, 즐겨찾기, 채팅 진입, WiFi 자동 연결 |

### 1-5. mypage/ (마이 탭)

| 화면 | 파일 | 기능 |
|---|---|---|
| 마이페이지 | `home_screen.dart::_MyPageTab` | 프로필, 메뉴 9개 통합 글래스 박스 |
| 내 회원 QR | `member_qr_screen.dart` | 60초 만료 QR. 점주 스캔 → 스탬프/쿠폰 자동 |
| 내 스탬프 | `stamps_screen.dart` (메모리) | 매장별 적립 현황, 매장 클릭 → 상세 |
| 내 쿠폰 | `coupons_screen.dart` | 탭(사용가능/사용완료/만료), 쿠폰 사용 확인 다이얼로그 |
| 즐겨찾기 | `favorites_screen.dart` | 매장 카드 리스트, 하트 토글 |
| 자녀 초대 | `parent_invite_screen.dart` | 법적 책임 동의 체크박스 + 자녀 이메일 + 코드 발급 |
| 친구 초대 | `friend_invite_qr_screen.dart` | QR/링크 공유, 가입 보상 hook |
| 회원 탈퇴 | `delete_account_screen.dart` | 비밀번호 확인 + 즉시 처리 + 14일 후 재가입 가능 |

### 1-6. chat/ (매장 채팅)

| 화면 | 파일 | 기능 |
|---|---|---|
| 채팅 목록 | `chat_list_screen.dart` | 매장별 1:1 채팅방 리스트 |
| 채팅 상세 | `chat_detail_screen.dart` | 메시지(자동번역, P8b), 매장 신고/차단 메뉴 |

### 1-7. notifications/ (알림 탭)

| 화면 | 파일 | 기능 |
|---|---|---|
| 알림 (탭) | `home_screen.dart::_NotificationsTab` | "최근 알림" 글래스 카드 + 전체 알림 보기 |
| 알림 목록 | `notifications_screen.dart` | 인박스(개인) / 공지(시스템) 2 탭, 읽음 처리 |

### 1-8. settings/ (설정)

| 화면 | 파일 | 기능 |
|---|---|---|
| 설정 | `settings_screen.dart` | 계정/알림/고객지원/서버/약관 섹션 |
| 비밀번호 변경 | `change_password_screen.dart` | 현재 + 새 비번 |
| 차단 목록 | `blocked_facilities_screen.dart` | 차단 매장 리스트 + 해제 |
| 정책 보기 | `policy_view_screen.dart` | 약관/개인정보/위치기반 등 본문 |
| 마케팅 동의 토글 | `_MarketingConsentToggleTile` | SharedPreferences 저장 |
| 알림 카테고리 | `_NotificationPreferencesSection` | 카테고리별 ON/OFF |

### 1-9. support/ (고객센터)

| 화면 | 파일 | 기능 |
|---|---|---|
| 고객센터 | `support_screen.dart` | 3 탭: FAQ / 내 문의 / 신고하기 |
| FAQ | (탭 1) | 카테고리별 (account/connectivity/쿠폰 등) Q&A, 검색 |
| 내 문의 | (탭 2) | 영업시간 안내 + 문의 작성 (PwSheet) + 내 티켓 리스트 |
| 신고하기 | (탭 3) | 시설 검색 → 확인 다이얼로그 → 사유 라디오 + 첨부 사진 3장 + 상세 |
| 문의 작성 시트 | `_CreateTicketSheet` | 카테고리 + 제목 + 내용 + 첨부 |
| 문의 상세 | `support_detail_screen.dart` | 운영자와 1:1 대화 |

### 1-10. splash_screen.dart

| 기능 | — |
|---|---|
| 초기 부팅 — AuthService 토큰 로딩 + 버전 강제/권장 업데이트 체크 (`routes/version`) → 로그인/홈 분기 |

---

## 2. provider-web (시설 사장) — React

`src/pages/` 25 페이지.

### 2-1. 인증

| 페이지 | 파일 | 기능 |
|---|---|---|
| 로그인 | `Login.jsx` | 이메일+비번, 비번 찾기 |
| 회원가입 | `Signup.jsx` | 사업자등록증 업로드 + 매장 기본 정보 + 약관 |
| 비번 찾기 | `ForgotPassword.jsx` | 이메일 인증 |

### 2-2. 메인

| 페이지 | 파일 | 기능 |
|---|---|---|
| 대시보드 | `Dashboard.jsx` | 매장 현황, 오늘 방문, 스탬프/쿠폰 발급 통계 |
| 매장 정보 | `StoreInfo.jsx` | 이름, 주소, 영업시간, 카테고리, 사진, 비콘 ID |
| 매장 다국어 (제거 예정) | `StoreTranslations.jsx` | 메모리 정책: provider 단일 언어, 슈퍼어드민이 매장별 다국어 관리 (Phase 2+) |
| WiFi 설정 | `WifiSettings.jsx` | SSID + 비밀번호 (AES 암호화) + 등록 비콘 |
| 메뉴 관리 | `MenuManagement.jsx` | 메뉴 항목 CRUD, 디바이스 OCR 사진 업로드 → 자동 번역 |

### 2-3. 운영

| 페이지 | 파일 | 기능 |
|---|---|---|
| 회원 체크인 | `MemberCheckin.jsx` | 회원 QR 스캔 → 스탬프/쿠폰 자동 적용 |
| 회원 프로필 | `MemberProfile.jsx` | 체크인 후 회원 정보 확인 |
| 스탬프 정책 | `Stamps.jsx` + `StampForm.jsx` | 적립 단위, 보상 조건, BLE 자동 스탬프 ON/OFF |
| 쿠폰 발급 | `Coupons.jsx` + `CouponForm.jsx` | 쿠폰 CRUD, 발급 대상, 유효기간 |
| 고객 채팅 | `CustomerChat.jsx` | 회원과 1:1, 자동 번역 |
| 알림 발송 | `Notifications.jsx` | 공지/이벤트 푸시. 알림 부가서비스 quota 차감 |

### 2-4. 결제·구독

| 페이지 | 파일 | 기능 |
|---|---|---|
| 결제 관리 | `PaymentManagement.jsx` | 카드 등록(빌링키), 결제 내역 |
| 구독 | `Subscriptions.jsx` | 서비스 신청(비콘, 알림 등), 월/연 단위, 자동 갱신 |

### 2-5. 직원

| 페이지 | 파일 | 기능 |
|---|---|---|
| 직원 관리 | `StaffManagement.jsx` | 직원 초대, 역할(matre/staff), 권한 분리 |

### 2-6. 부가

| 페이지 | 파일 | 기능 |
|---|---|---|
| 시설 (매장 다중 — 정책상 1매장) | `Facilities.jsx` | 1계정 1매장 정책 (메모리). 향후 확장 hook |
| 서비스 신청 | `ServiceRequest.jsx` | 비콘 등 서비스 신청, 신청 → 어드민 승인 → 비콘 매칭 → 발송 |
| 고객지원 | `Support.jsx` | FAQ / 내 문의 / 신고 |
| 약관 보기 | `PolicyView.jsx` | 정책 본문 |
| 설정 | `Settings.jsx` | 비번 변경, 알림 설정, 계정 |

---

## 3. admin-web (슈퍼어드민) — React

`src/pages/` 28 페이지. LNB 5 그룹: 메인 / 운영 / 결제·정책 / 고객지원 / 시스템.

### 3-1. 메인 그룹

| 페이지 | 파일 | 기능 |
|---|---|---|
| 대시보드 | `Dashboard.jsx` | 매장/사용자/매출/알림 KPI |
| 비콘 | `Beacons.jsx` | 비콘 입고(CSV), 매장 배정, 상태(inventory→active→inactive/lost) |
| 서비스 신청 | `ServiceRequests.jsx` | provider 의 비콘 신청 → 매칭 → 발송 단계 |
| 사장 가입 승인 | `Approvals.jsx` | facility_accounts 의 verified=0 → 1 승인 |

### 3-2. 운영 그룹

| 페이지 | 파일 | 기능 |
|---|---|---|
| 배터리 모니터링 | `Battery.jsx` | 비콘 배터리 상태, low_threshold 알림 |
| 시스템 공지 | `Announcements.jsx` | audience(all/users/facilities/staff) 별 공지 작성, 푸시 발송 |
| 알림 검토 | `Notifications.jsx` | provider 가 보낸 알림 검토(차단어 블록리스트) |
| 회원 관리 | `Users.jsx` | 사용자 리스트, 강제 탈퇴 |
| 직원 모니터 | `StaffMonitor.jsx` | provider 의 직원 리스트, 활동 로그 |
| 채팅 모니터 | `ChatMonitor.jsx` | 매장 채팅 검토 (신고 처리 보조) |
| 신고 처리 | `AbuseReports.jsx` | 사용자/매장 신고 큐, 검토, 조치 |

### 3-3. 결제·정책 그룹

| 페이지 | 파일 | 기능 |
|---|---|---|
| 결제 내역 | `Payments.jsx` | 전체 결제 내역, 환불 처리, **gateway/fallback_from 표시** (이번 PR 추가) |
| 약관/정책 | `Policies.jsx` | 약관(8 종) ko+en 동시 등록, 버전 관리, 동의 푸시 발송 |
| 쿠폰 통계 | `CouponStats.jsx` | 발급/사용/만료 통계 |

### 3-4. 고객지원 그룹

| 페이지 | 파일 | 기능 |
|---|---|---|
| 고객지원 | `Support.jsx` | 1:1 문의 큐, 답변 |
| FAQ | `Faq.jsx` | FAQ CRUD, 카테고리, 언어별 |
| 지원 통계 | `SupportStats.jsx` | 응답 시간, 카테고리별 통계 |

### 3-5. 시스템 그룹

| 페이지 | 파일 | 기능 |
|---|---|---|
| 법인 정보 | `CompanyInfo.jsx` | 3 콘솔 footer 자동 동기 (사업자번호/통신판매업/위치기반/주소 등) |
| 업종 카테고리 | `Categories.jsx` | 국세청 100대 생활업종 시드 + CRUD |
| 앱 버전 | `AppVersions.jsx` | iOS/Android 강제 + 권장 업데이트 |
| 시스템 점검 | `SystemHealth.jsx` | 외부 의존(PG/이메일/푸시) health 체크 |
| AI 비용 모니터 | `CostMonitor.jsx` | DeepL/Claude/Vision 등 사용량 + 임계점(50/80/100) 알림 |
| 앱 배경 테마 | `Themes.jsx` | 시즌별(spring/summer/autumn/winter) + 이벤트 배경 이미지 등록, 활성화, 무재배포 운영 |
| 다국어 번역 | `Translations.jsx` | DB 기반 i18n 키 + 23 언어, DeepL 자동, 사람 검수 |

### 3-6. 인증

| 페이지 | 파일 | 기능 |
|---|---|---|
| 로그인 | `Login.jsx` | 슈퍼어드민 전용, JWT |

---

## 4. backend API — Flask (34 라우트)

`routes/` 디렉토리. 각 라우트는 자체 Blueprint + `app.py` 에 등록.

### 4-1. 인증/계정

| 라우트 | 기능 |
|---|---|
| `auth.py` | 일반 회원 인증 (이메일 가입/로그인/refresh). JWT 발급. sub_type='user' |
| `facility.py` | 시설 사장 가입/로그인. 사업자등록증 첨부. sub_type='facility' |
| `staff.py` | 직원 초대/관리. sub_type='staff' |
| `admin.py` | 슈퍼어드민 API. sub_type='super_admin' |
| `social_kakao.py` | Kakao OAuth 토큰 교환 |
| `social_naver.py` | Naver OAuth 토큰 교환 |

### 4-2. 매장/검색

| 라우트 | 기능 |
|---|---|
| `store.py` | 시설 CRUD (FR-STORE-001) |
| `search.py` | 매장 검색 + 좌표 기반 거리 정렬 (FR-STORE-002, Haversine) |
| `categories.py` | 업종 카테고리 — 공개 GET + admin CRUD |
| `favorite.py` | 사용자 즐겨찾기 |
| `block.py` | 사용자 → 시설 채팅 차단 |

### 4-3. 비콘/WiFi

| 라우트 | 기능 |
|---|---|
| `beacon.py` | 비콘 CRUD, CSV 입고, 매장 배정, 상태 전환 |
| `service_request.py` | 비콘 서비스 신청 (provider → admin → 발송) |
| `checkin.py` | 회원 QR 발급/검증 + 점주 스캔 처리 |

### 4-4. 스탬프/쿠폰

| 라우트 | 기능 |
|---|---|
| `stamp.py` | 스탬프 정책, BLE 자동 적립 (FR-STAMP-001/002) |
| `coupon.py` | 쿠폰 발급/사용 (FR-COUPON-001/002) |
| `invitation.py` | 초대 코드 (회원/매장/직원 발급, 친구·자녀 초대) |

### 4-5. 채팅/메뉴/번역

| 라우트 | 기능 |
|---|---|
| `chat.py` | 매장 1:1 채팅, 자동 번역 (P8b) |
| `menu.py` | 메뉴 항목 CRUD + OCR 결과 저장 + 자동 번역 캐시 (D-4-a) |
| `i18n.py` | DB 기반 23 언어 번역 키, GET /api/i18n/{lang} |

### 4-6. 알림/공지/신고

| 라우트 | 기능 |
|---|---|
| `notification.py` | 알림 발송 + quota 차감 (FR-NOTI-001/002) |
| `notification_preferences.py` | 카테고리별 ON/OFF |
| `push.py` | 푸시 토큰 등록/해제 (FCM/APNs) |
| `announcement.py` | 시스템 공지 — audience 별 발송 |
| `abuse_report.py` | 사용자/매장 신고, 첨부 사진 3장 (이번 변경) |
| `report.py` | 통계 리포트 |

### 4-7. 결제/구독

| 라우트 | 기능 |
|---|---|
| `billing.py` | 카드 등록 (빌링키), 구독 결제, 결제 내역. PG **fallback (제로페이→토스)** 적용 |

### 4-8. 정책/약관

| 라우트 | 기능 |
|---|---|
| `policy.py` | 약관 본문 + 동의 메타데이터 + 운영자 CRUD (PR #46, C-2-4) |
| `company_info.py` | 법인 정보 — 3 콘솔 footer 자동 동기 |
| `version.py` | 앱 버전 강제/권장 업데이트 체크 |

### 4-9. 고객지원

| 라우트 | 기능 |
|---|---|
| `support.py` | 고객센터 티켓 + 메시지 |
| `faq.py` | FAQ — 사용자/사장 분리, 언어별 |

### 4-10. 디자인 (시즌 배경)

| 라우트 | 기능 |
|---|---|
| `theme.py` | 사용자 앱 시즌 배경 — 슈퍼어드민 등록 이미지 활성화. 무재배포 (`GET /api/theme/current` + admin CRUD) |

---

## 5. 인프라/환경 상세

### 5-1. DB 스키마 (sqlite 개발 / PostgreSQL 운영)

**테이블 수**: 30+ (`models/database.py` 기준)

| 테이블 | 핵심 컬럼 |
|---|---|
| `users` | id, email, password, language, age_group, invited_via_code |
| `email_codes` | email, code, expires_at (회원가입/비번 찾기 인증) |
| `facilities` | id, name, address, lat, lng, image_url, phone, business_hours, category |
| `facility_accounts` | business_no, company_name, email, password, verified, status |
| `facility_translations` | facility_id, language, name/address/description |
| `facility_images` | facility_id, image_url, is_primary |
| `facility_menu_uploads` | image_url, ocr_status, ocr_result |
| `facility_menu_items` | facility_id, language, name, price, source('manual'/'ocr'/'translated') |
| `beacons` | id, uuid, major, minor, battery, status, facility_id |
| `wifi_profiles` | ssid, password_enc (AES), facility_id |
| `beacon_wifi` | beacon_id, wifi_profile_id |
| `units` | 서비스 신청 단위 |
| `service_requests` | account_id, status (pending/approved/shipped) |
| `service_request_units` | request_id, beacon_id |
| `wifi_access_grant` | 매장 WiFi 접근 권한 부여 |
| `devices` | 사용자 디바이스 |
| `user_wifi_logs` | WiFi 연결 로그 |
| `stamps` | user_id, facility_id, granted_by_actor, expires_at |
| `stamp_policies` | facility_id, auto_stamp_enabled (BLE) |
| `coupons` | benefit, used_at, used_by_actor, issued_by_actor |
| `staff_accounts` | owner_account_id, role |
| `staff_invitations` | code, accepted_at |
| `super_admin_accounts` | email, password, role('super'/'admin') |
| `billing_keys` | facility_account_id, pg_key (AES 암호화) |
| `service_subscriptions` | service_type, quantity, period_months, ends_at |
| `payments` | order_no, amount, vat, total, pg_tid, status, **gateway, fallback_from** (이번 추가) |
| `push_tokens` | user_id, token, platform('fcm'/'apns'), language |
| `chat_rooms` | facility_id, user_id |
| `chat_messages` | room_id, sender, body, body_lang |
| `chat_message_translations` | message_id, lang, value |
| `notifications` | type, payload, audience |
| `notification_recipients` | notification_id, user_id, read_at |
| `notification_quota` | account_id, period, remaining |
| `notification_blocklist` | term, severity (차단어/플래그어) |
| `invitations` | code, inviter_user_id/facility_id/staff_id, accepted_user_id |
| `user_favorites` | user_id, facility_id |
| `translations` | key, lang, value, verified, source('manual'/'deepl'/'seed') |
| `announcements` | title, body, audience, push_sent, pinned |
| `support_tickets` | kind('user'/'provider'), category, status, priority |
| `support_messages` | ticket_id, sender, body_lang |
| `policy_versions` | kind, language, version, body, effective_at |
| `consent_records` | user_id/account_id, kind, version, agreed_at |
| `theme_configs` | season, image_url, overlay_alpha, active (시즌 배경) |
| `ai_usage_logs` | provider, tokens, cost (비용 모니터) |
| `admin_alert_dismissals` | alert_id, snoozed_until |

### 5-2. 환경 변수 (`.env.example` 기준)

| 카테고리 | 키 | 용도 |
|---|---|---|
| 보안 | `SECRET_KEY`, `PATHWAVE_AES_KEY`, `CORS_ORIGINS`, `FLASK_DEBUG` | JWT/AES/CORS |
| DB | `DATABASE_URL` | PostgreSQL 운영 강제 |
| **PG (이번 추가)** | `PG_PROVIDER=fallback`, `FALLBACK_PRIMARY=zeropay`, `FALLBACK_SECONDARY=toss`, `TOSS_SECRET_KEY`, `TOSS_API_BASE`, `ZEROPAY_MID`, `ZEROPAY_API_KEY`, `ZEROPAY_API_BASE` | 결제 폴백 |
| 이메일 | `EMAIL_PROVIDER=sendgrid\|smtp`, `SENDGRID_API_KEY`, `SMTP_USER`, `SMTP_PASS` | 이메일 발송 |
| 푸시 | `PUSH_PROVIDER=multi\|fcm\|apns`, `APNS_KEY_PATH/ID/TEAM_ID/BUNDLE_ID`, `FIREBASE_CREDENTIALS` | iOS+Android 푸시 |
| 슈퍼어드민 | `BOOTSTRAP_SUPER_ADMIN_EMAIL`, `BOOTSTRAP_SUPER_ADMIN_PASSWORD` | 초기 부트스트랩 (super_admin_accounts 0건일 때만) |
| 환경 | `PATHWAVE_ENV=development\|production` | 운영 강제 검증 (app.py `_validate_production_env`) |

운영 모드(`PATHWAVE_ENV=production`)에서 누락 시 부팅 차단되는 키 (`app.py` 검증):
- SECRET_KEY (dev 기본값 금지)
- PATHWAVE_AES_KEY
- CORS_ORIGINS
- FLASK_DEBUG=0
- DATABASE_URL (postgresql:// 시작)
- PG_PROVIDER=toss 시 TOSS_SECRET_KEY
- EMAIL_PROVIDER=sendgrid 시 SENDGRID_API_KEY (smtp 시 USER+PASS)
- PUSH_PROVIDER=apns|multi 시 APNs 키 4개
- PUSH_PROVIDER=fcm|multi 시 FIREBASE_CREDENTIALS

### 5-3. 배포 (Procfile)

```
web: gunicorn -c gunicorn.conf.py wsgi:app
```

- 운영: gunicorn (멀티 워커, gunicorn.conf.py)
- 로컬: `python app.py` (개발 모드, debug)

### 5-4. 운영 / 클론 환경 분리 (사용자 결정 2026-06-05)

| 항목 | 운영 (Production) | 클론 (Staging) |
|---|---|---|
| 호스트 | Contabo VPS (한국 리전 검토) | Contabo VPS 별도 또는 Docker compose 분리 |
| 도메인 | api.pathwave.??? | stage-api.pathwave.??? |
| `PATHWAVE_ENV` | production | staging (또는 development) |
| DB | PostgreSQL 운영 | PostgreSQL 별도 (마스킹 카피 또는 시드) |
| `PG_PROVIDER` | fallback (실 키) | sim (또는 sandbox) |
| `EMAIL_PROVIDER` | sendgrid (실 키) | stub 또는 dev 수신함 |
| `PUSH_PROVIDER` | multi (실 키) | stub |
| Sentry env | production | staging |
| 외부 노출 | Cloudflare → Nginx → gunicorn | 동일 또는 IP 화이트리스트 |

### 5-5. 배포 흐름

```
1. feature 브랜치 (개발)
   ↓
2. PR 생성 → GitHub Actions CI (pytest, dart analyze, vite build)
   ↓
3. 머지 main → 클론 자동 배포 (deploy script)
   ↓
4. 클론 페르소나 시나리오 검증 (수동)
   ↓
5. 운영 수동 승격 (DB 마이그레이션 분리 적용 + 코드 배포)
   ↓
6. Sentry release tag + 모니터링
```

### 5-6. 모니터링

| 영역 | 도구 | 비고 |
|---|---|---|
| 에러 추적 | Sentry (Team, $26/월) | env 별 분리 |
| AI 비용 | admin-web CostMonitor.jsx | `ai_usage_logs` 테이블 기반 |
| 시스템 health | admin-web SystemHealth.jsx | PG/이메일/푸시 ping |
| 배터리 (비콘) | admin-web Battery.jsx + 알림 | low_threshold 자동 알림 |
| 로그 | gunicorn + Python logging | 운영 stdout → 호스팅 로그 수집 |

### 5-7. 보안

| 영역 | 적용 |
|---|---|
| 비밀번호 | bcrypt 해시 |
| WiFi 비밀번호 / PG 키 | AES (PATHWAVE_AES_KEY) 암호화 |
| JWT | HS256, access + refresh 분리, sub_type 강제 |
| CORS | 운영은 화이트리스트 (CORS_ORIGINS), dev 는 전체 허용 |
| Rate limit | flask_limiter (in-memory 개발 / Redis 운영 권장) |
| 약관 동의 | policy_versions + consent_records 영속 |
| 신고 | abuse_reports (사진 3장 첨부) |
| 차단어 | notification_blocklist (block/flag) |
| 미성년자 | users.age_group + WiFi grant 제한 |

---

## 6. 의존성 매트릭스 (3 콘솔 × 도메인)

| 도메인 | mobile | provider-web | admin-web |
|---|---|---|---|
| 인증 | ✅ | ✅ | ✅ |
| 매장 (CRUD) | 읽기 | ✅ 본인 매장 | ✅ 전체 |
| 비콘 | ⚪ 자동 감지 | 신청 | ✅ CRUD |
| 스탬프 | 보기 | 정책+적립 | 통계 |
| 쿠폰 | 사용 | 발급 | 통계 |
| 채팅 | ✅ 1:1 | ✅ 1:1 | 모니터 |
| 메뉴 | 보기 + 자동번역 | CRUD + OCR | ⚪ |
| 푸시 | 수신 | 발송 | 공지 발송 |
| 결제 | ⚪ (Phase 2 매장 결제) | ✅ 구독 | 환불·통계 |
| 약관 | 동의 + 보기 | 동의 + 보기 | ✅ CRUD |
| 신고 | 신고 작성 | 신고 작성 | ✅ 처리 |
| 시즌 배경 | 적용 | ⚪ | ✅ 등록 |

→ 새 도메인 추가 시 항상 3 콘솔 영향도 매트릭스 먼저 작성 (메모리 정책).

---

## 7. 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-06-05 | v1.0 — 코드 기반 추출. 라우트 34 / mobile 화면 30+ / provider 25 / admin 28 + DB 30+ 테이블 + ENV + 배포 / 클론 분리 정책. PG 폴백(payments.gateway/fallback_from) 반영. |

---

## 8. 관련 문서

| 문서 | 용도 |
|---|---|
| `pathwave_feature_spec_2026-06-05.md` | **종합 기능정의서 v1.0** (출시 결정 사항 통합) |
| `pathwave_launch_master_plan_2026-05-20.md` | 출시 마스터 플랜 (워크스트림 W1~W8) |
| `pathwave_phase1_plan_2026-05-21.md` | Phase 1 PR 계획 (P1~P22) |
| `pathwave_persona_test_plan_C-3_2026-05-23.md` | 페르소나 통합 테스트 |
| `Pathwave_MVP_FunctionSpec_v1.0.docx` | 창업지원단 SOW 제출용 (보수적) |
| `translation_cost_runaway_plan.md` | 번역 비용 폭주 방지 |
| **본 문서** | **3 콘솔 + 인프라/환경 상세 (개발 트랙)** |
