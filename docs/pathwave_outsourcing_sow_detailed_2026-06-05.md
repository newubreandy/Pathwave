# PathWave — 외주 개발 과업지시서 (상세본)

> **버전**: v1.1 (2026-06-05)
> **요약본**: `pathwave_outsourcing_sow_2026-06-05.md` (v1.0, 391 줄)
> **본 문서**: 각 모듈의 데이터 흐름·API 인터페이스·DB 스키마·코드 패턴 포함. 외주 개발사가 본 문서만 보고 작업 시작 가능한 수준.
> **출처**: PathWave 자체 코드(`routes/`, `models/`, `mobile/lib/`, `admin-web/`, `provider-web/`) 에서 직접 추출.

---

## 목차

1. 작성 원칙 + 역할 분담
2. 디자인 시스템 (3 콘솔 공통)
3. 인증 / JWT / 권한 가드
4. Feature Flag (모듈화)
5. 모듈 상세 — 1차 (12 모듈)
   - 5.1 wifi_roaming / beacon
   - 5.2 stamp
   - 5.3 coupon
   - 5.4 chat + chat_translate
   - 5.5 menu_translate + menu_ocr_device
   - 5.6 push + email_notify
   - 5.7 subscription_payment_toss
   - 5.8 season_theme
6. 정책·약관 / 신고 / 차단
7. 다국어 (i18n) 23 언어
8. 환경 분리 (운영 / 클론) + 배포
9. 보안 + 운영 검증
10. 테스트 + QA
11. 모듈 상세 — 2차 (8 모듈)
12. API 스펙 요약
13. 산출물 / 검수 / 일정 / 변경 관리

---

## 1. 작성 원칙 + 역할 분담 (v1.0 SOW 와 동일)

| 역할 | 발주사 (트리거소프트) | 개발사 |
|---|---|---|
| 기획·요구사항·UX·콘텐츠·정책 | ✅ | — |
| 디자인 시각화 / 디자인 시스템 | — | ✅ |
| 퍼블리싱 (HTML/CSS·반응형·접근성) | — | ✅ |
| 개발 (mobile / 3 콘솔 / 백엔드) | — | ✅ |
| 테스트 지원 (단위·통합·페르소나·QA·자동화·실기기) | — | ✅ |
| 배포·운영 지원 (CI/CD·서버 셋업·모니터링 연동) | — | ✅ |
| 인프라 계약·앱스토어 가입·외부 SaaS 가입·법인 행정·외부 가맹 | ✅ | — |
| 최종 검수·의사결정 | ✅ | — |

---

## 2. 디자인 시스템 (3 콘솔 공통)

### 2-1. 컬러 정책 (메모리 확정)

| 콘솔 | 포인트 색 |
|---|---|
| mobile | 보라 `#8B5CF6` |
| provider-web | 녹색 `#22C55E` |
| admin-web | 블루 `#2563EB` |

→ 3 콘솔 모두 동일 클래스 / 색상 토큰만 차이.

### 2-2. mobile 디자인 토큰

`lib/utils/app_theme.dart` 단일 소스. 화면/위젯에서 **하드코딩 금지**.

```dart
class AppTheme {
  // 색상 (변경 금지)
  static const Color primary       = Color(0xFF7C3AED); // 보라
  static const Color primaryLight  = Color(0xFFA78BFA);
  static const Color secondary     = Color(0xFF06B6D4); // 시안
  static const Color background    = Color(0xFF0F0F1A);
  static const Color surface       = Color(0xFF1E1E2E);
  static const Color textPrimary   = Color(0xFFFFFFFF);
  static const Color textSecondary = Color(0xC8FFFFFF);  // white 78%
  static const Color textHint      = Color(0x8AFFFFFF);  // white 54%
  // 라운드
  static const double rSm = 12, rMd = 16, rLg = 20, rXl = 28, rPill = 999;
  // 여백 (4 배수)
  static const double s1 = 4, s2 = 8, s3 = 12, s4 = 16, s5 = 20, s6 = 24;
}
```

### 2-3. 공통 위젯 (mobile)

| 위젯 | 용도 | 정책 |
|---|---|---|
| `PwAppBar` | 모든 push 화면 | raw `AppBar` 금지. `flexibleSpace` 에 흰 글래스 6% + blur 14 + 하단 보더 |
| `PwButton` | 모든 버튼 | primary(보라+흰) / secondary(흰 글래스+흰) / outlined / text / danger. **흰 텍스트 통일**, w600 / 16px / radius 16 |
| `PwTextField` | 모든 입력 | `inputDecorationTheme` 자동 (흰 글래스 12% + 흰 보더) |
| `PwCard` | 모든 카드 | 디폴트 = 흰 글래스(반투명+blur). `glass: false` 로 단색 회귀 |
| `GlassCard` / `GlassPill` | 글래스 변형 | BackdropFilter blur 20 + 흰 1px 보더 |
| `PwDialog` / `showPwDialog` | 모든 팝업 | barrier 에 blur 10 + 검정 45% scrim. 카드는 흰 글래스 16% + 보더 + 라운드 20. **타이틀 중앙, actions 중앙** |
| `PwSheet` / `showPwSheet` | 모든 하단 시트 | 글래스 + 드래그 핸들 + blur barrier |
| `PwSwitch` | 모든 토글 | Material 3 `Switch` (Switch.adaptive 금지 — iOS 녹색 강제됨). 글로벌 `switchTheme` 보라 ON |
| `SeasonalBackground` | 모든 Scaffold 배경 | MaterialApp builder 에서 전역 적용. 활성 테마 이미지 또는 fallback 그라데이션 |
| `SeasonalParticles` | 시즌 파티클 | 정적(애니메이션 없음). 봄=꽃잎 / 여름=물방울 / 가을=단풍 / 겨울=눈송이 |

### 2-4. 글로벌 ThemeData (NeuTheme — 실제 사용 테마)

```dart
ThemeData get themeData => ThemeData(
  useMaterial3: true,
  brightness: Brightness.dark,
  scaffoldBackgroundColor: Colors.transparent,
  appBarTheme: const AppBarTheme(
    backgroundColor: Colors.transparent,
    surfaceTintColor: Colors.transparent,
    elevation: 0, scrolledUnderElevation: 0,
  ),
  switchTheme: SwitchThemeData(
    thumbColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? Colors.white : Colors.white.withValues(alpha: 0.85)),
    trackColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? primary : Colors.black.withValues(alpha: 0.40)),
  ),
  checkboxTheme: CheckboxThemeData(
    fillColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? primary : Colors.transparent),
    checkColor: WidgetStateProperty.all(Colors.white),
  ),
  // tabBarTheme / dialogTheme / bottomSheetTheme / dividerTheme / navigationBarTheme 모두 흰 글래스 톤 통일
);
```

### 2-5. 안내/경고 문구 가이드

박스(PwCard) 없이 평문 흰. 앞에 `※` prefix. 11~13px, line-height 1.5.

```dart
// 가이드 — 안내/경고는 박스 없이 평문 흰. ※ prefix.
Padding(
  padding: const EdgeInsets.symmetric(horizontal: 4),
  child: Text('※ ${_error!}',
    style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.5)),
)
```

### 2-6. 모달 / 시트 정책

| 용도 | 위젯 |
|---|---|
| 안내 / 확인 (Yes/No, OK) | `showPwDialog` (중앙 카드 — 흰 글래스 + 블러 딤) |
| 작성 / 긴 입력 / 약관 보기 | `showPwSheet` (하단 시트 — 흰 글래스 + 드래그 핸들 + 블러 딤) |

raw `showDialog` / `showModalBottomSheet` 금지.

### 2-7. provider-web / admin-web 디자인 시스템

- 토큰: `src/index.css` 의 CSS 변수 (`--bg`, `--bg-2`, `--bg-3`, `--text`, `--text-hint`, `--accent`, `--border` 등)
- 공통 클래스: `.modern-page`, `.page-header-section`, `.page-header-row`, `.btn`, `.btn-primary`, `.btn-ghost`, `.form-input`, `.form-label`, `.form-hint`, `.form-error`
- Modal: `components/Modal.jsx` (`open`, `onClose`, `title`, `children`, `footer`, `size`)
- 아이콘: `lucide-react`
- WCAG AA — 텍스트 대비 4.5:1 이상 (사용자 정책)

