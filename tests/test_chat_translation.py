"""P8b — 채팅 자동 번역 회귀 테스트.

검증 범위
---------
1) 송신 ``lang_hint`` → ``chat_messages.body_lang`` 저장
2) 수신 viewer_lang 기준 lazy 번역 + ``chat_message_translations`` 캐시
3) viewer_lang 결정: ``?lang=`` > ``users.language`` > 매장(ko)
4) 지원 외 언어 → ``en`` fallback
5) ``lang_hint`` 누락(=body_lang NULL) → 번역 시도 안 함 (비용 안전장치)
6) 같은 언어끼리(ko↔ko) → 번역 0회
7) 캐시 적중: 재요청 시 translator 미호출 (cache row 안 늘어남)
8) 채팅 푸시: 토큰별 ``push_tokens.language`` 기반 자동 번역 + fallback
9) ``push_to_users`` 호환성: title_lang/body_lang 미명시 시 원문 그대로

stub translator (``[<target>] <원문>`` 형식) 로 검증 — 실 API 키 없이 동작.
"""
import os
import json
import sqlite3
import tempfile

import bcrypt

# DB 격리 — 다른 테스트와 분리
tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB']           = tmp.name
os.environ['TRANSLATION_PROVIDER']  = 'stub'
os.environ['PUSH_PROVIDER']         = 'stub'

