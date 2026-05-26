# spec/ — 정교한 개발 스펙

`architecture.md` §12 인덱스 참조. 각 .md 파일은 **사용자 요청 시** 작성/채움.
한꺼번에 작성하지 않음 (토큰 효율 + 정확성 우선).

## 작성 우선순위

1. `data-architecture.md` — 마스터 DB / read 인덱스 / 환경 분리
2. `beacon-protocol.md` + `wifi-roaming.md` — Phase B 핵심 USP
3. `function-spec.md` — 3 콘솔 기능 (가장 큼, 분할 가능)
4. `i18n-strategy.md` — 23개 언어
5. `payment-integration.md` — 결제 + 면세
6. `automation-roadmap.md` — 자동화
7. `store-review-compliance.md` — 심의 가이드

## 작성 규칙

- **정확성** > 분량. 모르면 ⚠️ 표시.
- **PR 번호 명기** — 관련 코드와 1:1 매핑.
- **수치 명시** — "협의" 금지. 측정 가능한 값으로.
- **메모리 인용 시** `(메모리: project_xxx.md 2026-05-xx)` 형식.
- **다이어그램 OK** — Mermaid 우선, ASCII fallback.

## 현재 상태 (2026-05-26)

모든 spec 파일 ⏳ TBD. 본 PR 은 디렉토리 구조 + README + architecture 골격만.