### 2-8. 디자인 산출물 (개발사)

- Figma 또는 동등 파일 (mobile + web 분리)
- 토큰표 + 컴포넌트 라이브러리
- 시즌 배경 톤 가이드 (4 계절 + 이벤트)
- 아이콘 세트 (필요 시 추가)

---

## 3. 인증 / JWT / 권한 가드

### 3-1. 토큰 4 종 (sub_type 분리)

| sub_type | 발급 라우트 | 보호 데코레이터 |
|---|---|---|
| `user` | `auth.py /api/auth/login` | `decode_access_token(expected_sub_type='user')` |
| `facility` | `facility.py /api/facility/login` | `require_facility_actor(['owner'])` |
| `staff` | `staff.py /api/staff/login` | `require_facility_actor(['matre', 'staff'])` |
| `super_admin` | `admin.py /api/admin/login` | `require_super_admin(roles=['super'])` |

### 3-2. JWT 구조

```python
{
  "user_id": 123,
  "sub_type": "user|facility|staff|super_admin",
  "role": "super|admin|owner|matre|staff",  # sub_type 별 의미 다름
  "kind": "access|refresh",
  "exp": 1234567890,
}
```

서명: HS256 (`SECRET_KEY`). access 1시간 / refresh 30일 (운영).

### 3-3. 가드 데코레이터 패턴

```python
# routes/auth.py
def require_super_admin(roles=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_hdr = request.headers.get('Authorization', '')
            if not auth_hdr.startswith('Bearer '):
                return jsonify({'success': False, 'message': '인증 토큰이 없습니다.'}), 401
            token = auth_hdr.split(' ', 1)[1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return jsonify({'success': False, 'message': '토큰이 만료되었습니다.'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'success': False, 'message': '유효하지 않은 토큰입니다.'}), 401
            if payload.get('sub_type') != 'super_admin':
                return jsonify({'success': False, 'message': 'Super Admin 토큰이 아닙니다.'}), 401
            actor_role = payload.get('role') or 'admin'
            if roles and actor_role not in roles:
                return jsonify({'success': False, 'message': f'권한이 없습니다.'}), 403
            payload['actor_role'] = actor_role
            g.auth = payload
            return fn(*args, **kwargs)
        return wrapper
    return decorator
```

### 3-4. 라우트 보호 예시

```python
@theme_bp.route('/api/admin/themes', methods=['POST'])
@require_super_admin()
def create_theme():
    season = request.form.get('season')
    # ...
```

### 3-5. mobile 토큰 저장

`flutter_secure_storage`. 키: `pathwave_token`, `pathwave_refresh_token`, `pathwave_user`.

```dart
class ApiClient {
  static const _kToken = 'pathwave_token';
  static const _storage = FlutterSecureStorage();

  Future<Map<String, String>> _headers() async {
    final h = {'Content-Type': 'application/json', 'Accept': 'application/json'};
    final t = await _storage.read(key: _kToken);
    if (t != null && t.isNotEmpty) h['Authorization'] = 'Bearer $t';
    return h;
  }

  /// 401 발생 시 자동 로그아웃 콜백
  static void Function()? onUnauthorized;
}
```

### 3-6. SNS 로그인 5 종

- Google: Firebase Auth + ID Token
- Apple: Sign in with Apple (iOS 네이티브 + Apple 공식 위젯)
- Facebook: Meta SDK
- Kakao: `kakao_flutter_sdk_user` (네이티브 설정 + URL scheme)
- Naver: Naver Developers (네이티브 설정)

백엔드 라우트: `social_kakao.py`, `social_naver.py` — OAuth 토큰 교환 → users INSERT/UPDATE → 자체 JWT 발급.

---

## 4. Feature Flag (모듈화)

### 4-1. 정책 (사용자 결정 2026-06-05)

> 모든 기능을 메뉴·기능 단위 모듈화. 오픈 시점에 임의 모듈 ON/OFF 가능. 후속 변경에도 다른 모듈 영향 X.

### 4-2. 백엔드 구현 (개발사 작업)

#### DB 스키마

```sql
CREATE TABLE IF NOT EXISTS feature_flags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT NOT NULL,           -- 'wifi_roaming', 'payment_zeropay' 등
  env TEXT NOT NULL DEFAULT 'production',  -- 'production' | 'staging' | 'development'
  enabled INTEGER NOT NULL DEFAULT 0,
  updated_by_admin_id INTEGER,
  updated_at TEXT DEFAULT (datetime('now')),
  UNIQUE (key, env),
  FOREIGN KEY (updated_by_admin_id) REFERENCES super_admin_accounts(id)
);
CREATE INDEX IF NOT EXISTS idx_feature_flags_key_env ON feature_flags(key, env);
```

#### 데코레이터

```python
# models/feature_flag.py (개발사 신규)
from functools import wraps
from flask import jsonify
from models.database import get_db

def is_feature_enabled(key: str, env: str = None) -> bool:
    if env is None:
        env = os.environ.get('PATHWAVE_ENV', 'development')
    db = get_db()
    row = db.execute(
        "SELECT enabled FROM feature_flags WHERE key=? AND env=?",
        (key, env),
    ).fetchone()
    return bool(row and row['enabled'])

def require_feature(key: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not is_feature_enabled(key):
                return jsonify({
                    'success': False, 'message': f'feature {key} 비활성',
                }), 503  # Service Unavailable
            return fn(*args, **kwargs)
        return wrapper
    return decorator
```

#### 라우트 적용

```python
@checkout_bp.route('/api/checkout/store', methods=['POST'])
@require_feature('store_payment')
@decode_access_token(expected_sub_type='user')
def store_checkout():
    # 매장 결제 (2차)
    ...
```

#### 클라이언트 API

```python
@me_bp.route('/api/me/features', methods=['GET'])
def my_features():
    env = os.environ.get('PATHWAVE_ENV', 'development')
    rows = get_db().execute(
        "SELECT key, enabled FROM feature_flags WHERE env=?", (env,)
    ).fetchall()
    return jsonify({
        'success': True,
        'features': {r['key']: bool(r['enabled']) for r in rows},
    })
```

### 4-3. 어드민 UI

`admin-web/src/pages/FeatureFlags.jsx` 신규 — 각 모듈 키 + env 별 토글.

### 4-4. mobile 클라이언트

```dart
// services/feature_service.dart (개발사 신규)
class FeatureService extends ChangeNotifier {
  Map<String, bool> _flags = const {};
  bool isOn(String key) => _flags[key] ?? false;

  Future<void> refresh() async {
    final data = await ApiClient.instance.get('/api/me/features');
    _flags = Map<String, bool>.from(data['features'] ?? {});
    notifyListeners();
  }
}

// 사용:
if (context.read<FeatureService>().isOn('store_payment')) {
  // 매장 결제 UI 노출
}
```

### 4-5. 1차 모듈 키 (활성)

```
wifi_roaming, beacon, stamp, coupon, chat, chat_translate,
menu_translate, menu_ocr_device, push, email_notify,
subscription_payment_toss, season_theme
```

### 4-6. 1차 비활성 / 2차 활성 후보

```
store_payment, payment_zeropay, alipay_wechat, tax_refund,
social_auto_post, ai_chatbot, voice_call_ai, crm_ads_auto,
woorichat_translate_proxy
```

---

## 5. 모듈 상세 — 1차

### 5-1. wifi_roaming + beacon

#### 흐름

```
[admin-web]
  ↓ 비콘 입고 (CSV) — Beacons.jsx
  ↓ 매장 배정 (Beacons.jsx)
  ↓ 상태 = 'active'

[provider-web]
  ↓ 매장 WiFi 등록 (WifiSettings.jsx)
  ↓ SSID + 비밀번호(AES) + 비콘 매핑

[mobile 사용자]
  ↓ 앱 진입 → BleService.startScan()
  ↓ 비콘 감지 → ble.pendingWifi 세팅
  ↓ 홈 화면에 'WiFi 발견' 배너
  ↓ 탭 → wifi_connect_screen
  ↓ mobileconfig 다운로드 + 설치
  ↓ iOS 시스템 설정 → 자동 신뢰
  ↓ 매장 WiFi 자동 연결
  ↓ 다른 매장으로 이동 → 새 비콘 감지 → 위 흐름 반복 (다건 mobileconfig 누적)
```

#### DB 스키마 (`models/database.py`)

