"""PathWave dev 데모 시드 v2 (2026-06-09) — 실 컬럼명 정합.

대상:
- preview@dev.local — dev-preview-login 사용자
- dev-provider@pathwave.kr / demo-cafe / demo-resto / demo-hotel — provider 콘솔
- admin@pathwave.kr — 슈퍼어드민

사용:
    cd /Users/m5pro16/Desktop/pathwave
    venv/bin/python scripts/seed_dev_full_demo.py
"""
import secrets
import sqlite3
import uuid as _uuid
from datetime import datetime, timedelta

import bcrypt

DB = 'pathwave.db'
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()


def get_or_create_user(email):
    row = cur.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if row:
        return row['id']
    pw = bcrypt.hashpw(b'DemoPass2026!', bcrypt.gensalt()).decode()
    cur.execute(
        "INSERT INTO users (email, password, provider, language, verified, age_group) "
        "VALUES (?, ?, 'email', 'ko', 1, 'adult_19_plus')", (email, pw))
    return cur.lastrowid


def get_or_create_provider(email, biz, company):
    row = cur.execute("SELECT id FROM facility_accounts WHERE email=?", (email,)).fetchone()
    if row:
        return row['id']
    pw = bcrypt.hashpw(b'DemoProvider2026!', bcrypt.gensalt()).decode()
    cur.execute(
        "INSERT INTO facility_accounts (business_no, company_name, email, password, "
        "phone, manager_name, verified, status) "
        "VALUES (?, ?, ?, ?, '02-1234-5678', '담당자', 1, 'verified')",
        (biz, company, email, pw))
    return cur.lastrowid


user_id = get_or_create_user('preview@dev.local')
print(f'  preview user id = {user_id}')

provider_ids = []
for email, biz, name in [
    ('demo-cafe@pathwave.kr',  '210-86-12345', '시청 카페 (데모)'),
    ('demo-resto@pathwave.kr', '220-87-54321', '광장 식당 (데모)'),
    ('demo-hotel@pathwave.kr', '230-88-99999', '명동 호텔 (데모)'),
]:
    pid = get_or_create_provider(email, biz, name)
    provider_ids.append(pid)
    print(f'  provider {pid} {name}')


# ── 업종 카테고리 (store_categories) ──
for name, group in [
    ('카페', 'food'), ('음식점', 'food'), ('숙박', 'hospitality'),
    ('편의점', 'retail'), ('주점', 'food'),
]:
    cur.execute(
        "INSERT OR IGNORE INTO store_categories (name, group_name, active, sort_order) "
        "VALUES (?, ?, 1, 0)", (name, group))
print('  카테고리 5')


# ── 매장 ──
# (owner_id, name, address, phone, hours, lat, lng, desc, image)
facility_data = [
    (provider_ids[0], '시청 카페 (데모)',  '서울 중구 세종대로 110', '02-100-1001',
     '평일 08:00~22:00', 37.5665, 126.9780, '데모용 카페 — 스탬프·쿠폰 테스트',
     'https://picsum.photos/seed/pwcafe1/800/450'),
    (provider_ids[0], '광화문 분점 (데모)', '서울 종로구 세종로 1', '02-100-1002',
     '평일 09:00~21:00', 37.5759, 126.9769, '광화문 인근 분점',
     'https://picsum.photos/seed/pwcafe2/800/450'),
    (provider_ids[1], '광장 식당 (데모)',  '서울 중구 을지로 1가', '02-200-2001',
     '평일 11:00~22:00', 37.5666, 126.9821, '점심·저녁 한식',
     'https://picsum.photos/seed/pwresto/800/450'),
    (provider_ids[2], '명동 호텔 (데모)',  '서울 중구 명동길 26', '02-300-3001',
     '24시간', 37.5635, 126.9856, 'WiFi 자동연결 검증 매장',
     'https://picsum.photos/seed/pwhotel/800/450'),
    (provider_ids[1], '을지로 펍 (데모)',  '서울 중구 을지로 100', '02-400-4001',
     '평일 18:00~02:00', 37.5665, 126.9889, '저녁 운영',
     'https://picsum.photos/seed/pwpub/800/450'),
]
facility_ids = []
categories_of = []
for fd in facility_data:
    oid, name = fd[0], fd[1]
    row = cur.execute(
        "SELECT id FROM facilities WHERE owner_id=? AND name=?", (oid, name)
    ).fetchone()
    if row:
        facility_ids.append(row['id'])
        continue
    cur.execute(
        "INSERT INTO facilities (owner_id, name, address, phone, business_hours, "
        "latitude, longitude, description, image_url, active) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)", fd)
    facility_ids.append(cur.lastrowid)
