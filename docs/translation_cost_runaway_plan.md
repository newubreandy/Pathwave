# 외부 번역 비용 폭주 대응 — 자체 AI 서버 전환 가이드

> **트리거**: 월 누적 외부 AI 비용 **$80 (₩120,816)** 도달 시 PoC 시작 / **$100 (₩151,020)** 시 즉시 전환 작업
> **예상 시점**: 출시 후 M+3 ~ M+6
> **목표**: 사용량 비례 비용을 고정 비용 (월 $30~80) 으로 전환 + 데이터 주권 확보

---

## 1. 임계점 동작 (이미 구현됨)

| 진행률 | 동작 |
|---|---|
| **50%** ($50 / ₩75,510) | admin-web 사이드바 배지 (조용) |
| **80%** ($80 / ₩120,816) | 슈퍼어드민 알림 팝업 (24h snooze) + 이메일 — **PoC 시작 신호** |
| **100%** ($100 / ₩151,020) | 알림 팝업 (2h snooze) + 번역 호출 자동 차단 |

차단되면 채팅 메시지는 원본 그대로 저장/전달 — 사용자에게 별도 안내 없음 (자연스럽게 동작 중단).

---

## 2. 후보 모델 비교 (자체 호스팅)

| 모델 | 라이선스 | 한↔외 정확도 | 메모리 | 권장 GPU | 추가 비용 |
|---|---|---|---|---|---|
| **Helsinki-NLP Opus-MT** (언어쌍별) | MIT | ★★★ | 1~2 GB / 쌍 | T4 / 무 GPU 가능 | $0~30/월 |
| **Meta NLLB-200** (다국어 단일) | CC-BY-NC | ★★★★ | 4~10 GB | T4 / A10 | $30~80/월 |
| **Meta SeamlessM4T** | CC-BY-NC | ★★★★ | 10~20 GB | A10 / A100 | $80~200/월 |
| **mBART50** | MIT | ★★★ | 5 GB | T4 | $30~60/월 |
| **GPT4o-mini** (호스팅된 API) | 유료 | ★★★★★ | — | — | DeepL 수준 |

**1차 권장**: **NLLB-200 distilled (1.3B params)** — 한↔외 정확도 좋음, 메모리 적당, MIT 비슷한 CC-BY-NC (상업 사용은 조건 검토 필요).

---

## 3. 호스팅 옵션

| 옵션 | 월 비용 | 셋업 난이도 | 적합성 |
|---|---|---|---|
| **RunPod** (서버리스 GPU) | 사용량 비례 (분당 $0.0004 ~ $0.001) → 적당히 ~$30~80 | 중 | 출시 직후 시험 |
| **Modal.com** (서버리스 GPU) | 비슷 | 중 | RunPod 와 유사 |
| **Hugging Face Inference Endpoints** | 시간당 $0.6 ~ $1.5 → 항상 켜면 $400+ | 낮음 | 비용 비효율 |
| **자체 EC2 g4dn.xlarge** | 약 $380/월 | 높음 | 트래픽 큰 후 |
| **로컬 M5pro/M1 Mac mini + Tailscale Funnel** | $0 (전기/인터넷) | 높음 | 1인 회사 1차 |

**1차 권장**: **로컬 M5pro/M1 Mac mini + Tailscale Funnel**로 시작 → 안정화 후 RunPod 백업.

---

## 4. 마이그레이션 단계

### 단계 0: 임계점 80% 도달 — PoC 시작
- [ ] 본 가이드 재검토
- [ ] 모델/호스팅 선택 (제안: NLLB-200 distilled + 로컬 M5pro)
- [ ] 별도 브랜치 `claude/translation-self-hosted` 생성

### 단계 1: 백엔드 provider 추상화 (이미 코드 자리 있음)
- [ ] `models/translation_provider.py` 추상화 클래스 신설 (현재 DeepL 호출 위치)
- [ ] 환경변수 `TRANSLATION_PROVIDER=deepl|nllb_self|stub` 으로 분기
- [ ] `NLLBSelfProvider` 신규 — HTTP 로 자체 호스팅 모델 호출