```sql
CREATE TABLE IF NOT EXISTS beacons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  uuid TEXT NOT NULL,
  major INTEGER NOT NULL,
  minor INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'inventory',  -- inventory|active|inactive|lost
  battery INTEGER,
  facility_id INTEGER,
  model TEXT,                                 -- 'FSC-BP108B' 등
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  UNIQUE (uuid, major, minor),
  FOREIGN KEY (facility_id) REFERENCES facilities(id)
);

CREATE TABLE IF NOT EXISTS wifi_profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  facility_id INTEGER NOT NULL,
  ssid TEXT NOT NULL,
  password_enc TEXT NOT NULL,    -- AES (PATHWAVE_AES_KEY)
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (facility_id) REFERENCES facilities(id)
);

CREATE TABLE IF NOT EXISTS beacon_wifi (
  beacon_id INTEGER NOT NULL,
  wifi_profile_id INTEGER NOT NULL,
  PRIMARY KEY (beacon_id, wifi_profile_id)
);

CREATE TABLE IF NOT EXISTS user_wifi_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  facility_id INTEGER,
  beacon_id INTEGER,
  event TEXT NOT NULL,         -- 'detected'|'connected'|'disconnected'
  created_at TEXT DEFAULT (datetime('now'))
);
```

#### 비콘 명세 (기본 모델)

| 필드 | 값 |
|---|---|
| UUID | 32 hex (8-4-4-4-12) |
| Major | 0~65535 (매장 그룹) |
| Minor | 0~65535 (개별 비콘) |
| 신호 강도 | RSSI |
| 배터리 보고 | 슈퍼어드민에서 임계점 설정 (admin Battery.jsx) |

#### API 라우트 (`routes/beacon.py`)

```
GET    /api/admin/beacons                   # 목록 + 필터
POST   /api/admin/beacons/import             # CSV 입고
PATCH  /api/admin/beacons/<id>               # 메타 수정
POST   /api/admin/beacons/<id>/assign        # 매장 배정
POST   /api/admin/beacons/<id>/unassign      # 회수
GET    /api/admin/beacons/battery-status     # 배터리 상태
GET    /api/admin/beacons/<id>/battery-history
GET    /api/beacon/<uuid>/<major>/<minor>    # mobile 조회 (매장+WiFi 매핑)
```

#### 서비스 신청 → 매칭 → 발송 흐름 (`routes/service_request.py`)

```
provider Signup → 비콘 서비스 신청 (units = 비콘 개수)
  → admin Approvals (status='pending' → 'approved')
  → admin Beacons (각 unit 에 inventory 비콘 매칭)
  → admin Ship (status='shipped' + 운송장 번호)
  → 도착 후 provider 가 매장에 설치 + WiFi 등록
```

#### mobile 핵심 코드

```dart
// services/ble_service.dart
class BleService extends ChangeNotifier {
  Map<String, dynamic>? pendingWifi;  // {'facility': {...}, 'wifi': {...}}
  bool isScanning = false;

  Future<void> startScan({String? userId}) async {
    // FlutterBluePlus 또는 동등 사용
    // 비콘 감지 → 백엔드 매칭 조회 → pendingWifi 세팅
    // notifyListeners()
  }
}
```

#### mobile UI

`home_screen.dart` _HomeTab — BLE 카드 + WifiBanner. `wifi_connect_screen.dart` — mobileconfig 설치 안내.

#### Phase 1 정책

- B 풀 스코프 (Phase 1 Plan P14~P19)
- units / grant·managed 는 v1 비공개 (Feature Flag)
- mobileconfig 다건 설치 = 매장 간 자동 핸드오프

---

### 5-2. stamp

#### 흐름

```
[provider-web]
  ↓ 스탬프 정책 등록 (Stamps.jsx + StampForm.jsx)
  ↓ stamp_policies.auto_stamp_enabled = 1 (BLE 자동)

[자동 적립 (BLE)]
  사용자 mobile → 매장 비콘 감지 → 자동 스탬프 INSERT
  같은 매장 24시간 내 재방문 = 1회만 (정책)

[수동 적립 (QR 스캔)]
  사용자 mobile 마이 → "내 회원 QR" → 60초 만료 QR
  provider MemberCheckin.jsx → 카메라 스캔 → 백엔드 검증
  → stamps INSERT + 회원 프로필 표시

[보상]
  stamps.count >= stamp_policies.reward_threshold → 쿠폰 자동 발급
```

#### DB

```sql
CREATE TABLE IF NOT EXISTS stamps (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  facility_id INTEGER NOT NULL,
  granted_by_account_id INTEGER,
  granted_by_actor_role TEXT,    -- 'owner'|'staff'|'auto'
  granted_by_actor_id INTEGER,
  expires_at TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS stamp_policies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  facility_id INTEGER NOT NULL UNIQUE,
  reward_threshold INTEGER NOT NULL DEFAULT 10,
  reward_coupon_id INTEGER,
  auto_stamp_enabled INTEGER DEFAULT 0,
  expires_days INTEGER,           -- 만료 일수 (NULL = 무제한)
  created_at TEXT DEFAULT (datetime('now'))
);
```

#### API (`routes/stamp.py` + `routes/checkin.py`)

```
POST /api/checkin/issue-qr            # 사용자 QR 발급 (60초 만료)
POST /api/checkin/scan                # provider 스캔 (QR 검증 + stamp INSERT)
GET  /api/me/stamps                   # 내 스탬프 (mobile)
GET  /api/me/stamps/<facility_id>     # 매장별 상세
POST /api/admin/stamps/grant          # 어드민 수동 적립 (예외)
```

#### 회원 QR 발급

```python
# routes/checkin.py
@checkin_bp.route('/api/checkin/issue-qr', methods=['POST'])
@require_user
def issue_qr():
    user_id = g.auth['user_id']
    token = secrets.token_urlsafe(24)
    expires_at = datetime.utcnow() + timedelta(seconds=60)
    db.execute(
        "INSERT INTO member_qr_tokens (user_id, token, expires_at) VALUES (?,?,?)",
        (user_id, token, expires_at.isoformat()),
    )
    db.commit()
    return jsonify({'success': True, 'token': token, 'expires_in': 60})
```

---

### 5-3. coupon

#### 흐름

```
[provider 발급]
  CouponForm.jsx → 쿠폰 정책 (혜택/대상/유효기간)
  → POST /api/provider/coupons → coupons INSERT (status='issued')

[사용자 사용]
  mobile coupons_screen → 쿠폰 선택
  → "사용하기" 다이얼로그 confirm
  → POST /api/me/coupons/<id>/use
  → coupons.used_at + used_by_actor 기록
  → status='used'

[자동 발급 — 스탬프 보상]
  stamp_policies.reward_threshold 도달 → 자동 issue
```

#### DB

```sql
CREATE TABLE IF NOT EXISTS coupons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  facility_id INTEGER NOT NULL,
  policy_id INTEGER,
  benefit TEXT,             -- '아메리카노 1잔 무료' 등
  status TEXT NOT NULL DEFAULT 'issued',  -- issued|used|expired
  expires_at TEXT,
  used_at TEXT,
  used_by_actor_role TEXT,
  used_by_actor_id INTEGER,
  issued_by_actor_role TEXT,
  issued_by_actor_id INTEGER,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_coupons_user_status ON coupons(user_id, status);
```

#### API

```
GET  /api/me/coupons?status=issued|used|expired   # 내 쿠폰
POST /api/me/coupons/<id>/use                     # 사용
POST /api/provider/coupons                        # 쿠폰 발급
GET  /api/admin/coupons                           # 통계
```

#### mobile UI

`coupons_screen.dart` — 3 탭 (사용가능/사용완료/만료). 사용 시 `PwDialog` 확인.

---

### 5-4. chat + chat_translate

#### 흐름

```
[mobile 사용자] ↔ [provider CustomerChat.jsx]
1:1 매장 채팅 (chat_rooms = 매장×사용자 UNIQUE)

[자동 번역 — P8b]
  sender 가 한국어로 보냄 → chat_messages.body_lang='ko'
  수신자(외국인) 언어 = 'en' 이면 → 백엔드 DeepL → chat_message_translations INSERT
  수신자 mobile 은 자기 언어로 표시

[캐시]
  동일 (message_id, target_lang) 재요청 시 chat_message_translations 캐시 사용
```

#### DB

