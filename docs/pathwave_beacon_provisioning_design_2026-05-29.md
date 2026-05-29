# PathWave 비콘 프로비저닝 워크플로우 설계 (2026-05-29)

> 성격: **실제 개발 설계 문서** (SOW/제출용 아님). 구현 전 합의용.
> 결정자: 사용자(2026-05-29) — "슈퍼어드민 주도 + 점주 신청 시 설치위치 입력 + 라벨 프린트 자동화".

## 1. 목표 (사용자 정의 플로우)

```
① 점주: 서비스 신청 — 설치위치 + WiFi(SSID/PW) + 수량 입력
② 슈퍼어드민: 신청 내역을 보고, 위치마다 인벤토리 비콘을 매칭·할당·활성화
③ 슈퍼어드민: "어느 비콘 = 어느 위치" 라벨(스티커) 인쇄 → 비콘에 부착
④ 발송 → 점주 수령 → 지정 위치에 부착 → 매장정보에서 확인(읽기전용)
```
운영자 주도. 수작업 최소화(라벨 자동 인쇄).

## 2. 현재 상태 (2026-05-29 코드 검증)

| 단계 | 현재 | 비고 |
|---|---|---|
| ① 신청서(위치+WiFi+수량) UI | ✅ 있음 | `ServiceRequest.jsx` 항목별 location/ssid/password/기간 |
| ① 신청 제출 → 저장 | ❌ 없음 | `:334` TODO, console.log만. 저장 안 됨 |
| ② 슈퍼어드민 신청 조회 | ❌ 없음 | `Approvals`는 '계정 승인'만 |
| ② 비콘 매칭·할당·활성 | ◑ 수동 | admin assign + location_label API 있음, 신청 연결 없음 |
| ③ 라벨 인쇄 | ❌ 없음 | 본 설계로 신규 |
| ④ 점주 읽기전용 확인 | ✅ #235 | location_label 포함 목록 |

핵심 공백 = **①저장 · ②슈퍼어드민 매칭 · ③라벨인쇄**.

## 3. 데이터 모델

신규 테이블 2개 (기존 beacons/wifi_profiles/beacon_wifi 와 연계):

```
service_requests
  id, facility_id, facility_account_id, service_type('wifi'|...),
  status('pending'|'matched'|'shipped'|'installed'|'canceled'),
  created_at, note

service_request_units              -- 신청 1건 안의 위치별 유닛 (N개)
  id, request_id,
  location_label,                  -- 점주가 입력한 설치위치 ("정문 입구", "객실 101")
  ssid, wifi_password_enc,         -- AES-256-GCM 암호화 저장 (models/crypto 재사용)
  period_start, period_end,
  beacon_id,                       -- 매칭된 인벤토리 비콘 (NULL=미매칭)
  status('pending'|'matched')
```

매칭 시 (슈퍼어드민이 unit ↔ 인벤토리 비콘 선택):
- `beacons.facility_id = request.facility_id`, `status='active'`, `location_label = unit.location_label`
- `wifi_profiles` 생성(ssid/pw) + `beacon_wifi` 연결
- `service_request_units.beacon_id = 선택 비콘`, unit.status='matched'

## 4. 화면

- **provider `ServiceRequest`** — 현 UI 유지, **제출 배선만** 추가 → `POST /api/service-requests`.
- **admin 신청관리(신규)** — pending 신청 목록 → 상세(유닛별 위치/WiFi) → 유닛마다 인벤토리 비콘 선택(시리얼 드롭다운) → **일괄 할당·활성**.
- **admin 라벨 인쇄** — 매칭된 유닛 → "라벨 인쇄" 버튼 → 라벨 시트 → `window.print()`.
- **provider 매장정보** — 읽기전용 목록 (#235 완료).

## 5. ⭐ 라벨(스티커) 인쇄 설계

- **방식**: 브라우저 `window.print()` + 전용 print CSS. OS 인쇄창에서 **저렴한 스티커/라벨 프린터** 선택 → 별도 드라이버/플러그인 불필요. (정밀 무다이얼로그 인쇄가 필요해지면 QZ Tray 등 후속 검토)
- **크기**: 비콘(48×37mm)보다 작게 → 기본 **40×25mm** (프린터 라벨지 규격에 맞춰 설정 가능).
  ```css
  @page { size: 40mm 25mm; margin: 0; }
  @media print { body * { visibility: hidden; } .label-sheet, .label-sheet * { visibility: visible; } }
  .label { width: 40mm; height: 25mm; page-break-after: always; }
  ```
- **라벨 내용 (확정: 텍스트만)**: 매장명(작게) / **설치위치(굵게, 메인)** / 시리얼(아주 작게).
  - QR 미포함 — 40×25mm 라벨에 텍스트+QR 둘 다는 빡빡(비콘 자체가 작음). QR은 추후 더 큰 라벨 사용 시 옵션으로.
- 라벨 1개당 1페이지(라벨 프린터 피드 단위). 여러 개면 연속.
- 크기는 admin 설정값(기본 40×25mm) — `@page size` 에 주입.

## 6. 단계별 구현 (phase)

- **P-A**: `service_requests`/`units` 테이블 + `POST/GET /api/service-requests` + provider 제출 배선 + WiFi PW 암호화
- **P-B**: admin 신청관리·비콘 매칭 화면 + 매칭 API(unit↔beacon 할당·활성·wifi 연결)
- **P-C**: admin 라벨 인쇄 (라벨 시트 + print CSS, 크기 설정)
- **P-D**: 상태 추적(shipped/installed) + 점주 확인(읽기전용 #235 활용)

## 7. 결정 (사용자, 2026-05-29 확정)

1. **라벨 규격**: 40×25mm 기본 + admin 설정값(폭×높이 조정). 추후 라벨지 모델에 맞춤.
2. **라벨 QR**: 미포함(텍스트만). QR은 큰 라벨 쓸 때 옵션으로 후속.
3. **WiFi 비밀번호**: 점주 신청 시 입력(현 UI) + AES-256-GCM 암호화 저장. ✅
4. **순서**: P-A → P-B → P-C → P-D. ✅

## 8. 진행 로그

- 2026-05-29: 설계 확정.
- ✅ **P-A** (#236) — service_requests/units + 저장 API + provider 제출 배선 + WiFi PW 암호화.
- ✅ **P-B** (#237) — admin 신청관리 + 비콘 매칭(할당·활성·major/minor·설치위치·WiFi 연결).
- ✅ **P-C** — admin 라벨 인쇄(매칭 유닛별 1장, 새 창 격리 print CSS, 크기 설정 기본 40×25mm, 텍스트: 매장명/설치위치/시리얼).
- ⬜ **P-D** — 상태 추적(shipped/installed) + 점주 확인(읽기전용 #235).
