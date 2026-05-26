# docs/internal/ — 실제 개발 문서 트랙

> ⚠️ **이 트리는 창업지원단 제출용이 아닙니다.**
> 창업지원단 제출용 문서는 `docs/Pathwave_MVP_SOW_v1.x.docx` 별도 관리.
> 자세한 정책: [project_doc_separation_policy.md](/Users/m5pro16/.claude/projects/-Users-m5pro16-Desktop-pathwave/memory/project_doc_separation_policy.md)

## 1. 분리 정책 요약

| 트랙 | 위치 | 톤 | 목적 |
|---|---|---|---|
| **창업지원단 제출용** | `docs/*.docx` | 보수적·캐주얼 | 과제 수행 완료 안전 |
| **실제 개발 (이 트리)** | `docs/internal/**/*.md` | 정교·상세 | 진짜 PathWave 스펙 |

## 2. 트리 구조

```
docs/internal/
├── README.md                       ← 본 문서
├── architecture.md                 ← 전체 시스템 아키텍처
└── spec/
    ├── README.md                   ← spec/ 인덱스
    ├── function-spec.md            ← 정교한 기능 정의 (3 콘솔)
    ├── beacon-protocol.md          ← BLE 5.x + nonce + TTL + 무중단 핸드오프
    ├── wifi-roaming.md             ← 비콘 주도 방식 C 상세 (Phase B)
    ├── i18n-strategy.md            ← 23개 언어 (Phase 1 = 10개 우선)
    ├── data-architecture.md        ← 마스터 DB + read 인덱스 분리
    ├── payment-integration.md      ← 토스페이먼츠 + 알리페이/위챗페이 + 면세
    ├── automation-roadmap.md       ← Stage 1~3 자동화 (출시 후)
    └── store-review-compliance.md  ← Apple HIG + Material 3 + 심의 체크
```

## 3. 기존 docs/ 와의 관계

- `docs/pathwave_launch_master_plan_2026-05-20.md` — 단일 추적 문서 (그대로 유지)
- `docs/pathwave_phase1_plan_2026-05-21.md` — Phase 1 PR 22개 plan (그대로 유지)
- `docs/internal/spec/*.md` — 위 두 문서가 가리키는 **정교한 스펙 본문**.
  마스터 플랜에서 spec 으로 링크.

## 4. 작성 원칙

- **정확성 우선** — 실제 코드/PR 과 일치해야 함. 메모리 인용 시 ⚠️ 표시.
- **수치 명시** — "협의" 대신 실제 목표값 (예: 1500ms, 1000 동시접속, 95% 핸드오프 성공).
- **PR 링크** — 관련 PR 번호 명기 (예: `→ PR #194`).
- **다이어그램 OK** — Mermaid / ASCII 자유롭게.

## 5. 현재 상태 (2026-05-26)

- ✅ 트리 초기화 (이 PR)
- ⏳ architecture.md 골격 작성 중
- ⏳ spec/*.md 본문 — 빈 placeholder. 사용자 요청 시 채움.

## 6. 다음 작성 순서 (추천)

1. `architecture.md` — 골격 완성 (현재 PR)
2. `spec/data-architecture.md` — 마스터 DB / read 인덱스 / 환경 분리
3. `spec/beacon-protocol.md` + `spec/wifi-roaming.md` — Phase B 핵심
4. `spec/function-spec.md` — 3 콘솔 기능 (가장 큼, 분할 가능)
5. 나머지 (i18n / payment / automation / store-review)