### 단계 2: 모델 호스팅
- [ ] M5pro 에 `transformers + torch` 설치
- [ ] NLLB-200 distilled 모델 다운로드 (~5 GB)
- [ ] FastAPI 로 `/translate` 엔드포인트 래핑
- [ ] Tailscale Funnel 로 외부에서 HTTPS 접근 가능하게 노출
- [ ] 환경변수 `NLLB_ENDPOINT=https://my-mac.tail-xxx.ts.net/translate`

### 단계 3: 점진 전환
- [ ] 신규 채팅 메시지부터 자체 모델로 전환 (캐시는 유지)
- [ ] A/B 테스트 — DeepL 응답 vs NLLB 응답 비교 (운영자 검수 1주)
- [ ] 정확도 OK 면 전체 전환, DeepL Pro 다음달 갱신 X

### 단계 4: 비용 모니터링 갱신
- [ ] `models/ai_cost.py` 의 `_PRICING` 에 `('nllb_self', 'translate'): 0.0` 추가
- [ ] 자체 호스팅 비용 (전기 + 인터넷 + 하드웨어 amortize) 은 별도 BI 에서 추적

---

## 5. 폴백 정책

자체 모델이 다운되거나 응답 못 받으면:
- DeepL Pro 로 자동 폴백 (env `TRANSLATION_FALLBACK=deepl`)
- 폴백 횟수가 일 1000건 초과 시 슈퍼어드민 알림 (서버 다운 가능성)

---

## 6. 데이터 주권 / 보안

- 자체 모델 = 채팅 메시지가 외부 (DeepL 서버) 로 안 나감 → 개인정보 보호 강화
- 약관/개인정보처리방침에 "번역은 자체 모델 사용" 명시 가능 (외국인 사용자 신뢰 ↑)

---

## 7. 비용 비교 시뮬레이션 (M+12 가정)

| 항목 | DeepL Pro | NLLB-200 self-hosted (M5pro) |
|---|---|---|
| 고정 비용 | $25/월 | $0 (이미 보유) |
| 사용량 비용 | $25/M chars × 약 28M = **$700/월** | $0 (전기/인터넷 amortize) |
| 백업/폴백 | — | DeepL Pro ($25 + 사용량 — 평소엔 거의 0) |
| **합계** | **$725/월** | **$25/월 (백업만)** |
| **절감** | — | **약 $700/월 (₩1,057,000) — 96% 절감** |

→ M+6 ~ M+12 사이 전환 완료 시 누적 절감 6개월 × $700 = **$4,200 (≈ ₩6,343,000)**.

---

## 8. 위험 / 주의

| 위험 | 완화 |
|---|---|
| NLLB 정확도가 DeepL 보다 낮을 수 있음 (특히 일본어/태국어) | A/B 1주 + 운영자 검수 |
| 모델 첫 로드 cold-start ~10초 | warm 인스턴스 유지 + worker pool |
| 로컬 Mac mini 다운 시 채팅 마비 | DeepL Pro 폴백 자동 |
| CC-BY-NC 라이선스 상업 사용 검토 필요 | NLLB distilled 1.3B 는 CC-BY-NC-4.0 — PathWave 가 "사업"이라 검토 필요. MIT 인 Helsinki-NLP 으로 fallback 가능. |

---

## 9. 본 문서 트리거 — 어떻게 발견?

슈퍼어드민 알림 팝업 (`cost-80` 또는 `cost-100`) 에 본 문서 링크 표시:
```
🚨 외부 AI 비용 임계점 초과 — 번역 호출 자동 차단됨
가이드: docs/translation_cost_runaway_plan.md
```

또는 admin-web `/dashboard/cost-monitor` 페이지 하단에 "전환 가이드 보기" 링크.

---

**작성**: 2026-05-25
**리뷰**: 80% 도달 직전
**책임**: 트리거소프트 운영자 (= PathWave 슈퍼어드민)