print(f'  매장 {len(facility_ids)}개')

# ── 매장 추가 이미지 (facility_images 갤러리) ──
for fid in facility_ids:
    has = cur.execute(
        "SELECT id FROM facility_images WHERE facility_id=?", (fid,)).fetchone()
    if has:
        continue
    for idx in range(2):
        primary = 1 if idx == 0 else 0
        cur.execute(
            "INSERT INTO facility_images (facility_id, image_url, is_primary, sort_order) "
            "VALUES (?, ?, ?, ?)",
            (fid, f'https://picsum.photos/seed/pwfac{fid}_{idx}/800/450', primary, idx))
print('  매장 이미지')


# ── 비콘 ──
for i, fid in enumerate(facility_ids, 1):
    has = cur.execute("SELECT id FROM beacons WHERE facility_id=?", (fid,)).fetchone()
    if has:
        continue
    cur.execute(
        "INSERT INTO beacons (uuid, major, minor, facility_id, status, battery_pct, "
        "firmware_ver, serial_no) "
        "VALUES (?, ?, ?, ?, 'active', 85, '1.0.0', ?)",
        (str(_uuid.uuid4()), 100, i, fid, f'PW-BC-{i:04d}'))
print('  비콘 5개')


# ── WiFi 프로파일 ──
for i, fid in enumerate(facility_ids, 1):
    has = cur.execute("SELECT id FROM wifi_profiles WHERE facility_id=?", (fid,)).fetchone()
    if has:
        continue
    cur.execute(
        "INSERT INTO wifi_profiles (facility_id, ssid, password, active, credential_mode) "
        "VALUES (?, ?, ?, 1, 'static')",
        (fid, f'PathWave_Demo_{i}', 'demo-encrypted-pw'))
print('  WiFi 프로파일')


# ── 메뉴 ──
menu_seed = {
    0: [('아메리카노', 4500), ('카페라떼', 5000), ('카푸치노', 5500), ('치즈케이크', 6500)],
    1: [('아메리카노', 4500), ('바닐라라떼', 5500), ('스콘', 4000)],
    2: [('비빔밥', 9000), ('김치찌개', 8500), ('된장찌개', 8500), ('제육볶음', 10000)],
    3: [('스탠다드룸', 120000), ('디럭스룸', 180000), ('스위트', 280000)],
    4: [('생맥주', 6000), ('소주', 5000), ('치킨', 22000), ('감자튀김', 8000)],
}
for idx, fid in enumerate(facility_ids):
    has = cur.execute(
        "SELECT id FROM facility_menu_items WHERE facility_id=? LIMIT 1", (fid,)).fetchone()
    if has:
        continue
    for sort, (n, p) in enumerate(menu_seed.get(idx, [])):
        cur.execute(
            "INSERT INTO facility_menu_items (facility_id, language, name, price, source, sort_order, active) "
            "VALUES (?, 'ko', ?, ?, 'manual', ?, 1)",
            (fid, n, p, sort))
print('  메뉴 시드')


# ── 즐겨찾기 ──
for fid in facility_ids[:3]:
    cur.execute(
        "INSERT OR IGNORE INTO user_favorites (user_id, facility_id) VALUES (?, ?)",
        (user_id, fid))
print('  즐겨찾기 3개')


# ── 스탬프 정책 + 스탬프 ──
for fid in facility_ids[:3]:
    has = cur.execute(
        "SELECT id FROM stamp_policies WHERE facility_id=?", (fid,)).fetchone()
    if has:
        continue
    cur.execute(
        "INSERT INTO stamp_policies (facility_id, reward_threshold, reward_description, active, "
        "reward_coupon_title, reward_coupon_benefit, reward_coupon_validity_days) "
        "VALUES (?, 10, '음료 1잔 무료 쿠폰', 1, '무료 음료', '아메리카노 1잔 무료', 30)",
        (fid,))

for fid in facility_ids[:3]:
    existing = cur.execute(
        "SELECT COUNT(*) c FROM stamps WHERE user_id=? AND facility_id=?",
        (user_id, fid)).fetchone()
    if existing['c'] >= 2:
        continue
    for i in range(3):
        cur.execute(
            "INSERT INTO stamps (user_id, facility_id, amount, granted_by_account_id, "
            "granted_by_actor_role, granted_by_actor_id, created_at) "
            "VALUES (?, ?, 1, ?, 'owner', ?, datetime('now', ?))",
            (user_id, fid, provider_ids[0], provider_ids[0], f'-{i+1} days'))
