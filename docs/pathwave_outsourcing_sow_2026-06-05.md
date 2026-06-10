# PathWave — 외주 개발 과업지시서 (SOW)

> **버전**: v1.0 (2026-06-05)
> **발주사**: 주식회사 트리거소프트 (triggersoft)
> **프로젝트**: PathWave — 한국 방문 외국인 관광객 매장 자동 유치 + 23개 언어 자동 응대 플랫폼
> **본 문서 목적**: 외주 개발사 발주용 과업지시서. 창업지원단 제출용 SOW(`Pathwave_MVP_SOW_v1.x.docx`)와는 별개 트랙.

---

## 0. 작성 원칙

| 원칙 | 내용 |
|---|---|
| 1 | **1차 범위 = 확실히 진행 가능한 항목만**. 애매하거나 외부 협약 필요한 것은 2차로 분리. |
| 2 | **2차 범위 = 업무협약/사양 확정 후 진행**. 본 문서에 항목·전제·확정 조건 명시. |
| 3 | **추론 없이 명시된 사실만 작성**. 미정 항목은 "협의 후 확정"으로 명기. |
| 4 | **3 콘솔 동시 영향도** 항상 고려 (mobile / provider-web / admin-web). |
| 5 | **모든 기능 모듈화** — Feature Flag 시스템 기반 ON/OFF 가능. |
| 6 | **환경 분리** — 운영(Production) + 클론(Staging). 클론 검증 후 운영 승격. |

---

## 1. 역할 분담

| 영역 | 담당 |
|---|---|
| **기획** (요구사항·UX 흐름·콘텐츠·정책·약관·다국어 키·디자인 컨셉 방향) | **발주사 (트리거소프트)** |
| **디자인** (UI 시각화·디자인 시스템·아이콘·시즌 배경 톤) | **개발사** |
| **퍼블리싱** (HTML/CSS·반응형·웹 접근성) | **개발사** |
| **개발** (mobile Flutter / provider·admin React / backend Flask) | **개발사** |
| **테스트 지원** (단위·통합·페르소나 시나리오·QA 자동화·실기기 검증) | **개발사** |
| **배포·운영 지원** (CI/CD·서버 셋업·모니터링 연동) | **개발사** |
| **인프라 계약** (도메인·서버·외부 SaaS·앱스토어 가입) | **발주사** |
| **외부 서비스 가맹/협약** (토스페이먼츠·제로페이·법인 행정) | **발주사** |
| **검수 / 최종 의사결정** | **발주사** |

---

## 2. 1차 과업 범위 (확실 진행 가능)

### 2-1. 사용자 앱 (mobile) — Flutter (iOS / Android)

#### 2-1-1. 인증 (auth/)
- 이메일+비밀번호 로그인 / 회원가입 (이메일 코드 인증 → 정책 동의 → 프로필 → 완료)
- 비밀번호 찾기 (이메일 인증 → 새 비번)
- SNS 로그인 5종 — Google · Apple · Facebook · Kakao · Naver
- "로그인 없이 둘러보기" (preview 모드)
- 회원 탈퇴 (비밀번호 확인 + 14일 후 재가입 가능)

#### 2-1-2. 홈 / 비콘 / WiFi (home/)
- 4 탭 컨테이너 (홈 / 검색 / 마이 / 알림)
- BLE 비콘 자동 스캔 (백그라운드)
- 매장 비콘 감지 시 WiFi 자동 연결 화면 진입 (`wifi_connect_screen`)
- mobileconfig 설치 안내 (다건 설치 = 매장 간 자동 핸드오프)
- 1매장 1회 인증 + 매장 간 자동 전환 (Phase 1 B 스코프)

#### 2-1-3. 검색 (search/)
- 매장 키워드 검색 + 좌표 기반 거리 정렬 (Haversine, OS geolocator)
- 즐겨찾기 하트 토글

#### 2-1-4. 매장 상세 (facility/)
- 매장 이미지 슬라이드 + 정보 + 영업시간
- 메뉴 표시 (사용자 언어 자동 번역, 캐시)
- WiFi 자동 연결 진입
- 채팅 진입 (1:1)
- 즐겨찾기 / 신고

