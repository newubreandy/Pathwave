# spec/ — 정교한 개발 스펙

`architecture.md` §12 인덱스 참조. 각 .md 파일은 코드와 1:1 매핑.

## 작성 규칙

- **정확성** > 분량. 모르면 ⚠️ 표시.
- **PR 번호 명기** — 관련 코드와 1:1 매핑.
- **수치 명시** — "협의" 금지. 측정 가능한 값으로.
- **메모리 인용 시** `(메모리: project_xxx.md 2026-05-xx)` 형식.
- **다이어그램 OK** — Mermaid 우선, ASCII fallback.

## 현재 상태 (2026-05-26)

| spec | 상태 | 주요 내용 |
|---|---|---|
| `data-architecture.md` | ✅ v0.1 | 마스터 DB / read 인덱스 / 환경 분리 / 55 테이블 분류 |
| `beacon-protocol.md` | ✅ v0.1 | BLE 5.x + handshake + DB 스키마 + 보안 위협 모델 |
| `wifi-roaming.md` | ✅ v0.1 | 방식 C 비콘 주도 / iOS .mobileconfig + Android suggestion |
| `i18n-strategy.md` | ✅ v0.1 | 23개 언어 DB i18n + DeepL + 자동번역 (메뉴/채팅/푸시) |
| `subscription-billing.md` | ✅ v0.1 | provider 구독료 only (토스 빌링키). 사용자결제·면세 X |
| `store-review-compliance.md` | ✅ v0.1 | Apple HIG / Material 3 / Privacy Manifest / UGC / 법적 |
| `automation-roadmap.md` | ✅ v0.1 | Stage 1~3 (**출시 후**). 챗봇 / SNS / 광고 / CRM |
| `function-spec.md` | ✅ v0.1 | 3 콘솔 화면 81개 + API + 권한 매트릭스 |

## 갱신 정책

- 각 spec 은 PR 머지 후 / 사용자 정책 변경 시 갱신.
- v0.x → v1.x 는 출시 직전 한 차례 정리.
- 사용자 결정으로 분량 폭증한 spec 은 분할 (예: `function-spec-mobile.md` 등).
