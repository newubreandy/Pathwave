# PathWave — IA (정보 구조) 감사 보고서

> **작성일**: 2026-06-09
> **대상**: mobile (Flutter) + provider-web (React) + admin-web (React) 3 콘솔
> **목적**: 카드 도착 전 메뉴·라우트 구조 일관성·중복·누락·SOW v1.3 정책 매핑 점검

---

## 1. mobile (사용자 앱) — 4 탭 + 라우트 26

### 1-1. 4 탭 (BottomNavigationBar)

| Idx | 탭 | 진입 화면 | 위젯 |
|---|---|---|---|
| 0 | 홈 | `_HomeTab` | BLE 카드 + 시즌 배경 + 인근 매장 |
| 1 | 검색 | `SearchScreen` | 키워드/거리 정렬 + 즐겨찾기 토글 |
| 2 | 마이 | `_MyPageTab` | 프로필 + 9 메뉴 통합 박스 |
| 3 | 알림 | `_NotificationsTab` | 인박스/공지 + **미읽음 뱃지 ✅** |

### 1-2. 라우트 전체 (26개)

```
/splash                                  /home
/auth/login                              /wifi-connect
/auth/register                           /facility/:id
/auth/forgot                             /mypage
/auth/find-email      🆕 (이번 세션)     /mypage/stamps
/mypage/coupons                          /mypage/favorites
/mypage/parent-invite                    /mypage/member-qr
/mypage/friend-invite                    /mypage/delete-account
/notifications                           /settings
/chat                                    /settings/change-password
/chat/:facilityId                        /settings/blocked-facilities
/support                                 /support/:tid
/policy/:kind
```

### 1-3. mobile IA 이슈 🔍

| # | 이슈 | 영향 | 권장 |
|---|---|---|---|
| M1 | **채팅 진입점 누락** | 4 탭에 채팅 탭 없음. `/chat` 라우트는 있지만 마이페이지에서만 진입 | ✅ 마이페이지 메뉴 9에서 자연스럽게 진입 (현재 패턴 유지 OK) |
| M2 | `/mypage/parent-invite` (자녀 초대) 메뉴 노출 | SOW v1.3 = **자녀 초대 P2 이관** | ⚠️ Feature Flag `parent_invite=false` 추가 + 메뉴 가림 |
| M3 | 평점 기능 없음 | SOW v1.3 = P2 이관 → 정상 | — |

→ **mobile IA = 거의 정상**. M2 만 Feature Flag 처리 필요.

---

## 2. provider-web (시설관리자) — 13 메뉴 + GNB 액션

### 2-1. 메인 메뉴 13개 (현재 순서)

| Idx | 경로 | 라벨 | 비고 |
|---|---|---|---|
| 1 | `/dashboard/chat` | 채팅 | **순서 이상** — 대시보드 위 |
| 2 | `/dashboard` | (대시보드) | — |
| 3 | `/dashboard/store` | 매장안내 | — |
| 4 | `/dashboard/menu` | 메뉴 관리 | — |
| 5 | `/dashboard/wifi` | 와이파이 | — |
| 6 | `/dashboard/stamps` | 스탬프 | — |
| 7 | `/dashboard/coupons` | 쿠폰 | — |
| 8 | `/dashboard/notifications` | 알림발송 | — |
| 9 | `/dashboard/report` | 리포트 | — |
| 10 | `/dashboard/staff` | 직원 관리 | **중복** (GNB 우상단에도 진입점 있음) |
| 11 | `/dashboard/payments` | 결제관리 | — |
| 12 | `/dashboard/service-request` | 서비스 신청 | — |
| 13 | `/dashboard/support` | 고객센터 | — |
| 14 | `/dashboard/settings` | 설정 | **중복** (GNB 우상단에도 진입점 있음) |

### 2-2. GNB 우상단 액션

- 🔔 알림 (`/dashboard/notifications?tab=inbox`) — 받은 알림 (메인 메뉴의 알림발송과 다른 탭)
- 👥 직원 관리 (`/dashboard/staff`) — **중복**
- ⚙️ 설정 (`/dashboard/settings`) — **중복**

### 2-3. provider IA 이슈 🔍