#### 2-1-5. 마이페이지 (mypage/)
- 프로필 + 메뉴 통합 글래스 박스
- 내 회원 QR (60초 만료, 점주 스캔 → 스탬프/쿠폰 자동)
- 내 스탬프 / 내 쿠폰 (탭: 사용가능 / 사용완료 / 만료)
- 즐겨찾기 리스트
- 자녀 초대 (법적 책임 동의 + 자녀 이메일 + 코드 발급)
- 친구 초대 (QR/링크 공유, 가입 보상 hook)

#### 2-1-6. 채팅 (chat/)
- 매장별 1:1 채팅 목록
- 채팅 상세 (메시지 자동 번역, body_lang 기반)
- 신고 / 차단 메뉴

#### 2-1-7. 알림 (notifications/)
- 인박스(개인) / 공지(시스템) 2 탭
- 읽음 처리
- 푸시 토큰 등록 (FCM/APNs)

#### 2-1-8. 설정 (settings/)
- 비밀번호 변경
- 차단 매장 목록
- 약관/정책 보기 (8 종)
- 마케팅 동의 토글
- 알림 카테고리별 ON/OFF
- 회원 탈퇴

#### 2-1-9. 고객센터 (support/)
- 3 탭: FAQ / 내 문의 / 신고하기
- FAQ 카테고리별 + 검색
- 문의 작성 (글래스 시트, 카테고리 + 제목 + 내용 + 첨부 1~3장)
- 신고하기 (시설 검색 → 확인 다이얼로그 → 사유 라디오 + 첨부 사진 최대 3장 + 상세)

#### 2-1-10. 부가
- splash (버전 강제/권장 업데이트 체크 → 로그인/홈 분기)
- 시즌 배경 (slug `theme.season`, 무재배포 운영, fallback 그라데이션)
- 다국어 23개 (DB 기반 i18n key, 디바이스 언어 자동 감지)

### 2-2. 시설 사장 콘솔 (provider-web) — React + Vite

| 영역 | 페이지 |
|---|---|
| 인증 | 로그인 / 회원가입 (사업자등록증 업로드 + 매장 기본 정보 + 약관) / 비번 찾기 |
| 대시보드 | 오늘 방문·스탬프·쿠폰 발급 KPI |
| 매장 정보 | 이름·주소·영업시간·카테고리·사진·비콘 ID |
| WiFi 설정 | SSID + 비밀번호(AES 암호화) + 비콘 매핑 |
| 메뉴 관리 | 메뉴 항목 CRUD + 디바이스 OCR 사진 업로드 → 자동 번역 |
| 회원 체크인 | 회원 QR 스캔 → 스탬프/쿠폰 자동 적용 + 회원 프로필 표시 |
| 스탬프 정책 | 적립 단위·보상 조건·BLE 자동 스탬프 ON/OFF |
| 쿠폰 발급 | 쿠폰 CRUD·발급 대상·유효기간 |
| 고객 채팅 | 회원과 1:1 (자동 번역) |
| 알림 발송 | 공지/이벤트 푸시 (quota 차감) |
| 결제 관리 | 카드 등록(빌링키) + 결제 내역 |
| 구독 | 서비스 신청(비콘·알림 등) + 월/연 자동 갱신 |
| 직원 관리 | 직원 초대 + 역할(matre/staff) |
| 서비스 신청 | 비콘 서비스 신청 → 어드민 승인 → 매칭 → 발송 |
| 고객지원 | FAQ / 내 문의 / 신고 |
| 약관 보기 / 설정 | 정책 본문 / 비번 변경·알림 설정 |

### 2-3. 운영자 콘솔 (admin-web) — React + Vite

| LNB 그룹 | 페이지 |
|---|---|
| **메인** | 대시보드 / 비콘 (CSV 입고·매장 배정·상태) / 서비스 신청 / 사장 가입 승인 |
| **운영** | 배터리 모니터링 / 시스템 공지 (audience 별) / 알림 검토 / 회원 관리 / 직원 모니터 / 채팅 모니터 / 신고 처리 |
| **결제·정책** | 결제 내역 (gateway/fallback 표시 + 환불) / 약관·정책 (ko+en 동시, 버전 관리) / 쿠폰 통계 |
| **고객지원** | 고객지원 / FAQ CRUD / 지원 통계 |
| **시스템** | 법인 정보 (3 콘솔 footer 동기) / 업종 카테고리 / 앱 버전 강제 업데이트 / 시스템 점검 / AI 비용 모니터 / 앱 배경 테마 / 다국어 번역 (DeepL 자동 + 사람 검수) |

