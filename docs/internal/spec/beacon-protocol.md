# spec/beacon-protocol.md — BLE 비콘 클라우드 핸드셰이크 프로토콜 (정교)

> **트랙**: 실제 개발 (`docs/internal/`) · 정교·상세
> **버전**: v0.1 (2026-05-26)
> **창업지원단 별첨 2 (캐주얼) 와 비교**: `docs/Pathwave_MVP_BeaconProtocol_v1.0.docx`
> **관련 코드**: `routes/beacon.py`, `models/database.py` (beacons / beacon_wifi / wifi_profiles / wifi_access_grant / user_wifi_logs)

---

## 1. 본 문서의 위치

- 본 문서는 **실제 구현 기준** 정교한 명세.
- 창업지원단 제출용 문서는 캐주얼·간단 (UUID + Nonce + TTL 추상 설명 만).
- 본 문서는 코드와 1:1 매핑되어야 하며, 변경 시 PR 번호 명기.

## 2. 시스템 그림

```
┌─────────────┐   BLE 광고      ┌─────────────┐  HTTPS POST       ┌──────────────┐
│  Beacon     │ ───────────►   │  Mobile App │ ───────────────► │   Backend    │
│ (FSC-BP108B)│  UUID + Major   │   (Flutter) │  /api/beacon/    │   (Flask)    │
│ BLE 5.x     │  + Minor + ext  │   BLE scan  │  handshake       │              │
└─────────────┘                 └─────────────┘                  └──────┬───────┘
                                       ▲                                │
                                       │  ssid+pw+grant_id              │
                                       │  + wifis[] (multi-SSID)        │
                                       │◄───────────────────────────────┘
                                       │
                                       ▼
                                  iOS/Android WiFi
                                  Settings API 호출
                                  → AP 접속
```

## 3. 하드웨어 — FSC-BP108B (테스트용 9대)

| 항목 | 값 |
|---|---|
| 모델 | FSC-BP108B (메모리: `project_beacon_spec.md`) |
| BLE 규격 | Bluetooth 5.x |
| 전원 | 배터리 또는 USB 상시전원 |
| 펌웨어 OTA | 가능 (양산 단계 운영, 본 단계는 수동 적용) |
| 상태 | inventory → active → inactive / lost |
| 신호 강도 (RSSI) | -50 ~ -90 dBm (실내 환경) |

테스트용 비콘 9대 한정 (SOW v1.1 §4.4).
양산은 별도 협의.

## 4. DB 스키마 (코드 일치)

### 4.1 `beacons`
| 컬럼 | 타입 | 의미 |
|---|---|---|
| id | INTEGER PK | 내부 ID |
| serial_no | TEXT | 비콘 일련번호 (CSV 입고 시) |
| uuid | TEXT | iBeacon UUID (광고 패킷) |
| major | INTEGER | 매장 식별 (0~65535) |
| minor | INTEGER | 비콘 위치 식별 (0~65535) |
| facility_id | INTEGER FK | claim 된 매장 |
| status | TEXT | `inventory` / `active` / `inactive` / `lost` |
| battery_pct | INTEGER | 배터리 잔량 (%) |
| battery_voltage_mv | INTEGER | 배터리 전압 (mV) |
| battery_updated_at | TEXT | 마지막 보고 시각 |
| firmware_ver | TEXT | 펌웨어 버전 |
| role | TEXT | (Phase B) 비콘 역할 — entry / corridor / room 등 |
| last_seen_at | TEXT | 마지막 인식 시각 |
| created_at | TEXT | 입고 시각 |

### 4.2 `beacon_wifi` — 비콘 ↔ SSID 매핑
| 컬럼 | 의미 |
|---|---|
| beacon_id | FK beacons |
| wifi_profile_id | FK wifi_profiles |
| **priority** | **Phase B 무중단 핸드오프 시 우선순위 (낮을수록 높음)** |

### 4.3 `wifi_profiles`
| 컬럼 | 의미 |
|---|---|
| facility_id | FK |
| ssid | SSID |
| password | AES-GCM 암호화 (`secrets.encrypt_secret()`) |
| **scope** | `'facility'` / `'unit'` — Phase B 의 unit grant |
| **unit_id** | FK units (방/구역) — scope='unit' 일 때 |
| **credential_mode** | `'shared'` / `'individual'` — Phase B `managed` 자격증명 |
| bssid | (선택) AP MAC — 동일 SSID 다중 AP 시 |
| country | 국가코드 (regulatory) |
| active | 1/0 |

