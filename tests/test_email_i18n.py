"""P8d — 이메일 본문 다국어 (ko/en) 회귀 테스트.

사용자 정책 (P12 와 일관)
------------------------
- lang === 'ko' → ko 본문
- 그 외 모든 lang → en 본문
- 누락 → ko (legacy 호환)

검증
----
1) /api/auth/send-code lang='ko' → 한국어 subject
2) /api/auth/send-code lang='en' → 영어 subject
3) /api/auth/send-code lang='ja' → 영어 (fallback)
4) /api/auth/send-code lang 누락 → ko (legacy)
5) /api/admin/policies/<pid>/notify — user.language 따라 ko/en 본문 분기
6) Accept-Language 헤더로도 lang 받기
"""
import os
import sqlite3
import tempfile

import bcrypt
from datetime import datetime, timedelta

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB']    = tmp.name
os.environ['EMAIL_PROVIDER'] = 'console'

import models.database as _dbmod
_dbmod.DB_PATH = tmp.name
_dbmod.init_db()

from app import app                                          # noqa: E402
from routes.auth import make_jwt                             # noqa: E402
from models.email_provider import ConsoleEmailProvider       # noqa: E402

c = app.test_client()


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


import json as _json
def _post(path, data=None, lang=None, token=None):
    h = {'Content-Type': 'application/json'}
    if lang:  h['Accept-Language'] = lang
    if token: h['Authorization']   = f'Bearer {token}'
    r = c.post(path, data=_json.dumps(data or {}), headers=h)
    return r.status_code, r.get_json()


def _last_email():
    return ConsoleEmailProvider.sent_log[-1] if ConsoleEmailProvider.sent_log else None


# ── 시드 ────────────────────────────────────────────────────────────────
print('\n[0] 시드 — super admin + 사용자(en) + 정책 row')
db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
hashed = bcrypt.hashpw(b'pw', bcrypt.gensalt()).decode()
db.execute("INSERT INTO super_admin_accounts (email, password, role) VALUES ('a@a', ?, 'super')", (hashed,))
db.execute("INSERT INTO users (email, password, language) VALUES ('alice@x.com', ?, 'en')", (hashed,))
db.execute("INSERT INTO users (email, password, language) VALUES ('kim@x.com', ?, 'ko')", (hashed,))
# 약관 pending row 1 개 (notify 대상)
effective = (datetime.utcnow() + timedelta(days=1)).isoformat()
db.execute(
    """INSERT INTO policies (kind, lang, version, title, body, change_log, effective_at)
       VALUES ('terms', 'ko', '1.0', '서비스 이용약관', '본문...',
               '결제 정책 명확화', ?)""",
    (effective,)
)
pid = db.execute("SELECT last_insert_rowid() AS id").fetchone()['id']
db.commit(); db.close()
admin_token = make_jwt(1, 'a@a', sub_type='super_admin')


# ── 1. lang='ko' → 한국어 ──────────────────────────────────────────────
print('\n[1] send-code lang=ko → 한국어 subject')
ConsoleEmailProvider.sent_log.clear()
status, j = _post('/api/auth/send-code', {'email': 'new1@x.com', 'lang': 'ko'})
_ok('200 응답',                status == 200, j)
rec = _last_email()
_ok("subject = 한국어",         rec and '인증 코드' in rec['subject'], rec)


# ── 2. lang='en' → 영어 ────────────────────────────────────────────────
print('\n[2] send-code lang=en → 영어 subject')
ConsoleEmailProvider.sent_log.clear()
status, j = _post('/api/auth/send-code', {'email': 'new2@x.com', 'lang': 'en'})
rec = _last_email()
_ok("subject = English",       rec and 'Verification Code' in rec['subject'], rec)


# ── 3. lang='ja' → 영어 fallback ───────────────────────────────────────
print('\n[3] send-code lang=ja → 영어 fallback')
ConsoleEmailProvider.sent_log.clear()
status, j = _post('/api/auth/send-code', {'email': 'new3@x.com', 'lang': 'ja'})
rec = _last_email()
_ok("subject = English (fallback)", rec and 'Verification Code' in rec['subject'], rec)


# ── 4. lang 누락 → ko (legacy) ─────────────────────────────────────────
print('\n[4] send-code lang 누락 → ko (legacy)')
ConsoleEmailProvider.sent_log.clear()
status, j = _post('/api/auth/send-code', {'email': 'new4@x.com'})
rec = _last_email()
_ok("subject = 한국어 (legacy)", rec and '인증 코드' in rec['subject'], rec)


# ── 5. Accept-Language 헤더로도 ────────────────────────────────────────
print('\n[5] Accept-Language 헤더로 lang 받기')
ConsoleEmailProvider.sent_log.clear()
status, j = _post('/api/auth/send-code', {'email': 'new5@x.com'}, lang='en-US')
rec = _last_email()
_ok("subject = English (헤더)",  rec and 'Verification Code' in rec['subject'], rec)


# ── 6. policy notify — user.language 따라 분기 ──────────────────────────
print('\n[6] policy notify — alice(en)/kim(ko) 각자 lang 본문')
ConsoleEmailProvider.sent_log.clear()
status, j = _post(f'/api/admin/policies/{pid}/notify',
                  {'sub_type': 'user'}, token=admin_token)
_ok('200 응답',                status == 200, j)

# alice 와 kim 각각 한 통씩 발송
logs = list(ConsoleEmailProvider.sent_log)
by_email = {rec['to']: rec for rec in logs}
_ok('alice@x.com 발송됨',       'alice@x.com' in by_email, list(by_email.keys()))
_ok('kim@x.com 발송됨',         'kim@x.com'   in by_email, list(by_email.keys()))
_ok("alice subject = English Update Notice",
    'Update Notice' in by_email['alice@x.com']['subject'], by_email['alice@x.com'])
_ok("kim subject = 한국어 변경 안내",
    '변경 안내' in by_email['kim@x.com']['subject'], by_email['kim@x.com'])


print('\n=== P8d 이메일 본문 다국어 — 전체 시나리오 PASS ===')
os.unlink(tmp.name)
