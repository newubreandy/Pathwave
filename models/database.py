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
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            business_no     TEXT    UNIQUE NOT NULL,   -- 사업자등록번호
            company_name    TEXT    NOT NULL,
            email           TEXT    UNIQUE NOT NULL,
            password        TEXT    NOT NULL,
            phone           TEXT,
            manager_name    TEXT,
            manager_phone   TEXT,
            manager_email   TEXT,
            verified        INTEGER DEFAULT 0,
            created_at      TEXT    DEFAULT (datetime('now'))
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

    db.commit()
    db.close()


def _add_column_if_missing(db, table: str, column: str, ddl: str) -> None:
    """``column``이 ``table``에 이미 있으면 no-op, 없으면 ALTER ADD COLUMN.

    SQLite는 ``ALTER TABLE ... ADD COLUMN``이 idempotent하지 않으므로
    ``PRAGMA table_info``로 먼저 확인한다.
    """
    existing = {r['name'] for r in db.execute(f'PRAGMA table_info({table})').fetchall()}
    if column not in existing:
        db.execute(f'ALTER TABLE {table} ADD COLUMN {ddl}')