```sql
CREATE TABLE IF NOT EXISTS chat_rooms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  facility_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE (facility_id, user_id)
);

CREATE TABLE IF NOT EXISTS chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  room_id INTEGER NOT NULL,
  sender TEXT NOT NULL,        -- 'user'|'facility'|'staff'
  sender_id INTEGER NOT NULL,
  body TEXT NOT NULL,
  body_lang TEXT,              -- 'ko'|'en'|'ja' 등 (P8b)
  read_at TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (room_id) REFERENCES chat_rooms(id)
);

CREATE TABLE IF NOT EXISTS chat_message_translations (
  message_id INTEGER NOT NULL,
  lang TEXT NOT NULL,
  value TEXT NOT NULL,
  source TEXT DEFAULT 'deepl',   -- 'deepl'|'manual'|'woorichat'
  created_at TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (message_id, lang),
  FOREIGN KEY (message_id) REFERENCES chat_messages(id)
);
```

#### API (`routes/chat.py`)

```
GET  /api/chat/rooms                         # 내 채팅방 목록
GET  /api/chat/rooms/<id>/messages?lang=en   # 메시지 + 자동번역
POST /api/chat/rooms/<id>/messages           # 메시지 전송 (body, body_lang)
POST /api/chat/rooms/<id>/read               # 읽음 처리
POST /api/chat/reports                       # 매장 신고
POST /api/chat/block                         # 매장 차단
```

#### 자동 번역 패턴 (백엔드)

```python
# routes/chat.py
def _translate_if_needed(msg, target_lang):
    if msg['body_lang'] == target_lang or not msg['body_lang']:
        return msg['body']
    cached = db.execute(
        "SELECT value FROM chat_message_translations WHERE message_id=? AND lang=?",
        (msg['id'], target_lang),
    ).fetchone()
    if cached:
        return cached['value']
    # DeepL 호출 (또는 2차: woorichat_translate_proxy)
    translated = translator.translate(msg['body'],
                                       source=msg['body_lang'], target=target_lang)
    db.execute(
        "INSERT INTO chat_message_translations (message_id, lang, value, source) VALUES (?,?,?,?)",
        (msg['id'], target_lang, translated, 'deepl'),
    )
    db.commit()
    return translated
```

#### 신고 / 차단

- `abuse_reports` 테이블 (target_kind='facility', target_id, reason_code, attachments)
- `block_list` 테이블 (user_id, target_facility_id)
- mobile 의 `ChatMenu` → 매장 신고 / 매장 차단

---

### 5-5. menu_translate + menu_ocr_device

#### 흐름

```
[provider MenuManagement.jsx]
방법 A — 수동 입력
  메뉴명 + 가격 + 설명 (한국어)
  → POST /api/provider/menu/items
  → facility_menu_items INSERT (language='ko', source='manual')

방법 B — 사진 OCR
  사진 업로드 → mobile/web 디바이스 OCR (Apple Vision / ML Kit)
  → 추출된 텍스트를 클라이언트가 파싱 (메뉴명/가격 분리)
  → POST /api/provider/menu/items (source='ocr')

[자동 번역 — 백엔드]
  ko 원본 INSERT 트리거
  → DeepL 비동기 호출 (Celery 또는 백그라운드 task)
  → 23 언어 facility_menu_items INSERT (base_item_id=원본, source='translated')
  → 자동 번역 임계점 초과 시 ko 만 노출 (fallback_blocked)

[변경 감지]
  facility_menu_items.body_hash (SHA256) 비교
  → 해시 변경된 메뉴만 재번역
  → 다른 언어 캐시 자동 무효화
```

#### DB

```sql
CREATE TABLE IF NOT EXISTS facility_menu_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  facility_id INTEGER NOT NULL,
  language TEXT NOT NULL,         -- 'ko' (원본) | 'en' | 'ja' | ...
  name TEXT NOT NULL,
  price TEXT,                     -- 항상 KRW ('9,000원' / '₩9,000')
  description TEXT,
  sort_order INTEGER DEFAULT 0,
  source TEXT DEFAULT 'manual',   -- 'manual' | 'ocr' | 'deepl' | 'translated'
  upload_id INTEGER,              -- OCR origin (있다면)
  base_item_id INTEGER,           -- 자동 번역 시 원본 추적
  body_hash TEXT,                 -- name+description SHA256 (변경 감지)
  active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (facility_id) REFERENCES facilities(id),
  FOREIGN KEY (base_item_id) REFERENCES facility_menu_items(id)
);
CREATE INDEX IF NOT EXISTS idx_menu_items_facility_lang
  ON facility_menu_items(facility_id, language, active);
```

#### 가격 정책 (메모리)

- **항상 KRW 단위** (`9,000원` / `₩9,000`). 외국 통화 금지.
- 자동 번역 대상 = `name` + `description` 만. `price` 는 원본 유지.

#### 디바이스 OCR (mobile / web)

##### iOS (Apple Vision Framework)

```dart
// 개발사 신규 — apple_vision 패키지 또는 platform channel
final result = await AppleVision.recognizeText(
  imageBytes: bytes,
  languages: ['ko-KR', 'en-US', 'ja-JP', 'zh-Hans'],
);
// result.lines: [{text, boundingBox, confidence}]
```

##### Android (Google ML Kit)

```kotlin
// platform channel 통해 호출
val recognizer = TextRecognition.getClient(KoreanTextRecognizerOptions.Builder().build())
recognizer.process(InputImage.fromBitmap(bitmap, 0))
    .addOnSuccessListener { visionText ->
        // visionText.text, visionText.textBlocks
    }
```

##### 파서 (클라이언트)

```dart
// 가격 정규식 — 한국 가격 포맷
final pricePattern = RegExp(r'(?:₩|￦)?\s*([0-9,]+)\s*(?:원|won|\\)?');
List<MenuItem> parseLines(List<String> lines) {
  final items = <MenuItem>[];
  for (final line in lines) {
    final m = pricePattern.firstMatch(line);
    if (m != null) {
      final price = m.group(0)!;
      final name = line.substring(0, m.start).trim();
      if (name.isNotEmpty) items.add(MenuItem(name: name, price: price));
    }
  }
  return items;
}
```

#### API (`routes/menu.py`)

```
GET  /api/facility/<id>/menu?lang=en       # 메뉴 + 자동 번역 (캐시 포함)
POST /api/provider/menu/items              # 메뉴 추가 (source='manual'|'ocr')
PATCH /api/provider/menu/items/<id>        # 수정 (body_hash 변경 → 재번역)
DELETE /api/provider/menu/items/<id>       # 삭제
```

#### 번역 비용 안전장치

`docs/translation_cost_runaway_plan.md` 참조. AI 사용량 임계점 50/80/100% 알림 + 100% 도달 시 자동 차단 (admin CostMonitor.jsx).

---

### 5-6. push + email_notify

#### 푸시 흐름

```
[mobile 등록]
  앱 시작 → FCM/APNs 토큰 획득
  → POST /api/push/tokens (token, platform, language)
  → push_tokens INSERT/UPDATE (UNIQUE token+platform)

[발송]
  notification.py — push_to_users(user_ids, title, body, data)
  → push_tokens 조회 (user_id IN)
  → platform 별 PushProvider 분기:
      apns → APNs HTTP/2 (.p8 키)
      fcm  → FCM HTTP v1
  → 응답 통계 (sent / failed / no_tokens)

[다국어 자동 번역]
  title_lang + body_lang 명시 시:
  → push_tokens.language 기준 자동 번역 (DeepL 캐시)
  → 사용자 언어로 푸시
```

#### DB

```sql
CREATE TABLE IF NOT EXISTS push_tokens (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  token TEXT NOT NULL,
  platform TEXT NOT NULL,        -- 'fcm' | 'apns'
  language TEXT,                  -- 푸시 언어 힌트
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  UNIQUE (token, platform),
  FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_push_tokens_user ON push_tokens(user_id);
```

#### PushProvider 추상화 (`models/push.py`)