### 2-4. 백엔드 (Flask + PostgreSQL)

| 영역 | 라우트 |
|---|---|
| 인증 | `auth.py` 사용자 / `facility.py` 사장 / `staff.py` 직원 / `admin.py` 어드민 / `social_kakao.py` / `social_naver.py` |
| 매장·검색 | `store.py` / `search.py` (Haversine 거리) / `categories.py` / `favorite.py` / `block.py` |
| 비콘·WiFi | `beacon.py` / `service_request.py` / `checkin.py` (QR 발급·검증) |
| 스탬프·쿠폰 | `stamp.py` / `coupon.py` / `invitation.py` |
| 채팅·메뉴·번역 | `chat.py` / `menu.py` / `i18n.py` |
| 알림·공지·신고 | `notification.py` / `notification_preferences.py` / `push.py` / `announcement.py` / `abuse_report.py` (사진 3장 첨부) / `report.py` |
| 결제 | `billing.py` — **토스페이먼츠 (1차)** |
| 정책 | `policy.py` / `company_info.py` / `version.py` |
| 고객지원 | `support.py` / `faq.py` |
| 디자인 | `theme.py` (시즌 배경, 무재배포) |

#### DB 스키마
- 30+ 테이블 (`models/database.py`): users / facilities / facility_accounts / beacons / wifi_profiles / stamps / coupons / chat_messages / notifications / payments / billing_keys / service_subscriptions / translations / announcements / theme_configs 등
- 마이그레이션 자동 (`_add_column_if_missing`)
- 운영 = PostgreSQL 강제 (개발 sqlite 허용)

### 2-5. 외부 서비스 (1차 — 발주사 가입 후 키 인계)

| 서비스 | 용도 |
|---|---|
| Apple Developer ($99/년) | iOS 배포 + APNs |
| Google Play Console ($25 일회) | Android 배포 |
| Firebase (Spark, 무료) | FCM 푸시 + 소셜 인증 백엔드 |
| SendGrid (Essentials, $19.95/월) | 회원 이메일 발송 |
| **토스페이먼츠** | provider 구독료 정기결제 (빌링키) |
| **DeepL Pro Advanced** ($25/월) | 채팅·메뉴 23 언어 자동 번역 — woorichat AI 서버 활용은 2차 |
| Sentry (Team, $26/월) | 크래시·에러 추적 |
| Google Workspace Business Starter ($7.20/월) | support@ 이메일 |
| Cloudflare (무료) | CDN + Tunnel |
| ADOBE Creative Cloud (월 ₩72,600) | 디자인 자산 |
| OpenStreetMap + MapLibre (Flutter `flutter_map`) / Apple MapKit (`apple_maps_flutter`) | 지도 (무료) |
| Apple Vision Framework (iOS) / Google ML Kit (Android) | 메뉴 OCR (디바이스 처리, 무료) |

### 2-6. 환경 분리

- 운영 (Production) + 클론 (Staging) 2환경
- 도메인: `api.pathwave.???` / `stage-api.pathwave.???`
- DB 분리, ENV 분리, 외부 키 분리 (운영 실 키 / 클론 sim·sandbox)
- 배포 흐름: feature 브랜치 → CI → 클론 자동 배포 → 수동 시나리오 검증 → 운영 수동 승격
- DB 마이그레이션은 코드 배포와 분리 적용

### 2-7. 모듈화 (Feature Flag)

- `feature_flags` 테이블 (key, value, env)
- 백엔드: `@require_feature("...")` 데코레이터
- API: `GET /api/me/features` — 클라이언트가 자기 환경 활성 모듈 받음
- mobile: `FeatureService` 분기 (UI 노출/숨김)
- web: `useFeature("...")` 훅

#### 1차 활성 모듈
`wifi_roaming` · `beacon` · `stamp` · `coupon` · `chat` · `chat_translate` · `menu_translate` · `menu_ocr_device` · `push` · `email_notify` · `subscription_payment_toss` · `season_theme`

#### 1차 비활성 (코드는 존재, ON 시 활성 — 2차 협의 후 ON)
`store_payment` · `payment_zeropay` · `alipay_wechat` · `tax_refund` · `social_auto_post` · `ai_chatbot` · `voice_call_ai` · `crm_ads_auto`

### 2-8. 보안 (1차 필수)

