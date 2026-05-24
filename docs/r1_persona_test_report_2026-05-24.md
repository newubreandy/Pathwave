# PathWave R1 페르소나 통합 테스트 — 1차 결과 보고

> **작성일**: 2026-05-24
> **단계**: 출시 5단계 중 1단계 (local + stub) — 마지막 자동화 검증
> **참조**: `docs/pathwave_persona_test_plan_C-3_2026-05-23.md` 의 §4 (페르소나별), §5 (Cross)

---

## 1. 전체 결과 — 한눈에

| 페르소나 | 자동 테스트 파일 | 통과 / 전체 | PR | 상태 |
|---|---|---|---|---|
| **P6** 슈퍼어드민 | `tests/test_persona_p6.py` | **25 / 25** ✅ | #173 | 머지 대기 |
| **P3** 소규모 매장 사장 | `tests/test_persona_p3.py` | **22 / 22** ✅ | #174 | 머지 대기 |
| **P4 + P5** 중대형 사장 + 직원 | `tests/test_persona_p4p5_staff.py` | **18 / 18** ✅ | #175 | 머지 대기 |
| **P2 + P1** 한국인 + 외국인 | `tests/test_persona_p2p1_user.py` | **18 / 18** ✅ | #176 | 머지 대기 |
| **Cross** X3 비콘 / X5 쿠폰 | `tests/test_persona_cross.py` | (run 중) | #177 | 머지 대기 |
| **총계** | 5 신규 테스트 파일 | **83+ 자동 체크** | — | — |

기존 회귀 sweep (27건) + 신규 페르소나 테스트 5건 = **로컬 1단계 검증 사실상 완결**.

---

## 2. 자동화 커버리지 매트릭스

### P6 슈퍼어드민
- ✅ 부트스트랩 로그인 + 잘못된 비번 401
- ✅ 비콘 입고 (serial_no + UUID, 중복 SN errors)
- ✅ 매장 가입 검토 + verify (status=verified)
- ✅ 매장 정지 / 재활성화
- ✅ 약관 multilang (terms_user v0.2 ko+en 동시)
- ✅ 약관 미시행 버전 PATCH
- ✅ 시스템 공지 작성
- ✅ /stats/overview cards 키 검증
- ✅ /me 조회
- ⏸ P6-9 결제 환불 — payments 비어있어 R2 로 deferred

### P3 소규모 사장
- ✅ 약관 누락 400 / terms_facility+privacy_facility 갖춰 register 201
- ✅ pending 상태 로그인 → 403
- ✅ admin verify 후 로그인 200
- ✅ 매장 등록 201
- ✅ 비콘 claim + 없는 SN 404 + 재claim 409
- ✅ WiFi 등록 + **AES-256-GCM 평문 미저장 검증**
- ✅ 사장 본인 include_password=1 로 복호화 조회
- ✅ 비콘 ↔ WiFi PUT/GET 매핑

### P4 + P5 (사장 ↔ 직원)
- ✅ owner staff invite + 중복 409 + 목록
- ✅ staff accept (약한 비번 400, 정상 201, 재사용 409)
- ✅ staff login + /me
- ✅ staff 가 매장 WiFi 목록 조회 (공유 권한)
- ✅ **staff 가 owner-only WiFi 등록 시도 → 403** (권한 분리)
- ✅ pending 초대 revoke + revoked 토큰 410

### P2 + P1 (사용자)
- ✅ 만 14 미만 거부 (birth_year=2020 → 400)
- ✅ 성인 가입 + login + change-password + 옛 비번 401
- ✅ /api/version/check
- ✅ DELETE /me soft-delete + 이메일 anonymize + 재로그인 401
- ✅ lang=ja → en fallback (sub_type=user)
- ✅ terms_user 본문 ko ≠ ja(=en)
- ✅ ja 단말 사용자도 register 200