| # | 이슈 | 영향 | 권장 |
|---|---|---|---|
| **P1** | **메뉴 순서 — 채팅이 대시보드 위** | UX 비일관 — 시설관리자는 대시보드부터 봐야 | 🛠 **수정**: 채팅을 9번 뒤로 (또는 매장운영 그룹 안) |
| **P2** | **`/dashboard/staff`** 메뉴 + GNB 중복 | UX 혼란 | 🛠 GNB 우상단에서 제거 (메뉴 유지) — line 133 |
| **P3** | **`/dashboard/settings`** 메뉴 + GNB 중복 | UX 혼란 | 🛠 GNB 우상단 유지 (글로벌 도구) + 메뉴에서 제거 — line 81 |
| **P4** | 알림 = 메인 메뉴 "알림발송" + GNB 🔔 "받은 알림" 2 종 | 라벨로 구분되긴 함 | ✅ 라벨 명확화: 메인 = "알림발송", GNB = "받은 알림" |
| **P5** | LNB 그룹화 없음 — 13 항목 1차원 나열 | 직원이 헤매기 쉬움 | 🛠 그룹화 도입: 매장운영(매장정보·메뉴·WiFi·비콘) / 마케팅(스탬프·쿠폰·알림발송·채팅) / 운영(리포트·결제·구독신청·직원) / 지원(고객센터) |
| **P6** | `/dashboard/store` 라벨 = "매장안내" | provider 가 직접 운영하므로 "매장 관리" 가 더 자연스러움 | 🛠 라벨 변경 |
| **P7** | **자녀 초대 / 평점 기능 SP 측 메뉴 없음** | 정상 (mobile 전용) | — |

→ **provider 우선순위 = P1, P2, P3, P5 (그룹화)**.

---

## 3. admin-web (슈퍼어드민) — 5 그룹 × 28 페이지

### 3-1. LNB 그룹 + 페이지

| 그룹 | 페이지 (현재) | SOW v1.3 분류 |
|---|---|---|
| **메인** | Dashboard / Beacons / ServiceRequests / Approvals | 모두 1차 ✅ |
| **운영** | Battery / Announcements / Notifications / Users / **StaffMonitor** / **ChatMonitor** / AbuseReports | StaffMonitor·ChatMonitor = **2차 이관** |
| **결제·정책** | Payments / Policies / **CouponStats** | CouponStats = **2차 이관** |
| **고객지원** | Support / Faq / **SupportStats** | SupportStats = **2차 이관** |
| **시스템** | CompanyInfo / Categories / AppVersions / SystemHealth / **CostMonitor** / Themes / **Features (오늘 추가)** / i18n | CostMonitor = **2차 이관** |

### 3-2. admin IA 이슈 🔍

| # | 이슈 | 영향 | 권장 |
|---|---|---|---|
| **A1** | **2차 이관 5 페이지 (StaffMonitor·ChatMonitor·CouponStats·SupportStats·CostMonitor) 자동 가림 없음** | 1차 출시 시 공개되면 안 됨 | 🛠 **Feature Flag 연계** — `admin_extra_tools` 키 1개로 5 페이지 메뉴 일괄 가림 |
| A2 | **운영 그룹 항목 7개 = 너무 많음** | 스크롤 길어짐 | 🛠 2차 페이지 가리면 자연스레 4개로 감소 (A1 처리 시 자동) |
| A3 | `i18n` 메뉴 라벨 = 영어 코드 그대로 | UX | 🛠 라벨 = "다국어 번역" |
| A4 | Themes (앱 배경 테마) 가 시스템 그룹 — UI 운영 도구 | 운영 그룹이 더 자연스러움 | ⚠️ 의견 갈림 — 현재 위치 유지 OK (재배포 없음 = 시스템) |
| A5 | Features 페이지 (오늘 추가) — DEFAULT 와 다른 모듈에 "재정의됨" 뱃지 ✅ | 정상 | — |
| A6 | Approvals 메뉴에 badge:3 하드코딩 (line 의 `badge: 3`) | 더미 값 노출 | 🛠 실 대기 카운트 API 연동 |
| A7 | 알림(인박스) 같은 사용자 대상 화면이 admin 에 없음 | 슈퍼어드민 = 시스템 공지 받는 곳 없음 | 검토 — 공지는 슈퍼어드민에서 발송하므로 큰 문제 아님 |

