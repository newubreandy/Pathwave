# spec/function-spec.md — 3 콘솔 정교 기능 명세

> **트랙**: 실제 개발 · 정교·상세 · v0.1 (2026-05-26)
> **창업지원단 별첨 1 (캐주얼) 와 비교**: `docs/Pathwave_MVP_FunctionSpec_v1.0.docx`
> **분할 가능성**: 본 문서 비대 시 `function-spec-mobile.md` / `-provider.md` / `-admin.md` 로 분리.

---

## 0. 본 문서의 위치

- 3 콘솔 (mobile / provider-web / admin-web) 의 화면·기능을 **API + DB + 권한** 까지 정교하게 매핑.
- 코드와 1:1. 변경 시 PR 번호 명기.
- 본 문서는 출시 직전까지 살아있는 문서 — 모든 PR 머지 후 업데이트.

## 1. 공통 (3 콘솔)

### 1.1 디자인 토큰 (메모리 `project_color_palette.md`)
| 콘솔 | 포인트 색 | 다크 톤 |
|---|---|---|
| mobile | `#8B5CF6` (보라) | 적용 |
| provider-web | `#22C55E` (녹색) | 적용 |
| admin-web | `#2563EB` (블루) | 적용 |

3 콘솔 **동일 클래스 / 색상 토큰만 차이**.

### 1.2 인증 (JWT)
- 로그인 → `access_token` + `refresh_token`
- 401 자동 redirect → 로그인 화면 (메모리 `auto-401-redirect`)
- 권한 데코레이터:
  - `@require_login()` — 일반 사용자
  - `@require_facility_actor(roles=['owner'])` — provider 사장
  - `@require_facility_actor(roles=['staff'])` — provider 직원
  - `@require_super_admin()` — 슈퍼어드민

### 1.3 i18n
- 자세히: [`i18n-strategy.md`](i18n-strategy.md)
- 모든 텍스트는 `t(key)` 호출.

### 1.4 신고·차단 (UGC)
- 자세히: [`store-review-compliance.md`](store-review-compliance.md) §5
- 채팅·후기·공지에 적용

### 1.5 알림 (FCM)
- `routes/push.py`, `routes/notification.py`, `routes/notification_preferences.py`
- 푸시 + 인앱 알림 동시
- 알림별 세분화된 ON/OFF 설정 (push pref)

---

## 2. Mobile (사용자 앱 — Flutter)

### 2.1 화면 인벤토리 + 권한
| 화면 ID | 화면명 | 권한 | 주요 API |
|---|---|---|---|
| M-01 | 스플래시 + 강제 업데이트 체크 | 공개 | `GET /api/version/check` |
| M-02 | 온보딩 (3 페이지) | 공개 | — |
| M-03 | 게스트 진입 / 로그인 / 가입 선택 | 공개 | — |
| M-04 | 가입 (이메일 + 비번 + 약관 동의) | 공개 | `POST /api/auth/signup` |
| M-05 | 로그인 | 공개 | `POST /api/auth/login` |
| M-06 | 비밀번호 찾기 | 공개 | `POST /api/auth/forgot-password` ⚠️ app.py 재시작 필요 |
| M-07 | 홈 (BLE 스캔 + 주변 매장) | login | `GET /api/facilities/nearby`, `POST /api/beacon/handshake` |
| M-08 | 매장 상세 (메뉴 / 영업시간 / 공지) | login | `GET /api/facilities/<id>` |
| M-09 | WiFi 자동 연결 진행 / 결과 | login | `POST /api/beacon/handshake` 응답 후 OS WiFi API |
| M-10 | 스탬프 리스트 | login | `GET /api/stamps/mine` |
| M-11 | 쿠폰 리스트 | login | `GET /api/coupons/mine` |
| M-12 | 쿠폰 사용 (QR) | login | `POST /api/coupons/<id>/use` |
| M-13 | 즐겨찾기 | login | `GET /api/favorites` |
| M-14 | 검색 | login | `GET /api/search/facilities` |
| M-15 | 채팅 목록 | login | `GET /api/chat/rooms` |
| M-16 | 채팅 상세 (1:1) | login | `GET /api/chat/messages/<rid>`, SSE |
| M-17 | 채팅 첨부 (카메라 / 갤러리) | login | `POST /api/chat/upload` |
| M-18 | 알림 목록 | login | `GET /api/notifications` |
| M-19 | 알림 설정 (세분화) | login | `GET/PATCH /api/notification-preferences` |
| M-20 | 마이페이지 | login | `GET /api/users/me` |
| M-21 | 프로필 편집 | login | `PATCH /api/users/me` |
| M-22 | 약관 보기 (3 종) | 공개 | `GET /api/policies/<kind>` |
| M-23 | FAQ | 공개 | `GET /api/faqs` |
| M-24 | 1:1 문의 (지원) | login | `POST /api/support/tickets` |
| M-25 | 회원탈퇴 | login | `DELETE /api/users/me` |
| M-26 | 매장 신고 / 채팅 신고 | login | `POST /api/reports` |
| M-27 | 사용자 차단 관리 | login | `GET/POST/DELETE /api/blocks` |

