"""Phase C — 매장 도메인 + 비콘 + 사용자/알림/쿠폰 mock seed.

idempotent:
  - 같은 email/serial_no 가 이미 있으면 skip 또는 update.

mocked entities
---------------
- 매장 5개 (스타벅스 강남 / 메가커피 홍대 / 파리바게뜨 신촌 / 호텔 인스 광화문(adult_only) / 노래방 종로(adult_only))
- 매장 사장(facility_account) 3개 (매장 1~3 소유, 매장 4~5 는 미할당 — 검색만 가능)
- 비콘 9개 FSC-BP108B 시뮬레이션:
    매장 1 → 비콘 3개 (minor 1/2/3, major=1)
    매장 2 → 비콘 3개 (minor 1/2/3, major=2)
    매장 3 → 비콘 3개 (minor 1/2/3, major=3)
- 일반 사용자 5명 (mock@pathwave.test, ...)
- 시스템 공지 3개 (audience=users / facilities / all)
- 쿠폰 8개 (각 사용자에게 2~3개 — manual / welcome / stamp_reward)

실행:
    source venv/bin/activate
    python scripts/seed_phase_c.py
"""
from __future__ import annotations

import os
import sys

# repo root 를 path 에 추가 (scripts/ 에서 직접 실행 시)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt

from models.database import get_db, init_db
from models.crypto import encrypt_secret

# ── PathWave 공통 UUID (FSC-BP108B 9개 실물 동일 UUID 권장이지만, dev DB 의
# UNIQUE(uuid) 제약 때문에 시드용은 distinct UUID 사용. 실 환경 도입 시 마이그레이션 별도.)
_BASE_UUID = '11111111-2222-3333-4444-{:012X}'

# ── 매장 mock ─────────────────────────────────────────────────────────────
FACILITIES = [
    dict(name='스타벅스 강남R점', address='서울 강남구 강남대로 396',
         phone='02-1234-5678', business_hours='07:00-22:00',
         latitude=37.4979, longitude=127.0276,
         description='강남역 인근. WiFi/스탬프/쿠폰 트리거 시연 매장.',
         image_url='https://picsum.photos/seed/store1/600/400',
         adult_only=0),
    dict(name='메가MGC커피 홍대점', address='서울 마포구 양화로 162',
         phone='02-2345-6789', business_hours='08:00-23:00',
         latitude=37.5563, longitude=126.9239,
         description='홍대입구역. 학생/관광객 BLE 트래픽 테스트용.',
         image_url='https://picsum.photos/seed/store2/600/400',
         adult_only=0),
    dict(name='파리바게뜨 신촌점', address='서울 서대문구 신촌로 90',
         phone='02-3456-7890', business_hours='07:00-22:00',
         latitude=37.5599, longitude=126.9425,
         description='신촌역 1번 출구. 스탬프 정책 자동 적립 ON.',
         image_url='https://picsum.photos/seed/store3/600/400',
         adult_only=0),
    dict(name='호텔 인스 광화문', address='서울 중구 세종대로 100',
         phone='02-4567-8901', business_hours='24시간',
         latitude=37.5704, longitude=126.9764,
         description='성인 전용 시설(adult_only=1) — 미성년자 차단 검증용.',
         image_url='https://picsum.photos/seed/store4/600/400',
         adult_only=1),
    dict(name='싱숭생숭 노래방 종로', address='서울 종로구 종로 19',
         phone='02-5678-9012', business_hours='15:00-04:00',
         latitude=37.5701, longitude=126.9826,
         description='성인 전용 시설(adult_only=1) — 검색은 되지만 핸드셰이크 차단.',
         image_url='https://picsum.photos/seed/store5/600/400',
         adult_only=1),
]

# 매장 사장(facility_account) — 매장 1~3 만 owner 할당. 4~5 는 owner_id=NULL.
OWNERS = [
    dict(business_no='123-45-67890', company_name='강남R 스타벅스',
         email='owner1@pathwave.test', manager_name='김강남'),
    dict(business_no='234-56-78901', company_name='홍대 메가커피',
         email='owner2@pathwave.test', manager_name='이홍대'),
    dict(business_no='345-67-89012', company_name='신촌 파리바게뜨',
         email='owner3@pathwave.test', manager_name='박신촌'),
]
_OWNER_PASSWORD = 'owner1234!'  # dev mock — 운영 절대 금지