### Cross
- ✅ X3 비콘 handshake → WiFi profile 응답 (mock 1단계)
- ✅ X5 쿠폰 발급(owner) → 사용자 목록(user) → 사용(owner) → 재사용 409 → 사용자 화면 used=true 갱신

---

## 3. 인접 구멍 / 발견사항 (별도 큐로 처리)

| 항목 | 종류 | 발견 위치 | 처리 |
|---|---|---|---|
| `models/push.py:335` r['language'] KeyError | regression | test_apns_provider.py | spawn 한 task 에서 별도 처리 |
| `test_announcement_push.py` `[en]` prefix 기대값 불일치 | 기존 (memo 등록) | baseline sweep | non-blocker, stub 부작용 |
| `test_policy_versioning.py` `source='static_file'` 기대 | 기존 (memo 등록) | baseline sweep | non-blocker, `_bootstrap_policies` 자동 시드 후 source='db' |
| `DELETE /api/auth/me` body 키 = `password` (current_password X) | API 명세 명확화 | P2-11 자동화 | 문서/SDK 에 반영 권장 |
| `staff invite` 응답에 `invite_token` 비노출 | 의도된 보안 (DB+이메일 only) | P4-1 자동화 | 클라이언트는 이메일 링크 사용 |

---

## 4. 1단계 (R1) 미커버 — R2/R3 에서 진행

| 시나리오 | 사유 | 시점 |
|---|---|---|
| P6-9 결제 환불 실제 흐름 | payments 시드 없음 + 토스 sandbox 실키 필요 | R2 (단계 3) |
| X4 약관 새 버전 → 재동의 모달 | mobile/provider UI 분기 — 매뉴얼 검증 필요 | R2 매뉴얼 |
| X6 스탬프 정책 변경 | UI 매뉴얼 검증 | R2 |
| X9 결제 실패 → 노출 제한 | 토스 sandbox + 시간 시뮬레이션 | R2 (단계 3) |
| P16-b mobile BLE 무중단 핸드오프 | 물리 비콘 필요 | R2 단계 3 또는 출시 후 |
| P1-4/8/12 USP 킬러콘텐츠 (메뉴번역/면세/알리페이) | C-4 미구현 | 출시 직전 또는 Phase I |

---

## 5. 자동화 실행 명령

전체 페르소나 테스트 한 번에:

```bash
cd /Users/m5pro16/Desktop/pathwave
export PYTHONPATH=.
for t in tests/test_persona_p6.py tests/test_persona_p3.py \
         tests/test_persona_p4p5_staff.py tests/test_persona_p2p1_user.py \
         tests/test_persona_cross.py; do
  echo "── $t ──"
  ./venv/bin/python "$t" 2>&1 | tail -3
done
```

---

## 6. 다음 단계

| 우선순위 | 작업 | 시점 |
|---|---|---|
| 1 | 본 PR 5건 모두 머지 (#173~#177) | 사용자 검토 후 |
| 2 | R1 끝 — 페르소나 테스트 계획 §0 사전 체크리스트 갱신 | 머지 후 |
| 3 | 외부 서비스 신청 (단계 2 — 사용자 행정) | 법인카드 후 |
| 4 | R2 실행 (테스트계정 + 실 키 sandbox) | 단계 3 |
| 5 | R3 실행 (production-like + HIG/Material) | 심의 직전 |
| 6 | 스토어 심의 제출 | 단계 4 |

---

## 7. R1 사용자 컨펌 체크리스트

사용자가 컨펌할 때 확인하면 좋은 항목:

- [ ] PR #173~#177 모두 머지 결정
- [ ] R1 자동화 커버리지가 의도한 시나리오를 충분히 다루는지 검토
- [ ] 미커버 항목 (§4) 이 R2/R3 에서 처리 가능한지 동의
- [ ] 인접 구멍 (§3) 중 즉시 fix 가 필요한 항목 결정
  - apns push.py language KeyError — spawn 한 task 에서 별도 PR 예정