print('  스탬프 9개')


# ── 쿠폰 ──
expired = (datetime.utcnow() - timedelta(days=2)).isoformat()
active  = (datetime.utcnow() + timedelta(days=14)).isoformat()
coupon_seed = [
    (0, '음료 1잔 무료',     '아메리카노 1잔 무료',  active,  0),
    (0, '20% 할인',            '전 메뉴 20% 할인',     active,  0),
    (1, '디저트 1개 증정',     '치즈케이크 1개 증정',  active,  1),  # 사용완료
    (2, '저녁 식사 10%',      '저녁 메뉴 10% 할인',   expired, 0),  # 만료
]
for fidx, title, benefit, exp, used in coupon_seed:
    fid = facility_ids[fidx]
    has = cur.execute(
        "SELECT id FROM coupons WHERE user_id=? AND facility_id=? AND title=?",
        (user_id, fid, title)).fetchone()
    if has:
        continue
    cur.execute(
        "INSERT INTO coupons (user_id, facility_id, title, benefit, expires_at, used, "
        "issued_by_actor_role, issued_by_actor_id, source) "
        "VALUES (?, ?, ?, ?, ?, ?, 'owner', ?, 'manual')",
        (user_id, fid, title, benefit, exp, used, provider_ids[0]))
    if used:
        cur.execute(
            "UPDATE coupons SET used_at=datetime('now','-1 day'), used_by_actor_role='owner' "
            "WHERE id=?", (cur.lastrowid,))
print('  쿠폰 4개 (활성2 / 사용1 / 만료1)')


# ── 채팅방 + 메시지 ──
for fid in facility_ids[:2]:
    row = cur.execute(
        "SELECT id FROM chat_rooms WHERE user_id=? AND facility_id=?",
        (user_id, fid)).fetchone()
    if row:
        room_id = row['id']
    else:
        cur.execute(
            "INSERT INTO chat_rooms (user_id, facility_id, last_message_at) "
            "VALUES (?, ?, datetime('now'))", (user_id, fid))
        room_id = cur.lastrowid
    if cur.execute("SELECT COUNT(*) c FROM chat_messages WHERE room_id=?",
                   (room_id,)).fetchone()['c'] > 0:
        continue
    msgs = [
        ('facility', '안녕하세요! 매장에 오신 것을 환영합니다.'),
        ('user',     'WiFi 비밀번호 알려주세요'),
        ('facility', '자동연결되니 비밀번호 불필요해요 :)'),
        ('user',     '감사합니다!'),
    ]
    for s, body in msgs:
        cur.execute(
            "INSERT INTO chat_messages (room_id, sender_type, body, body_lang) "
            "VALUES (?, ?, ?, 'ko')", (room_id, s, body))
print('  채팅방 2 + 메시지 8')


# ── 알림 ──
for i, fid in enumerate(facility_ids[:3]):
    title = f'특별 이벤트 {i+1}'
    has = cur.execute(
        "SELECT id FROM notifications WHERE facility_id=? AND title=?",
        (fid, title)).fetchone()
    if has:
        continue
    cur.execute(
        "INSERT INTO notifications (facility_id, title, body, target_type, status, sent_at, "
        "issued_by_actor_role, issued_by_actor_id, body_lang) "
        "VALUES (?, ?, ?, 'all_visited', 'sent', datetime('now', ?), 'owner', ?, 'ko')",
        (fid, title, f'데모 알림 {i+1} — 회원 전용 혜택!', f'-{i} hours', provider_ids[0]))
    nid = cur.lastrowid
    cur.execute(
        "INSERT OR IGNORE INTO notification_recipients (notification_id, user_id) "
        "VALUES (?, ?)", (nid, user_id))
print('  알림 3개')


# ── 공지 ──
for title, body in [
    ('PathWave 베타 오픈 안내', '데모 환경 — 매장·쿠폰·스탬프 자유롭게 테스트하세요.'),
    ('점검 안내 (모의)',         '6월 15일 새벽 2시~3시 시스템 점검 예정입니다.'),
]:
    has = cur.execute("SELECT id FROM announcements WHERE title=?", (title,)).fetchone()
    if has:
        continue
    cur.execute(
        "INSERT INTO announcements (audience, title, body, pinned, push_sent, body_lang) "
        "VALUES ('all_users', ?, ?, 1, 0, 'ko')", (title, body))