### 2.2 핵심 흐름 — BLE → WiFi (USP)
자세히: [`wifi-roaming.md`](wifi-roaming.md), [`beacon-protocol.md`](beacon-protocol.md)

1. M-07 진입 → BLE 스캔 자동 시작
2. 비콘 인식 → handshake → wifis[] 수신
3. M-09 진행 → OS WiFi 자동 연결
4. 첫 방문이면 → 자동 스탬프 + 자동 쿠폰 (서버측)
5. M-07 으로 복귀 → 매장 카드에 "연결됨" 배지

### 2.3 핵심 흐름 — 채팅 자동 번역
- 사용자가 자국어로 입력 → 백엔드가 매장 언어 (한국어) 로 번역해서 저장 + 표시
- 매장이 한국어로 응답 → 사용자에게 자국어로 번역해서 표시
- `chat_message_translations` 캐시
- P8b PR (현재 OPEN)

### 2.4 핵심 흐름 — 회원탈퇴
1. M-25 → "정말 탈퇴하시겠습니까?" 모달
2. 비밀번호 재확인
3. 동의 체크박스 ("개인정보 30일 후 완전 삭제")
4. DELETE /api/users/me → `users.status='deleted'`, `deleted_at` 기록
5. 30일 후 cron 으로 완전 삭제 (이메일·전화번호·채팅 마스킹)
6. 매장 / 슈퍼어드민 에게는 익명 처리된 데이터만 남음

---

## 3. Provider-Web (시설관리자 — 반응형 PC 웹)

