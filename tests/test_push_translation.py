"""P8c — 푸시 알림 본문 다국어 회귀 테스트.

P8b 의 push_to_users(title_lang/body_lang) 옵션을 announcement/notification
도메인에서 활성화한 것을 검증.

검증 범위
---------
1) 사장 알림 신청 lang_hint → notifications.body_lang 저장
2) 스케줄러 dispatch → 토큰별 lang 자동 번역 (en/ko/지원외/NULL)
3) 어드민 announcement lang_hint → announcements.body_lang 저장
4) announcement 즉시 push → 토큰별 자동 번역
5) 같은 (text, src, tgt) memoize (비용 절감)

stub translator + stub push provider — 외부 키 없이 검증.
"""
import os
import json
import sqlite3
import tempfile
from datetime import datetime, timedelta

import bcrypt

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB']          = tmp.name
os.environ['TRANSLATION_PROVIDER'] = 'stub'
os.environ['PUSH_PROVIDER']        = 'stub'
os.environ.pop('ANTHROPIC_API_KEY', None)

import models.database as _dbmod
def _patched_get_db():
    conn = sqlite3.connect(os.environ['PATHWAVE_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn
_dbmod.get_db  = _patched_get_db
_dbmod.DB_PATH = tmp.name

from app import app                                              # noqa: E402
from routes.auth import make_jwt                                 # noqa: E402
from models.push import StubPushProvider, _PUSH_TRANSLATION_MEMO # noqa: E402

c = app.test_client()


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


def _post(path, data=None, token=None):
    h = {'Content-Type': 'application/json'}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.post(path, data=json.dumps(data or {}), headers=h)
    return r.status_code, r.get_json()


# ── 0. 시드 ──────────────────────────────────────────────────────────────
print('\n[0] 시드 — 사용자 4명 (en/ko/지원외/NULL 토큰) + 매장 + quota')
db = _patched_get_db()
hashed = bcrypt.hashpw(b'pw', bcrypt.gensalt()).decode()
db.execute("INSERT INTO facility_accounts (business_no, company_name, email, password, verified, status) VALUES ('001','S','o@x.com',?,1,'verified')", (hashed,))
db.execute("INSERT INTO facilities (name, owner_id, active) VALUES ('Cafe', 1, 1)")
# 사용자 4명 + 매장 방문 이력
for i in range(1, 5):
    db.execute("INSERT INTO users (email, password) VALUES (?, ?)", (f'u{i}@x.com', hashed))
    db.execute("INSERT INTO user_wifi_logs (user_id, facility_id) VALUES (?, 1)", (i,))
# 4개 다른 토큰 (각 사용자별)
db.executemany(
    "INSERT INTO push_tokens (user_id, token, platform, language) VALUES (?,?,?,?)",
    [(1, 'tok-en',   'fcm', 'en'),
     (2, 'tok-ko',   'fcm', 'ko'),
     (3, 'tok-mn',   'fcm', 'mn'),     # 지원 외 → en fallback
     (4, 'tok-null', 'fcm', None)],    # NULL → en fallback
)
# super admin
db.execute("INSERT INTO super_admin_accounts (email, password, role) VALUES ('a@a', ?, 'super')", (hashed,))
# quota 100건
ends = (datetime.utcnow() + timedelta(days=30)).isoformat()
db.execute("INSERT INTO notification_quota (facility_account_id, quantity_purchased, expires_at) VALUES (1, 100, ?)", (ends,))
db.commit(); db.close()

facility_token = make_jwt(1, 'o@x.com', sub_type='facility')
admin_token    = make_jwt(1, 'a@a',     sub_type='super_admin')


# ── 1. 사장이 한국어 알림 신청 + lang_hint='ko' ──────────────────────────
print('\n[1] notification.create_notification — lang_hint 저장')
future_iso = (datetime.utcnow() + timedelta(hours=13)).isoformat()
status, j = _post('/api/facilities/1/notifications',
                  {'title': '쿠폰 도착',
                   'body':  '10% 할인 쿠폰이 도착했어요',
                   'target_type': 'all_visited',
                   'scheduled_at': future_iso,
                   'lang_hint': 'ko'},
                  token=facility_token)
_ok('201 응답',                  status == 201, j)
nid = j['notification']['id']
db = _patched_get_db()
row = db.execute('SELECT body_lang FROM notifications WHERE id=?', (nid,)).fetchone()
db.close()
_ok("body_lang == 'ko' 저장",     row['body_lang'] == 'ko', dict(row))


# ── 2. 어드민 즉시 dispatch → 4 토큰 자동 번역 ───────────────────────────
print('\n[2] 어드민 dispatch — 토큰별 자동 번역 (P8c 핵심)')
# 어드민 승인 + 즉시 발송 (status=pending 이라 approve 불필요)
StubPushProvider.sent_log.clear()
_PUSH_TRANSLATION_MEMO.clear()
status, j = _post(f'/api/admin/notifications/{nid}/dispatch', token=admin_token)
_ok('200 응답',                  status == 200, j)

log = {rec['token']: rec for rec in StubPushProvider.sent_log}
_ok('4 토큰 모두 발송',           len(log) == 4, list(log.keys()))
# en 토큰 → 영어 번역 ([en] prefix)
_ok("tok-en  title '[en] 쿠폰 도착'",
    log['tok-en']['title']  == '[en] 쿠폰 도착',  log['tok-en'])
_ok("tok-en  body  '[en] 10% 할인…'",
    log['tok-en']['body']   == '[en] 10% 할인 쿠폰이 도착했어요', log['tok-en'])
# ko 토큰 → 원문
_ok("tok-ko  title 원문 그대로",
    log['tok-ko']['title']  == '쿠폰 도착',         log['tok-ko'])
_ok("tok-ko  body  원문 그대로",
    log['tok-ko']['body']   == '10% 할인 쿠폰이 도착했어요', log['tok-ko'])
# mn (지원 외) → en fallback
_ok("tok-mn  title '[en] …' (지원 외→en)",
    log['tok-mn']['title']  == '[en] 쿠폰 도착',    log['tok-mn'])
_ok("tok-mn  body  '[en] …' fallback",
    log['tok-mn']['body']   == '[en] 10% 할인 쿠폰이 도착했어요', log['tok-mn'])
# NULL → en fallback
_ok("tok-null title '[en] …' (NULL→en)",
    log['tok-null']['title']== '[en] 쿠폰 도착',    log['tok-null'])

# 메모이즈: 4 토큰 처리에 entry 2개 (title ko→en, body ko→en)
_ok(f"memoize entries == 2 (현재 {len(_PUSH_TRANSLATION_MEMO)})",
    len(_PUSH_TRANSLATION_MEMO) == 2, dict(_PUSH_TRANSLATION_MEMO))


# ── 3. announcement (어드민 공지) ───────────────────────────────────────
print('\n[3] announcement — lang_hint 저장 + 즉시 푸시 자동 번역')
StubPushProvider.sent_log.clear()
_PUSH_TRANSLATION_MEMO.clear()
status, j = _post('/api/admin/announcements',
                  {'title': '서비스 점검 안내',
                   'body':  '6월 1일 새벽 2~4시 서비스가 일시 중단됩니다.',
                   'audience':  'all',
                   'send_push': True,
                   'lang_hint': 'ko'},
                  token=admin_token)
_ok('201 응답',                  status == 201, j)
aid = j['announcement']['id']
db = _patched_get_db()
row = db.execute('SELECT body_lang FROM announcements WHERE id=?', (aid,)).fetchone()
db.close()
_ok("announcements.body_lang == 'ko' 저장", row['body_lang'] == 'ko', dict(row))

# 사용자 4명 → 4 토큰 모두 발송
log = {rec['token']: rec for rec in StubPushProvider.sent_log}
_ok('4 토큰 모두 발송',           len(log) == 4, list(log.keys()))
_ok("tok-en  title '[en] 서비스 점검 안내'",
    log['tok-en']['title']  == '[en] 서비스 점검 안내', log['tok-en'])
_ok("tok-ko  title 원문 그대로",
    log['tok-ko']['title']  == '서비스 점검 안내',       log['tok-ko'])
_ok("tok-mn  title '[en] …' (지원 외→en)",
    log['tok-mn']['title']  == '[en] 서비스 점검 안내', log['tok-mn'])
_ok("tok-null title '[en] …' (NULL→en)",
    log['tok-null']['title']== '[en] 서비스 점검 안내', log['tok-null'])

# 메모이즈 동작
_ok(f"memoize entries == 2 (현재 {len(_PUSH_TRANSLATION_MEMO)})",
    len(_PUSH_TRANSLATION_MEMO) == 2, dict(_PUSH_TRANSLATION_MEMO))


# ── 4. lang_hint 미명시 시 default 'ko' (announcement) ───────────────────
print('\n[4] announcement lang_hint 미명시 → body_lang 기본 ko')
status, j = _post('/api/admin/announcements',
                  {'title': '점검 안내2', 'body': '내일 새벽 점검',
                   'audience': 'all', 'send_push': False},
                  token=admin_token)
_ok('201 응답',                  status == 201, j)
aid2 = j['announcement']['id']
db = _patched_get_db()
row = db.execute('SELECT body_lang FROM announcements WHERE id=?', (aid2,)).fetchone()
db.close()
_ok("body_lang == 'ko' (default)", row['body_lang'] == 'ko', dict(row))


# ── 5. notification lang_hint 미명시 → body_lang NULL → 번역 시도 안 함 ──
print('\n[5] notification lang_hint 누락 → body_lang NULL → 번역 안 함')
# quota 복구
db = _patched_get_db()
db.execute('UPDATE notification_quota SET quantity_used = 0')
db.commit(); db.close()
status, j = _post('/api/facilities/1/notifications',
                  {'title': '안내', 'body': 'hint 없는 메시지',
                   'target_type': 'all_visited', 'scheduled_at': future_iso},
                  token=facility_token)
_ok('201 응답',                  status == 201, j)
nid2 = j['notification']['id']
db = _patched_get_db()
row = db.execute('SELECT body_lang FROM notifications WHERE id=?', (nid2,)).fetchone()
db.close()
_ok('body_lang IS NULL',         row['body_lang'] is None, dict(row))

# dispatch 시 — body_lang None 이라 본문 번역 시도 X. title 만 'ko' source 로 번역.
StubPushProvider.sent_log.clear()
_PUSH_TRANSLATION_MEMO.clear()
status, j = _post(f'/api/admin/notifications/{nid2}/dispatch', token=admin_token)
log = {rec['token']: rec for rec in StubPushProvider.sent_log}
# title 은 'ko' 소스 → en 토큰엔 '[en] 안내' 로 번역됨
_ok("tok-en  title 번역됨 ('[en] 안내')",
    log['tok-en']['title']  == '[en] 안내',         log['tok-en'])
# body 는 body_lang=None 이라 번역 안 됨 (원문 그대로)
_ok('tok-en  body 원문 그대로 (body_lang=None)',
    log['tok-en']['body']   == 'hint 없는 메시지',  log['tok-en'])


print('\n=== P8c 푸시 알림 본문 다국어 — 전체 시나리오 PASS ===')
os.unlink(tmp.name)
