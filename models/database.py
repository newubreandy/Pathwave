import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'pathwave.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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
            uuid        TEXT    UNIQUE NOT NULL,       -- 암호화된 UUID
            facility_id INTEGER,
            status      TEXT    DEFAULT 'inactive',   -- active / inactive / inventory
            battery_pct INTEGER DEFAULT 100,
            firmware_ver TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS wifi_profiles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER NOT NULL,
            ssid        TEXT    NOT NULL,
            password    TEXT    NOT NULL,              -- AES 암호화 저장
            active      INTEGER DEFAULT 1,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

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
            read_at       TEXT,
            created_at    TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (room_id) REFERENCES chat_rooms(id)
        );
        CREATE INDEX IF NOT EXISTS idx_chat_messages_room ON chat_messages(room_id);

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

    # ── Super Admin 부트스트랩 ──────────────────────────────────────────────
    # ENV BOOTSTRAP_SUPER_ADMIN_EMAIL/PASSWORD가 설정되고 super admin이 0명이면
    # 최초 1명을 자동 생성. 이후 ENV 변경/삭제해도 무시됨 (idempotent).
    _bootstrap_super_admin(db)

    db.commit()
    db.close()


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
    print(f'[super-admin] Bootstrapped initial super admin: {email}')


def _add_column_if_missing(db, table: str, column: str, ddl: str) -> None:
    """``column``이 ``table``에 이미 있으면 no-op, 없으면 ALTER ADD COLUMN.

    SQLite는 ``ALTER TABLE ... ADD COLUMN``이 idempotent하지 않으므로
    ``PRAGMA table_info``로 먼저 확인한다.
    """
    existing = {r['name'] for r in db.execute(f'PRAGMA table_info({table})').fetchall()}
    if column not in existing:
        db.execute(f'ALTER TABLE {table} ADD COLUMN {ddl}')