```python
class PushProvider(Protocol):
    name: str
    def send(self, *, token: str, platform: str, title: str, body: str,
             data: dict | None = None) -> dict: ...

class StubPushProvider:
    name = 'stub'
    def send(self, **kw): return {'success': True}

class FcmPushProvider:
    name = 'fcm'
    def __init__(self, server_key: str): ...
    def send(self, *, token, platform, title, body, data=None):
        # urllib.request → FCM legacy 또는 HTTP v1
        ...

class ApnsPushProvider:
    name = 'apns'
    def __init__(self, key_path, key_id, team_id, bundle_id, use_sandbox=False):
        self._key, self._kid, self._tid, self._bundle = ...
    def _get_jwt(self) -> str:
        # ES256 서명, 30분 캐시
        ...
    def send(self, *, token, platform, title, body, data=None):
        if platform != 'apns':
            return {'success': False, 'error': f'unsupported_platform:{platform}'}
        # httpx HTTP/2 → APNs
        ...

class MultiPlatformPushProvider:
    """platform 별 자동 분기."""
    name = 'multi'
    def send(self, *, token, platform, title, body, data=None):
        if platform == 'fcm': return self._fcm.send(...)
        if platform == 'apns': return self._apns.send(...)
```

#### 다국어 push_to_users

```python
def push_to_users(db, user_ids: list[int], *, title: str, body: str,
                  data: dict | None = None,
                  title_lang: str | None = None,
                  body_lang: str | None = None) -> dict:
    if not user_ids:
        return {'sent': 0, 'failed': 0, 'no_tokens': 0}
    placeholders = ','.join('?' * len(user_ids))
    rows = db.execute(
        f"SELECT user_id, token, platform, language FROM push_tokens "
        f"WHERE user_id IN ({placeholders})", user_ids
    ).fetchall()
    sent, failed = 0, 0
    provider = get_push_provider()
    for r in rows:
        target_lang = _resolve_push_target_lang(r['language'])
        t_title = _translate_push_text(title, title_lang, target_lang) if title_lang else title
        t_body  = _translate_push_text(body,  body_lang,  target_lang) if body_lang else body
        res = provider.send(token=r['token'], platform=r['platform'],
                            title=t_title, body=t_body, data=data)
        if res.get('success'): sent += 1
        else: failed += 1
    return {'sent': sent, 'failed': failed, 'provider': provider.name}
```

#### 이메일 (SendGrid)

`models/email_provider.py` 동일 패턴:
- `EmailProvider` Protocol
- `StubEmailProvider` (개발)
- `SendGridEmailProvider` (운영)
- `SmtpEmailProvider` (대안)

ENV: `EMAIL_PROVIDER=sendgrid|smtp|stub`, `SENDGRID_API_KEY`.

---

### 5-7. subscription_payment_toss

#### 흐름

```
[provider 카드 등록]
  PaymentManagement.jsx → 토스 결제창 (위젯)
  → 빌링키 발급 (토스)
  → POST /api/billing/cards
  → billing_keys INSERT (facility_account_id, pg_key=AES(billing_key), active=1)

[구독 신청]
  Subscriptions.jsx → service_type + quantity + period_months 선택
  → POST /api/billing/subscriptions
  → service_subscriptions INSERT
  → _charge() 호출:
      provider = get_payment_provider()  # ENV: toss (1차)
      res = provider.charge(billing_key=..., total=..., order_no=..., customer_email=...)
  → payments INSERT (gateway, fallback_from, status='paid'|'failed')

[정기 갱신]
  매월/매년 ends_at 도래 → 백그라운드 task → _charge() 재호출
  성공 시 ends_at 갱신, 실패 시 status='past_due' + provider 알림
```

#### DB

```sql
CREATE TABLE IF NOT EXISTS billing_keys (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  facility_account_id INTEGER NOT NULL,
  pg_key TEXT NOT NULL,            -- AES (PATHWAVE_AES_KEY)
  card_last4 TEXT,
  card_brand TEXT,
  active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS service_subscriptions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  facility_account_id INTEGER NOT NULL,
  service_type TEXT NOT NULL,     -- 'beacon'|'notification'|'wifi' 등
  quantity INTEGER NOT NULL,
  period_months INTEGER NOT NULL, -- 1 또는 12
  unit_price INTEGER NOT NULL,
  total_price INTEGER NOT NULL,
  ends_at TEXT NOT NULL,
  status TEXT DEFAULT 'pending',  -- pending|active|past_due|canceled
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  facility_account_id INTEGER NOT NULL,
  subscription_id INTEGER,
  order_no TEXT NOT NULL UNIQUE,
  amount INTEGER NOT NULL,
  vat INTEGER NOT NULL,
  total INTEGER NOT NULL,
  pg_tid TEXT,
  status TEXT DEFAULT 'pending',
  receipt_email TEXT,
  paid_at TEXT,
  gateway TEXT,             -- 'toss' | 'zeropay' | 'sim' (이번 PR 추가)
  fallback_from TEXT,       -- 폴백 발생 시 원래 시도 PG
  created_at TEXT DEFAULT (datetime('now'))
);
```

#### PaymentProvider 추상화 (`models/payment_provider.py`)

이미 구현됨. 1차는 `PG_PROVIDER=toss`, 2차는 `PG_PROVIDER=fallback`.

```python
class PaymentProvider(Protocol):
    name: str
    def charge(self, *, billing_key: str, total: int, order_no: str,
               customer_email: str | None = None) -> dict: ...
    def refund(self, *, payment_key: str, amount: int,
               reason: str | None = None) -> dict: ...

# 1차: TossPaymentsProvider
class TossPaymentsProvider:
    name = 'toss'
    def __init__(self, secret_key: str, api_base: str | None = None): ...

    def charge(self, *, billing_key, total, order_no, customer_email=None):
        try:
            data = self._post(f'/v1/billing/{billing_key}', {
                'amount': total,
                'orderId': order_no,
                'orderName': f'PathWave 구독 {order_no}',
                'customerEmail': customer_email,
                'customerKey': billing_key,
            })
            return {'success': True,
                    'payment_key': data.get('paymentKey'),
                    'pg_tid': data.get('transactionKey') or data.get('paymentKey'),
                    'provider': 'toss'}
        except _TossError as e:
            return {'success': False, 'error': e.code, 'message': e.message,
                    'provider': 'toss'}

    def refund(self, *, payment_key, amount, reason=None):
        data = self._post(f'/v1/payments/{payment_key}/cancel',
                          {'cancelReason': reason or 'admin_refund',
                           'cancelAmount': amount})
        return {'success': True, 'raw': data, 'provider': 'toss'}

# 2차: ZeropayProvider + FallbackPaymentProvider
# (제로페이 가맹 협약 후 활성. 1차 골격 + stub 이미 구현됨.)
```

#### 라우트 (`routes/billing.py`)

```python
def _charge(card_pg_key, total, order_no, customer_email=None) -> dict:
    provider = get_payment_provider()
    res = provider.charge(billing_key=card_pg_key, total=total,
                          order_no=order_no, customer_email=customer_email)
    ok = bool(res.get('success'))
    return {
        'success': ok,
        'pg_tid':        res.get('pg_tid') if ok else None,
        'payment_key':   res.get('payment_key') if ok else None,
        'gateway':       res.get('provider'),
        'fallback_from': res.get('fallback_from'),
    }
```

INSERT payments — gateway / fallback_from 컬럼 채움.

#### 환불 (admin Payments.jsx)

```python
# routes/admin.py
@admin_bp.route('/api/admin/payments/<int:pid>/refund', methods=['POST'])
@require_super_admin()
def refund_payment(pid: int):
    row = db.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
    provider = get_payment_provider()
    # FallbackPaymentProvider 면 gateway 인자 전달
    if hasattr(provider, 'refund'):
        sig = inspect.signature(provider.refund)
        if 'gateway' in sig.parameters:
            res = provider.refund(payment_key=row['payment_key'],
                                  amount=row['total'],
                                  reason=request.json.get('reason'),
                                  gateway=row['gateway'])
        else:
            res = provider.refund(payment_key=row['payment_key'],
                                  amount=row['total'],
                                  reason=request.json.get('reason'))
    return jsonify(res)
```

---

### 5-8. season_theme

#### 흐름

```
[admin Themes.jsx]
  계절(spring/summer/autumn/winter) 또는 event 별 이미지 업로드
  → POST /api/admin/themes (multipart)
  → static/themes/{uuid}.{ext} 저장
  → theme_configs INSERT
  → 활성화 (활성 1개만, 같은 season 내 배타)

[mobile]
  앱 시작 → ThemeService.init()
  → SharedPreferences 캐시 즉시 로드 → notifyListeners
  → 백그라운드 GET /api/theme/current (1h TTL)
  → 이미지 url 받아 CachedNetworkImage 로 표시 (BoxFit.cover)
  → fallback (이미지 없음) = SeasonUtils.fallbackGradient(season)
  → pull-to-refresh = 캐시 무시 + 즉시 fetch
```

