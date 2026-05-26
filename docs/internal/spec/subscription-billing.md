# spec/subscription-billing.md — Provider 구독료 (토스페이먼츠 빌링키)

> **트랙**: 실제 개발 · 정교·상세 · v0.1 (2026-05-26)
> **스코프 (사용자 직접)**: provider(시설관리자) 구독료만. **사용자 결제·면세·외국인결제 모두 v1 X (Phase 2+)**
> **메모리**: `project_payment_and_automation_scope.md`
> **관련 코드**: `routes/billing.py`, 테이블 `billing_keys` / `service_subscriptions` / `payments`

---

## 1. 스코프 명확화

### 1.1 v1 에 있는 것
- ✅ provider 가 카드 등록 → 빌링키 발급
- ✅ provider 가 PathWave 서비스 구독 (월/연)
- ✅ 정기결제 (subscription) 자동 갱신
- ✅ 영수증 / VAT 분리
- ✅ 구독 취소 / 연장
- ✅ 결제 실패 / 카드 만료 안내

### 1.2 v1 에 없는 것 (Phase 2+ 검토)
- ❌ **사용자(mobile) 결제** — 매장에 결제 X
- ❌ **면세 자동** — 외국인 부가세 환급 X
- ❌ **알리페이 / 위챗페이** — 외국인 결제 X
- ❌ **POS 통합 / 영수증 발급** — X
- ❌ **다중 통화** — KRW only
- ❌ **분할 결제 / 할부** — 토스 기본만

## 2. DB 스키마

### 2.1 `billing_keys` — 카드 등록 (PG 빌링키)
| 컬럼 | 의미 |
|---|---|
| id | PK |
| facility_account_id | FK provider 계정 |
| pg_key | 토스 빌링키 (암호화 대상) |
| card_brand | 카드사 (예: '국민', '신한') |
| masked_card | 마스킹된 번호 (예: `1234-****-****-1234`) |
| active | 1/0 (해지 시 0) |
| created_at | 등록 시각 |

⚠️ 카드번호 자체는 우리가 보관 X (토스만). 우리는 `pg_key` 만. PCI-DSS 경량.

### 2.2 `service_subscriptions` — 구독
| 컬럼 | 의미 |
|---|---|
| id | PK |
| facility_account_id | FK |
| service_type | `'basic'` / `'premium'` 등 (정의 필요) |
| quantity | 수량 (예: 비콘 수 비례 과금 시) |
| period_months | 1 / 12 (월 / 연) |
| unit_price | KRW |
| total_price | unit × quantity × period |
| started_at | 시작 |
| ends_at | 종료 (다음 결제 예정일) |
| status | `'active'` / `'cancelled'` / `'expired'` / `'pending'` |

### 2.3 `payments` — 결제 이력
| 컬럼 | 의미 |
|---|---|
| id | PK |
| facility_account_id | FK |
| subscription_id | FK |
| order_no | 토스 주문번호 (PG 추적) |
| amount | 공급가액 |
| vat | 부가세 (amount × 10%) |
| total | 청구액 (amount + vat) |
| pg_tid | 토스 거래 ID |
| status | `'success'` / `'failed'` / `'cancelled'` / `'refunded'` |
| receipt_email | 영수증 발송 이메일 |
| paid_at | 결제 완료 시각 |

## 3. API 엔드포인트 (`routes/billing.py`)

### 3.1 카드 (`@require_facility_actor(roles=['owner'])`)
| Method | Path | 용도 |
|---|---|---|
| POST | `/api/billing/cards` | 빌링키 발급 (토스 위젯 token 받아 백엔드에서 변환) |
| GET | `/api/billing/cards` | 등록된 카드 목록 (마스킹) |
| DELETE | `/api/billing/cards/<cid>` | 카드 비활성화 (실삭제 X) |

### 3.2 구독
| Method | Path | 용도 |
|---|---|---|
| POST | `/api/billing/subscriptions` | 신규 구독 생성 + 첫 결제 |
| GET | `/api/billing/subscriptions` | 본인 구독 목록 |
| POST | `/api/billing/subscriptions/<sid>/cancel` | 즉시 취소 (남은 기간 환불 정책 별도) |
| POST | `/api/billing/subscriptions/<sid>/extend` | 수동 연장 (관리자 호출) |

### 3.3 admin (정산용)
- 모든 구독·결제 조회 권한 (`@require_super_admin()`)
- 환불 처리 (Phase 2)

## 4. 결제 흐름