### 3.1 화면 인벤토리
| 화면 ID | 화면명 | 권한 | 주요 API |
|---|---|---|---|
| P-01 | 로그인 | 공개 | `POST /api/auth/login` (provider role) |
| P-02 | 가입 (사업자 정보) | 공개 | `POST /api/auth/signup` (role='facility') |
| P-03 | 가입 → 매장 등록 | login | `POST /api/facilities` |
| P-04 | 가입 → 카테고리 선택 (드롭다운) | login | `GET /api/categories` |
| P-05 | 가입 → 약관 동의 | login | `POST /api/consents` |
| P-06 | 대시보드 (방문자 / 매출 / 비콘 상태) | provider login | `GET /api/facilities/me/stats` |
| P-07 | 매장 정보 편집 (영업시간 / 공지 / 사진) | provider login | `PATCH /api/facilities/me` |
| P-08 | 매장 사진 업로드 (다중) | provider login | `POST /api/facilities/me/images` |
| P-09 | 메뉴 등록 (직접 입력 + OCR) | provider login | `POST /api/menu/upload`, `POST /api/menu/items` |
| P-10 | 비콘 페어링 (claim) | provider login | `POST /api/beacons/claim` |
| P-11 | 비콘 상태 (배터리 / 마지막 인식) | provider login | `GET /api/beacons/mine` |
| P-12 | WiFi 프로파일 등록 (SSID + 비밀번호) | provider login | `POST /api/wifi/profiles` |
| P-13 | 비콘 ↔ WiFi 매핑 (priority) | provider login | `POST /api/beacons/<id>/wifi` |
| P-14 | 스탬프 정책 설정 | provider login | `POST /api/stamps/policies` |
| P-15 | 쿠폰 캠페인 (발급 / 일괄) | provider login | `POST /api/coupons` |
| P-16 | 결제수단 등록 (토스 위젯) | owner | `POST /api/billing/cards` |
| P-17 | 구독 플랜 (선택 + 결제) | owner | `POST /api/billing/subscriptions` |
| P-18 | 정산 / 매출 조회 | owner+staff | `GET /api/billing/payments` |
| P-19 | 채팅 (사용자 응대) | provider login | `GET /api/chat/rooms` (facility) |
| P-20 | 채팅 자동번역 토글 | provider login | `PATCH /api/facilities/me/chat-settings` |
| P-21 | 신고 처리 (내 매장) | provider login | `GET /api/reports/facility/me` |
| P-22 | 차단 사용자 관리 | provider login | `GET /api/blocks/facility/me` |
| P-23 | 직원 초대 | owner | `POST /api/staff/invitations` |
| P-24 | 직원 권한 관리 | owner | `PATCH /api/staff/<id>/roles` |
| P-25 | 1:1 문의 (PathWave 운영자) | provider login | `POST /api/support/tickets` |
| P-26 | 마이페이지 / 사장 프로필 | provider login | `GET /api/users/me` |
| P-27 | 매장 탈퇴 / 계정 삭제 | owner | `DELETE /api/facilities/me` |

### 3.2 핵심 흐름 — 가입 + 매장 등록
1. P-01 로그인 화면 → "신규 가입" 클릭
2. P-02 사업자 정보 (이름 / 사업자번호 / 대표자)
3. P-03 매장 정보 (상호 / 주소 / 카테고리)
4. P-04 카테고리 선택 (드롭다운, 자유입력 X)
5. P-05 약관 3종 동의 (이용약관 / 개인정보 / 위치기반)
6. 백엔드 → `users` + `facility_accounts` + `facilities` 행 생성, `status='pending'`
7. 슈퍼어드민에게 admin alert
8. 슈퍼어드민 승인 시 → `status='active'`, 사장에게 이메일 발송
9. 사장 첫 로그인 → P-06 대시보드

### 3.3 핵심 흐름 — 비콘 페어링
1. P-10 화면 → "비콘 추가" 클릭
2. 사장이 비콘 일련번호 (serial_no) 입력 또는 QR 스캔
3. POST /api/beacons/claim {serial_no}
4. 백엔드 → beacons.facility_id 갱신, status='active'
5. P-11 으로 자동 이동, 새 비콘 표시

### 3.4 핵심 흐름 — 채팅 운영
1. P-19 채팅 목록 (사용자별 미응답 카운트)
2. 사용자 → 자국어 메시지
3. 자동 번역 (P-20 토글 ON 시 한국어로 표시, 본문 + 원문)
4. 사장 한국어 응답
5. 자동 번역하여 사용자에게 전송
6. SSE 로 실시간 알림

### 3.5 1 계정 = 1 매장 정책
메모리 `project_account_store_policy.md`:
- provider 가입 시 1 매장 강제
- 다중 매장 카운트 / 스위처 UI 금지
- 매장 변경 = 로그아웃 → 재로그인

---

## 4. Admin-Web (슈퍼어드민 — PC 웹)