- 비밀번호 bcrypt
- WiFi 비번 / PG 키 AES 암호화 (`PATHWAVE_AES_KEY`)
- JWT HS256, access + refresh 분리, sub_type 강제
- CORS 화이트리스트 (운영)
- Rate limit (`flask_limiter`)
- 약관 동의 영속 (policy_versions + consent_records)
- 신고 첨부 사진 3장 + 차단어 블록리스트
- 미성년자 분리 (users.age_group)
- 사진 업로드 검증 (확장자 + MIME + 크기 캡 + 메타 EXIF 제거 — 개발사 보강)

### 2-9. 테스트 (개발사 지원)

- 백엔드 pytest (라우트별 회귀)
- mobile Flutter `dart analyze` + 화면 단위 위젯 테스트
- 페르소나 통합 테스트 시나리오 (`pathwave_persona_test_plan_C-3_2026-05-23.md` 참조)
- 실기기 검증 (iOS / Android 각 1대 이상)
- 클론 환경 시나리오 검증 (수동 / 자동 분리)

---

## 3. 2차 과업 범위 (업무협약 / 사양 확정 후 진행)

> **공통 전제**: 본 항목들은 외부 가맹·협약·자산 인계 등 발주사 책임 영역의 사전 조건이 충족된 후 진행. 1차 완료 시점 이후 별도 협의 + 추가 SOW 또는 변경 요청서로 처리.

### 3-1. 결제 확장 — 제로페이 + 매장 결제

| 항목 | 전제 / 확정 조건 |
|---|---|
| 제로페이 가맹점 신청 + 업무협약 | 발주사가 한국간편결제진흥원에 가맹점 신청 → 승인 → MID + API Key 발급 → 사양 문서 인계 |
| 제로페이 실 API 통합 (`ZeropayProvider.charge/refund`) | 위 사양 문서 인계 후. 백엔드 골격은 1차에서 이미 구현(키 미설정 시 stub). |
| **매장 결제 (사용자 → 매장, 1회)** | 별도 라우트 (`POST /api/checkout/...`) + mobile UI + provider 정산 UI. 제로페이 1차 + 토스 폴백 동작 검증 후. |
| 알리페이 / 위챗페이 | 외국인 결제 대안. 별도 가맹·계약 후. |
| 외국인 면세 자동 | 면세 사업자 등록 + 환급 PG 협약 후. |

### 3-2. AI · 번역 자산 활용 (woorichat 연계)

| 항목 | 전제 / 확정 조건 |
|---|---|
| woorichat AI 자동번역 서버 활용 (Contabo 싱가포르, 월 30만원 정액) | 발주사가 소스/API 사양 인계 (예정: 2주 내). DeepL Pro 대체 검증 후 결정. |
| woorichat OpenStreetMap 서버 활용 | 동일 — 사양 인계 + 응답속도 검증 후. |
| 한국 리전 백업 서버 도입 | Contabo 싱가포르 응답 속도 측정 결과 미달 시 도입 결정. |
| AI 응대 / 챗봇 (Claude API 등) | 모듈 `ai_chatbot` — Phase 2 출시 후. |

### 3-3. 외부 매장 등록 자동화

| 항목 | 전제 |
|---|---|
| 카카오 맵 / 네이버 지도 매장 등록 | 원칙: 매장 측 책임. PathWave 자동화 도입은 별도 사업 결정 후. |
| 카카오 Local API 지오코딩 | 1차는 OSM Nominatim 사용. Nominatim 정확도 부족 시 2차 도입. |

### 3-4. 자동화 (출시 후 단계 도입)

| Stage | 도구 | 시점 |
|---|---|---|
| Stage 1 | 카톡 챗봇 + 이메일 AI | 출시 +1~3개월 |
| Stage 2 | AI 음성통화 + SNS 자동 게시 (페북/유튜브/틱톡/인스타) + 행동 시퀀스 | 출시 +3~6개월 |
| Stage 3 | CRM + 광고 자동 (Meta/Google Ads) | 출시 +6~12개월 |

→ 모든 자동화는 매출 발생 후 단계 검증하면서 도입 (PathWave 메모리 정책: 출시 전 작업 금지).

### 3-5. 매장 다국어 슈퍼어드민 관리

- 1차: provider-web 단일 언어 (한국어) — 사용자 결정 (2026-05-27)
- 2차: 슈퍼어드민에서 매장별 다국어 노출 국가 설정. `facility_translations` 테이블 활용. DeepL 자동 번역 + 사람 검수.