#### DB

```sql
CREATE TABLE IF NOT EXISTS theme_configs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  season TEXT NOT NULL,           -- 'spring'|'summer'|'autumn'|'winter'|'event'
  name TEXT NOT NULL,
  image_url TEXT NOT NULL,        -- '/static/themes/{uuid}.{ext}'
  image_filename TEXT NOT NULL,
  overlay_alpha REAL DEFAULT 0.45,
  text_on_dark INTEGER DEFAULT 1,
  accent_color TEXT,
  active INTEGER DEFAULT 0,
  event_starts_at TEXT,
  event_ends_at TEXT,
  created_by_admin_id INTEGER,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_theme_configs_season_active
  ON theme_configs(season, active);
```

#### API (`routes/theme.py`)

```
GET    /api/theme/current               # 공개. KST 기준 자동 + ?season=xxx 강제
GET    /api/admin/themes                # 전체 목록
POST   /api/admin/themes                # multipart (image + meta)
PATCH  /api/admin/themes/<id>           # 메타 + 이미지 교체
POST   /api/admin/themes/<id>/activate  # 같은 season 의 active 배타 1개로 지정
DELETE /api/admin/themes/<id>           # 파일 + row 삭제
```

#### mobile ThemeService

```dart
class ThemeService extends ChangeNotifier {
  static const _kCacheJson = 'theme.cache.v1.json';
  static const _kCacheTimestamp = 'theme.cache.v1.ts';
  static const Duration _ttl = Duration(hours: 1);

  ThemeConfig? _activeTheme;
  Season _season = SeasonUtils.currentKst();

  Future<void> init() async {
    await _loadFromCache();
    notifyListeners();
    if (SeasonUtils.devForcedSeason != null) {
      unawaited(_fetch());
    } else {
      unawaited(_fetchIfStale());
    }
  }

  Future<void> refresh() async => _fetch();
}
```

#### 무재배포 운영

슈퍼어드민이 admin-web 에서 활성 테마 변경 → 다음 fetch 시점(앱 재실행 / pull-to-refresh / 1h 경과)에 자동 반영. 앱 재배포 X.

---

## 6. 정책·약관 / 신고 / 차단

### 6-1. 약관 8 종

| kind | 사용자 | 사장 |
|---|---|---|
| `service` | 서비스 이용약관 | ✅ |
| `privacy` | 개인정보 처리방침 | ✅ |
| `location` | 위치기반서비스 이용약관 | ✅ |
| `marketing` | 마케팅 정보 수신 (선택) | ✅ |
| `push` | 푸시 알림 동의 | ✅ |
| `third_party` | 제3자 정보제공 (소셜로그인) | ✅ |
| `terms_facility` | 사장 전용 약관 | — / ✅ |
| `terms_facility_payment` | 사장 결제 약관 | — / ✅ |

### 6-2. DB

```sql
CREATE TABLE IF NOT EXISTS policy_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  language TEXT NOT NULL DEFAULT 'ko',
  version TEXT NOT NULL,             -- 'v1.0', 'v1.1'
  title TEXT,
  body TEXT NOT NULL,
  effective_at TEXT NOT NULL,
  change_log TEXT,
  is_required INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE (kind, language, version)
);

CREATE TABLE IF NOT EXISTS consent_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  facility_account_id INTEGER,
  policy_version_id INTEGER NOT NULL,
  agreed INTEGER NOT NULL,
  agreed_at TEXT DEFAULT (datetime('now')),
  ip TEXT,
  user_agent TEXT,
  FOREIGN KEY (policy_version_id) REFERENCES policy_versions(id)
);
```

### 6-3. API (`routes/policy.py`)

```
GET    /api/policies/<kind>                  # 현재 활성 약관 (사용자 언어)
GET    /api/policies/<kind>/versions         # 전체 버전
POST   /api/consent                          # 동의 기록
GET    /api/admin/policies                   # 어드민 목록
POST   /api/admin/policies                   # 단일 버전 추가
POST   /api/admin/policies/multilang         # ko+en 동시 (트랜잭션)
POST   /api/admin/policies/<id>/notify       # 변경 푸시 발송
```

### 6-4. 신고 (abuse_report)

```sql
CREATE TABLE IF NOT EXISTS abuse_reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reporter_user_id INTEGER NOT NULL,
  target_kind TEXT NOT NULL,           -- 'facility' 만 (사용자 앱 정책)
  target_id INTEGER NOT NULL,
  reason_code TEXT NOT NULL,           -- 'spam'|'abuse'|'illegal'|'inappropriate'|'other'
  reason_detail TEXT,
  attachment_count INTEGER DEFAULT 0,  -- v1 = count 만. multipart 업로드는 v2
  status TEXT DEFAULT 'pending',       -- pending|reviewed|action_taken|dismissed
  created_at TEXT DEFAULT (datetime('now'))
);
```

### 6-5. 차단

```sql
CREATE TABLE IF NOT EXISTS user_facility_blocks (
  user_id INTEGER NOT NULL,
  facility_id INTEGER NOT NULL,
  reason TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (user_id, facility_id)
);
```

차단 시 chat_rooms 비활성 + 알림 차단 + 검색 결과 숨김.

---

## 7. 다국어 (i18n) 23 언어

### 7-1. Phase 1 = 10 언어 (한국 방문 관광객 우선)

```
ko / en / zh-CN / ja / zh-TW / vi / th / tl / id / ms
```

### 7-2. Phase 2 = 13 언어 추가

```
ru / hi / es / de / fr / pt / it / nl / pl / ar / tr / he / sv
```

### 7-3. DB

```sql
CREATE TABLE IF NOT EXISTS translations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT NOT NULL,              -- 예: 'mypage.title'
  lang TEXT NOT NULL,             -- ISO 코드
  value TEXT NOT NULL,
  verified INTEGER DEFAULT 0,     -- 0=자동, 1=사람 검수
  source TEXT DEFAULT 'manual',   -- 'manual'|'deepl'|'seed'
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  UNIQUE (key, lang)
);
```

### 7-4. API (`routes/i18n.py`)

```
GET /api/i18n/<lang>                # 전체 번역 (lang 기준 dict)
POST /api/admin/i18n/seed           # 시드 (DeepL 일괄)
PATCH /api/admin/i18n/<key>/<lang>  # 사람 검수 (verified=1)
```

### 7-5. mobile I18nService

```dart
class I18nService {
  static final I18nService instance = I18nService._();
  Map<String, String> _cache = const {};

  Future<void> init() async {
    final lang = await _detectLang();
    // 1) 캐시 로드 → 2) 백그라운드 fetch (24h TTL)
    final cached = await _loadCache(lang);
    if (cached != null) _cache = cached;
    unawaited(_fetch(lang));
  }

  String t(String key, {String? defaultValue}) {
    return _cache[key] ?? defaultValue ?? key;
  }
}

// 화면에서:
context.t('mobile.mypage.title', defaultValue: '마이페이지')
```

### 7-6. 번역 비용 안전장치

`docs/translation_cost_runaway_plan.md` 참조.
- 매장당 일일 신규 키 제한 (예: 100/일)
- 임계점 50/80/100% admin 알림
- 100% 도달 시 자동 차단 + fallback (ko 원본 표시)

---

## 8. 환경 분리 (운영 / 클론) + 배포

### 8-1. 환경 변수 분리

```bash
# 운영 .env
PATHWAVE_ENV=production
DATABASE_URL=postgresql://prod_user:xxx@db.prod:5432/pathwave_prod
PG_PROVIDER=toss
TOSS_SECRET_KEY=live_sk_xxx
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.prod_xxx
PUSH_PROVIDER=multi
APNS_KEY_PATH=/secrets/apns_prod.p8
FIREBASE_CREDENTIALS=/secrets/firebase_prod.json
SECRET_KEY=<64자 랜덤>
PATHWAVE_AES_KEY=<32자 랜덤>
CORS_ORIGINS=https://app.pathwave.???,https://admin.pathwave.???,https://provider.pathwave.???
FLASK_DEBUG=0

# 클론 .env
PATHWAVE_ENV=staging
DATABASE_URL=postgresql://stage_user:xxx@db.stage:5432/pathwave_stage
PG_PROVIDER=sim
EMAIL_PROVIDER=stub
PUSH_PROVIDER=stub
# (운영과 동일한 SECRET_KEY/AES_KEY 사용 금지 — 별도 발급)
```