### 4.4 `wifi_access_grant` — 사용자별 발급 토큰
| 컬럼 | 의미 |
|---|---|
| user_id | FK users |
| target_type | `'beacon'` / `'facility'` / `'unit'` |
| target_id | 위 type 의 ID |
| valid_from / valid_until | 유효기간 (Phase B 다건 동시 발급 시) |
| source | `'handshake'` / `'manual'` / `'invitation'` |
| granted_by_actor_role | `'system'` / `'super_admin'` / `'facility_owner'` |
| granted_by_actor_id | 부여자 ID |
| revoked_at | 회수 시각 (null 이면 활성) |

### 4.5 `user_wifi_logs` — 감사
- user_id × facility_id × timestamp → 첫 방문 / 재방문 판단
- 자동 스탬프·쿠폰 발급의 조건 (handshake 첫 진입 시)

## 5. 핸드셰이크 흐름 — `POST /api/beacon/handshake`

### 5.1 요청 (mobile → backend)

```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "major": 1234,
  "minor": 1,
  "rssi": -65,                  // (선택) 신호강도 — Phase B 핸드오프 입력
  "scan_at": "2026-05-26T10:30:00Z"
}
```

### 5.2 백엔드 처리 (`routes/beacon.py` 기준)

```
1. Rate limit 검사 — 60/min, 600/hour per IP
2. UUID+major+minor 로 beacons 조회. 못 찾으면 UUID-only fallback.
3. beacon.status != 'active' 이면 403.
4. beacon.facility_id 확인.
5. beacon_wifi 에서 매핑된 wifi_profiles 조회 (priority ASC).
   없으면 facility 전체 active wifi_profiles fallback.
6. wifi 응답 구성:
   - 호환 필드: wifi = {ssid, password(복호화)}  (첫 번째)
   - 신규 필드: wifis = [{ssid, password, priority}, ...]  (전체)
7. user_wifi_logs 에서 (user, facility) 첫 방문 확인.
8. 첫 방문이면 — 자동 스탬프 + 자동 쿠폰 발급 시도.
9. 응답.
```

### 5.3 응답

```json
{
  "ok": true,
  "facility_id": 42,
  "wifi": {                       // 호환용 (단일)
    "ssid": "PathWave-Cafe",
    "password": "복호화된 평문"   // ⚠️ HTTPS 필수
  },
  "wifis": [                       // Phase B 다건
    {"ssid": "PathWave-Cafe",   "password": "...", "priority": 0},
    {"ssid": "PathWave-Cafe-5G","password": "...", "priority": 1}
  ],
  "granted_stamp": {"id": ..., "current_count": 3, "target_count": 10},
  "granted_coupons": [{"id": ..., "title": "...", "expires_at": "..."}],
  "auto_stamp_skipped_reason": null  // 또는 'already_today' 등
}
```

## 6. 본 단계 (Phase 1 B 스코프) vs 향후

| 항목 | Phase 1 B (현재) | Phase 2+ (향후) |
|---|---|---|
| 광고 패킷 nonce | ⚠️ **광고 패킷에 nonce 미포함** — UUID+major+minor 정적 | 광고 페이로드에 rolling nonce 추가 (replay 방지) |
| 광고 TTL | ⚠️ 서버측 TTL 없음 — 매 요청마다 검증 | 광고에 TS+TTL → 서버가 거부 |
| RSSI 기반 신호 검증 | ⚠️ 미사용 (요청 body 받기만) | 평균 RSSI < -90 거부, 위·변조 비콘 탐지 |
| 핸드셰이크 응답 다건 SSID | ✅ `wifis[]` 구현됨 | (유지) Phase B 핸드오프 입력 |
| 자동 스탬프 / 쿠폰 | ✅ 첫 방문 시 발급 | (유지) 정책 정교화 |
| `wifi_access_grant` 발급 | ⚠️ 발급 미구현 — wifi 평문만 응답 | grant 발급 + token 회수 가능 구조 |
| OTA 펌웨어 | 수동 적용 | 양산 시 OTA 서버 신설 |
| KC 인증 | 시제품 등록 | 양산 단계에서 정식 |
| 보안 | AES-GCM 비밀번호 암호화 ✅ | + nonce / TTL / RSSI 검증 / grant 토큰 |

⚠️ 갭은 [`wifi-roaming.md`](wifi-roaming.md) 의 Phase B P14~P19 PR 로 단계적 해소.