### 3-6. 한국 리전 인프라 (필요 시)

| 항목 | 트리거 조건 |
|---|---|
| 한국 리전 운영 서버 추가 | Contabo 싱가포르 응답속도 측정 결과 국내 사용자 P95 > 500ms 또는 규제 요구 발생 시 |
| 한국 리전 클론 | 운영 한국 리전 도입 시 동시 |
| Cloudflare 한국 엣지 / Workers | 국내 정적 자산 최적화 검토 시 |

---

## 4. 산출물 (1차)

| 분류 | 산출물 |
|---|---|
| 코드 | mobile Flutter / provider-web / admin-web / backend (Flask) — Git 저장소 + 브랜치 정책 (main + feature) |
| DB | PostgreSQL 스키마 SQL + 마이그레이션 스크립트 + ERD |
| 디자인 | 디자인 시스템 (Figma 또는 동등) + 아이콘 세트 + 시즌 배경 톤 가이드 |
| 문서 | 기능 정의서 (본 SOW + `pathwave_feature_spec` + `pathwave_function_detail`) / API 문서 (OpenAPI 또는 동등) / 운영 매뉴얼 / 배포 매뉴얼 |
| 테스트 | pytest 결과 + Flutter 분석 결과 + 페르소나 시나리오 결과 + 실기기 검증 보고서 |
| 환경 | 운영·클론 두 환경 셋업 + `.env.example` 최신 + CI/CD 파이프라인 (GitHub Actions 또는 동등) |
| 외부 키 인계 | 발주사 보관, 개발사 운영 ENV 주입 (인계 시점 기록) |

---

## 5. 일정 (1차)

| 시기 (D-day = 출시) | 마일스톤 |
|---|---|
| **T-8 (이번 주)** | 발주사: 법인카드 / 도메인 / Workspace / DUNS / Apple Dev 가입. 개발사: 환경 셋업 시작 (개발 + 클론) |
| **T-7** | 발주사: 위치기반서비스 신고. 개발사: 디자인 시스템 확정 + ADOBE 자산 시작 |
| **T-6** | 발주사: 토스페이먼츠 신청 (심사 1~2주). 개발사: 핵심 코드 안정화 (mobile + 3 콘솔) |
| **T-5** | 개발사: FCM / APNs / SendGrid 연동 + 푸시 알림 회귀 테스트 |
| **T-4** | 개발사: DeepL Pro 연동 + 다국어 번역 시드 + Sentry 운영 env 연결 |
| **T-3** | 개발사: 운영 + 클론 서버 완전 셋업 + PostgreSQL 마이그레이션 검증 |
| **T-2** | 발주사: 페르소나 통합 테스트 + 페르소나별 시나리오 수동 검증 (개발사 지원) |
| **T-1** | 발주사: Apple App Store + Google Play 심사 제출. 개발사: 심사 대응 |
| **출시 (~8월 초)** | 운영 라이브 + 모니터링 시작 |

**개발사 가용 인력 / 일정 조정은 본 SOW 체결 후 별도 협의.**

---

## 6. 검수 기준

| 항목 | 기준 |
|---|---|
| 기능 | 본 SOW 의 1차 범위 100% 동작. 운영 환경 페르소나 시나리오 통과. |
| 성능 | 사용자 앱 콜드 스타트 ≤ 3초 (시뮬레이터). API P95 ≤ 500ms (싱가포르 서버 한국 사용자 기준 — 미달 시 2차 한국 리전 검토). |
| 안정성 | Sentry 운영 env 24시간 무 크래시. 백엔드 health ping 99% 이상. |
| 보안 | 운영 모드 ENV 검증 통과 (`app.py::_validate_production_env`). HTTPS 강제. JWT 만료 검증. |
| 디자인 | 디자인 시스템 1.0 토큰 일치. 글래스 + 시즌 배경 + 모듈화 위젯(`PwAppBar / PwButton / PwTextField / PwDialog / PwSheet / PwSwitch / PwCard / GlassCard`) 사용. |
| 다국어 | 23 언어 키 95% 이상 커버. 미커버 키는 자동 fallback (영어 또는 한국어). |
| 접근성 | WCAG AA (텍스트 컨트라스트, 터치 영역 ≥ 44pt). |
| 문서 | 본 SOW 산출물 전체 인계 + 운영 매뉴얼 1회 워크스루. |

---

## 7. 변경 관리 / 리스크

