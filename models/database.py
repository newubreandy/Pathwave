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
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            address     TEXT,
            latitude    REAL,
            longitude   REAL,
            description TEXT,
            image_url   TEXT,
            owner_id    INTEGER,                       -- facility_accounts.id
            active      INTEGER DEFAULT 1,
            created_at  TEXT    DEFAULT (datetime('now'))
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

        CREATE TABLE IF NOT EXISTS stamps (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER NOT NULL,
            user_id     INTEGER NOT NULL,
            amount      INTEGER DEFAULT 1,
            note        TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS coupons (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER NOT NULL,
            user_id     INTEGER NOT NULL,
            title       TEXT    NOT NULL,
            used        INTEGER DEFAULT 0,
            expires_at  TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

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
    db.commit()
    db.close()