### 8-2. 운영 부팅 검증 (`app.py::_validate_production_env`)

```python
def _validate_production_env() -> None:
    if os.environ.get('PATHWAVE_ENV', 'development') != 'production':
        return
    errors: list[str] = []
    secret = os.environ.get('SECRET_KEY', '')
    if not secret or secret == _DEV_SECRET_DEFAULT:
        errors.append('SECRET_KEY (dev 기본값 금지)')
    if not os.environ.get('PATHWAVE_AES_KEY', ''):
        errors.append('PATHWAVE_AES_KEY')
    if not os.environ.get('CORS_ORIGINS', '').strip():
        errors.append('CORS_ORIGINS')
    if os.environ.get('FLASK_DEBUG', '0') == '1':
        errors.append('FLASK_DEBUG=1 금지')
    db_url = os.environ.get('DATABASE_URL', '').strip()
    if not db_url or db_url.startswith('sqlite:'):
        errors.append('DATABASE_URL (PostgreSQL — postgresql:// 으로 시작)')
    pg = os.environ.get('PG_PROVIDER', 'sim').lower()
    if pg == 'toss' and not os.environ.get('TOSS_SECRET_KEY', '').strip():
        errors.append('TOSS_SECRET_KEY')
    # ... 이메일 / 푸시 / Firebase 검증
    if errors:
        raise RuntimeError('운영 환경 부팅 차단 — 누락된 ENV:\n  - ' + '\n  - '.join(errors))
```

### 8-3. 배포 흐름 (개발사 셋업)

```
1. feature 브랜치
2. PR 생성 → GitHub Actions CI:
   - backend: pytest (라우트별 회귀 + 마이그레이션)
   - mobile: dart analyze + flutter test
   - admin-web / provider-web: vite build + lint
3. 머지 main
4. 자동 배포 → 클론 환경:
   - rsync 또는 Docker image push → 클론 서버 pull
   - DB 마이그레이션 자동 적용 (`init_db()` 의 _add_column_if_missing)
   - gunicorn 재시작
5. 클론에서 페르소나 시나리오 수동 검증
6. 운영 수동 승격:
   - 발주사 결재 (간단한 체크리스트)
   - DB 마이그레이션 dry-run → 실 적용
   - 코드 배포 (운영 서버)
   - gunicorn graceful reload
   - Sentry release tag
7. 모니터링 (15분 워치)
```

### 8-4. Procfile (운영)

```
web: gunicorn -c gunicorn.conf.py wsgi:app
```

### 8-5. gunicorn 설정 예시

```python
# gunicorn.conf.py
import multiprocessing
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
bind = '0.0.0.0:8080'
timeout = 30
keepalive = 5
errorlog = '-'
accesslog = '-'
```

### 8-6. 인프라 (1차 확정)

- 운영: Contabo VPS (한국 리전 검토는 2차)
- 클론: Contabo VPS 별도 인스턴스 또는 Docker compose 분리
- DB: PostgreSQL (운영) / sqlite (개발 로컬)
- 정적: Cloudflare Tunnel → Nginx → gunicorn

---

## 9. 보안 + 운영 검증

### 9-1. 비밀번호 / 키

| 영역 | 방식 |
|---|---|
| 비밀번호 | bcrypt (`bcrypt.hashpw`) |
| WiFi 비밀번호 / PG 빌링키 | AES-256 (`PATHWAVE_AES_KEY`) |
| JWT 서명 | HS256 (`SECRET_KEY`, 64자 권장) |

### 9-2. AES 헬퍼 (`models/crypto.py`)

```python
def encrypt_secret(plaintext: str) -> str:
    key = os.environ.get('PATHWAVE_AES_KEY', '').encode()
    if not key: raise RuntimeError('PATHWAVE_AES_KEY 누락')
    # AES-256-GCM 권장
    ...

def decrypt_secret(ciphertext: str) -> str:
    ...
```

### 9-3. Rate Limit

`flask_limiter` (in-memory 개발 / Redis 운영 권장):

```python
@auth_bp.route('/api/auth/login', methods=['POST'])
@limiter.limit('10 per minute')
def login():
    ...
```

### 9-4. CORS

```python
_cors_origins_raw = os.environ.get('CORS_ORIGINS', '').strip()
if _cors_origins_raw:
    _origins = [o.strip() for o in _cors_origins_raw.split(',') if o.strip()]
    CORS(app, resources={r'/api/*': {'origins': _origins}}, supports_credentials=True)
else:
    CORS(app)  # 개발만
```

### 9-5. 사진 업로드 검증 (예: 신고/메뉴)

```python
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp'}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB

def _save_image(file_storage) -> tuple[str, str]:
    if not file_storage or not file_storage.filename:
        raise ValueError('이미지 파일이 없습니다.')
    orig = secure_filename(file_storage.filename)
    ext = orig.rsplit('.', 1)[-1].lower() if '.' in orig else ''
    if ext not in ALLOWED_EXT:
        raise ValueError(f'허용되지 않는 확장자: .{ext}')
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > MAX_UPLOAD_BYTES:
        raise ValueError(f'파일이 너무 큽니다: {size // 1024 // 1024}MB')
    new_name = f'{uuid.uuid4().hex}.{ext}'
    path = os.path.join(_themes_dir(), new_name)
    file_storage.save(path)
    return new_name, f'/static/themes/{new_name}'
```

### 9-6. 미성년자 분리

```sql
-- users.age_group: 'adult'|'minor_14_18'|'minor_under_14'|'unknown'
-- minor_* 의 경우:
--   * 푸시 알림은 마케팅 카테고리 제한
--   * WiFi grant 자동 차단 (관리자 승인 필요)
--   * 채팅 신고 우선순위 ↑
```

---

## 10. 테스트 + QA

### 10-1. 백엔드 pytest

```python
# tests/test_payment_provider.py
import os
def test_fallback_provider_zeropay_stub_success():
    os.environ.update({
        'PG_PROVIDER': 'fallback',
        'FALLBACK_PRIMARY': 'zeropay',
        'FALLBACK_SECONDARY': 'toss',
        'TOSS_SECRET_KEY': 'test_sk',
    })
    from models.payment_provider import get_payment_provider
    prov = get_payment_provider()
    res = prov.charge(billing_key='bk-test', total=1000, order_no='ORD-001')
    assert res['success'] is True
    assert res.get('provider') == 'zeropay'
```

### 10-2. mobile Flutter 위젯 테스트

```dart
testWidgets('PwButton primary renders white text on purple', (tester) async {
  await tester.pumpWidget(MaterialApp(
    theme: NeuTheme.themeData,
    home: PwButton(onPressed: () {}, child: const Text('Login')),
  ));
  expect(find.text('Login'), findsOneWidget);
  // 색 검증 추가 가능
});
```

### 10-3. 페르소나 시나리오

`docs/pathwave_persona_test_plan_C-3_2026-05-23.md` 참조. 6 페르소나 (외국인 / 한국인 / 소규모 매장 / 중대형 매장 / 직원 / 슈퍼어드민) × 25+ 시나리오.

### 10-4. CI/CD 매트릭스

| 영역 | 도구 | 통과 기준 |
|---|---|---|
| backend | pytest, ruff, mypy | 모든 테스트 PASS + lint 0 error |
| mobile | dart analyze, flutter test | No issues found |
| admin-web | vite build, eslint | build 성공 + lint 0 error |
| provider-web | vite build, eslint | 동일 |

---

## 11. 모듈 상세 — 2차

### 11-1. payment_zeropay + store_payment + alipay_wechat

#### 전제 조건

| # | 조건 |
|---|---|
| 1 | 발주사 — 한국간편결제진흥원 가맹점 신청 + 승인 + MID/API Key 발급 |
| 2 | 발주사 — 제로페이 API 사양 문서 인계 (가맹점 협의 시 별도 제공) |
| 3 | 알리페이/위챗페이 — 별도 가맹·계약 (외국인 결제) |
| 4 | 외국인 면세 — 면세 사업자 등록 + 환급 PG 협약 |

