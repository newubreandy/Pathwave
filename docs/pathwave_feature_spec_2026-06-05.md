# PathWave — 전체 기능정의서 (최종본)

> **버전**: v1.0 (2026-06-05 확정)
> **회사**: 주식회사 트리거소프트 (triggersoft)
> **서비스**: PathWave (사용자 앱) + woorichat (글로벌 데이팅, 별도 서비스)
> **출시 목표**: Phase 1 — 2026년 7월 하순 ~ 8월 초

---

## 0. 문서 작성 원칙 (사용자 결정 2026-06-05)

1. **추론 없이 명시된 사실만 작성**. 미정 항목은 "미정" 으로 표기.
2. **모든 기능은 메뉴·기능 단위 모듈화**. 오픈 시점에 임의의 서비스를 숨기거나 켜도 다른 서비스에 영향 없도록 개발.
3. **서버 세팅은 운영(Production) + 클론(Staging) 으로 분리**. 모든 변경은 클론에서 검증 후 운영에 반영.

---

## 1. 서비스 개요

### 1-1. USP (재정의)

> "한국 방문 외국인 관광객 매장 자동 유치 + 23개 언어 자동 응대"

기존 국내 플랫폼(카카오/네이버/구글)이 진입하지 못한 빈 시장 점유.

### 1-2. 핵심 가치

| 페르소나 | 가치 제안 |
|---|---|
| **외국인 관광객** | 한국 매장 자동 검색 + 메뉴/채팅 자동 번역 + 무중단 WiFi |
| **한국인 사용자** | 매장 추천 + 스탬프/쿠폰 + 1회 인증 후 매장 간 WiFi 자동 연결 |
| **매장(시설) 사장** | 외국인·한국인 자동 유치 + 마케팅 자동화 + 다국어 응대 |
| **PathWave 운영** | provider 구독료 + 트래픽 데이터 + B2B 확장 |

### 1-3. 핵심 서비스 — 무중단 WiFi 로밍

신호강도 기반 매장 간 자동 핸드오프. 리조트/상권에서 1회 인증 후 이동해도 끊김 없이 WiFi 유지.

- **Phase 1**: 비콘(BLE) 감지 → mobileconfig 다건 설치 → 1매장 1회 인증 + 매장 간 자동 전환 (B 풀 스코프, PR P14~P19)
- **Phase 2**: 거리/시간/IP 기반 정교한 핸드오프 정책

---

## 2. 3 콘솔 구조 (3 콘솔 동시 개발/테스트 정책)

| 콘솔 | 대상 | 기술 스택 | 브랜드 색 | 도메인 (예정) |
|---|---|---|---|---|
| **mobile** | 사용자 (외국인 + 한국인) | Flutter (iOS/Android) | 보라 `#8B5CF6` | 앱 |
| **provider-web** | 시설/매장 사장 | React + Vite | 녹색 `#22C55E` | provider.<pathwave 도메인> |
| **admin-web** | PathWave 운영자 (슈퍼어드민) | React + Vite | 블루 `#2563EB` | admin.<pathwave 도메인> |
| **backend** | API + 비즈 로직 | Flask (Python) + PostgreSQL (운영) | — | api.<pathwave 도메인> |

### 정책

- 1계정 1매장 (provider-web): 매장 변경 = 로그아웃 + 재로그인
- 마스터 DB 는 슈퍼어드민(admin-web) 만 보유. provider/mobile 은 read 인덱스(배치 delta sync) 만.
- 모든 도메인 작업은 3 콘솔 영향도 매트릭스 기준 동시 수정 (개별 진행 금지)

---

## 3. 모듈화 시스템 (Feature Flag)

### 3-1. 원칙

오픈 시점에 임의 모듈 ON/OFF 가능. 후속 변경에도 다른 모듈에 영향 없도록 격리.

### 3-2. 구현

| 레이어 | 구조 |
|---|---|
| **백엔드** | `feature_flags` 테이블 (key, value, env) + `@require_feature("...")` 데코레이터 |
| **API 응답** | `GET /api/me/features` — 클라이언트가 자기 환경에서 켜진 기능 목록 받음 |
| **모바일** | `FeatureService` (싱글톤). `if (feature.menuTranslate) {...}` 분기로 UI 노출 |
| **Web (admin/provider)** | `useFeature("...")` 훅. 메뉴 항목/페이지 자체를 가림 |

### 3-3. 모듈 단위 (Phase 별)

