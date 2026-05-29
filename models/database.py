import os
import sqlite3  # noqa: F401  (호환성 — 외부 모듈에서 sqlite3.Row 등 import 시 대비)

from models.db_adapter import open_connection, use_postgres

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'pathwave.db')


def get_db():
    """DB connection — DATABASE_URL ENV 가 postgres 면 PostgreSQL, 아니면 SQLite (PR #51).

    반환되는 connection 객체는 양쪽 모두 ``execute / commit / close / cursor``
    인터페이스를 동일하게 제공 (PostgreSQL 측은 sqlite3 호환 wrapper).
    """
    return open_connection(sqlite_path=DB_PATH)


def init_db():
    db = get_db()
    db.executescript("""
        -- 사용자 DB
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT    UNIQUE NOT NULL,
            password    TEXT,                          -- 소셜 로그인은 NULL 가능
            provider    TEXT    DEFAULT 'email',       -- email / google / apple / kakao / naver
            social_id   TEXT,                          -- 소셜 로그인 고유 ID
            language    TEXT    DEFAULT 'ko',          -- 기본 언어
            verified    INTEGER DEFAULT 1,
            deleted_at  TEXT,                          -- 탈퇴일 (7일 후 재가입 가능)
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS email_codes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT    NOT NULL,
            code        TEXT    NOT NULL,
            expires_at  TEXT    NOT NULL,
            used        INTEGER DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        -- 시설/비콘 DB
        CREATE TABLE IF NOT EXISTS facilities (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT    NOT NULL,
            address        TEXT,
            phone          TEXT,                          -- SRS FR-STORE-001
            business_hours TEXT,                          -- SRS FR-STORE-001 (opaque, 프론트가 포맷 결정)
            latitude       REAL,
            longitude      REAL,
            description    TEXT,
            image_url      TEXT,
            owner_id       INTEGER,                       -- facility_accounts.id
            active         INTEGER DEFAULT 1,
            created_at     TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS facility_accounts (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            business_no           TEXT    UNIQUE NOT NULL,
            company_name          TEXT    NOT NULL,
            email                 TEXT    UNIQUE NOT NULL,
            password              TEXT    NOT NULL,
            phone                 TEXT,
            manager_name          TEXT,
            manager_phone         TEXT,
            manager_email         TEXT,
            verified              INTEGER DEFAULT 0,        -- 호환용 (status='verified'와 동기화)
            status                TEXT    DEFAULT 'pending',-- pending|verified|suspended
            business_doc_url      TEXT,                     -- 사업자등록증 이미지
            approved_at           TEXT,
            approved_by_admin_id  INTEGER,                  -- super_admin_accounts.id
            suspended_at          TEXT,
            suspended_reason      TEXT,
            created_at            TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS beacons (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_no   TEXT    UNIQUE NOT NULL,       -- SN (FSC-BP108B)
            uuid        TEXT    UNIQUE NOT NULL,       -- iBeacon UUID (디바이스마다 고유 저장)
            major       INTEGER,                       -- iBeacon Major (= facility_id)
            minor       INTEGER,                       -- iBeacon Minor (매장 내 순번)
            facility_id INTEGER,
            status      TEXT    DEFAULT 'inactive',   -- active / inactive / inventory / lost
            battery_pct INTEGER DEFAULT 100,
            firmware_ver TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        );
        -- idx_beacons_major_minor 인덱스는 ALTER TABLE ADD COLUMN 이후 별도 생성 (Phase C 마이그레이션).

        CREATE TABLE IF NOT EXISTS wifi_profiles (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id     INTEGER NOT NULL,
            ssid            TEXT    NOT NULL,
            password        TEXT    NOT NULL,              -- AES 암호화 저장
            -- P14 — WiFi 로밍 확장 (B 풀 스코프 선반영, 일부 v1 미사용·flag)
            scope           TEXT    DEFAULT 'public',      -- 'public'|'private'
            unit_id         INTEGER,                       -- units.id (private)
            credential_mode TEXT    DEFAULT 'static',      -- 'static'|'managed'|'radius'
            bssid           TEXT,                          -- AP MAC 검증용 (선택)
            country         TEXT    DEFAULT 'KR',          -- .mobileconfig 용
            active          INTEGER DEFAULT 1,
            created_at      TEXT    DEFAULT (datetime('now')),
            updated_at      TEXT    DEFAULT (datetime('now'))
        );

        -- P14 — 비콘 ↔ WiFi 매핑 (N:N).
        CREATE TABLE IF NOT EXISTS beacon_wifi (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            beacon_id       INTEGER NOT NULL,
            wifi_profile_id INTEGER NOT NULL,
            priority        INTEGER DEFAULT 0,
            created_at      TEXT    DEFAULT (datetime('now')),
            UNIQUE (beacon_id, wifi_profile_id),
            FOREIGN KEY (beacon_id)       REFERENCES beacons(id),
            FOREIGN KEY (wifi_profile_id) REFERENCES wifi_profiles(id)
        );
        CREATE INDEX IF NOT EXISTS idx_beacon_wifi_beacon ON beacon_wifi(beacon_id);
        CREATE INDEX IF NOT EXISTS idx_beacon_wifi_wifi   ON beacon_wifi(wifi_profile_id);

        -- P14 — 기간제 공간 단위 (호실/자리/주차구역).
        CREATE TABLE IF NOT EXISTS units (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER NOT NULL,
            name        TEXT    NOT NULL,                  -- '301호' / 'A-12'
            type        TEXT    NOT NULL DEFAULT 'room',   -- 'room'|'seat'|'parking'
            description TEXT,
            active      INTEGER DEFAULT 1,
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (facility_id) REFERENCES facilities(id)
        );
        CREATE INDEX IF NOT EXISTS idx_units_facility ON units(facility_id);

        -- 비콘 프로비저닝 — 점주 서비스 신청 (설계 2026-05-29).
        -- 점주가 설치위치 + WiFi 를 신청 → 슈퍼어드민이 인벤토리 비콘을 매칭·발송.
        CREATE TABLE IF NOT EXISTS service_requests (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id         INTEGER,
            facility_account_id INTEGER NOT NULL,
            service_type        TEXT    NOT NULL DEFAULT 'wifi',
            status              TEXT    NOT NULL DEFAULT 'pending', -- pending|matched|shipped|installed|canceled
            note                TEXT,
            created_at          TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (facility_id)         REFERENCES facilities(id),
            FOREIGN KEY (facility_account_id) REFERENCES facility_accounts(id)
        );
        CREATE INDEX IF NOT EXISTS idx_service_requests_acct ON service_requests(facility_account_id);

        -- 신청 1건 안의 위치별 유닛 (1:N). 설치위치 = 점주 입력값.
        CREATE TABLE IF NOT EXISTS service_request_units (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id        INTEGER NOT NULL,
            location_label    TEXT,                              -- 점주 입력 설치위치
            ssid              TEXT,
            wifi_password_enc TEXT,                              -- AES-256-GCM 암호화
            period_start      TEXT,
            period_end        TEXT,
            beacon_id         INTEGER,                           -- 매칭된 비콘 (NULL=미매칭)
            status            TEXT    NOT NULL DEFAULT 'pending', -- pending|matched
            created_at        TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (request_id) REFERENCES service_requests(id),
            FOREIGN KEY (beacon_id)  REFERENCES beacons(id)
        );
        CREATE INDEX IF NOT EXISTS idx_sru_request ON service_request_units(request_id);

        -- P14 — WiFi 접근 권한 (시간제).
        CREATE TABLE IF NOT EXISTS wifi_access_grant (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            target_type TEXT    NOT NULL,                  -- 'unit'|'facility'
            target_id   INTEGER NOT NULL,
            valid_from  TEXT    NOT NULL,
            valid_until TEXT,                              -- NULL = 무기한
            source      TEXT    DEFAULT 'manual',          -- 'check_in'|'manual'|'qr'
            granted_by_actor_role TEXT,
            granted_by_actor_id   INTEGER,
            revoked_at  TEXT,                              -- soft revoke
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_wifi_grant_user   ON wifi_access_grant(user_id);
        CREATE INDEX IF NOT EXISTS idx_wifi_grant_target ON wifi_access_grant(target_type, target_id);
        CREATE INDEX IF NOT EXISTS idx_wifi_grant_valid  ON wifi_access_grant(valid_until);

        -- P14 — 사용자/사장 디바이스 (앱·노트북·태블릿).
        CREATE TABLE IF NOT EXISTS devices (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            account_kind TEXT    NOT NULL,                 -- 'user'|'facility'|'staff'
            account_id   INTEGER NOT NULL,
            device_id    TEXT    NOT NULL,                 -- 앱이 생성한 UUID
            device_label TEXT,
            platform     TEXT,                             -- 'ios'|'android'|'web'|'desktop'
            kind         TEXT    DEFAULT 'app',            -- 'app'|'portal'|'browser'
            last_seen_at TEXT    DEFAULT (datetime('now')),
            created_at   TEXT    DEFAULT (datetime('now')),
            UNIQUE (account_kind, account_id, device_id)
        );
        CREATE INDEX IF NOT EXISTS idx_devices_account  ON devices(account_kind, account_id);
        CREATE INDEX IF NOT EXISTS idx_devices_lastseen ON devices(last_seen_at);

        CREATE TABLE IF NOT EXISTS user_wifi_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            facility_id INTEGER NOT NULL,
            connected_at TEXT   DEFAULT (datetime('now'))
        );

        -- 스탬프 적립 이력 (SRS FR-STAMP-002)
        CREATE TABLE IF NOT EXISTS stamps (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER NOT NULL,
            user_id     INTEGER NOT NULL,
            amount      INTEGER DEFAULT 1,
            note        TEXT,
            granted_by_account_id INTEGER,                 -- facility_accounts.id (소속 사장님)
            granted_by_actor_role TEXT,                    -- 'owner' | 'admin' | 'staff'
            granted_by_actor_id   INTEGER,                 -- staff_accounts.id 또는 facility_accounts.id
            expires_at  TEXT,                              -- 정책 기반 만료일 (NULL = 무기한)
            created_at  TEXT    DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_stamps_facility_user
            ON stamps(facility_id, user_id);

        -- 스탬프 정책 (SRS FR-STAMP-001) — 매장당 1개 (active=1)
        CREATE TABLE IF NOT EXISTS stamp_policies (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id        INTEGER NOT NULL,
            reward_threshold   INTEGER NOT NULL,           -- N개 모으면 보상
            reward_description TEXT    NOT NULL,           -- 예: '아메리카노 1잔 무료'
            expires_days       INTEGER,                    -- 적립일 기준 N일 (NULL=무기한)
            design_image_url   TEXT,                       -- 스탬프 카드 디자인 이미지
            auto_stamp_enabled INTEGER DEFAULT 0,          -- BLE 자동 적립 ON/OFF
            auto_stamp_cooldown_minutes INTEGER DEFAULT 60,-- 같은 사용자 재적립 쿨다운
            active             INTEGER DEFAULT 1,
            created_at         TEXT    DEFAULT (datetime('now')),
            updated_at         TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (facility_id) REFERENCES facilities(id)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_stamp_policies_active
            ON stamp_policies(facility_id) WHERE active=1;

        -- 쿠폰 (SRS FR-COUPON-001/002)
        CREATE TABLE IF NOT EXISTS coupons (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER NOT NULL,
            user_id     INTEGER NOT NULL,
            title       TEXT    NOT NULL,
            benefit     TEXT,                              -- 혜택 내용
            used        INTEGER DEFAULT 0,
            used_at     TEXT,                              -- 사용 시각
            used_by_actor_role TEXT,                       -- 'owner'|'admin'|'staff'
            used_by_actor_id   INTEGER,
            issued_by_actor_role TEXT,
            issued_by_actor_id   INTEGER,
            expires_at  TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_coupons_facility_user
            ON coupons(facility_id, user_id);
        CREATE INDEX IF NOT EXISTS idx_coupons_user
            ON coupons(user_id);

        -- 직원/관리자 계정 (SRS FR-STAFF-002)
        -- 사장님(facility_accounts) 1:N 직원(staff_accounts).
        -- role: 'admin'(운영) | 'staff'(제한)
        CREATE TABLE IF NOT EXISTS staff_accounts (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_account_id INTEGER NOT NULL,           -- 부모 (owner)
            email               TEXT    UNIQUE NOT NULL,
            password            TEXT    NOT NULL,
            role                TEXT    NOT NULL,
            name                TEXT,
            phone               TEXT,
            invitation_id       INTEGER,                    -- 추적용
            created_at          TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (facility_account_id) REFERENCES facility_accounts(id),
            FOREIGN KEY (invitation_id)       REFERENCES staff_invitations(id)
        );
        CREATE INDEX IF NOT EXISTS idx_staff_accounts_owner
            ON staff_accounts(facility_account_id);

        -- 직원 초대 (SRS FR-STAFF-001/002)
        -- 사장님(facility_account)이 이메일로 admin/staff 초대 발송.
        -- status: pending(초대중) / accepted(수락) / expired(만료) / revoked(취소)
        CREATE TABLE IF NOT EXISTS staff_invitations (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_account_id INTEGER NOT NULL,           -- 초대한 사장님
            email               TEXT    NOT NULL,           -- 초대받는 사람 이메일
            role                TEXT    NOT NULL,           -- 'admin' | 'staff'
            invite_token        TEXT    NOT NULL UNIQUE,
            expires_at          TEXT    NOT NULL,
            status              TEXT    DEFAULT 'pending',
            accepted_at         TEXT,
            created_at          TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (facility_account_id) REFERENCES facility_accounts(id)
        );
        CREATE INDEX IF NOT EXISTS idx_staff_invitations_owner
            ON staff_invitations(facility_account_id);
        CREATE INDEX IF NOT EXISTS idx_staff_invitations_email
            ON staff_invitations(email);

        -- Super Admin 계정 (PathWave 운영자 — 사장님과 별도)
        -- role: 'super' (최고 권한, 다른 super admin 추가/삭제 가능) | 'admin' (운영)
        CREATE TABLE IF NOT EXISTS super_admin_accounts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT    UNIQUE NOT NULL,
            password      TEXT    NOT NULL,
            name          TEXT,
            role          TEXT    NOT NULL DEFAULT 'admin',
            active        INTEGER DEFAULT 1,
            last_login_at TEXT,
            created_at    TEXT    DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_super_admin_accounts_email
            ON super_admin_accounts(email);

        -- 결제 (SRS FR-PAY-001~005)
        CREATE TABLE IF NOT EXISTS billing_keys (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_account_id INTEGER NOT NULL,
            pg_key              TEXT    NOT NULL,            -- PG 빌링키 (시뮬: 'sim-' + uuid)
            card_brand          TEXT,                        -- 카드사
            masked_card         TEXT,                        -- ****-****-****-6789
            active              INTEGER DEFAULT 1,
            created_at          TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (facility_account_id) REFERENCES facility_accounts(id)
        );
        CREATE INDEX IF NOT EXISTS idx_billing_keys_owner
            ON billing_keys(facility_account_id);

        -- 서비스 구독 (FR-PAY-002/003)
        CREATE TABLE IF NOT EXISTS service_subscriptions (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_account_id INTEGER NOT NULL,
            service_type        TEXT    NOT NULL,            -- 'wifi'|'event'|'notification'
            quantity            INTEGER NOT NULL,
            period_months       INTEGER NOT NULL,            -- 1=월간, 12=연간
            unit_price          INTEGER NOT NULL,            -- KRW
            total_price         INTEGER NOT NULL,            -- 부가세 포함
            started_at          TEXT    DEFAULT (datetime('now')),
            ends_at             TEXT,
            status              TEXT    DEFAULT 'active',    -- active|expired|canceled
            created_at          TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (facility_account_id) REFERENCES facility_accounts(id)
        );
        CREATE INDEX IF NOT EXISTS idx_subscriptions_owner
            ON service_subscriptions(facility_account_id);

        -- 결제 내역 (FR-PAY-004)
        CREATE TABLE IF NOT EXISTS payments (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_account_id INTEGER NOT NULL,
            subscription_id     INTEGER,
            order_no            TEXT    NOT NULL UNIQUE,
            amount              INTEGER NOT NULL,            -- 공급가
            vat                 INTEGER NOT NULL,            -- 부가세 (10%)
            total               INTEGER NOT NULL,            -- 합계
            pg_tid              TEXT,                        -- PG 거래번호 (시뮬)
            status              TEXT    DEFAULT 'pending',   -- pending|paid|failed
            receipt_email       TEXT,
            paid_at             TEXT,
            created_at          TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (facility_account_id) REFERENCES facility_accounts(id),
            FOREIGN KEY (subscription_id) REFERENCES service_subscriptions(id)
        );
        CREATE INDEX IF NOT EXISTS idx_payments_owner
            ON payments(facility_account_id);

        -- 푸시 토큰 (SRS FR-NOTI 푸시 발송 / FR-CHAT 새 메시지 알림)
        -- 한 사용자가 여러 디바이스 가능. 같은 (token, platform)은 UNIQUE.
        CREATE TABLE IF NOT EXISTS push_tokens (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            token       TEXT    NOT NULL,
            platform    TEXT    NOT NULL,                  -- 'fcm' | 'apns'
            language    TEXT,                              -- 푸시 언어 힌트
            created_at  TEXT    DEFAULT (datetime('now')),
            updated_at  TEXT    DEFAULT (datetime('now')),
            UNIQUE (token, platform),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_push_tokens_user ON push_tokens(user_id);

        -- 채팅 (SRS FR-CHAT-001/002) — 1:1 사용자-매장
        -- chat_rooms: 매장×사용자 단일성 (UNIQUE)
        CREATE TABLE IF NOT EXISTS chat_rooms (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id     INTEGER NOT NULL,
            user_id         INTEGER NOT NULL,
            last_message_at TEXT,
            created_at      TEXT    DEFAULT (datetime('now')),
            UNIQUE (facility_id, user_id),
            FOREIGN KEY (facility_id) REFERENCES facilities(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_chat_rooms_facility ON chat_rooms(facility_id);
        CREATE INDEX IF NOT EXISTS idx_chat_rooms_user     ON chat_rooms(user_id);

        CREATE TABLE IF NOT EXISTS chat_messages (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id       INTEGER NOT NULL,
            sender_type   TEXT    NOT NULL,                -- 'user' | 'facility'
            sender_actor_role TEXT,                        -- 'owner'|'admin'|'staff' (facility 측만)
            sender_actor_id   INTEGER,
            body          TEXT    NOT NULL,
            body_lang     TEXT,                            -- 원문 언어 (lang_hint, P8b). NULL=미상
            read_at       TEXT,
            created_at    TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (room_id) REFERENCES chat_rooms(id)
        );
        CREATE INDEX IF NOT EXISTS idx_chat_messages_room ON chat_messages(room_id);

        -- P8b — 채팅 메시지 번역 캐시. (message_id, lang) UNIQUE.
        -- lazy 번역: viewer 의 lang 으로 처음 요청될 때 1회 번역 후 영구 캐시.
        -- facility_translations 와 동일한 캐시 패턴.
        CREATE TABLE IF NOT EXISTS chat_message_translations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id      INTEGER NOT NULL,
            lang            TEXT    NOT NULL,              -- viewer 언어 (ko/en/ja/zh-CN/...)
            translated_text TEXT    NOT NULL,
            provider        TEXT,                          -- 'stub'|'google'|'deepl' (감사용)
            created_at      TEXT    DEFAULT (datetime('now')),
            UNIQUE (message_id, lang),
            FOREIGN KEY (message_id) REFERENCES chat_messages(id)
        );
        CREATE INDEX IF NOT EXISTS idx_chat_msg_translations_message
            ON chat_message_translations(message_id);

        -- 알림 발송 (SRS FR-NOTI-001/002)
        -- status: pending(예약 대기) / sent(발송 완료) / failed / canceled
        -- target_type: all_visited(매장 방문 이력 있는 모든 사용자) | specific
        CREATE TABLE IF NOT EXISTS notifications (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id        INTEGER NOT NULL,
            title              TEXT    NOT NULL,
            body               TEXT    NOT NULL,
            target_type        TEXT    NOT NULL,
            scheduled_at       TEXT,                       -- NULL=즉시
            sent_at            TEXT,
            status             TEXT    DEFAULT 'pending',
            recipient_count    INTEGER DEFAULT 0,
            issued_by_actor_role TEXT,
            issued_by_actor_id   INTEGER,
            created_at         TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (facility_id) REFERENCES facilities(id)
        );
        CREATE INDEX IF NOT EXISTS idx_notifications_facility
            ON notifications(facility_id);

        CREATE TABLE IF NOT EXISTS notification_recipients (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            notification_id INTEGER NOT NULL,
            user_id         INTEGER NOT NULL,
            read_at         TEXT,
            created_at      TEXT    DEFAULT (datetime('now')),
            UNIQUE (notification_id, user_id),
            FOREIGN KEY (notification_id) REFERENCES notifications(id)
        );
        CREATE INDEX IF NOT EXISTS idx_notification_recipients_user
            ON notification_recipients(user_id);

        -- P11 — 알림 부가서비스 수량(quota) 관리 (사장 결제 단위로 1 row).
        -- 결제 시 INSERT, 발송마다 quantity_used += 1. expires_at 도래 시 만료.
        -- 사장이 동일 service_type 으로 여러 번 결제하면 row 가 누적.
        CREATE TABLE IF NOT EXISTS notification_quota (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_account_id INTEGER NOT NULL,
            subscription_id     INTEGER,                       -- service_subscriptions.id
            payment_id          INTEGER,                       -- payments.id (감사용)
            quantity_purchased  INTEGER NOT NULL,
            quantity_used       INTEGER NOT NULL DEFAULT 0,
            expires_at          TEXT,                          -- NULL=무기한 (출시 v1 은 항상 명시)
            created_at          TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (facility_account_id) REFERENCES facility_accounts(id),
            FOREIGN KEY (subscription_id)     REFERENCES service_subscriptions(id),
            FOREIGN KEY (payment_id)          REFERENCES payments(id)
        );
        CREATE INDEX IF NOT EXISTS idx_notification_quota_owner
            ON notification_quota(facility_account_id);
        CREATE INDEX IF NOT EXISTS idx_notification_quota_expires
            ON notification_quota(expires_at);

        -- P11 — 어드민이 관리하는 금칙어 블록리스트.
        -- AI 검토 1차 단계: term 이 알림 title/body 에 포함되면 severity 따라 분기:
        --   'block' = 자동 reject, 'flag' = review 큐로 (수동 승인 대기).
        CREATE TABLE IF NOT EXISTS notification_blocklist (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            term                TEXT    NOT NULL,
            severity            TEXT    NOT NULL DEFAULT 'flag',  -- 'block' | 'flag'
            note                TEXT,                              -- 어드민 메모
            created_by_admin_id INTEGER,                           -- super_admin_accounts.id
            created_at          TEXT    DEFAULT (datetime('now')),
            UNIQUE (term)
        );
        CREATE INDEX IF NOT EXISTS idx_notification_blocklist_severity
            ON notification_blocklist(severity);

        -- 매장 다국어 캐시 (SRS FR-I18N-002)
        -- 매장명/주소/설명을 언어별로 캐시. (facility_id, language) UNIQUE.
        CREATE TABLE IF NOT EXISTS facility_translations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER NOT NULL,
            language    TEXT    NOT NULL,                  -- 'ko' | 'en' | 'ja' | 'zh' | ...
            name        TEXT,
            address     TEXT,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now')),
            updated_at  TEXT    DEFAULT (datetime('now')),
            UNIQUE (facility_id, language),
            FOREIGN KEY (facility_id) REFERENCES facilities(id)
        );
        CREATE INDEX IF NOT EXISTS idx_facility_translations_facility
            ON facility_translations(facility_id);

        -- C-4 USP — 매장 메뉴 OCR + 자동 번역 (D-4-a).
        -- facility_menu_uploads: 사장이 업로드한 원본 메뉴 이미지 + OCR 상태/raw 결과.
        -- facility_menu_items:   OCR 또는 수동 등록 메뉴 항목 (lang 별 번역 캐시).
        --   - price 는 항상 KRW 단위 ("9,000원" / "₩9,000"). 외국 통화 금지.
        --   - 자동 번역 대상 = name / description 만. price 는 원본 유지.
        CREATE TABLE IF NOT EXISTS facility_menu_uploads (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER NOT NULL,
            image_url   TEXT    NOT NULL,
            ocr_status  TEXT    DEFAULT 'pending',    -- 'pending' | 'success' | 'failed'
            ocr_provider TEXT,                        -- 'stub' | 'gcv' | 'claude' | 'clova'
            ocr_result  TEXT,                         -- JSON: provider raw 결과
            uploaded_by_actor_role TEXT,
            uploaded_by_actor_id   INTEGER,
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (facility_id) REFERENCES facilities(id)
        );
        CREATE INDEX IF NOT EXISTS idx_facility_menu_uploads_facility
            ON facility_menu_uploads(facility_id);

        CREATE TABLE IF NOT EXISTS facility_menu_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id     INTEGER NOT NULL,
            language        TEXT    NOT NULL,         -- 'ko' (원본) | 'en' | 'ja' | ...
            name            TEXT    NOT NULL,
            price           TEXT,                     -- 항상 KRW (예: '9,000원')
            description     TEXT,
            sort_order      INTEGER DEFAULT 0,
            source          TEXT    DEFAULT 'manual', -- 'ocr' | 'manual' | 'deepl' | 'translated'
            upload_id       INTEGER,                  -- OCR origin (있다면)
            base_item_id    INTEGER,                  -- 자동 번역 시 원본 item (lang!=ko) 추적
            active          INTEGER DEFAULT 1,
            created_at      TEXT    DEFAULT (datetime('now')),
            updated_at      TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (facility_id)  REFERENCES facilities(id),
            FOREIGN KEY (upload_id)    REFERENCES facility_menu_uploads(id),
            FOREIGN KEY (base_item_id) REFERENCES facility_menu_items(id)
        );
        CREATE INDEX IF NOT EXISTS idx_facility_menu_items_facility_lang
            ON facility_menu_items(facility_id, language, active);

        -- 매장 다중 이미지 (SRS FR-STORE-001)
        -- facilities.image_url은 대표 이미지의 URL을 미러링한다 (핸드셰이크 호환).
        CREATE TABLE IF NOT EXISTS facility_images (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER NOT NULL,
            image_url   TEXT    NOT NULL,
            is_primary  INTEGER DEFAULT 0,
            sort_order  INTEGER DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (facility_id) REFERENCES facilities(id)
        );
        CREATE INDEX IF NOT EXISTS idx_facility_images_facility
            ON facility_images(facility_id);

        -- 회원 폐쇄형 가입을 위한 초대 코드 (PR #29 와이파이 초대)
        -- 발급자(inviter)는 다음 셋 중 하나:
        --   ① 일반 회원 (다른 지인을 추천)
        --   ② 시설 사장 (매장 부트스트랩 가입 코드)
        --   ③ 시설 직원 (매장 카운터에서 즉시 발급)
        CREATE TABLE IF NOT EXISTS invitations (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            code                TEXT UNIQUE NOT NULL,           -- 공유 가능한 짧은 코드
            inviter_user_id     INTEGER,                        -- 회원 추천 시
            inviter_facility_id INTEGER,                        -- 매장 발급 시
            inviter_staff_id    INTEGER,                        -- 직원 발급 시
            invitee_email       TEXT,                           -- 받는 사람 이메일 (선택)
            invitee_phone       TEXT,                           -- 받는 사람 전화 (선택)
            channel             TEXT,                           -- 'kakao'|'sms'|'link'|'qr'
            accepted_user_id    INTEGER,                        -- 가입 완료된 user
            accepted_at         TEXT,
            rewarded            INTEGER DEFAULT 0,              -- 보상 지급 여부
            expires_at          TEXT,
            created_at          TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (inviter_user_id)     REFERENCES users(id),
            FOREIGN KEY (inviter_facility_id) REFERENCES facilities(id),
            FOREIGN KEY (inviter_staff_id)    REFERENCES staff_accounts(id),
            FOREIGN KEY (accepted_user_id)    REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_invitations_code        ON invitations(code);
        CREATE INDEX IF NOT EXISTS idx_invitations_inviter     ON invitations(inviter_user_id);
        CREATE INDEX IF NOT EXISTS idx_invitations_facility    ON invitations(inviter_facility_id);

        -- 사용자 즐겨찾기 (Phase C) — 사용자가 매장을 즐겨찾기에 담는다.
        CREATE TABLE IF NOT EXISTS user_favorites (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            facility_id INTEGER NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now')),
            UNIQUE (user_id, facility_id),
            FOREIGN KEY (user_id)     REFERENCES users(id),
            FOREIGN KEY (facility_id) REFERENCES facilities(id)
        );
        CREATE INDEX IF NOT EXISTS idx_user_favorites_user
            ON user_favorites(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_favorites_facility
            ON user_favorites(facility_id);

        -- Phase D — i18n DB 기반 번역 저장소 (글로벌 i18n 전략 메모리).
        -- 키 하나에 23개 언어가 행으로 펼쳐진다. (key, lang) UNIQUE.
        -- DeepL/수동 입력 모두 이 테이블 한 곳에 모인다.
        CREATE TABLE IF NOT EXISTS translations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            key         TEXT    NOT NULL,                   -- 예: 'mypage.title'
            lang        TEXT    NOT NULL,                   -- ISO 코드 (ko / en / ja / zh-CN / ...)
            value       TEXT    NOT NULL,
            verified    INTEGER DEFAULT 0,                  -- 0=자동 번역, 1=사람 검수 완료
            source      TEXT    DEFAULT 'manual',           -- 'manual' | 'deepl' | 'seed'
            created_at  TEXT    DEFAULT (datetime('now')),
            updated_at  TEXT    DEFAULT (datetime('now')),
            UNIQUE (key, lang)
        );
        CREATE INDEX IF NOT EXISTS idx_translations_lang
            ON translations(lang);
        CREATE INDEX IF NOT EXISTS idx_translations_updated
            ON translations(updated_at);
        CREATE INDEX IF NOT EXISTS idx_translations_key
            ON translations(key);

        -- 시스템 공지 (PR #33) — 운영자가 사용자/사장/직원에게 일괄 공지
        CREATE TABLE IF NOT EXISTS announcements (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            title                TEXT    NOT NULL,
            body                 TEXT    NOT NULL,
            audience             TEXT    NOT NULL,  -- 'all'|'users'|'facilities'|'staff'
            created_by_admin_id  INTEGER,
            push_sent            INTEGER DEFAULT 0,
            pinned               INTEGER DEFAULT 0,
            starts_at            TEXT,
            ends_at              TEXT,
            created_at           TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_announcements_audience ON announcements(audience);
        CREATE INDEX IF NOT EXISTS idx_announcements_starts   ON announcements(starts_at);

        -- Phase I — 고객센터 (support tickets + messages + categories) -----
        CREATE TABLE IF NOT EXISTS support_tickets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            kind        TEXT    NOT NULL,         -- 'user' | 'provider'
            user_id     INTEGER,                  -- kind=user
            facility_account_id INTEGER,          -- kind=provider
            category    TEXT,                     -- code: 'usage' | 'beacon' | 'coupon' | 'payment' | 'etc' (user)
                                                  -- 'store_ops' | 'beacon' | 'payment' | 'settlement' | 'staff' (provider)
            subject     TEXT    NOT NULL,
            body        TEXT    NOT NULL,
            status      TEXT    DEFAULT 'open',   -- 'open' | 'replied' | 'closed'
            priority    TEXT    DEFAULT 'normal', -- 'low' | 'normal' | 'high' | 'urgent'
            replied_at  TEXT,
            closed_at   TEXT,
            created_at  TEXT    DEFAULT (datetime('now')),
            updated_at  TEXT    DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_support_tickets_user
            ON support_tickets(kind, user_id);
        CREATE INDEX IF NOT EXISTS idx_support_tickets_facility
            ON support_tickets(kind, facility_account_id);
        CREATE INDEX IF NOT EXISTS idx_support_tickets_status
            ON support_tickets(status, kind);

        CREATE TABLE IF NOT EXISTS support_messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id   INTEGER NOT NULL,
            sender      TEXT    NOT NULL,         -- 'user' | 'admin'
            sender_admin_id INTEGER,              -- super_admin_accounts.id (sender=admin)
            body        TEXT    NOT NULL,
            body_lang   TEXT,                     -- 원문 언어 (lang_hint, P8b). NULL=미상
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (ticket_id) REFERENCES support_tickets(id)
        );
        CREATE INDEX IF NOT EXISTS idx_support_messages_ticket
            ON support_messages(ticket_id);

        -- P8b — 사용자 문의 메시지 번역 캐시. chat_message_translations 와 동일 패턴.
        CREATE TABLE IF NOT EXISTS support_message_translations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id      INTEGER NOT NULL,
            lang            TEXT    NOT NULL,
            translated_text TEXT    NOT NULL,
            provider        TEXT,
            created_at      TEXT    DEFAULT (datetime('now')),
            UNIQUE (message_id, lang),
            FOREIGN KEY (message_id) REFERENCES support_messages(id)
        );
        CREATE INDEX IF NOT EXISTS idx_support_msg_translations_message
            ON support_message_translations(message_id);

        -- 어드민이 카테고리 마스터를 직접 관리 (label 은 i18n key)
        CREATE TABLE IF NOT EXISTS support_categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            kind        TEXT    NOT NULL,         -- 'user' | 'provider'
            code        TEXT    NOT NULL,         -- 'usage' | 'beacon' | ...
            label_key   TEXT    NOT NULL,         -- i18n key e.g. 'support.cat.user.usage'
            sort_order  INTEGER DEFAULT 0,
            active      INTEGER DEFAULT 1,
            created_at  TEXT    DEFAULT (datetime('now')),
            UNIQUE (kind, code)
        );
        CREATE INDEX IF NOT EXISTS idx_support_categories_kind
            ON support_categories(kind, active);

        -- FAQ
        CREATE TABLE IF NOT EXISTS faqs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            kind        TEXT    NOT NULL,         -- 'user' | 'provider'
            category    TEXT,                     -- support_categories.code 와 매칭 (선택)
            question    TEXT    NOT NULL,
            answer      TEXT    NOT NULL,
            lang        TEXT    NOT NULL DEFAULT 'ko',
            sort_order  INTEGER DEFAULT 0,
            active      INTEGER DEFAULT 1,
            created_at  TEXT    DEFAULT (datetime('now')),
            updated_at  TEXT    DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_faqs_kind_lang
            ON faqs(kind, lang, active);
        CREATE INDEX IF NOT EXISTS idx_faqs_category
            ON faqs(category);

        -- 신고 (abuse report) — 사용자 → 매장/사용자
        CREATE TABLE IF NOT EXISTS abuse_reports (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            target_kind     TEXT    NOT NULL,     -- 'facility' | 'user'
            target_id       INTEGER NOT NULL,
            reporter_kind   TEXT    NOT NULL,     -- 'user' | 'facility' (서로 신고 가능)
            reporter_id     INTEGER NOT NULL,
            reason_code     TEXT    NOT NULL,     -- 'spam' | 'abuse' | 'illegal' | 'inappropriate' | 'other'
            reason_detail   TEXT,
            status          TEXT    DEFAULT 'open', -- 'open' | 'in_review' | 'action_taken' | 'dismissed'
            resolution_note TEXT,
            resolved_by_admin_id INTEGER,
            resolved_at     TEXT,
            created_at      TEXT    DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_abuse_reports_target
            ON abuse_reports(target_kind, target_id);
        CREATE INDEX IF NOT EXISTS idx_abuse_reports_status
            ON abuse_reports(status);

        -- 채팅 차단 (block) — 손님(user)이 매장(facility)을 차단.
        -- 차단되면 양쪽 채팅방 목록에서 숨김 + 메시지 전송 차단 (UGC 모더레이션).
        -- 해지 가능 (DELETE). UNIQUE 로 중복 차단 방지.
        CREATE TABLE IF NOT EXISTS chat_blocks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            facility_id INTEGER NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now')),
            UNIQUE (user_id, facility_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (facility_id) REFERENCES facilities(id)
        );
        CREATE INDEX IF NOT EXISTS idx_chat_blocks_user
            ON chat_blocks(user_id);
        CREATE INDEX IF NOT EXISTS idx_chat_blocks_facility
            ON chat_blocks(facility_id);

        -- 공지 읽음 처리
        CREATE TABLE IF NOT EXISTS announcement_reads (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            announcement_id INTEGER NOT NULL,
            reader_kind     TEXT    NOT NULL,         -- 'user'|'facility'|'staff'
            reader_id       INTEGER NOT NULL,
            read_at         TEXT    DEFAULT (datetime('now')),
            UNIQUE(announcement_id, reader_kind, reader_id),
            FOREIGN KEY (announcement_id) REFERENCES announcements(id)
        );
        CREATE INDEX IF NOT EXISTS idx_announcement_reads_reader
            ON announcement_reads(reader_kind, reader_id);

        -- 앱 버전 강제 업데이트 (mobile 부팅 시 GET /api/version/check)
        CREATE TABLE IF NOT EXISTS app_versions (
            platform       TEXT PRIMARY KEY,        -- 'ios' | 'android'
            min_supported  TEXT NOT NULL,           -- semver 'X.Y.Z' (이 미만은 강제 업데이트)
            latest         TEXT NOT NULL,           -- 최신 권장 버전
            store_url      TEXT,                    -- 앱스토어/플레이스토어 링크
            force_message  TEXT,                    -- 강제 업데이트 안내 문구
            updated_at     TEXT DEFAULT (datetime('now'))
        );

        -- 알림 카테고리별 on/off 설정 (사용자 / 시설 별도) — Phase L
        CREATE TABLE IF NOT EXISTS notification_preferences (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sub_type    TEXT    NOT NULL,           -- 'user' | 'facility'
            subject_id  INTEGER NOT NULL,           -- users.id 또는 facility_accounts.id
            category    TEXT    NOT NULL,           -- 도메인별 카테고리 코드
            enabled     INTEGER NOT NULL DEFAULT 1, -- 0=off, 1=on (기본 on)
            updated_at  TEXT    DEFAULT (datetime('now')),
            UNIQUE (sub_type, subject_id, category)
        );
        CREATE INDEX IF NOT EXISTS idx_notif_prefs_subject
            ON notification_preferences(sub_type, subject_id);

        -- 법인 정보 (3 콘솔 footer 자동 동기) — Phase M
        -- 단일 행 (id=1) 패턴. 슈퍼어드민이 GET/PUT 으로 관리.
        CREATE TABLE IF NOT EXISTS company_info (
            id              INTEGER PRIMARY KEY CHECK (id = 1),
            company_name    TEXT,           -- 상호
            ceo             TEXT,           -- 대표자
            biz_number      TEXT,           -- 사업자등록번호 (예: 000-00-00000)
            commerce_number TEXT,           -- 통신판매업신고번호
            address         TEXT,           -- 사업장 주소
            phone           TEXT,           -- 대표 전화
            email           TEXT,           -- 대표 이메일 (운영 미지정 시 default 사용)
            hosting         TEXT,           -- 호스팅 제공자
            updated_at      TEXT    DEFAULT (datetime('now'))
        );

        -- 매장 업종 카테고리 (DB 시드 + admin CRUD).
        -- 국세청 100대 생활업종 기준 시드. 사장이 자유 입력 금지 (파편화 방지).
        CREATE TABLE IF NOT EXISTS store_categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    UNIQUE NOT NULL,
            group_name  TEXT,                            -- '음식' | '소매' | '서비스/숙박' | ...
            sort_order  INTEGER DEFAULT 0,
            active      INTEGER DEFAULT 1,
            created_at  TEXT    DEFAULT (datetime('now')),
            updated_at  TEXT    DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_store_categories_active
            ON store_categories(active, group_name, sort_order);

        -- 외부 AI API 사용량/비용 로그 (D-4-pre: 비용 모니터링).
        -- DeepL / Anthropic / Google Cloud Vision / 기타 외부 호출마다 기록.
        -- 월 합계로 임계점 ($100/월 = ₩151,020) 추적 → 슈퍼어드민 알림.
        CREATE TABLE IF NOT EXISTS ai_usage_logs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            provider      TEXT    NOT NULL,                -- 'deepl' | 'anthropic' | 'gcv' | 'sendgrid' | ...
            operation     TEXT    NOT NULL,                -- 'translate' | 'ocr' | 'image-analyze' | 'email-send'
            units         INTEGER DEFAULT 0,               -- chars (DeepL), tokens (Anthropic), pages (OCR), emails (SendGrid)
            cost_usd      REAL    DEFAULT 0.0,             -- 추정 비용 (USD)
            status        TEXT    DEFAULT 'ok',            -- 'ok' | 'error' | 'cached'
            facility_id   INTEGER,                         -- 매장 컨텍스트 (있다면)
            user_id       INTEGER,                         -- 사용자 컨텍스트 (있다면)
            actor_role    TEXT,                            -- 'user'|'facility'|'super_admin'|'system'
            created_at    TEXT    DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_created
            ON ai_usage_logs(created_at);
        CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_provider
            ON ai_usage_logs(provider, created_at);

        -- 슈퍼어드민 알림 snooze (D-4-pre).
        -- (admin_id, alert_id) 별 snoozed_until 시각 기록.
        -- 비용 임계점 50/80/100 외 향후 다른 critical 알림 (서버 다운 등) 재사용.
        CREATE TABLE IF NOT EXISTS admin_alert_dismissals (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id      INTEGER NOT NULL,
            alert_id      TEXT    NOT NULL,                -- 'cost-50' | 'cost-80' | 'cost-100' | ...
            snoozed_until TEXT    NOT NULL,                -- ISO datetime
            created_at    TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (admin_id) REFERENCES super_admin_accounts(id)
        );
        CREATE INDEX IF NOT EXISTS idx_admin_alert_dismissals_admin_alert
            ON admin_alert_dismissals(admin_id, alert_id);
    """)

    # ── 마이그레이션: 기존 DB에 없는 컬럼은 ADD COLUMN ────────────────────────
    _add_column_if_missing(db, 'facilities', 'phone',          'phone TEXT')
    _add_column_if_missing(db, 'facilities', 'business_hours', 'business_hours TEXT')
    # stamps에 grantor/expiry 추적 컬럼 (FR-STAMP-002)
    _add_column_if_missing(db, 'stamps', 'granted_by_account_id', 'granted_by_account_id INTEGER')
    _add_column_if_missing(db, 'stamps', 'granted_by_actor_role', 'granted_by_actor_role TEXT')
    _add_column_if_missing(db, 'stamps', 'granted_by_actor_id',   'granted_by_actor_id INTEGER')
    _add_column_if_missing(db, 'stamps', 'expires_at',            'expires_at TEXT')
    # coupons에 발급/사용 메타 (FR-COUPON-001/002)
    _add_column_if_missing(db, 'coupons', 'benefit',              'benefit TEXT')
    _add_column_if_missing(db, 'coupons', 'used_at',              'used_at TEXT')
    _add_column_if_missing(db, 'coupons', 'used_by_actor_role',   'used_by_actor_role TEXT')
    _add_column_if_missing(db, 'coupons', 'used_by_actor_id',     'used_by_actor_id INTEGER')
    _add_column_if_missing(db, 'coupons', 'issued_by_actor_role', 'issued_by_actor_role TEXT')
    _add_column_if_missing(db, 'coupons', 'issued_by_actor_id',   'issued_by_actor_id INTEGER')
    # stamp_policies: BLE 자동 적립 (FR-STAMP-001)
    _add_column_if_missing(db, 'stamp_policies', 'auto_stamp_enabled',
                           'auto_stamp_enabled INTEGER DEFAULT 0')
    _add_column_if_missing(db, 'stamp_policies', 'auto_stamp_cooldown_minutes',
                           'auto_stamp_cooldown_minutes INTEGER DEFAULT 60')
    # 자동 쿠폰 발급 (FR-COUPON-001 자동 발급)
    _add_column_if_missing(db, 'stamp_policies', 'reward_coupon_title',
                           "reward_coupon_title TEXT")
    _add_column_if_missing(db, 'stamp_policies', 'reward_coupon_benefit',
                           "reward_coupon_benefit TEXT")
    _add_column_if_missing(db, 'stamp_policies', 'reward_coupon_validity_days',
                           "reward_coupon_validity_days INTEGER")
    _add_column_if_missing(db, 'facilities', 'welcome_coupon_title',
                           "welcome_coupon_title TEXT")
    _add_column_if_missing(db, 'facilities', 'welcome_coupon_benefit',
                           "welcome_coupon_benefit TEXT")
    _add_column_if_missing(db, 'facilities', 'welcome_coupon_validity_days',
                           "welcome_coupon_validity_days INTEGER")
    _add_column_if_missing(db, 'coupons', 'source',
                           "source TEXT")  # 'manual'|'welcome'|'stamp_reward'

    # facility_accounts 가입 승인 흐름 (PR #26)
    _add_column_if_missing(db, 'facility_accounts', 'status',
                           "status TEXT DEFAULT 'pending'")
    _add_column_if_missing(db, 'facility_accounts', 'business_doc_url', 'business_doc_url TEXT')
    _add_column_if_missing(db, 'facility_accounts', 'approved_at', 'approved_at TEXT')
    _add_column_if_missing(db, 'facility_accounts', 'approved_by_admin_id', 'approved_by_admin_id INTEGER')
    _add_column_if_missing(db, 'facility_accounts', 'suspended_at', 'suspended_at TEXT')
    _add_column_if_missing(db, 'facility_accounts', 'suspended_reason', 'suspended_reason TEXT')
    # 기존 row 정합화: verified=1이면 status='verified'로 (한 번만 의미 있음, idempotent)
    db.execute(
        "UPDATE facility_accounts SET status='verified' WHERE verified=1 AND (status='pending' OR status IS NULL)"
    )

    # users 테이블: 가입 시 사용한 초대 코드 추적 (PR #29)
    _add_column_if_missing(db, 'users', 'invited_via_code', 'invited_via_code TEXT')
    # invitations: 사장 actor 추적 (매장 미등록 단계에서도 발급자 식별)
    _add_column_if_missing(db, 'invitations', 'inviter_facility_account_id',
                           'inviter_facility_account_id INTEGER')

    # beacons: 배터리 모니터링 메타 (PR #34)
    _add_column_if_missing(db, 'beacons', 'battery_updated_at', 'battery_updated_at TEXT')
    _add_column_if_missing(db, 'beacons', 'battery_voltage_mv', 'battery_voltage_mv INTEGER')
    _add_column_if_missing(db, 'beacons', 'last_seen_at',       'last_seen_at TEXT')

    # beacons: iBeacon Major/Minor (Phase C — FSC-BP108B 9개 실물 테스트 대응)
    # Major = 매장 ID, Minor = 매장 내 비콘 순번. UUID 는 PathWave 전체 통일.
    _add_column_if_missing(db, 'beacons', 'major', 'major INTEGER')
    _add_column_if_missing(db, 'beacons', 'minor', 'minor INTEGER')
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_beacons_major_minor ON beacons(major, minor)"
    )

    # P14 — WiFi 로밍 데이터 모델 (기존 DB 마이그레이션).
    # 신규 테이블(beacon_wifi/units/wifi_access_grant/devices)은 위 executescript 의
    # CREATE TABLE IF NOT EXISTS 로 멱등 생성.
    _add_column_if_missing(db, 'wifi_profiles', 'scope',
                           "scope TEXT DEFAULT 'public'")
    _add_column_if_missing(db, 'wifi_profiles', 'unit_id',
                           'unit_id INTEGER')
    _add_column_if_missing(db, 'wifi_profiles', 'credential_mode',
                           "credential_mode TEXT DEFAULT 'static'")
    _add_column_if_missing(db, 'wifi_profiles', 'bssid',
                           'bssid TEXT')
    _add_column_if_missing(db, 'wifi_profiles', 'country',
                           "country TEXT DEFAULT 'KR'")
    # SQLite ADD COLUMN 은 non-constant default 불가 → default 없이 추가 (기존 row=NULL).
    # 신규 row 는 위 CREATE TABLE 의 datetime('now') default 적용.
    _add_column_if_missing(db, 'wifi_profiles', 'updated_at', 'updated_at TEXT')
    # beacons.role — wifi / cashier (계산대 비콘 - cashier 는 결제·스탬프 트리거)
    _add_column_if_missing(db, 'beacons', 'role',
                           "role TEXT DEFAULT 'wifi'")

    # P8b — 채팅/사용자 문의 메시지 원문 언어 컬럼 (기존 DB 마이그레이션).
    # 신규 테이블(chat_message_translations / support_message_translations)은
    # 위 executescript 의 CREATE TABLE IF NOT EXISTS 로 멱등 생성.
    _add_column_if_missing(db, 'chat_messages',    'body_lang', 'body_lang TEXT')
    _add_column_if_missing(db, 'support_messages', 'body_lang', 'body_lang TEXT')

    # P8c — 푸시 알림 본문 다국어 (announcements / notifications).
    # 작성자의 원문 언어 저장 → 수신자 토큰 lang 으로 자동 번역(P8b push_to_users 통합).
    _add_column_if_missing(db, 'announcements',  'body_lang', 'body_lang TEXT')
    _add_column_if_missing(db, 'notifications',  'body_lang', 'body_lang TEXT')

    # P11 — 알림 부가서비스 어드민 워크플로 (기존 DB 마이그레이션).
    # ai_review_status: null | 'auto_pass' | 'flagged' | 'blocked'
    # status 확장: 기존 'pending' | 'sent' | 'failed' | 'canceled' 에 더해
    #             'unpaid'(quota 부족) | 'review'(어드민 수동 승인 대기) 추가.
    # 신규 테이블(notification_quota / notification_blocklist) 은 위 executescript
    # CREATE TABLE IF NOT EXISTS 로 멱등 생성.
    _add_column_if_missing(db, 'notifications', 'ai_review_status',
                           'ai_review_status TEXT')
    _add_column_if_missing(db, 'notifications', 'ai_review_reason',
                           'ai_review_reason TEXT')
    _add_column_if_missing(db, 'notifications', 'approved_by_admin_id',
                           'approved_by_admin_id INTEGER')
    _add_column_if_missing(db, 'notifications', 'approved_at',
                           'approved_at TEXT')

    # 비콘 배터리 시계열 (PR #34)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS beacon_battery_history (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            beacon_id    INTEGER NOT NULL,
            battery_pct  INTEGER,
            voltage_mv   INTEGER,
            reported_at  TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (beacon_id) REFERENCES beacons(id)
        );
        CREATE INDEX IF NOT EXISTS idx_beacon_battery_beacon
            ON beacon_battery_history(beacon_id);
        CREATE INDEX IF NOT EXISTS idx_beacon_battery_reported
            ON beacon_battery_history(reported_at);

        -- 회원가입 동의 기록 (PR #45) — 한국 정보통신망법 / 개인정보보호법 대응.
        -- 한 계정이 여러 동의 항목 + 향후 약관 개정 시 버전 갱신 가능.
        CREATE TABLE IF NOT EXISTS consents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sub_type    TEXT NOT NULL,    -- 'user' | 'facility' | 'staff'
            account_id  INTEGER NOT NULL, -- users.id / facility_accounts.id / staff_accounts.id
            kind        TEXT NOT NULL,    -- 'terms' | 'privacy' | 'age14' | 'location' | 'camera' | 'storage' | 'push' | 'marketing' | 'third_party'
            version     TEXT NOT NULL,    -- 정책 버전 (e.g. '2026-05-05', '1.0')
            accepted    INTEGER NOT NULL, -- 1 = 동의, 0 = 거부 (선택 항목)
            accepted_at TEXT DEFAULT (datetime('now')),
            ip          TEXT,
            user_agent  TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_consents_account
            ON consents(sub_type, account_id);
        CREATE INDEX IF NOT EXISTS idx_consents_kind
            ON consents(kind, version);

        -- 정책 본문 버전 관리 (PR #46) — 약관/개인정보 등 모든 버전 보존.
        -- 운영자 발행 → 적용일 도달 → 회원 자동 공지 + 재동의 요청.
        CREATE TABLE IF NOT EXISTS policies (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            kind            TEXT NOT NULL,
            lang            TEXT NOT NULL DEFAULT 'ko',
            version         TEXT NOT NULL,
            title           TEXT,
            body            TEXT NOT NULL,
            change_log      TEXT,
            effective_at    TEXT NOT NULL,
            created_by_admin_id INTEGER,
            created_at      TEXT DEFAULT (datetime('now')),
            email_notified  INTEGER DEFAULT 0,
            UNIQUE (kind, lang, version)
        );
        CREATE INDEX IF NOT EXISTS idx_policies_kind_lang
            ON policies(kind, lang, effective_at);
    """)

    # ── PR #47 — 연령 분류 + 부모 초대 + 미성년자 시설 제한 컬럼 추가 ────────
    # 미성년자(만 14~18) 는 부모 초대 코드로만 가입. 일부 시설(숙박/유흥)은
    # adult_only=1 로 표시 → 핸드셰이크 / 검색에서 자동 제외.
    _add_column_if_missing(db, 'users', 'birth_year',
                           'birth_year INTEGER')
    _add_column_if_missing(db, 'users', 'age_group',
                           "age_group TEXT")  # 'minor_14_18' | 'adult_19_plus'
    _add_column_if_missing(db, 'users', 'parent_invitation_id',
                           'parent_invitation_id INTEGER')
    _add_column_if_missing(db, 'facilities', 'adult_only',
                           'adult_only INTEGER NOT NULL DEFAULT 0')
    _add_column_if_missing(db, 'invitations', 'is_minor_invite',
                           'is_minor_invite INTEGER NOT NULL DEFAULT 0')
    _add_column_if_missing(db, 'invitations', 'inviter_liability_accepted_at',
                           'inviter_liability_accepted_at TEXT')

    # ── Super Admin 부트스트랩 ──────────────────────────────────────────────
    # ENV BOOTSTRAP_SUPER_ADMIN_EMAIL/PASSWORD가 설정되고 super admin이 0명이면
    # 최초 1명을 자동 생성. 이후 ENV 변경/삭제해도 무시됨 (idempotent).
    _bootstrap_super_admin(db)

    # ── 약관/정책 자동 등록 (Phase J) ────────────────────────────────────
    # static/policies/*.ko.md 가 있고 DB 에 (kind, version, lang) 가 없으면
    # v0.1 로 등록. 푸터 링크에서 본문이 정상적으로 노출되도록 보장.
    # (idempotent — 이미 있으면 skip)
    _bootstrap_policies(db)

    # ── FAQ 초기 시드 (C-2-3) ────────────────────────────────────────────
    # 출시 직후 빈 FAQ 화면을 피하기 위해 사용자 5건 + 사장 5건 × ko/en = 20행.
    # 슈퍼어드민이 admin-web /faq 에서 수정/추가/비활성화 가능.
    # (idempotent — 같은 kind+lang+question 이 이미 있으면 skip)
    _bootstrap_faqs(db)

    # ── 매장 업종 카테고리 초기 시드 ────────────────────────────────────
    # 국세청 100대 생활업종 기준. 사장 가입 시 자유 입력 금지 (파편화 방지).
    # 슈퍼어드민이 admin-web /categories 에서 추가/수정/비활성화 가능.
    _bootstrap_categories(db)

    db.commit()
    db.close()


_POLICY_KIND_TITLES = {
    # legacy 공용 — 신규 가입은 _user / _facility 분리본을 사용 (C-2-4a)
    'terms':            '서비스 이용약관',
    'privacy':          '개인정보 수집·이용 동의',
    'location':         '위치 정보 이용 동의',
    'age14':            '만 14세 이상 동의',
    'camera':           '카메라 접근 권한',
    'storage':          '저장공간 접근 권한',
    'push':             '푸시 알림 동의',
    'marketing':        '마케팅 정보 수신 동의',
    'third_party':      '제3자 정보 제공 동의',
    # C-2-4a — user / facility 별도 약관 (terms / privacy 만 분리, 나머지 7종은 공용)
    'terms_user':       '서비스 이용약관 (사용자)',
    'terms_facility':   '서비스 이용약관 (사장)',
    'privacy_user':     '개인정보 수집·이용 동의 (사용자)',
    'privacy_facility': '개인정보 수집·이용 동의 (사장)',
}

# P12 — 약관은 사용자 정책상 ko/en 두 언어만 유지.
# 디바이스 언어 한국어 → ko, 그 외 모두 → en (자동 fallback).
_POLICY_KIND_TITLES_EN = {
    'terms':            'Terms of Service',
    'privacy':          'Privacy Policy',
    'location':         'Location Information Consent',
    'age14':            'Age 14+ Consent',
    'camera':           'Camera Permission',
    'storage':          'Storage Permission',
    'push':             'Push Notification Consent',
    'marketing':        'Marketing Communication Consent',
    'third_party':      'Third-Party Information Sharing',
    # C-2-4a — user / facility 별도 약관
    'terms_user':       'Terms of Service (User)',
    'terms_facility':   'Terms of Service (Provider)',
    'privacy_user':     'Privacy Policy (User)',
    'privacy_facility': 'Privacy Policy (Provider)',
}


def _bootstrap_policies(db) -> None:
    """static/policies/<kind>.ko.md 를 v0.1 로 자동 등록 (idempotent).

    PR #45 fallback 은 정적 파일이지만, admin-web 정책 관리 / 푸터 링크 /
    가입 동의가 일관되게 동작하려면 DB 에 row 가 있어야 한다.
    이미 같은 (kind, lang='ko', version='0.1') 이 있으면 skip.
    """
    from datetime import datetime as _dt, timedelta as _td
    policies_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'static', 'policies'
    )
    if not os.path.isdir(policies_dir):
        return
    effective_at = (_dt.utcnow() - _td(minutes=1)).isoformat()
    inserted = 0
    for kind, title in _POLICY_KIND_TITLES.items():
        path = os.path.join(policies_dir, f'{kind}.ko.md')
        if not os.path.isfile(path):
            continue
        existing = db.execute(
            "SELECT id FROM policies WHERE kind=? AND lang='ko' AND version='0.1'",
            (kind,)
        ).fetchone()
        if existing:
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                body = f.read()
        except Exception:
            continue
        db.execute(
            """INSERT INTO policies
                 (kind, lang, version, title, body, change_log, effective_at)
               VALUES (?, 'ko', '0.1', ?, ?, '정적 파일에서 v0.1 자동 등록', ?)""",
            (kind, title, body, effective_at)
        )
        inserted += 1

        # P12 — 영어 v0.1 자동 시드. DeepL 키 있으면 실 번역, 없으면 stub.
        #       어드민이 admin-web 에서 본문 교체 가능.
        existing_en = db.execute(
            "SELECT id FROM policies WHERE kind=? AND lang='en' AND version='0.1'",
            (kind,)
        ).fetchone()
        if not existing_en:
            try:
                from services.translation_ai import translate as _tx
                en_body  = _tx(body, target_lang='en', source_lang='ko')
            except Exception:
                en_body = f'[en] {body}'  # 안전 fallback
            en_title = _POLICY_KIND_TITLES_EN.get(kind, title)
            db.execute(
                """INSERT INTO policies
                     (kind, lang, version, title, body, change_log, effective_at)
                   VALUES (?, 'en', '0.1', ?, ?, 'Auto-translated from ko v0.1', ?)""",
                (kind, en_title, en_body, effective_at)
            )

    if inserted:
        from models.log import logger as _lg
        _lg.info('[policies] Bootstrapped %d policy versions (v0.1 ko+en)', inserted)


# ──────────────────────────────────────────────────────────────────────────────
# C-2-3 — FAQ 초기 시드.
# 출시 직후 화면이 비어 보이지 않도록 사용자/사장 각 5건씩 ko/en 자동 등록.
# 운영자는 admin-web 의 FAQ 관리 화면에서 자유 수정/추가/비활성화.
# ──────────────────────────────────────────────────────────────────────────────
_FAQ_SEEDS = [
    # (kind, category, sort_order, ko_question, ko_answer, en_question, en_answer)
    ('user', 'account', 10,
     '회원가입은 어떻게 하나요?',
     '앱 첫 화면에서 "회원가입"을 누르고 이메일·비밀번호·필수 약관 동의를 진행하면 됩니다. 만 14세 미만은 보호자 동의가 필요합니다.',
     'How do I sign up?',
     'Tap "Sign up" on the first screen, then enter your email, password, and accept the required terms. Users under 14 need a guardian\'s consent.'),
    ('user', 'account', 20,
     '비밀번호를 잊어버렸어요.',
     '로그인 화면의 "비밀번호 찾기"에서 가입한 이메일을 입력하면 재설정 링크를 보내드립니다.',
     'I forgot my password.',
     'Tap "Forgot password" on the login screen and enter your registered email. We\'ll send you a reset link.'),
    ('user', 'feature', 30,
     '스탬프는 어떻게 적립되나요?',
     '매장에 방문해 비콘이 감지되거나 매장에서 발급한 QR을 직원이 스캔하면 적립됩니다. 매장별 정책(1일 1회 등)이 다를 수 있습니다.',
     'How do I earn stamps?',
     'Stamps are credited when our beacon detects your visit or a staff member scans the store\'s QR code. Each store may have its own rules (e.g. once a day).'),
    ('user', 'feature', 40,
     '쿠폰은 어떻게 사용하나요?',
     '"쿠폰" 메뉴에서 사용할 쿠폰을 선택해 QR을 표시한 뒤 매장 직원에게 보여주면 됩니다. 만료일이 지나면 사용할 수 없습니다.',
     'How do I use a coupon?',
     'Open the "Coupons" menu, select the coupon you want to use, and show the QR code to a staff member. Coupons cannot be used after expiry.'),
    ('user', 'connectivity', 50,
     '매장 WiFi 자동 연결이 안 됩니다.',
     '위치/블루투스 권한이 켜져 있는지 확인해 주세요. iOS는 설치된 프로파일을 사용하므로 처음 1회 설치 동의가 필요합니다. 그래도 안 되면 매장 직원에게 문의해 주세요.',
     'WiFi auto-connect doesn\'t work.',
     'Please make sure Location and Bluetooth permissions are enabled. iOS requires a one-time profile installation. If it still doesn\'t work, please contact the store.'),

    ('provider', 'onboarding', 10,
     '매장 가입 승인은 얼마나 걸리나요?',
     '사업자등록증 검증 후 보통 영업일 기준 1~2일 안에 승인 처리됩니다. 추가 자료가 필요한 경우 가입 이메일로 안내드립니다.',
     'How long does store approval take?',
     'After verifying your business registration, approval usually completes within 1–2 business days. We\'ll email you if additional documents are required.'),
    ('provider', 'beacon', 20,
     '비콘은 어떻게 등록하나요?',
     'PathWave에서 발송한 비콘을 받으신 뒤, 운영자 페이지의 "비콘"에서 동봉된 비콘 ID를 입력하면 매장에 활성화됩니다.',
     'How do I register beacons?',
     'After receiving the beacons from PathWave, open "Beacons" in the operator console and enter the beacon ID printed on the unit to activate it for your store.'),
    ('provider', 'wifi', 30,
     'WiFi 비밀번호는 안전하게 저장되나요?',
     '네. 모든 WiFi 비밀번호는 서버에 저장되기 전 AES-256-GCM으로 암호화되며, 운영자 본인 외에는 평문으로 노출되지 않습니다.',
     'Is my WiFi password stored securely?',
     'Yes. Every WiFi password is encrypted with AES-256-GCM before being stored, and is never shown in plain text to anyone except you.'),
    ('provider', 'billing', 40,
     '구독 결제는 언제 정산되나요?',
     '매월 정해진 결제일에 자동 결제가 진행됩니다. 결제 실패 시 3일 유예 후 매장 노출이 제한됩니다. 영수증은 "결제" 메뉴에서 확인할 수 있습니다.',
     'When is the subscription billed?',
     'Subscriptions auto-renew on the same date each month. If a payment fails, your store will be hidden after a 3-day grace period. Receipts are available in the "Billing" menu.'),
    ('provider', 'staff', 50,
     '직원을 어떻게 초대하나요?',
     '"직원" 메뉴에서 초대 코드를 발급해 직원에게 전달하세요. 직원은 코드로 가입하면 QR 스캔·채팅 응대 등 일부 기능을 사용할 수 있습니다.',
     'How do I invite staff?',
     'Open "Staff" and issue an invitation code, then send it to the staff member. Once they sign up using the code, they can scan QR codes and respond to chats.'),
]


def _bootstrap_faqs(db) -> None:
    """초기 FAQ 자동 등록 (idempotent — 같은 kind+lang+question 이 이미 있으면 skip)."""
    inserted = 0
    for kind, category, sort_order, q_ko, a_ko, q_en, a_en in _FAQ_SEEDS:
        for lang, q, a in (('ko', q_ko, a_ko), ('en', q_en, a_en)):
            existing = db.execute(
                "SELECT id FROM faqs WHERE kind=? AND lang=? AND question=?",
                (kind, lang, q),
            ).fetchone()
            if existing:
                continue
            db.execute(
                """INSERT INTO faqs (kind, category, question, answer, lang, sort_order, active)
                   VALUES (?,?,?,?,?,?,1)""",
                (kind, category, q, a, lang, sort_order),
            )
            inserted += 1
    if inserted:
        from models.log import logger as _lg
        _lg.info('[faqs] Bootstrapped %d FAQ entries (user/provider × ko/en)', inserted)


# ──────────────────────────────────────────────────────────────────────────────
# 매장 업종 카테고리 초기 시드 — 국세청 100대 생활업종 기반.
# (사장 가입 시 자유 입력 금지 → DB 파편화 방지. 슈퍼어드민이 admin-web 에서
#  추가/수정/비활성화 가능.)
# ──────────────────────────────────────────────────────────────────────────────
_CATEGORY_SEEDS = [
    ('음식', [
        '한식전문점', '중식전문점', '일식전문점', '서양식전문점', '기타외국식전문점',
        '분식점', '패스트푸드점', '치킨전문점', '제과점', '아이스크림가게',
        '커피음료점', '호프/주점', '구내식당', '도시락전문점', '출장뷔페',
    ]),
    ('소매', [
        '슈퍼마켓', '편의점', '식료품가게', '정육점', '과일채소가게',
        '생선가게', '건어물가게', '반찬가게', '건강보조식품점', '옷가게',
        '신발가게', '가방가게', '화장품가게', '안경점', '시계귀금속점',
        '서점', '문구점', '철물점', '가구점', '가전제품가게',
        '컴퓨터판매점', '핸드폰가게', '꽃집', '애완동물샵', '장난감가게',
        '악기가게', '자전거가게', '스포츠용품점', '캠핑용품점', '주류전문점',
    ]),
    ('서비스/숙박', [
        '미용실', '이발소', '피부관리업', '네일샵', '목욕탕/사우나',
        '마사지샵', '세탁소', '사진관', '부동산중개업', '여행사',
        '결혼상담소', '예식장', '장례식장', '인테리어/설비', '청소/방역업',
        '이삿짐센터', '카센터', '세차장', '주유소/충전소', '렌터카',
        '여관/모텔', '호텔/리조트', '펜션/민박', '게스트하우스',
    ]),
    ('오락/스포츠', [
        '노래방', 'PC방', '당구장', '골프연습장', '스크린골프장',
        '볼링장', '헬스클럽', '요가/필라테스', '수영장', '탁구장',
        '키즈카페', '보드게임카페', '방탈출카페', '만화방', '영화관/공연장',
    ]),
    ('교육', [
        '입시학원', '외국어학원', '예체능학원', '기술/직업학원', '자동차운전학원',
        '교습소/공부방', '독서실', '스터디카페', '어린이집/유치원', '요리/제빵학원',
    ]),
    ('의료/보건', [
        '종합병원', '내과/소아과', '치과', '한의원', '안과',
        '이비인후과', '피부과/비뇨기과', '산부인과', '정형외과/신경외과', '정신건강의학과',
        '기타의원', '약국', '동물병원', '산후조리원', '요양원/실버타운',
    ]),
    ('기타', [
        '공유오피스', '변호사/법무사', '회계사/세무사', '건축사/설계사', '기타전문직',
    ]),
]


def _bootstrap_categories(db) -> None:
    """초기 카테고리 자동 등록 (idempotent — 같은 name 이 이미 있으면 skip)."""
    inserted = 0
    sort_base = 0
    for group_name, names in _CATEGORY_SEEDS:
        for name in names:
            sort_base += 10
            existing = db.execute(
                "SELECT id FROM store_categories WHERE name=?", (name,)
            ).fetchone()
            if existing:
                continue
            db.execute(
                """INSERT INTO store_categories (name, group_name, sort_order, active)
                   VALUES (?, ?, ?, 1)""",
                (name, group_name, sort_base),
            )
            inserted += 1
    if inserted:
        from models.log import logger as _lg
        _lg.info('[categories] Bootstrapped %d store categories (국세청 100대 생활업종)',
                 inserted)


def _bootstrap_super_admin(db) -> None:
    """ENV로 첫 super admin 계정 자동 생성 (0명일 때만)."""
    email    = os.environ.get('BOOTSTRAP_SUPER_ADMIN_EMAIL', '').strip().lower()
    password = os.environ.get('BOOTSTRAP_SUPER_ADMIN_PASSWORD', '')
    if not email or not password:
        return
    existing = db.execute(
        "SELECT COUNT(*) AS n FROM super_admin_accounts"
    ).fetchone()['n']
    if existing > 0:
        return
    import bcrypt as _bcrypt
    hashed = _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()
    db.execute(
        """INSERT INTO super_admin_accounts (email, password, role, name)
           VALUES (?,?,'super','Bootstrap Admin')""",
        (email, hashed)
    )
    from models.log import logger as _lg
    _lg.info('[super-admin] Bootstrapped initial super admin: %s', email)


def _add_column_if_missing(db, table: str, column: str, ddl: str) -> None:
    """``column``이 ``table``에 이미 있으면 no-op, 없으면 ALTER ADD COLUMN.

    SQLite/PostgreSQL 모두 호환 (PR #51).
    """
    if use_postgres():
        # PostgreSQL: information_schema.columns
        row = db.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name=? AND column_name=?",
            (table, column),
        ).fetchone()
        if row is None:
            db.execute(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {ddl}')
    else:
        # SQLite: PRAGMA table_info
        existing = {r['name'] for r in db.execute(f'PRAGMA table_info({table})').fetchall()}
        if column not in existing:
            db.execute(f'ALTER TABLE {table} ADD COLUMN {ddl}')