#### 골격 (1차에 이미 구현됨)

`models/payment_provider.py` 의 `ZeropayProvider` + `FallbackPaymentProvider`.
ENV `PG_PROVIDER=fallback` + 키 주입 시 stub → 실 API 자동 전환.

#### 2차 작업

```python
class ZeropayProvider:
    def charge(self, *, billing_key, total, order_no, customer_email=None):
        if self._stub:
            return {'success': True, ...}  # 1차 stub
        # 2차 — 실 API 호출
        payload = {
            'mid': self._mid,
            'orderId': order_no,
            'amount': total,
            # ... 제로페이 사양에 맞춰 작성
        }
        # signed_payload = self._sign(payload, self._key)
        # response = httpx.post(f'{self._base}/charge', json=signed_payload)
        # return self._parse_response(response)
```

#### 매장 결제 라우트 (`routes/checkout.py` 신규)

```python
@checkout_bp.route('/api/checkout/store', methods=['POST'])
@require_feature('store_payment')
@decode_access_token(expected_sub_type='user')
def store_checkout():
    data = request.get_json()
    facility_id = data['facility_id']
    items = data['items']  # [{menu_id, qty}, ...]
    # 가격 계산 (DB의 facility_menu_items 참조)
    # _charge() 호출 → 폴백 동작
    # store_payments INSERT
    ...
```

### 11-2. woorichat 자산 활용

#### 전제

발주사 — 소스/API 사양 인계 (예정: 2주 내).

#### 구현 안

```python
# models/translator.py — 신규 Provider 추가
class WoorichatTranslateProvider:
    name = 'woorichat'
    def __init__(self, base_url: str, api_key: str): ...

    def translate(self, text: str, *, source: str, target: str) -> str:
        # woorichat API 사양에 맞춰 작성
        # response = httpx.post(f'{self._base}/translate', ...)
        ...

def get_translator():
    name = os.environ.get('TRANSLATOR_PROVIDER', 'deepl').lower()
    if name == 'woorichat':
        return WoorichatTranslateProvider(
            base_url=os.environ.get('WOORICHAT_TRANSLATE_BASE', ''),
            api_key=os.environ.get('WOORICHAT_TRANSLATE_KEY', ''),
        )
    return DeepLProvider(api_key=os.environ.get('DEEPL_API_KEY', ''))
```

#### 응답속도 검증

P95 측정 → 한국 사용자 500ms 이하 통과 시 운영 전환.

### 11-3. 자동화 Stage 1~3

| Stage | 모듈 | 시점 |
|---|---|---|
| Stage 1 | `ai_chatbot` (카톡 챗봇 + 이메일 AI) | 출시 +1~3개월 |
| Stage 2 | `voice_call_ai` + `social_auto_post` (SNS 자동 게시) + 행동 시퀀스 | 출시 +3~6개월 |
| Stage 3 | `crm_ads_auto` (CRM + Meta/Google Ads 자동) | 출시 +6~12개월 |

각 Stage 는 별도 SOW 또는 CR 로 분리. 본 SOW 의 1차에는 모듈 키만 정의(비활성).

---

## 12. API 스펙 요약 (개발사 참고)

### 12-1. 공통 응답 형식

```json
{
  "success": true,
  "data": { ... }
}
// 실패:
{
  "success": false,
  "message": "에러 메시지 (한국어)",
  "error_code": "OPTIONAL_CODE"
}
```

### 12-2. 인증

```
POST /api/auth/login
  body: {email, password, language}
  res: {success, token, refresh_token, user}

POST /api/auth/refresh
  body: {refresh_token}
  res: {success, token, refresh_token}

POST /api/auth/logout
  res: {success}

POST /api/auth/signup
  body: {email, password, language, consents: [{policy_version_id, agreed}]}
  res: {success, user, token, refresh_token}
```

### 12-3. 매장

```
GET /api/search/facilities?q=&lat=&lng=&radius_km=&lang=&limit=
  res: {success, results: [{id, name, address, image_url, distance_km, ...}]}

GET /api/facilities/<id>?lang=en
  res: {success, facility: {id, name, address, lat, lng, image_url,
                            phone, business_hours, category, ...}}

GET /api/facilities/<id>/images
GET /api/facilities/<id>/menu?lang=en
```

### 12-4. 결제

```
POST /api/billing/cards
  body: {billing_key, card_last4, card_brand}
  res: {success, card_id}

POST /api/billing/subscriptions
  body: {service_type, quantity, period_months, receipt_email}
  res: {success, subscription, payment: {gateway, fallback_from, status}}

POST /api/admin/payments/<id>/refund
  body: {amount, reason}
  res: {success, provider}
```

### 12-5. 푸시

```
POST /api/push/tokens
  body: {token, platform: 'fcm'|'apns', language}
  res: {success}

DELETE /api/push/tokens/<token>
  res: {success}
```

### 12-6. 시즌 배경 (이미 구현됨)

```
GET /api/theme/current[?season=&at=ISO]
  res: {success, theme: {id, season, image_url, overlay_alpha, ...} | null,
        season: 'summer', fallback: false}

GET    /api/admin/themes
POST   /api/admin/themes              # multipart
PATCH  /api/admin/themes/<id>
POST   /api/admin/themes/<id>/activate
DELETE /api/admin/themes/<id>
```

---

## 13. 산출물 / 검수 / 일정 / 변경 관리

(v1.0 SOW 와 동일. 본 상세본은 v1.0 의 부록 + 코드 스펙으로 동작.)

### 13-1. 산출물

- 코드 4 저장소 (mobile / admin-web / provider-web / backend)
- DB 스키마 SQL + ERD
- 디자인 시스템 (Figma + 토큰표)
- API 문서 (OpenAPI 또는 동등)
- 운영 매뉴얼 + 배포 매뉴얼
- 테스트 결과 (pytest + flutter test + 페르소나)
- CI/CD 파이프라인
- 외부 키 인계 기록

### 13-2. 검수 기준

| 영역 | 기준 |
|---|---|
| 기능 | 1차 12 모듈 100% 동작. 페르소나 시나리오 통과. |
| 성능 | mobile 콜드 스타트 ≤ 3초. API P95 ≤ 500ms (싱가포르 → 한국 측정 미달 시 2차 한국 리전). |
| 안정성 | Sentry 24시간 무 크래시. 백엔드 health 99%+. |
| 보안 | `_validate_production_env` 통과. HTTPS 강제. JWT 만료 검증. |
| 디자인 | 디자인 시스템 100% 일치. 8 위젯 사용. |
| 다국어 | 23 언어 키 95%+ 커버. |
| 접근성 | WCAG AA. |
| 문서 | 본 SOW + 산출물 전체 인계 + 운영 매뉴얼 1회 워크스루. |

### 13-3. 일정

T-8 (이번 주) → T-1 → 출시 (2026-08 초). v1.0 SOW 와 동일.

### 13-4. 변경 관리

| 영역 | 처리 |
|---|---|
| 1차 범위 외 추가 요청 | CR 또는 2차 SOW |
| 외부 협약 지연 (토스/제로페이) | 키 미주입 = sim/stub 으로 출시 → 키 들어오면 ENV 변경 |
| woorichat 자산 인계 지연 | 1차는 DeepL Pro 단독. 인계 후 2차 활용 |
| 응답속도 미달 | 2차 한국 리전 검토 트리거 |

---

## 14. 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-06-05 | v1.1 상세본 — v1.0 요약본의 1차/2차 분리 + 역할 분담 유지. 디자인 시스템·인증·Feature Flag·12 모듈 코드 패턴·API 스펙 추가. |

---

## 15. 본 문서와 별개로 인계할 자료

- `models/payment_provider.py` — 결제 폴백 (이미 구현)
- `models/database.py` — 30+ 테이블 스키마 + 마이그레이션
- `routes/*.py` — 34 라우트 docstring
- `mobile/lib/utils/app_theme.dart` + `neu_theme.dart` — 디자인 토큰
- `mobile/lib/widgets/pw_*.dart` + `glass_card.dart` + `seasonal_background.dart` + `seasonal_particles.dart` — 공통 위젯
- `.env.example` — ENV 카테고리
- `Procfile` + `gunicorn.conf.py` — 배포 설정
- `pathwave_persona_test_plan_C-3_2026-05-23.md` — 페르소나 시나리오