| 모듈 키 | 설명 | Phase 1 | Phase 2 |
|---|---|---|---|
| `wifi_roaming` | 무중단 WiFi 핸드오프 | ✅ (B 스코프) | 강화 |
| `beacon` | BLE 비콘 감지 | ✅ | — |
| `stamp` | 스탬프 적립 (BLE 자동) | ✅ | — |
| `coupon` | 쿠폰 발급/사용 | ✅ | — |
| `chat` | 매장 1:1 채팅 | ✅ | — |
| `chat_translate` | 채팅 자동 번역 (P8b) | ✅ | — |
| `menu_translate` | 메뉴 자동 번역 | ✅ | — |
| `menu_ocr_device` | 디바이스 OCR (메뉴 사진) | ✅ | — |
| `push` | 푸시 알림 (FCM+APNs) | ✅ | — |
| `email_notify` | 이메일 알림 | ✅ | — |
| `subscription_payment` | provider 구독료 결제 | ✅ | — |
| `store_payment` | 매장 1회 결제 (사용자→매장) | ❌ | ✅ (제로페이+토스) |
| `alipay_wechat` | 알리페이/위챗페이 | ❌ | ✅ |
| `tax_refund` | 외국인 면세 자동 | ❌ | ✅ |
| `social_auto_post` | SNS 자동 게시 (페북/유튜브/틱톡/인스타) | ❌ | ✅ |
| `ai_chatbot` | 카톡 챗봇 + 이메일 AI | ❌ | ✅ |
| `voice_call_ai` | AI 음성통화 응대 | ❌ | ✅ |
| `crm_ads_auto` | CRM + 광고 자동 (Meta/Google Ads) | ❌ | ✅ |

---

## 4. 환경 분리 (운영 / 클론)

### 4-1. 구조

```
[개발자 로컬] → [클론 (Staging)] → [운영 (Production)]
                ↑ 검증 통과 시만 수동 승격
```

### 4-2. 환경별 사양

| 항목 | 운영 (Production) | 클론 (Staging) |
|---|---|---|
| 인프라 | Contabo VPS (한국 리전 검토) | Contabo VPS 별도 인스턴스 또는 동일 호스트 Docker 분리 |
| DB | PostgreSQL 운영 인스턴스 | PostgreSQL 별도 (운영 마스킹 카피 또는 시드) |
| 도메인 | api.<pathwave 도메인> | stage-api.<pathwave 도메인> |
| 결제 PG | 실 키 (토스 live_sk, 제로페이 운영 MID) | sim 모드 또는 sandbox 키 |
| 푸시 | 실 FCM/APNs | mock 또는 dev 키 |
| 이메일 | 실 SendGrid | dev 발송 (수신함 제한) |
| Sentry | production env | staging env |

### 4-3. 승격 흐름

1. feature 브랜치 → CI (테스트 통과) → 클론 자동 배포
2. 클론에서 수동 시나리오 검증 (페르소나별 테스트)
3. 운영 수동 승격 (DB 마이그레이션 + 코드 배포 분리)

---

## 5. 인프라

### 5-1. 도메인 (Namecheap 단일 출처)

| 도메인 | 용도 | 상태 |
|---|---|---|
| triggersoft.net | 회사 (트리거소프트) | ✅ 보유 |
| woori.chat | 글로벌 데이팅 (woorichat) | ✅ 보유 |
| pathwave.<TLD> | PathWave 서비스 | ⏳ 구매 예정 (TLD 미정 — .com / .app / .co 등) |

### 5-2. 서버

| 자산 | 위치 | 활용 |
|---|---|---|
| **트리거소프트 웹사이트 서버** | (확인 예정 — 개발자에게 루트 권한 받은 뒤 전달 예정) | PathWave 백엔드 후보 |
| **woorichat 서버 (Contabo, 싱가포르)** | 싱가포르 | OpenStreetMap + AI 자동번역 서버 운영 중 (월 30만원). PathWave 가 검증 후 공유 활용 가능 |
| **AI 자동번역 서버 (woorichat)** | Contabo 위에 운영 | DeepL Pro($25/월) 대체 가능 여부 검증 후 활용 |

**주의**: Contabo 싱가포르 = 국내 응답 속도 우려. 국내 매장·사용자 대상이므로 한국 리전(또는 KR CDN/엣지) 백업 검토 필요.

### 5-3. DB

- 개발: SQLite
- 운영/클론: PostgreSQL (DATABASE_URL ENV 강제)

---

## 6. 외부 서비스 결정 사항

### 6-1. 결제 (제로페이 + 토스 폴백) ✅ 백엔드 구현 완료

