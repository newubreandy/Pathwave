"""7종 동의 마이크로항목 영문 시드 (2026-05-29).

기존 ko 본문(version 0.1, 모두 시드됨)을 대상으로 동일 version 의 en 버전 추가.
대상 kind: age14 / camera / location / marketing / push / storage / third_party

멱등: (kind, lang='en', version='0.1') 이미 존재하면 skip.
구조: ko 본문의 markdown(헤더/불릿/blockquote) 형태를 그대로 유지해 PolicyView
렌더 일관성 보장.

사용
----
- 로컬 dev: ./venv/bin/python scripts/seed_consent_micro_en.py
- 운영: 운영 DB 에 동일 스크립트 실행 (1회).
"""
from __future__ import annotations

import os
import sqlite3

VERSION      = '0.1'
EFFECTIVE_AT = '2026-05-29 00:00:00'
# env PATHWAVE_DB 로 오버라이드 가능 (운영 / 다른 환경 DB 지정용).
DB_PATH      = os.environ.get('PATHWAVE_DB') or os.path.join(
    os.path.dirname(__file__), '..', 'pathwave.db'
)


# ──────────────────────────────────────────────────────────────────────────────
# 본문 — 각 ko 본문의 markdown 구조를 그대로 미러링 (번역만).
# ──────────────────────────────────────────────────────────────────────────────
POLICIES_EN: dict[str, dict] = {

    'age14': {
        'title': 'Age 14+ Confirmation',
        'body': """# Age 14+ Confirmation

I confirm that I am 14 years of age or older to use the PathWave service (operated by Trigger Soft).

Users under 14 cannot register. Certain venues (accommodations, age-restricted entertainment, etc.) are accessible only via an invitation issued by a guardian aged 19 or older; in such cases the guardian assumes legal responsibility for the minor's use.

For details, please review the Terms of Service and the Personal Information Collection & Use Consent.
""",
    },

    'camera': {
        'title': 'Camera Access',
        'body': """# Camera Access Consent (Optional)

PathWave (operated by Trigger Soft) uses the camera for the following features.

- Registering a profile image (taking a photo)
- Scanning in-store QR codes (e.g., coupon redemption)
- Attaching store photos (1:1 chat)

## Right to Decline

This consent is optional. Declining will limit some camera-based features but will not affect use of other core functionality.

You can change this at any time in OS Settings > App Permissions.
""",
    },

    'location': {
        'title': 'Location Information Use Consent',
        'body': """# Location Information Use Consent

> This consent is prepared in accordance with the Act on the Protection and Use of Location Information. (Draft)

## 1. Items Collected

Trigger Soft (hereinafter "the Company") collects the following.
- Location data at the moment of BLE beacon detection (at the city/district level or precise coordinates)
- GPS coordinates (used for distance sorting in store search; may be declined manually)

## 2. Purpose of Use

- Beacon-based automatic store recognition (Wi-Fi auto-connect, stamp earnings)
- Distance sort and radius filters in store search
- Fraud prevention for stamps and coupons

## 3. Retention Period

- Location data is destroyed immediately after the service is delivered.
- However, anonymized statistics may be retained for up to one year for dispute response and service-quality analysis.

## 4. Third-Party Provision

The Company does not provide member location data to third parties.

## 5. Member Rights

You may withdraw consent at any time via OS settings or in the in-app settings. Withdrawal may, however, limit beacon-based automatic services.
""",
    },

    'marketing': {
        'title': 'Marketing Communications Consent',
        'body': """# Marketing Communications Consent (Optional)

PathWave (operated by Trigger Soft) provides information about new services, events, and store discounts through the following channels.

## Channels

- In-app push notifications
- Email
- SMS / KakaoTalk AlimTalk

## Right to Decline

This consent is optional and declining does not restrict use of the service's core features.

You may withdraw at any time via in-app [Settings > Notifications] or via the unsubscribe link in email/SMS messages.
""",
    },

    'push': {
        'title': 'Push Notification Consent',
        'body': """# Push Notification Consent (Optional)

PathWave (operated by Trigger Soft) sends push notifications for the following.

- Stamp earnings and coupon issuance
- New chat messages with stores
- System notices and maintenance announcements
- (With marketing consent) Event and discount information

## Right to Decline

This consent is optional. Declining does not restrict service use, but you will not receive real-time alerts for stamps, coupons, etc.

You can change this at any time via OS settings or in-app [Settings > Notifications].
""",
    },

    'storage': {
        'title': 'Storage Access Consent',
        'body': """# Storage Access Consent (Optional)

PathWave (operated by Trigger Soft) accesses device storage for the following features.

- Selecting a profile image from the gallery
- Attaching store photos in chat (from the gallery)
- Saving coupon / receipt images

## Right to Decline

This consent is optional. Declining will limit some gallery-based photo registration / sharing features but will not affect other core functionality.

You can change this at any time in OS Settings > App Permissions.
""",
    },

    'third_party': {
        'title': 'Third-Party Information Provision Consent',
        'body': """# Third-Party Information Provision Consent (Optional)

> This consent applies to store-owner (merchant) members. Regular users provide a separate consent at the time of payment.

Trigger Soft (hereinafter "the Company") provides the following to third parties for payment and settlement processing.

## Recipient

- Payment gateway (PG): Toss Payments (Toss Payments Co., Ltd.) or another payment-service provider designated by the Company

## Items Provided

- Business name, business registration number
- Contact name and phone number
- Payment amount, payment time, payment method

## Purpose of Use

- Credit card / bank transfer payment processing
- Settlement remittance
- Fraud prevention

## Retention & Use Period

- Retained for 5 years after payment completion (Act on Consumer Protection in Electronic Commerce, etc.)

## Right to Decline

Declining this consent will restrict use of payment services.
""",
    },
}


def main() -> None:
    if not os.path.exists(DB_PATH):
        raise SystemExit(f'DB not found: {DB_PATH}')
    print(f'DB: {DB_PATH}')
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    inserted = 0
    skipped  = 0

    for kind, payload in POLICIES_EN.items():
        existing = cur.execute(
            """SELECT id FROM policies
               WHERE kind=? AND lang='en' AND version=?""",
            (kind, VERSION),
        ).fetchone()
        if existing:
            print(f'  skip  {kind}/en/{VERSION} (id={existing[0]})')
            skipped += 1
            continue
        cur.execute(
            """INSERT INTO policies
               (kind, lang, version, title, body, change_log, effective_at,
                created_by_admin_id, created_at, email_notified)
               VALUES (?, 'en', ?, ?, ?, ?, ?, NULL, datetime('now'), 0)""",
            (kind, VERSION, payload['title'], payload['body'],
             'Initial en translation seed (2026-05-29)', EFFECTIVE_AT),
        )
        print(f'  ✅ INSERT {kind}/en/{VERSION} (rowid={cur.lastrowid})')
        inserted += 1

    con.commit()

    print(f'\n=== 결과 ===')
    print(f'  INSERT {inserted}, skip {skipped}')

    print('\n=== 시드 후 동의 마이크로항목 7종 lang 커버리지 ===')
    for kind in POLICIES_EN:
        rows = cur.execute(
            "SELECT lang, version, title FROM policies WHERE kind=? ORDER BY lang",
            (kind,),
        ).fetchall()
        langs = ', '.join(f'{r[0]}({r[1]})' for r in rows)
        print(f'  {kind:15s}: {langs}')

    con.close()


if __name__ == '__main__':
    main()