### 4.1 카드 등록
```
1. provider-web → 토스 결제 위젯 호출
2. 사용자 카드번호 입력 (토스가 직접 받음, 우리는 X)
3. 토스 → 빌링키 + masked_card 반환
4. POST /api/billing/cards 으로 우리 DB 에 저장
5. 후속 결제는 빌링키로만 진행
```

### 4.2 신규 구독
```
1. provider 가 플랜 선택 (basic / premium / quantity)
2. POST /api/billing/subscriptions
   {service_type, period_months, quantity}
3. 백엔드:
   - active card 확인
   - total_price 계산
   - 토스 _charge() 호출 (pg_key + total + order_no)
   - payments 테이블 success/failed 기록
   - 성공 시 service_subscriptions status='active', ends_at=+N개월
4. 응답 (성공 시 영수증 URL)
```

### 4.3 자동 갱신 (cron 또는 webhook)
```
ends_at <= now+3일 인 active 구독 조회
  ↓ 활성 카드 확인
  ↓ _charge() 호출
  ↓ 성공: ends_at += period_months
  ↓ 실패: status='pending' + 알림 발송 (3회 재시도)
  ↓ 3회 실패: status='expired' + provider 강제 다운그레이드
```

⚠️ **현재 cron 미구현** — webhook 또는 background job 으로 신설 필요.

### 4.4 취소
- 즉시 취소 = `status='cancelled'`, `ends_at` 까지 사용 가능
- 환불 = Phase 2 (정책 미정)

## 5. 보안 / 컴플라이언스

| 항목 | 현재 | 출시 전 필수 |
|---|---|---|
| 카드번호 보관 | ❌ (우리 X, 토스만) | ✅ 유지 |
| `pg_key` 암호화 | ⚠️ 평문 저장 | AES-GCM 암호화 |
| HTTPS 강제 | ⏳ Cloudflare Tunnel | 필수 |
| 영수증 | 토스 URL 링크 | 자체 PDF (Phase 2) |
| PCI-DSS | 경량 (SAQ A) | 유지 |
| 위변조 / 사기 의심 | 토스 자체 처리 | 추가 모니터링 (Phase 2) |

## 6. 구독 플랜 (예시 — 사용자 확정 필요)

⚠️ **플랜 가격 미확정**. 아래는 추정.

| 플랜 | 월 가격 | 포함 |
|---|---|---|
| Basic | ₩29,900 | 매장 1개 / 비콘 1개 / 기본 기능 |
| Premium | ₩59,900 | 매장 1개 / 비콘 5개 / 통계 + 자동번역 |
| Enterprise | 협의 | 비콘 무제한 / 전용 지원 |

**연간 결제 시 2개월 할인** (예: Basic 연 ₩299,000)

→ Phase 1 출시 직전 사용자 결정 필요.

## 7. 결제 실패 / 카드 만료 처리

| 케이스 | 처리 |
|---|---|
| 카드 한도 초과 | payments.status='failed', 3회 재시도 (1일 간격) |
| 카드 만료 | provider 에게 알림 + 신규 카드 등록 유도 |
| 카드 정지 | 동일 |
| 토스 PG 장애 | 자동 재시도 (지수 백오프) |
| 3회 연속 실패 | service_subscriptions.status='expired' + 다운그레이드 |

## 8. 정산 / 영수증

- 현재: 토스 자체 영수증 URL.
- Phase 2: 자체 사업자등록번호 기반 세금계산서 발행 (홈택스 API 검토).

## 9. 측정 지표

| 지표 | 목표 |
|---|---|
| 첫 결제 성공률 | ≥ 95% |
| 자동 갱신 성공률 | ≥ 90% |
| 결제 실패 → 복구율 (재등록) | ≥ 60% |
| 평균 구독 유지 기간 | (출시 후 측정) |

## 10. 외부 서비스 의존성

- **토스페이먼츠** — 1순위 신청 (메모리 `project_launch_external_services.md`, 심사 1~2주)
- 결제수단 등록 화면 = 토스 위젯 사용 (자체 구현 X)

## 11. 현재 갭 / TODO

- [ ] `pg_key` AES-GCM 암호화 (출시 전 필수)
- [ ] 자동 갱신 cron / background job
- [ ] 결제 실패 알림 템플릿 (이메일 + 푸시)
- [ ] 구독 플랜 가격 확정 (사용자 결정)
- [ ] 환불 정책 (정기결제 중도 해지 시)
- [ ] 세금계산서 발행 (Phase 2)
- [ ] 토스 webhook 수신 엔드포인트 (현재 polling)

## 12. 관련 PR

- Phase G: billing / subscription / staff (메모리 `project_next_week_sprint.md`)
- 토스페이먼츠 통합 PR 번호 확정 필요
