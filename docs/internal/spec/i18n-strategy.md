# spec/i18n-strategy.md — 23개 언어 DB 기반 i18n

> **트랙**: 실제 개발 · 정교·상세 · v0.1 (2026-05-26)
> **메모리**: `project_i18n_global_strategy.md`
> **관련 코드**: `routes/i18n.py`, 테이블 `translations` / `units`

---

## 1. 전략 요약

- **DB 기반** (정적 .json 번들 X) — 운영 중 추가/수정 가능.
- **DeepL 1회 번역 + 캐시** — 비용 최소화 ($25 1회).
- **Phase 1 = 한국 방문 관광객 우선 10개**, Phase 2 = 13개 추가.
- 3 콘솔 (mobile / provider / admin) 동일 key 사용.

## 2. 지원 언어 (현재 591 row 시드 완료)

### 2.1 Phase 1 — 한국 방문 외국인 우선 (10개)
| 코드 | 언어 | 우선 이유 |
|---|---|---|
| `ko` | 한국어 | 기본 |
| `en` | 영어 | 공용어 |
| `zh-CN` | 중국어 간체 | 본토 관광객 1위 |
| `ja` | 일본어 | 관광객 2위 |
| `zh-TW` | 중국어 번체 | 대만/홍콩 |
| `vi` | 베트남어 | 동남아 |
| `th` | 태국어 | 동남아 |
| `tl` | 타갈로그 | 필리핀 |
| `id` | 인도네시아어 | 동남아 |
| `ms` | 말레이어 | 동남아 |

### 2.2 Phase 2 — 글로벌 확장 (13개)
`de` / `fr` / `es` / `it` / `pt` / `nl` / `pl` / `sv` / `tr` / `ru` / `ar` / `he` / `hi`

**현재 시드 상태**: 23개 언어 모두 한 번 자동 번역됨 (DB 591 row, 한국어 기준 ~25 key, 23개 언어).

⚠️ 시드는 자동 번역 한 번만. **운영 중 수정·추가 필요**.

## 3. DB 스키마

### 3.1 `translations`
| 컬럼 | 타입 | 의미 |
|---|---|---|
| key | TEXT | 점 구분 key (예: `mobile.beacon.connecting`) |
| lang | TEXT | 언어 코드 (`ko` / `en` / `zh-CN` ...) |
| value | TEXT | 번역문 |
| source | TEXT | `'manual'` / `'deepl'` / `'imported'` |
| updated_at | TEXT | 마지막 수정 |
| UNIQUE(key, lang) | | |

### 3.2 `units` — 단위 다국어
- 통화 / 거리 / 시간 / 수량 단위의 언어별 표기
- 예: `currency.krw` → `'원' / 'KRW' / '元' / '円' ...`

### 3.3 key 명명 규칙
- `{콘솔}.{영역}.{용도}` 형식
- 콘솔: `common` (공통) / `mobile` / `provider` / `admin`
- 예시:
  - `common.error.network` — 3 콘솔 공통
  - `mobile.beacon.connecting` — mobile 전용
  - `provider.facility.save_success` — provider 전용
  - `admin.beacon.csv_import_done` — admin 전용

## 4. API 엔드포인트 (`routes/i18n.py`)

### 4.1 공개
| Method | Path | 용도 |
|---|---|---|
| GET | `/api/i18n/<lang>` | 해당 언어의 전체 key:value (페이로드 캐싱 대상) |

### 4.2 admin (`@require_super_admin()`)
| Method | Path | 용도 |
|---|---|---|
| GET | `/api/admin/i18n` | grid (key × lang 매트릭스) |
| POST | `/api/admin/i18n/translate` | DeepL 자동 번역 (key 1~N개) |
| POST | `/api/admin/i18n/<path:key>/<lang>` | 수동 upsert |
| GET | `/api/admin/i18n/missing/<lang>` | 미번역 key 목록 |

## 5. 번역 흐름

### 5.1 신규 key 추가 (개발자)
```
1. 코드에서 t('mobile.new.label') 사용
2. 로컬에서 ko 만 manual upsert
3. admin grid 에서 미번역 key 발견 → "자동 번역" 클릭
4. DeepL 호출 → 모든 lang 채움 (source='deepl')
5. 사람이 검토 → 수정 시 source='manual' 로 변경
```