import models.database as _dbmod
def _patched_get_db():
    conn = sqlite3.connect(os.environ['PATHWAVE_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn
_dbmod.get_db = _patched_get_db
_dbmod.DB_PATH = tmp.name

from app import app                                  # noqa: E402
from routes.auth import make_jwt                     # noqa: E402
from models.push import StubPushProvider, _PUSH_TRANSLATION_MEMO  # noqa: E402

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


def _get(path, token=None):
    h = {}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.get(path, headers=h)
    return r.status_code, r.get_json()


# ── 0. 시드: 사용자(en) + 매장 + 채팅방 + 푸시 토큰 4종 ────────────────────────
print('\n[0] 시드')
db = _patched_get_db()
hashed = bcrypt.hashpw(b'pw', bcrypt.gensalt()).decode()
cur = db.execute(
    "INSERT INTO users (email, password, language) VALUES (?,?,?)",
    ('tourist@test.com', hashed, 'en')
)
user_id = cur.lastrowid
cur = db.execute(
    """INSERT INTO facility_accounts
         (business_no, company_name, email, password, verified, status)
       VALUES ('111-22-33333','Cafe Seoul','owner@test.com', ?, 1, 'verified')""",
    (hashed,)
)
owner_id = cur.lastrowid
cur = db.execute(
    "INSERT INTO facilities (name, owner_id, active) VALUES (?,?,1)",
    ('Cafe Seoul', owner_id)
)
facility_id = cur.lastrowid
cur = db.execute(
    "INSERT INTO chat_rooms (facility_id, user_id) VALUES (?,?)",
    (facility_id, user_id)
)
room_id = cur.lastrowid
db.executemany(
    "INSERT INTO push_tokens (user_id, token, platform, language) VALUES (?,?,?,?)",
    [(user_id, 'tok-en',   'fcm', 'en'),
     (user_id, 'tok-ko',   'fcm', 'ko'),
     (user_id, 'tok-mn',   'fcm', 'mn'),     # 지원 외 (몽골어)
     (user_id, 'tok-null', 'fcm', None)],    # NULL language
)
db.commit(); db.close()

user_token     = make_jwt(user_id,  'tourist@test.com', sub_type='user')
facility_token = make_jwt(owner_id, 'owner@test.com',   sub_type='facility')


# ── 1. 송신 lang_hint → body_lang 저장 + sender 본인 응답에 번역 없음 ────────
print('\n[1] 송신 lang_hint 저장 + sender 본인 응답 번역 없음')
status, j = _post(f'/api/chat/rooms/{room_id}/messages',
                  {'body': 'Hello, are you open today?', 'lang_hint': 'en'},
                  token=user_token)
_ok('201 응답', status == 201, j)
m1 = j['message']
_ok("body_lang == 'en'",                m1['body_lang'] == 'en', m1)
_ok('sender 응답에 translated_text 없음', 'translated_text' not in m1, m1)


# ── 2. 매장(viewer_lang=ko) 측에서 영어 메시지를 한국어로 번역해서 받음 ──────
print('\n[2] 매장(ko) viewer — 영어 메시지를 한국어 번역으로 받음')
status, j = _get(f'/api/chat/rooms/{room_id}/messages', token=facility_token)
_ok('200 응답',                   status == 200, j)
_ok("viewer_lang == 'ko'",        j['viewer_lang'] == 'ko', j)
m = j['messages'][0]
_ok('translated_text 머지',
    m.get('translated_text') == '[ko] Hello, are you open today?', m)
_ok("translated_lang == 'ko'",    m.get('translated_lang') == 'ko', m)
_ok("translated_provider stub",   m.get('translated_provider') == 'stub', m)


# ── 3. 캐시 적중 — 재요청 시 chat_message_translations row 안 늘어남 ─────────
print('\n[3] 캐시 적중')
db = _patched_get_db()
cache_before = db.execute(
    'SELECT COUNT(*) AS n FROM chat_message_translations'
).fetchone()['n']
db.close()
_get(f'/api/chat/rooms/{room_id}/messages', token=facility_token)
_get(f'/api/chat/rooms/{room_id}/messages', token=facility_token)  # 2번 더
db = _patched_get_db()
cache_after = db.execute(
    'SELECT COUNT(*) AS n FROM chat_message_translations'
).fetchone()['n']
db.close()
_ok(f'캐시 row before({cache_before}) == after({cache_after})',
    cache_before == cache_after)


# ── 4. 매장(ko) 답신 → user(en) 측 조회 — users.language fallback ────────────
print('\n[4] users.language fallback (?lang= 없음)')
status, j = _post(f'/api/chat/rooms/{room_id}/messages',
                  {'body': '네 오늘 영업합니다', 'lang_hint': 'ko'},
                  token=facility_token)
_ok('매장 응답 201',         status == 201, j)
_ok("매장 body_lang == 'ko'", j['message']['body_lang'] == 'ko', j)

status, j = _get(f'/api/chat/rooms/{room_id}/messages', token=user_token)
_ok("viewer_lang == 'en' (users.language)", j['viewer_lang'] == 'en', j)
m2 = j['messages'][1]
_ok('매장 ko 메시지가 user 측에 영어 번역으로 보임',
    m2.get('translated_text') == '[en] 네 오늘 영업합니다', m2)


# ── 5. ?lang=ja 쿼리 우선 (users.language=en 무시) ──────────────────────────
print('\n[5] ?lang= 쿼리 우선')
status, j = _get(f'/api/chat/rooms/{room_id}/messages?lang=ja',
                 token=user_token)
_ok("viewer_lang == 'ja' (쿼리 우선)", j['viewer_lang'] == 'ja', j)
m_ja = j['messages'][0]
_ok('영어 메시지가 일본어로',
    m_ja.get('translated_text') == '[ja] Hello, are you open today?', m_ja)


# ── 6. 지원 외 언어 → en fallback ───────────────────────────────────────────
print('\n[6] 지원 외 언어 → en fallback')
status, j = _get(f'/api/chat/rooms/{room_id}/messages?lang=mn',
                 token=user_token)
_ok("viewer_lang == 'en' (mn → en fallback)",
    j['viewer_lang'] == 'en', j)


# ── 7. lang_hint 누락 → body_lang NULL → 번역 시도 안 함 (비용 안전장치) ────
print('\n[7] lang_hint 누락 → 번역 시도 안 함')
status, j = _post(f'/api/chat/rooms/{room_id}/messages',
                  {'body': 'lang_hint 없는 메시지'},
                  token=user_token)
_ok('201 응답',           status == 201, j)
_ok('body_lang IS NULL',  j['message']['body_lang'] is None, j['message'])

mid3 = j['message']['id']
status, j = _get(
    f'/api/chat/rooms/{room_id}/messages?after_id={mid3 - 1}',
    token=facility_token
)
m3 = j['messages'][0]
_ok('body_lang NULL 메시지엔 translated_text 없음',
    'translated_text' not in m3, m3)


# ── 8. 같은 언어끼리 (ko↔ko) — 번역 0회 ─────────────────────────────────────
print('\n[8] ko↔ko 같은 언어 — 번역 없음')
db = _patched_get_db()
db.execute("UPDATE users SET language='ko' WHERE id=?", (user_id,))
db.commit(); db.close()

status, j = _post(f'/api/chat/rooms/{room_id}/messages',
                  {'body': '안녕하세요', 'lang_hint': 'ko'},
                  token=facility_token)
mid4 = j['message']['id']
status, j = _get(
    f'/api/chat/rooms/{room_id}/messages?after_id={mid4 - 1}',
    token=user_token
)
m4 = j['messages'][0]
_ok("user viewer_lang == 'ko' (DB 변경 반영)",
    j['viewer_lang'] == 'ko', j)
_ok('ko↔ko: translated_text 없음', 'translated_text' not in m4, m4)


# ── 9. 채팅 푸시 — 토큰별 자동 번역 + 지원 외/NULL → 영어 fallback ──────────
print('\n[9] 채팅 푸시 자동 번역')
# user 언어 다시 영어로 (현실 시나리오: 외국인이 매장 메시지 받음)
db = _patched_get_db()
db.execute("UPDATE users SET language='en' WHERE id=?", (user_id,))
db.commit(); db.close()

StubPushProvider.sent_log.clear()
_PUSH_TRANSLATION_MEMO.clear()

status, j = _post(f'/api/chat/rooms/{room_id}/messages',
                  {'body': '오늘 영업합니다', 'lang_hint': 'ko'},
                  token=facility_token)
_ok('매장 메시지 201', status == 201, j)

log_by_tok = {rec['token']: rec for rec in StubPushProvider.sent_log}
_ok('4개 토큰 모두 발송', len(log_by_tok) == 4,
    list(log_by_tok.keys()))

# en 토큰 → 영어 번역
_ok("tok-en: title '[en] 새 메시지'",
    log_by_tok['tok-en']['title'] == '[en] 새 메시지',
    log_by_tok['tok-en'])
_ok("tok-en: body  '[en] 오늘 영업합니다'",
    log_by_tok['tok-en']['body']  == '[en] 오늘 영업합니다',
    log_by_tok['tok-en'])

# ko 토큰 → 원문
_ok("tok-ko: title '새 메시지' (원문)",
    log_by_tok['tok-ko']['title'] == '새 메시지',
    log_by_tok['tok-ko'])
_ok("tok-ko: body  '오늘 영업합니다'",
    log_by_tok['tok-ko']['body']  == '오늘 영업합니다',
    log_by_tok['tok-ko'])

# mn (지원 외) → 영어 fallback
_ok("tok-mn: title '[en] 새 메시지' (지원 외→en)",
    log_by_tok['tok-mn']['title'] == '[en] 새 메시지',
    log_by_tok['tok-mn'])
_ok("tok-mn: body  '[en] 오늘 영업합니다'",
    log_by_tok['tok-mn']['body']  == '[en] 오늘 영업합니다',
    log_by_tok['tok-mn'])

# NULL → 영어 fallback
_ok("tok-null: title '[en] 새 메시지' (NULL→en)",
    log_by_tok['tok-null']['title'] == '[en] 새 메시지',
    log_by_tok['tok-null'])

# 메모이즈: 4 토큰 처리에 (title ko→en) + (body ko→en) = 2 entry
_ok(f'memoize entries == 2 (현재 {len(_PUSH_TRANSLATION_MEMO)})',
    len(_PUSH_TRANSLATION_MEMO) == 2, dict(_PUSH_TRANSLATION_MEMO))


# ── 10. 호환성 — title_lang/body_lang 미명시 시 원문 그대로 (announcement) ───
print('\n[10] push_to_users 호환성 (title_lang/body_lang 미명시)')
StubPushProvider.sent_log.clear()
from models.push import push_to_users
db = _patched_get_db()
push_to_users(db, [user_id],
              title='시스템 공지',
              body='서버 점검 안내',
              data={'type': 'announcement'})
db.close()
for rec in StubPushProvider.sent_log:
    _ok(f"{rec['token']}: title 원문 그대로",
        rec['title'] == '시스템 공지', rec)
    _ok(f"{rec['token']}: body  원문 그대로",
        rec['body']  == '서버 점검 안내', rec)


print('\n=== P8b 채팅 자동 번역 — 전체 시나리오 PASS ===')
os.unlink(tmp.name)