print('  공지 2')


# ── FAQ ──
faq_seed = [
    ('account',     '회원가입은 어떻게 하나요?',  '로그인 화면 > "회원가입" 진행.'),
    ('account',     '비밀번호를 잊었어요',         '로그인 화면 > 비밀번호 찾기.'),
    ('connectivity','WiFi 가 자동 연결되지 않아요','Bluetooth 권한 + 비콘 거리 확인.'),
    ('connectivity','BLE 비콘이 감지되지 않아요', 'BT ON + 위치 권한 허용.'),
    ('쿠폰',         '쿠폰 사용 방법',              '내 쿠폰 > 사용 버튼 > 매장 점원에게 QR 표시.'),
    ('비콘 / WiFi',   '리조트 매장간 자동 전환',      'mobileconfig 설치된 매장 간 자동 핸드오프.'),
]
for cat, q, a in faq_seed:
    has = cur.execute("SELECT id FROM faqs WHERE question=?", (q,)).fetchone()
    if has:
        continue
    cur.execute(
        "INSERT INTO faqs (kind, category, question, answer, lang, sort_order, active) "
        "VALUES ('user', ?, ?, ?, 'ko', 0, 1)", (cat, q, a))
print(f'  FAQ {len(faq_seed)}개')


# ── 고객지원 티켓 ──
has = cur.execute(
    "SELECT id FROM support_tickets WHERE kind='user' AND user_id=?", (user_id,)
).fetchone()
if not has:
    cur.execute(
        "INSERT INTO support_tickets (kind, user_id, category, subject, body, status, priority) "
        "VALUES ('user', ?, '기타', '데모 문의', '안녕하세요. 데모 환경 문의 테스트입니다.', 'open', 'normal')",
        (user_id,))
    tid = cur.lastrowid
    cur.execute(
        "INSERT INTO support_messages (ticket_id, sender, body, body_lang) "
        "VALUES (?, 'user', '추가 메시지 — 답변 부탁드립니다.', 'ko')", (tid,))
print('  고객지원 티켓 1건')


# ── 신고 ──
fid = facility_ids[-1]
has = cur.execute(
    "SELECT id FROM abuse_reports WHERE reporter_kind='user' AND reporter_id=? AND target_id=?",
    (user_id, fid)).fetchone()
if not has:
    cur.execute(
        "INSERT INTO abuse_reports (target_kind, target_id, reporter_kind, reporter_id, "
        "reason_code, reason_detail, status) "
        "VALUES ('facility', ?, 'user', ?, 'spam', '데모 — 스팸 신고 테스트', 'open')",
        (fid, user_id))
print('  신고 1건')


# ── 비콘 서비스 신청 ──
pid = provider_ids[0]
has = cur.execute(
    "SELECT id FROM service_requests WHERE facility_account_id=? AND service_type='beacon'",
    (pid,)).fetchone()
if not has:
    cur.execute(
        "INSERT INTO service_requests (facility_account_id, facility_id, service_type, status, note) "
        "VALUES (?, ?, 'beacon', 'pending', '데모 신청 — 비콘 추가 요청')",
        (pid, facility_ids[0]))
print('  서비스 신청 1건')


# ── 푸시 토큰 ──
has = cur.execute("SELECT id FROM push_tokens WHERE user_id=?", (user_id,)).fetchone()
if not has:
    cur.execute(
        "INSERT INTO push_tokens (user_id, token, platform, language) "
        "VALUES (?, ?, 'apns', 'ko')",
        (user_id, f'demo-token-{secrets.token_hex(8)}'))
print('  푸시 토큰')


con.commit()
con.close()

print()
print('✅ 데모 시드 완료. 시뮬레이터/Chrome 새로고침 후 즉시 사용 가능.')
print()
print('📱 mobile (둘러보기):')
print('   - 즐겨찾기 3 / 스탬프 9 / 쿠폰 4 / 알림 3 / 채팅방 2 / 신고 1 / 문의 1')
print('🏪 provider-web:')
print('   - dev-provider@pathwave.kr / DevProvider2026! (기존)')
print('   - demo-cafe@pathwave.kr / DemoProvider2026!')
print('   - demo-resto@pathwave.kr / DemoProvider2026!')
print('   - demo-hotel@pathwave.kr / DemoProvider2026!')
print('🛡 admin-web:')
print('   - admin@pathwave.kr / DevAdmin2026!')
