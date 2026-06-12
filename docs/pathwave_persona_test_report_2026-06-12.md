# 페르소나 통합 테스트 결과서 (C-3) — 2026-06-12

출시 전 체크리스트 3번. 6 페르소나를 4 트랙으로 나눠 **실제 API 호출 기반** 검증.
롤백 백업: `/tmp/pathwave_backup_persona_1654.db` (테스트 전 스냅샷).

## 1. 종합 결과

| 트랙 | 페르소나 | 결과 |
|---|---|---|
| T1 | 🌏 외국인 관광객 (en) | **12 단계 전부 PASS** — i18n/게스트 검색·상세/가입(`/api/auth/register`)/로그인/프로필(`/api/auth/me`)/쿠폰·스탬프 빈 상태/회원 QR(`POST /api/checkin/member-qr`)/채팅 생성·메시지/차단 왕복(`/api/blocks`) |
| T2 | 🇰🇷 한국인 사용자 | **12/12 PASS** — 검색/찜/QR 재발급/알림 읽음/FAQ·약관/문의/신고/버전체크/refresh |
| T3 | ☕ 신규 사장 + 직원 | **13/13 PASS** — 가입(pending)→로그인 차단→어드민 승인→매장 셋업(정보·메뉴·이미지·쿠폰·스탬프)→직원 초대·수락→**권한 경계 (직원 매장수정 403 정상)** |
| T4 | 🏨 중대형 + 슈퍼어드민 | **핵심 PASS** — 예약 알림 신청(→정리)/quota/구독/결제 mock/비콘/액션 보드 6키/심사/신고(비파괴)/정산/공지 발행·삭제 |

## 2. 발견 → 즉시 수정 (3건)

| # | 발견 (트랙) | 수정 |
|---|---|---|
| 1 | **매장 생성(POST) 시 categories/holidays/benefits 무시** — PATCH 만 처리, 신규 매장 첫 저장에서 조용히 유실 (T3) | `routes/store.py` 생성 INSERT 에 JSON 3종 추가. E2E: 생성 응답에 즉시 반영 확인 |
| 2 | **신규 사장이 매장을 만들 UI 경로 부재** — StoreInfo.handleSave 가 `update(null)` 만 호출 → 승인 직후 저장 불가 (T3 INFO-1 추적) | facilityId 없으면 `StoreService.create` 분기 + 신규 fid 반영 |
| 3 | **app_versions 미시드** — 버전체크가 빈 정책 (T2) | ios/android 1.0.0 시드. `/api/version/check` 정상 응답 확인 |

## 3. 무결 판정 (오탐 해명)

- "검색 한글 0건" (T1·T2) → **curl 이 raw 한글 전송한 테스트 아티팩트**. URL 인코딩 시 정상 (카페 2건). mobile 은 Uri 자동 인코딩 — 실사용 무결
- multipart 필드명 `image` (T3 INFO-4) → provider StoreService 도 `image` 로 전송 — 정합
- 채팅 번역 stub: dev 모드 정상 (운영 번역 키 단계에서 실번역)

## 4. 기록 (v1 정책 확인 / 후속 후보)

- 쿠폰 발급 = 특정 user 대상 직접 발급 (T3 INFO-3) — v1 회원 QR 운영 모델(P22)과 일치. 정책성 대량 발급은 Phase 2 후보
- 찜 POST 응답에 row id 없음 (T2) — mobile 미사용으로 무해, API 위생 차원 후속 후보
- pending 사장 로그인 403 + `pending_approval:true` — 의도된 정책 확인

## 5. 테스트 생성 데이터 (출시 전 일괄 정리 목록)

- 계정: `tourist1@persona.test`, `koreauser1@persona.test`(생성 시), `boss1@persona.test`, `staff1@persona.test`
- 매장: 페르소나 카페 (fid 12) — 메뉴 20·이미지 12·쿠폰 74(used)·스탬프정책 6
- 문의/신고: 제목·사유 "페르소나 테스트" 식별자
- 정리: `*@persona.test` 와 위 식별자 기준 DELETE (2호점 fid 13 은 검증 직후 정리 완료)

## 6. 결론

**1단계 (로컬 개발+테스트) 완료 판정.** 6 페르소나 전 여정이 실 API 로 통과했고,
발견 3건은 즉시 수정·재검증됨. 다음 = 법인카드 도착 시 외부 서비스 신청 (2단계),
물리 비콘 도착 시 P16-b BLE 핸드오프 + 비콘 통합 리허설.