### 4.1 화면 인벤토리
| 화면 ID | 화면명 | 권한 | 주요 API |
|---|---|---|---|
| A-01 | 로그인 | 공개 | `POST /api/auth/admin/login` |
| A-02 | 대시보드 (전체 현황) | super_admin | `GET /api/admin/stats` |
| A-03 | SP 심사 대기 큐 | super_admin | `GET /api/admin/facilities?status=pending` |
| A-04 | SP 상세 (사업자 정보 검토) | super_admin | `GET /api/admin/facilities/<id>` |
| A-05 | SP 승인 / 거절 | super_admin | `PATCH /api/admin/facilities/<id>/status` |
| A-06 | SP 정지 / 재활성화 | super_admin | `PATCH /api/admin/facilities/<id>/status` |
| A-07 | 비콘 자산 입고 (CSV 업로드) | super_admin | `POST /api/admin/beacons/bulk-import` |
| A-08 | 비콘 자산 조회 (필터 + 검색) | super_admin | `GET /api/admin/beacons` |
| A-09 | 비콘 배터리 모니터링 | super_admin | `GET /api/admin/beacons/battery-history` |
| A-10 | 비콘 회수 / 폐기 | super_admin | `PATCH /api/admin/beacons/<id>` |
| A-11 | 카테고리 마스터 관리 | super_admin | `GET/POST/PATCH/DELETE /api/admin/categories` |
| A-12 | 약관 마스터 관리 (다국어 + 버전) | super_admin | `POST /api/admin/policies` |
| A-13 | i18n 번역 grid | super_admin | `GET /api/admin/i18n`, `POST /api/admin/i18n/translate` |
| A-14 | 푸시 알림 발송 (대상 필터) | super_admin | `POST /api/admin/notifications/broadcast` |
| A-15 | 공지 작성 (전체 / 매장별) | super_admin | `POST /api/admin/announcements` |
| A-16 | 신고 처리 큐 | super_admin | `GET /api/admin/reports` |
| A-17 | 신고 상세 (채팅 원문 + 조치) | super_admin | `PATCH /api/admin/reports/<id>` |
| A-18 | 사용자 정지 / 영구 차단 | super_admin | `PATCH /api/admin/users/<id>/status` |
| A-19 | 매장 정산 처리 (월 정산) | super_admin | `GET /api/admin/billing/settlements` |
| A-20 | 결제 환불 처리 | super_admin | `POST /api/admin/payments/<id>/refund` |
| A-21 | 1:1 문의 응답 | super_admin | `POST /api/admin/support/tickets/<id>/reply` |
| A-22 | FAQ 마스터 관리 | super_admin | `POST/PATCH/DELETE /api/admin/faqs` |
| A-23 | 회사 정보 (footer) 편집 | super_admin | `PATCH /api/admin/company-info` |
| A-24 | 앱 버전 관리 (강제 업데이트) | super_admin | `PUT /api/admin/app-versions/<platform>` |
| A-25 | 어드민 계정 관리 (역할 분리) | super_admin | `POST/PATCH /api/admin/users` (super_admin role) |
| A-26 | 감사 로그 (admin_alert_dismissals) | super_admin | `GET /api/admin/audit-logs` (Phase 2) |
| A-27 | AI 사용량 모니터 (DeepL / Claude) | super_admin | `GET /api/admin/ai-usage` |

### 4.2 핵심 흐름 — 비콘 CSV 입고
1. A-07 진입 → CSV 양식 다운로드 (serial_no, uuid, major, minor)
2. CSV 편집 후 업로드
3. 백엔드 → `beacons` 일괄 INSERT (status='inventory', facility_id=NULL)
4. 결과 페이지 (성공 / 실패 / 중복) 표시
5. A-08 으로 자동 이동

### 4.3 핵심 흐름 — SP 심사
1. A-03 대기 큐 → 신규 SP 카드 표시
2. A-04 상세 → 사업자등록증 / 매장 사진 / 카테고리 검토
3. 사기 가능성 검사 (외부 사업자번호 조회 등)
4. A-05 승인 → 사장에게 이메일 + 첫 로그인 가이드
5. 거절 시 → 사유 입력 → 사장에게 이메일