- **시나리오 C**: 구독료(Phase 1) + 매장결제(Phase 2 활성) 둘 다 폴백 적용
- 1차: 제로페이 (수수료 0%, 매출 8억↓) — 외국인 무관 한국인 우선
- 2차: 토스페이먼츠 (외국인 카드 / 1차 실패 시)
- 구현: `models/payment_provider.py` — `ZeropayProvider` + `FallbackPaymentProvider` + `get_payment_provider()` 확장
- DB: `payments.gateway` + `payments.fallback_from` 컬럼 추가 (마이그레이션 자동)
- 운영 활성: 키만 ENV 에 주입하면 stub → 실 API 자동 전환
- 제로페이 가맹점 신청: **개발 완료 후 연계 문의 예정** (사용자 명시)

### 6-2. 지도 (OpenStreetMap 글로벌)

| 영역 | 솔루션 | 비용 |
|---|---|---|
| 사용자 위치 | Flutter `geolocator` (OS) | 무료 |
| 매장 위치 | DB lat/lng 저장 | 무료 |
| 거리 계산 | 백엔드 Haversine | 무료 |
| iOS 지도 | Apple MapKit (`apple_maps_flutter`) | 무료 (Apple Dev 포함) |
| Android 지도 | MapLibre + OpenStreetMap (`flutter_map`) | 무료 |
| Web (admin/provider) | Leaflet + OSM | 무료 |
| 매장 주소→좌표 (등록 시) | OSM Nominatim 또는 카카오 Local API (월 30만 무료) | 무료 |

**카카오/네이버 맵 등록**: PathWave 가 직접 안 함. 매장(provider) 측에서 자기 매장을 카카오/네이버에 등록하는 건 매장 책임.

### 6-3. OCR (디바이스 기능 차용)

| 플랫폼 | 솔루션 | 비용 |
|---|---|---|
| iOS | Apple Vision Framework (한·영·중·일 자동 인식) | 무료 |
| Android | Google ML Kit Text Recognition (on-device) | 무료 |

한국어 OCR 자체 구현 불필요 (외국인 대상 USP). Cloud Vision / Tesseract / PaddleOCR 모두 **제외**.

### 6-4. 메뉴 데이터 흐름

```
provider 메뉴 입력/사진
  → 디바이스 OCR (선택) → 텍스트
  → 백엔드 DeepL 번역 → translations 테이블 (key=menu_item, lang=23개)
  → 매장별 DB 저장 (facility_menu_items)
  → 변경 감지 (텍스트 해시) → 변경분만 재번역
  → 사용자 앱에 사용자 언어로 노출 (캐시)
```

### 6-5. 자동번역

- **1차**: woorichat AI 자동번역 서버 (Contabo, 월 30만원) — 검증 후 활용 (사용량 무관 정액)
- **2차**: DeepL Pro Advanced ($25/월, 200만자) — Contabo 싱가포르 서버 응답속도 부족 시 한국 리전 백업

### 6-6. 푸시 / 이메일

| 항목 | 솔루션 |
|---|---|
| Push (iOS) | APNs (.p8 키) — Apple Dev 포함 |
| Push (Android) | Firebase FCM (Spark 무료) |
| Email | SendGrid (Essentials $19.95/월) |

### 6-7. 사진 / 자산

- Provider 매장 이미지: 백엔드 `static/` + Cloudflare CDN (선택)
- 시즌 배경 테마 (사용자앱): `static/themes/` + 슈퍼어드민 업로드

---

## 7. 행정·법무

### 7-1. 사업자 / 법인

| 항목 | 상태 |
|---|---|
| 법인 등기 (트리거소프트) | ✅ 완료 (2026-05-20) |
| 사업자등록증 | ⏳ |
| 통신판매업 신고 | ⏳ |
| 위치기반서비스 사업자 신고 (KCC) | ⏳ |
| 법인카드 | ⏳ **1순위 — 모든 외부 결제의 게이트키퍼** |

### 7-2. 상표 등록 (3건 예정)

| 상표 | 종류 | 출원 시기 |
|---|---|---|
| 트리거소프트 | 회사명 | 출시 전 |
| 패스웨이브 | PathWave 서비스명 | 출시 전 |
| 우리쳇 (woori.chat) | woorichat 서비스명 | 별도 |

- 특허청 정부수수료: 출원 ₩62,000/류 + 등록 ₩211,000/류 (10년)
- 변리사비: 별도 견적 (₩30~80만/건 권장)

### 7-3. 노란우산공제 (출시 +3~6개월 후 가입 권장)

| 혜택 | 내용 |
|---|---|
| 종합소득세 공제 | 연 최대 ₩600만 (절세 ₩90~150만/년) |
| 압류 보호 | 폐업·체불 시 공제금 법적 보호 |
| 익산시 희망장려금 | 월 ₩1만 × 12개월 = ₩12만 (연 매출 3억 이하) |
| 전북 광역 희망장려금 | 월 ₩2만 × 12개월 = ₩24만 (중복 가능 여부 확인 필요) |
| 소상공인진흥공단 정책자금 | 직접대출 평가 가점 (부금납부확인서 제출) |