# 일반 사용자 mock
USERS = [
    dict(email='alice@pathwave.test', birth_year=1995, language='ko'),
    dict(email='bob@pathwave.test',   birth_year=2010, language='ko'),  # minor
    dict(email='charlie@pathwave.test', birth_year=1988, language='en'),
    dict(email='diana@pathwave.test', birth_year=1992, language='ja'),
    dict(email='eve@pathwave.test',   birth_year=2008, language='ko'),  # minor
]
_USER_PASSWORD = 'user1234!'

# 시스템 공지
ANNOUNCEMENTS = [
    dict(title='[공지] PathWave 신규 매장 5곳 오픈',
         body='강남/홍대/신촌/광화문/종로 5개 매장에서 PathWave 서비스를 이용하실 수 있습니다.',
         audience='users', pinned=1),
    dict(title='[운영] 비콘 입고 안내',
         body='FSC-BP108B 비콘 9개가 인벤토리에 입고되었습니다. 사장님은 SN 으로 claim 가능합니다.',
         audience='facilities', pinned=0),
    dict(title='[전체] 서비스 안정성 패치 적용',
         body='Phase C 매장 도메인 + 비콘 Major/Minor 컬럼 배포 완료.',
         audience='all', pinned=0),
]


def _hashed(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def _ensure_user(db, email: str, password: str, language: str = 'ko',
                 birth_year: int | None = None) -> int:
    row = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if row:
        return row['id']
    age_group = None
    if birth_year:
        from datetime import datetime as _dt
        age = _dt.now().year - birth_year
        age_group = 'minor_14_18' if 14 <= age < 19 else 'adult_19_plus'
    cur = db.execute(
        """INSERT INTO users (email, password, provider, language, verified,
                              birth_year, age_group)
           VALUES (?,?,?,?,1,?,?)""",
        (email, _hashed(password), 'email', language, birth_year, age_group)
    )
    return cur.lastrowid


def _ensure_owner(db, ow: dict) -> int:
    row = db.execute(
        "SELECT id FROM facility_accounts WHERE email=?", (ow['email'],)
    ).fetchone()
    if row:
        return row['id']
    cur = db.execute(
        """INSERT INTO facility_accounts
             (business_no, company_name, email, password,
              manager_name, status, verified, approved_at)
           VALUES (?,?,?,?,?, 'verified', 1, datetime('now'))""",
        (ow['business_no'], ow['company_name'], ow['email'],
         _hashed(_OWNER_PASSWORD), ow['manager_name'])
    )
    return cur.lastrowid


def _ensure_facility(db, fac: dict, owner_id: int | None) -> int:
    row = db.execute(
        "SELECT id FROM facilities WHERE name=?", (fac['name'],)
    ).fetchone()
    if row:
        # 기존 행은 그대로 두고 owner/adult_only만 동기화 (idempotent).
        db.execute(
            "UPDATE facilities SET owner_id=?, adult_only=? WHERE id=?",
            (owner_id, fac['adult_only'], row['id'])
        )
        return row['id']
    cur = db.execute(
        """INSERT INTO facilities
             (name, address, phone, business_hours, latitude, longitude,
              description, image_url, owner_id, active, adult_only)
           VALUES (?,?,?,?,?,?,?,?,?,1,?)""",
        (fac['name'], fac['address'], fac['phone'], fac['business_hours'],
         fac['latitude'], fac['longitude'], fac['description'],
         fac['image_url'], owner_id, fac['adult_only'])
    )
    return cur.lastrowid


def _ensure_wifi(db, facility_id: int) -> None:
    if db.execute(
        "SELECT id FROM wifi_profiles WHERE facility_id=? AND active=1",
        (facility_id,)
    ).fetchone():
        return
    db.execute(
        """INSERT INTO wifi_profiles (facility_id, ssid, password, active)
           VALUES (?,?,?,1)""",
        (facility_id, f'PathWave-Mock-{facility_id}',
         encrypt_secret('mock-wifi-password'))
    )


def _ensure_beacon(db, sn: str, uuid: str, major: int | None,
                   minor: int | None, facility_id: int | None) -> int:
    row = db.execute("SELECT id FROM beacons WHERE serial_no=?", (sn,)).fetchone()
    status = 'active' if facility_id else 'inventory'
    if row:
        db.execute(
            """UPDATE beacons
               SET uuid=?, major=?, minor=?, facility_id=?, status=?
               WHERE id=?""",
            (uuid, major, minor, facility_id, status, row['id'])
        )
        return row['id']
    cur = db.execute(
        """INSERT INTO beacons
             (serial_no, uuid, major, minor, facility_id, status,
              battery_pct, firmware_ver)
           VALUES (?,?,?,?,?,?,100,'1.0.0')""",
        (sn, uuid, major, minor, facility_id, status)
    )
    return cur.lastrowid


def _ensure_announcement(db, a: dict) -> None:
    if db.execute(
        "SELECT id FROM announcements WHERE title=?", (a['title'],)
    ).fetchone():
        return
    db.execute(
        """INSERT INTO announcements (title, body, audience, pinned)
           VALUES (?,?,?,?)""",
        (a['title'], a['body'], a['audience'], a['pinned'])
    )


def _ensure_coupon(db, facility_id: int, user_id: int, title: str,
                   benefit: str, source: str) -> None:
    existing = db.execute(
        """SELECT 1 FROM coupons
           WHERE facility_id=? AND user_id=? AND title=? AND source=?""",
        (facility_id, user_id, title, source)
    ).fetchone()
    if existing:
        return
    db.execute(
        """INSERT INTO coupons
             (facility_id, user_id, title, benefit, source,
              issued_by_actor_role, issued_by_actor_id)
           VALUES (?,?,?,?,?,?,?)""",
        (facility_id, user_id, title, benefit, source, 'system', None)
    )


def seed() -> None:
    init_db()
    db = get_db()

    # owners
    owner_ids: list[int] = []
    for ow in OWNERS:
        owner_ids.append(_ensure_owner(db, ow))
    db.commit()

    # facilities
    facility_ids: list[int] = []
    for i, fac in enumerate(FACILITIES):
        owner = owner_ids[i] if i < len(owner_ids) else None
        fid = _ensure_facility(db, fac, owner)
        facility_ids.append(fid)
        _ensure_wifi(db, fid)
    db.commit()

    # 9 비콘 — 매장 1~3 에 각 3개씩 (major=facility_id, minor=1~3)
    beacon_idx = 0
    for f_index in range(3):
        fid = facility_ids[f_index]
        for minor in (1, 2, 3):
            beacon_idx += 1
            sn = f'BP108B-{beacon_idx:06d}'
            uuid = _BASE_UUID.format(beacon_idx)
            _ensure_beacon(db, sn, uuid, major=fid, minor=minor,
                           facility_id=fid)
    db.commit()

    # users
    user_ids: list[int] = []
    for u in USERS:
        user_ids.append(_ensure_user(db, u['email'], _USER_PASSWORD,
                                     language=u['language'],
                                     birth_year=u['birth_year']))
    db.commit()

    # announcements
    for a in ANNOUNCEMENTS:
        _ensure_announcement(db, a)
    db.commit()

    # 쿠폰 — 각 사용자에게 매장 1~3 의 manual 쿠폰 발급
    coupon_specs = [
        ('아메리카노 10% 할인', '주문 시 10% 할인', 'manual'),
        ('첫 방문 환영 음료', '음료 1잔 무료', 'welcome'),
        ('스탬프 보상 — 케이크 1조각', '케이크 1조각 무료', 'stamp_reward'),
    ]
    for u_idx, uid in enumerate(user_ids):
        for f_idx in range(min(3, len(facility_ids))):
            title, benefit, source = coupon_specs[
                (u_idx + f_idx) % len(coupon_specs)
            ]
            _ensure_coupon(db, facility_ids[f_idx], uid, title, benefit, source)
    db.commit()

    # 즐겨찾기 — alice/charlie 가 매장 1~2 를 즐겨찾기 (idempotent)
    fav_pairs = [
        (user_ids[0], facility_ids[0]),
        (user_ids[0], facility_ids[1]),
        (user_ids[2], facility_ids[0]),
        (user_ids[2], facility_ids[2]),
    ]
    for uid, fid in fav_pairs:
        try:
            db.execute(
                "INSERT INTO user_favorites (user_id, facility_id) VALUES (?,?)",
                (uid, fid)
            )
        except Exception:
            pass
    db.commit()

    # 요약 출력
    print('Phase C seed 완료:')
    print(f'  facilities      : {len(facility_ids)}  (ids={facility_ids})')
    print(f'  facility owners : {len(owner_ids)}     (emails=owner1~3@pathwave.test, pw={_OWNER_PASSWORD})')
    print(f'  users           : {len(user_ids)}      (emails=alice/bob/charlie/diana/eve@pathwave.test, pw={_USER_PASSWORD})')
    print(f'  beacons         : 9                  (BP108B-000001 ~ 000009, major=1~3, minor=1~3)')
    print(f'  announcements   : {len(ANNOUNCEMENTS)}')
    print(f'  coupons (mock)  : per user x 3 facilities')
    print(f'  favorites       : alice→[1,2], charlie→[1,3]')

    db.close()


if __name__ == '__main__':
    seed()