### 4.4 핵심 흐름 — 약관 버전 관리
1. A-12 → 약관 종류 선택 (terms / privacy / location / marketing)
2. 언어별 본문 작성 (ko 필수, en 권장, 외국어 23개)
3. 신규 버전 발행 → `policies.version` 증가, `effective_at` 설정
4. effective_at 도달 → 모든 사용자에게 재동의 모달 표시
5. 동의 안 한 사용자는 서비스 일시 제한 (메모리 `project_pre_launch_checklist.md`)

### 4.5 핵심 흐름 — 신고 처리
1. A-16 큐 → 신규 신고 표시 (24시간 SLA)
2. A-17 상세 → 채팅 원문 / 신고 사유 / 사용자 이력
3. 조치 선택:
   - **무시** (false report)
   - **경고** (사용자에게 알림)
   - **임시 정지** (3일 / 7일 / 30일)
   - **영구 차단** (사용자 + 디바이스 + 이메일 도메인)
4. 양 당사자에게 결과 통지 (Phase 2)

---

## 5. 권한 매트릭스

| 기능 영역 | 사용자 | 게스트 | provider owner | provider staff | super_admin |
|---|---|---|---|---|---|
| 가입 / 로그인 | ✅ | — | ✅ | ✅ (초대만) | ✅ |
| BLE handshake | ✅ | ❌ | ❌ | ❌ | ❌ |
| 매장 조회 | ✅ | ✅ (제한) | ✅ (본인) | ✅ (본인) | ✅ (전체) |
| 매장 등록·편집 | ❌ | ❌ | ✅ | ❌ | ❌ |
| 비콘 claim | ❌ | ❌ | ✅ | ❌ | ✅ (admin) |
| WiFi 프로파일 등록 | ❌ | ❌ | ✅ | ❌ | ✅ |
| 결제수단 / 구독 | ❌ | ❌ | ✅ | ❌ | ✅ (조회) |
| 정산 조회 | ❌ | ❌ | ✅ | ✅ (조회) | ✅ |
| 신고 작성 | ✅ | ❌ | ✅ | ✅ | ❌ |
| 신고 처리 | ❌ | ❌ | ❌ | ❌ | ✅ |
| 약관 / 카테고리 마스터 | ❌ | ❌ | ❌ | ❌ | ✅ |
| 사용자 정지 | ❌ | ❌ | ❌ | ❌ | ✅ |

## 6. SSE / WebSocket 사용처

| 용도 | 위치 | 프로토콜 |
|---|---|---|
| 채팅 실시간 메시지 | mobile M-16 / provider P-19 | SSE (PR `claude/chat-sse`) |
| admin 신고 신규 알림 | admin A-16 | SSE 또는 폴링 |
| 비콘 상태 실시간 | admin A-08 | 폴링 (10초) |
| FCM 푸시 | OS 레벨 | FCM |

## 7. 분량 / 분할 정책

- **현재 27 + 27 + 27 = 81 화면** 인벤토리.
- 본 문서 1 파일로 유지하되, 한 콘솔의 화면 ≥ 50 도달 시 분할:
  - `function-spec-mobile.md`
  - `function-spec-provider.md`
  - `function-spec-admin.md`

## 8. 현재 갭 / TODO

- [ ] 각 화면 ID 와 실제 라우트 1:1 매핑 (코드 grep 으로 검증)
- [ ] Phase 1 plan §6 표와 PR 번호 동기화
- [ ] SSE 사양 (재연결 / heartbeat / 인증)
- [ ] 다국어 grid UI (A-13) 화면 디자인
- [ ] 회원탈퇴 30일 보관 cron
- [ ] 환불 정책 (A-20) 완성

## 9. 관련 메모리 / 문서

- `project_three_consoles_sync.md` — 3 콘솔 동시 개발 정책
- `project_console_impact_matrix.md` — 도메인별 PR 묶음표
- `project_account_store_policy.md` — 1 계정 1 매장
- `project_color_palette.md` — 색상 토큰
- 출시 마스터 플랜: `docs/pathwave_launch_master_plan_2026-05-20.md`
- Phase 1 plan: `docs/pathwave_phase1_plan_2026-05-21.md` §6