→ **admin 우선순위 = A1 (Feature Flag 연계), A6 (Approvals badge 실 카운트)**.

---

## 4. 3 콘솔 도메인 매핑 일관성

| 도메인 | mobile | provider-web | admin-web |
|---|---|---|---|
| **알림** | 4 탭 + 인박스/공지 ✅ | 메뉴 8 "알림발송" + GNB 🔔 "받은 알림" | LNB 운영 그룹 "알림 검토" |
| **스탬프** | 마이페이지 메뉴 ✅ | 메뉴 6 "스탬프" ✅ | (Phase 2 통계 — 2차 이관) |
| **쿠폰** | 마이페이지 + 매장 상세 사용 | 메뉴 7 "쿠폰" ✅ | LNB "쿠폰 통계" (2차) |
| **채팅** | `/chat` (마이페이지 진입) | 메뉴 1 "채팅" (순서 이상) | LNB "채팅 모니터" (2차) |
| **즐겨찾기** | 마이페이지 + 매장 상세 + 검색 ✅ | (provider 측 없음) | — |
| **신고** | 고객센터 신고 탭 ✅ | 고객센터 (사용자/SP 분리 필요 — SOW §4.2.2) | LNB "신고 처리" ✅ |
| **약관** | 설정 → `/policy/:kind` | 설정 → 약관 보기 | LNB "약관·정책" CRUD |
| **결제** | (1차 X) | 메뉴 11 "결제관리" + 구독 | LNB "결제 내역" (gateway/fallback 표시) |

→ **알림** 도메인이 3 콘솔에서 가장 복잡. provider 의 라벨 명확화 필요 (이슈 P4).

---

## 5. SOW v1.3 의 ※ 신규 기능 진입점 점검

| ※ 항목 | mobile 진입 | provider 진입 | admin 진입 |
|---|---|---|---|
| 회원 탈퇴 영구 차단 | 설정 → 회원탈퇴 ✅ | — | LNB 회원 관리 → 탈퇴 처리 |
| 이메일 찾기 | 로그인 → 이메일 찾기 ✅ | — | — |
| 신고 첨부 사진 | 고객센터 → 신고 (사진 1~3장) ✅ | — | LNB 신고 처리 (사진 표시) |
| 알림 미읽음 뱃지 | 4 탭 알림 아이콘 ✅ | GNB 🔔 뱃지 ⚠️ (필요) | LNB 알림 검토 ⚠️ (불필요) |
| Feature Flag | (FeatureService 분기로 UI 자체 가림) | (동일) | LNB → 시스템 → Feature Flag ✅ |
| 12 언어 | 디바이스 자동 감지 → 설정에서 변경 가능 | (1차 한국어만) | LNB → 시스템 → 다국어 번역 |
| 회원 QR | 마이페이지 → 회원 QR ✅ | (회원 체크인 화면 — 메뉴 추가 필요?) | — |

→ ⚠️ provider GNB 🔔 미읽음 뱃지 추가 검토. provider 의 회원 체크인 메뉴 진입 명확화 필요.

---

## 6. 즉시 수정 권장 우선순위

### 🔴 P0 — 출시 직전 필수
1. **A1**: Feature Flag `admin_extra_tools` 추가 + 5 페이지 자동 가림 (StaffMonitor·ChatMonitor·CouponStats·SupportStats·CostMonitor)
2. **M2**: Feature Flag `parent_invite` 추가 + mobile 마이페이지 메뉴 가림 (자녀 초대 P2 이관)

### 🟠 P1 — 출시 전 UX 개선
3. **P1**: provider 메뉴 순서 — 채팅을 마케팅 그룹으로 이동
4. **P2, P3**: provider GNB 우상단 vs 메뉴 중복 해소
5. **P5**: provider LNB 그룹화 (4 그룹 도입)
6. **P4**: provider 알림 라벨 명확화

### 🟡 P2 — 점진 개선
7. **A3**: admin i18n 라벨 → "다국어 번역"
8. **A6**: admin Approvals badge 실 카운트 API 연동
9. **P6**: provider 매장안내 → 매장 관리

---

## 7. 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-06-09 | v1.0 초안 — 3 콘솔 메뉴 매트릭스 + 이슈 18건 + SOW v1.3 매핑 + 즉시 수정 권장 9건. |