## 7. 보안 위협 모델

### 7.1 위협
1. **비콘 클로닝** — 광고 패킷 단순 UUID 라 누구나 송출 가능.
   → Phase 2 의 rolling nonce + 서버 nonce 검증으로 완화.
2. **Replay** — 같은 광고 다시 보내기.
   → 동일. nonce + TS+TTL 필요.
3. **WiFi 비밀번호 유출** — handshake 응답에 평문 포함.
   → 현재: HTTPS 필수. AES-GCM 은 DB 저장 시. 응답은 평문.
   → Phase 2: WPA-Enterprise (EAP) 로 전환 또는 grant 토큰 발급.
4. **사용자 토큰 탈취** — JWT 만 있으면 handshake 호출 가능.
   → Rate limit (60/min) 으로 부분 완화. Phase 2 에서 디바이스 binding.

### 7.2 완화 우선순위 (Phase 2)
1. Rolling nonce (광고 패킷)
2. RSSI 기반 거리 검증
3. `wifi_access_grant` 발급 + 토큰 회수
4. 디바이스 binding (push_token 또는 hw_id)

## 8. OTA 업데이트 (양산 단계)

- 본 단계 (9대) 는 수동 펌웨어 적용으로 충분.
- 양산 (100대+) 부터 OTA 서버 신설:
  - `/api/beacon/ota/manifest` — 펌웨어 버전 메타
  - `/api/beacon/ota/binary` — 서명된 펌웨어 바이너리
  - 비콘이 BLE → mobile relay → backend 로 다운로드
- 보안: 펌웨어 코드 서명 + 무결성 검증 (SHA-256)

## 9. 비콘 라이프사이클

```
[입고]
  ├ admin (CSV 업로드)
  ├ status = 'inventory'
  └ facility_id = NULL

[claim]
  ├ provider (매장 페어링)
  ├ status = 'active'
  └ facility_id = SP 매장 ID

[운영]
  ├ battery_pct 자동 보고
  ├ last_seen_at 갱신
  └ user_wifi_logs 누적

[이상]
  ├ inactive (battery < 5%)
  └ lost (last_seen_at > 30일)
```

## 10. 관련 PR / 로드맵

| PR | 내용 | 상태 |
|---|---|---|
| (Phase 1 P14) | handshake endpoint + AES-GCM | ✅ |
| (Phase 1 P15) | `wifis[]` multi-SSID 응답 | ✅ |
| Phase 1 P16-a | provider unit / unit grant CRUD | ✅ |
| Phase 1 P16-b | mobile BLE 무중단 핸드오프 | ⏳ 물리 비콘 도착 후 |
| Phase 1 P17 | rolling nonce 광고 페이로드 (Phase 2 이관 검토) | ⏳ |
| Phase 2 | RSSI 거리 검증 | ⏳ |
| Phase 2 | `wifi_access_grant` 발급 / 회수 | ⏳ |
| Phase 2 | OTA 서버 | ⏳ |

자세한 PR 상태: `docs/pathwave_phase1_plan_2026-05-21.md` §6 표.

## 11. 테스트 계획

### 11.1 비콘 단위 (9대)
- 광고 패킷 검증 (nRF Connect 앱)
- 배터리 → 임계 보고 시뮬레이션
- 펌웨어 수동 업데이트 1회

### 11.2 핸드셰이크 (mobile 시뮬레이터)
- 단일 SSID handshake → 응답 검증
- multi-SSID handshake → `wifis[]` 순서 검증 (priority ASC)
- inactive 비콘 → 403
- 미등록 UUID → 404
- rate limit 초과 → 429

### 11.3 통합 (월요일 비콘 통합 리허설 — 메모리 `project_next_week_sprint.md`)
- 실 비콘 9대 + mobile + provider + admin 3 콘솔 동시 검증
- BLE 인식 → handshake → WiFi 연결 → 스탬프 적립 → 채팅까지 end-to-end

## 12. 향후 검토 사항

- [ ] 광고 페이로드 nonce 도입 시점 (Phase 2 vs Phase 3)
- [ ] RSSI 거리 검증 알고리즘 (단순 임계값 vs Kalman filter)
- [ ] OTA 서버 — Mosquitto MQTT 대안 검토
- [ ] WPA-Enterprise 전환 검토 (대형 리조트 대상)
- [ ] 비콘 양산 모델 확정 (FSC-BP108B 유지 vs 변경)