---

## 8. 외부 서비스 가입 타임라인 (T = 출시 D-day)

| 시기 | 행정 | 외부 서비스 |
|---|---|---|
| **T-8 (이번 주)** | 법인카드 발급 + 사업자등록 + 통신판매업 | Namecheap pathwave 도메인 + Google Workspace Business Starter ($7.20/월) + DUNS (Apple 법인 가입용) |
| **T-7** | 위치기반서비스 신고 (KCC) | Apple Developer ($99/년) + Google Play Console ($25 일회) + ADOBE Creative Cloud (₩72,600/월) |
| **T-6** | — | 토스페이먼츠 신청 (심사 1~2주) ⭐ + 제로페이 가맹점 신청 |
| **T-5** | — | Firebase (FCM, 무료) + APNs .p8 키 + SendGrid Essentials ($19.95/월) |
| **T-4** | — | DeepL Pro Advanced ($25/월, woorichat 서버 활용 여부 결정 후) + Sentry Team ($26/월) |
| **T-3** | — | 운영 + 클론 서버 셋업 (Contabo 또는 한국 리전) + PostgreSQL |
| **T-2** | 페르소나 통합 테스트 | 모든 키 운영 ENV 반영 |
| **T-1** | — | Apple App Store + Google Play 심사 제출 |
| **출시 (~8월 초)** | 서비스 시작 | 토스 + 제로페이 라이브 |
| **+1~3개월** | — | Stage 1 자동화 (카톡 챗봇 + 이메일 AI, 월 ₩5~15만) |
| **+3~6개월** | 노란우산공제 가입 | Stage 2 자동화 (음성통화 + SNS 자동) |
| **+6~12개월** | — | Stage 3 (CRM + 광고 자동) |

---

## 9. 비용 요약 (확정 + 추정)

| 분류 | 1회 비용 | 월 고정비 | 비고 |
|---|---|---|---|
| 도메인 (pathwave 1건) | ₩15,000/년 | — | Namecheap |
| Apple Developer | ₩140,000/년 | — | $99/년 |
| Google Play Console | ₩35,000 | — | $25 일회 |
| Google Workspace Starter | — | ₩10,000 | $7.20/월 |
| ADOBE Creative Cloud | — | ₩72,600 | All Apps |
| Claude Pro | — | ₩30,000 | $20/월 |
| ChatGPT Plus | — | ₩30,000 | $20/월 (선택) |
| DeepL Pro (woorichat 활용 시 0) | — | ₩35,000 또는 0 | $25/월 |
| SendGrid Essentials | — | ₩27,000 | $19.95/월 |
| Sentry Team | — | ₩36,000 | $26/월 |
| 토스 결제 수수료 | — | 거래 기반 | ~2.9% + ₩30/건 |
| 제로페이 수수료 | — | 0~0.5% | 매출 구간별 |
| Contabo VPS (운영+클론 2대) | ~₩4만 setup | ~₩2.5만 | 또는 Vercel Hobby (0) |
| **고정비 합계 (출시 직전)** | — | **약 ₩20만~25만/월** | woorichat AI 번역 서버 활용 시 추가 ₩30만 (사용자 보유 자산이라 별도 청구 X) |

행정·사무 인프라 (창업보육센터 임대료/관리비, 주차비, 세무사, 자동차 등) 는 사용자 입력 필요 — 엑셀 체크리스트 참고.

---

## 10. 미정 / 다음 결정 필요

1. **pathwave 도메인 TLD** — .com / .app / .co / .kr / 등 (Namecheap 검색 후 결정)
2. **운영 서버 위치** — Contabo 싱가포르 그대로 vs 한국 리전 추가
3. **트리거소프트 / woorichat 서버 자산 상태 확인** — 개발자 루트 권한 받은 후 PathWave 통합 가능 여부 검토
4. **woorichat AI 자동번역 서버 API 사양** — PathWave 가 활용할 수 있는 인터페이스 확인 (2주 후 소스 공유 시점)
5. **제로페이 가맹점 신청 자료** — 신청 시점 도래하면 사용자에게 자료 목록 전달
6. **클론 환경 인프라 분리 방식** — Contabo VPS 2대 vs 1대 Docker 분리
7. **상표 변리사** — 견적 받을 변리사 선정

---

## 11. 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-06-05 | v1.0 초안 작성. 결제 폴백 / OCR 디바이스 / OSM / Workspace / 상표 3건 / 모듈화 / 운영·클론 분리 반영. PaymentProvider 백엔드 구현 완료 (`models/payment_provider.py` + 마이그레이션). |