### 5.2 외국인 사용자 흐름
```
1. mobile 첫 실행 시 OS locale 감지
2. 지원 언어 매핑 (예: zh-HK → zh-TW fallback)
3. GET /api/i18n/{lang} → 페이로드 캐시 (24h)
4. 모든 화면 t(key) 호출
5. fallback: lang 에 없으면 en, en 에도 없으면 ko, ko 에도 없으면 key 그대로
```

## 6. DeepL 통합

### 6.1 비용 모델
- DeepL Pro **$25 / 1M chars** (메모리 `project_i18n_global_strategy.md`)
- Phase 1 = ~5,000 key × 평균 30 chars × 22개 비-ko 언어 = 3.3M chars = **$83 (한 번)**
- Phase 2 추가 13개 언어 = $50 추가
- 운영 중 추가 key 는 cents 단위. 임계점 X.

### 6.2 자동 번역 정책
- admin 의 "자동 번역" 호출 시 missing key 만 처리 (중복 호출 X).
- DeepL 응답 = `source='deepl'` 로 저장.
- 사람이 검토 후 수정 = `source='manual'`. 다음 자동 번역 시 manual 은 건너뜀.

### 6.3 글로서리 (Glossary)
- "PathWave" / "WiFi" / "BLE" / "스탬프" / "쿠폰" 등 고정 번역 등록
- DeepL Pro 만 글로서리 지원

## 7. 콘솔별 통합

### 7.1 mobile (Flutter)
- 패키지: `flutter_localizations` + 커스텀 `t(key)` 함수
- 빌드 시 페이로드 임베드 X (런타임 fetch)
- OS locale 변경 감지 → 자동 reload
- 캐시: SharedPreferences (24h)

### 7.2 provider-web (React)
- i18next 또는 자체 `t(key)`
- 로그인 시 fetch + localStorage 캐시
- 로그아웃 시 캐시 클리어

### 7.3 admin-web
- ko / en 만 사용 (운영자는 한국어 기본)
- 단, **번역 grid UI** 는 23 언어 모두 표시

## 8. 자동 번역 컨텐츠 (Phase 2 USP)

### 8.1 메뉴 자동 번역
- provider 가 메뉴 사진 업로드 → tesseract OCR (한국어 텍스트 추출)
- DeepL 으로 23개 언어 번역
- `facility_menu_uploads` + `facility_menu_items` 저장
- mobile 사용자 언어로 자동 표시

### 8.2 채팅 자동 번역
- 사용자가 자국어로 채팅 → 매장 사장에게 한국어로 표시
- 매장 사장이 한국어로 응답 → 사용자에게 자국어로 표시
- `chat_message_translations` 테이블에 캐시
- 자세히: P8b PR (현재 OPEN)

### 8.3 푸시 알림 자동 번역
- 알림 발송 시 사용자 lang 으로 자동 번역 (P8c)

## 9. 현재 갭 / TODO

| 항목 | 상태 |
|---|---|
| 23 언어 시드 | ✅ 591 row 완료 (2026-05-21) |
| DB ↔ 코드 문구 불일치 | ⚠️ 18건 잔존 (메모리 `project_preexisting_state_2026_05_20.md`) |
| admin grid UI | ⏳ TBD |
| 자동 번역 cron (신규 key 야간 일괄) | ⏳ Phase 2 |
| DeepL glossary 등록 | ⏳ Phase 2 |
| 메뉴 OCR + 자동 번역 (P8b 외) | ⏳ Phase 2 |
| OS locale → 지원 언어 매핑 표 | ⏳ TBD |
| RTL 언어 (`ar` / `he`) UI 대응 | ⏳ Phase 2 |

## 10. 측정 지표 (KPI)

| 지표 | 목표 |
|---|---|
| 페이로드 fetch 응답 시간 | ≤ 200ms (p95) |
| 첫 화면까지 i18n 로딩 | ≤ 500ms |
| 누락 key (fallback 발동) 비율 | ≤ 1% |
| 자동 번역 정확도 (글로서리 적용 후) | ≥ 95% |

## 11. 관련 PR / 메모리

- P2: mobile i18n (메모리 `project_preexisting_state_2026_05_20.md`)
- P8b: 채팅 자동번역 (현재 OPEN)
- P8c: 푸시 알림 자동번역
- P8d: 이메일 다국어
- P12: 약관 ko/en only → 다국어 확장
- 메모리: `project_i18n_global_strategy.md` (전체 전략)