| 영역 | 처리 |
|---|---|
| 범위 변경 | 1차 범위 외 추가 요청은 **변경 요청서 (CR)** 또는 2차 SOW 로 분리. |
| 외부 협약 지연 | 토스 심사 / 제로페이 가맹 지연 시 1차 결제는 토스 단독 또는 sim 으로 출시 → 키 들어오면 ENV 만 변경. |
| Contabo 응답속도 미달 | 2차 한국 리전 검토 트리거. |
| woorichat 자산 인계 지연 | 1차는 DeepL Pro 단독으로 출시. 인계 후 2차 활용. |
| 앱스토어 심사 지연 | 1차 출시 일정 조정 가능. 본 SOW 의 1차 완료 = 심사 제출 시점. |

---

## 8. 부록

### 8-1. 모듈 키 (1차 + 2차)

```
[1차 활성]
wifi_roaming, beacon, stamp, coupon, chat, chat_translate,
menu_translate, menu_ocr_device, push, email_notify,
subscription_payment_toss, season_theme

[1차 비활성 / 2차 활성 후보]
store_payment, payment_zeropay, alipay_wechat, tax_refund,
social_auto_post, ai_chatbot, voice_call_ai, crm_ads_auto,
woorichat_translate_proxy
```

### 8-2. 환경 변수 (운영 검증 키)

본 SOW 1차 범위 운영 부팅 시 필수:
- `SECRET_KEY`, `PATHWAVE_AES_KEY`, `CORS_ORIGINS`, `FLASK_DEBUG=0`
- `DATABASE_URL` (postgresql://)
- `PG_PROVIDER=toss` (1차) — `TOSS_SECRET_KEY` 필수
- `EMAIL_PROVIDER=sendgrid` — `SENDGRID_API_KEY` 필수
- `PUSH_PROVIDER=multi` — APNs 4개 키 + `FIREBASE_CREDENTIALS`

2차 활성 시 추가:
- `PG_PROVIDER=fallback` + `FALLBACK_PRIMARY=zeropay` + `FALLBACK_SECONDARY=toss`
- `ZEROPAY_MID` + `ZEROPAY_API_KEY` (제로페이 협약 후)
- `WOORICHAT_TRANSLATE_BASE` + `WOORICHAT_TRANSLATE_KEY` (자산 인계 후)

### 8-3. 관련 문서

| 문서 | 용도 |
|---|---|
| `pathwave_feature_spec_2026-06-05.md` | 종합 기능정의서 (출시 결정 통합) |
| `pathwave_function_detail_2026-06-05.md` | 3 콘솔 + 인프라/환경 상세 (코드 기반) |
| `pathwave_launch_master_plan_2026-05-20.md` | 출시 마스터 플랜 |
| `pathwave_phase1_plan_2026-05-21.md` | Phase 1 PR 계획 |
| `pathwave_persona_test_plan_C-3_2026-05-23.md` | 페르소나 통합 테스트 |
| `Pathwave_MVP_FunctionSpec_v1.0.docx` | 창업지원단 SOW 제출용 (별개 트랙) |
| `translation_cost_runaway_plan.md` | 번역 비용 폭주 방지 |

### 8-4. 본 SOW 미정 항목 (협의 후 확정)

| # | 미정 |
|---|---|
| 1 | pathwave 도메인 TLD (.com / .app / .co 등) |
| 2 | 운영 서버 호스트 (Contabo 싱가포르 그대로 / 한국 리전 추가) |
| 3 | 클론 분리 방식 (VPS 2대 / 1대 Docker compose) |
| 4 | 변리사 선정 (상표 3건 출원: 트리거소프트 / 패스웨이브 / 우리쳇) |
| 5 | 트리거소프트 / woorichat 기존 서버 자산 인계 범위 (개발자 루트 권한 인계 후) |
| 6 | 개발사 인력 구성 + 일정 (본 SOW 체결 시) |
| 7 | 산출물 인계 형식 (Git 저장소 / 디자인 파일 / 문서 포맷) |

---

## 9. 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-06-05 | v1.0 초안. 1차/2차 분리, 역할 분담(기획=발주사, 디자인·퍼블·개발·테스트=개발사), 제로페이 2차, woorichat 자산 2차, 매장 결제 2차, 자동화 Stage 1~3 2차. 1차 = 토스 단독 + 모듈화 + 운영/클론 분리 + 보안 + 페르소나 테스트. |
