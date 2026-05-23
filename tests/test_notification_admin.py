"""P11 — 알림 부가서비스 어드민 워크플로 회귀 테스트.

검증 범위
---------
- 12시간 리드타임 (사장 신청 시)
- quota 검증/차감 (FIFO, expires_at)
- AI 자동 검토 분기 (auto_pass / flagged / blocked)
- status 자동 분기 (unpaid / review / pending)
- 어드민 라우트 (큐/필터/approve/reject/dispatch + blocklist CRUD)
- 자동 배치 스케줄러 (scripts/dispatch_due_notifications)
- 권한 분리 (사장 토큰 → 어드민 라우트 401/403)
- 결제 → quota 자동 연동 (routes/billing)

stub translator + stub push provider 로 외부 의존 없이 검증.
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
os.environ.pop('ANTHROPIC_API_KEY', None)   # AI 검토는 stub fallback
os.environ['PAYMENT_PROVIDER']     = 'sim'  # PG 시뮬

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
from models.push import StubPushProvider                         # noqa: E402

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


def _del(path, token=None):
    h = {}
    if token: h['Authorization'] = f'Bearer {token}'
    r = c.delete(path, headers=h)
    return r.status_code, r.get_json()


# ── 0. 시드 ───────────────────────────────────────────────────────────────
print('\n[0] 시드 — 매장/사장/사용자/quota/금칙어')
db = _patched_get_db()
hashed = bcrypt.hashpw(b'pw', bcrypt.gensalt()).decode()
db.execute(
    """INSERT INTO facility_accounts (business_no, company_name, email, password, verified, status)
       VALUES ('111-22-33333','Test Store','o@x.com',?,1,'verified')""",
    (hashed,)
)
db.execute("INSERT INTO facilities (name, owner_id, active) VALUES ('Cafe Seoul', 1, 1)")
db.execute("INSERT INTO users (email, password) VALUES ('u1@x.com', ?)", (hashed,))
db.execute("INSERT INTO users (email, password) VALUES ('u2@x.com', ?)", (hashed,))
db.execute('INSERT INTO user_wifi_logs (user_id, facility_id) VALUES (1, 1)')
db.execute('INSERT INTO user_wifi_logs (user_id, facility_id) VALUES (2, 1)')
db.execute("INSERT INTO super_admin_accounts (email, password, role) VALUES ('a@a', ?, 'super')", (hashed,))
db.execute("INSERT INTO notification_blocklist (term, severity, created_by_admin_id) VALUES ('대출', 'block', 1)")
ends = (datetime.utcnow() + timedelta(days=30)).isoformat()
db.execute("INSERT INTO notification_quota (facility_account_id, quantity_purchased, expires_at) VALUES (1, 100, ?)", (ends,))
db.commit(); db.close()

facility_token = make_jwt(1, 'o@x.com', sub_type='facility')
admin_token    = make_jwt(1, 'a@a',     sub_type='super_admin')

future12 = (datetime.utcnow() + timedelta(hours=13)).isoformat()
future6  = (datetime.utcnow() + timedelta(hours=6)).isoformat()


# ── 1. 12시간 리드타임 ────────────────────────────────────────────────────
print('\n[1] 12시간 리드타임 위반 → 400')
status, j = _post('/api/facilities/1/notifications',
                  {'title': '안내', 'body': '테스트',
                   'target_type': 'all_visited', 'scheduled_at': future6},
                  token=facility_token)
_ok('400 응답',           status == 400, j)
_ok('에러 메시지 명확',    '12시간' in j['message'], j)

print('\n[2] scheduled_at 누락 → 400')
status, j = _post('/api/facilities/1/notifications',
                  {'title': '안내', 'body': '테스트', 'target_type': 'all_visited'},
                  token=facility_token)
_ok('400 응답',           status == 400, j)


# ── 3. quota 충분 + 안전 메시지 → pending ────────────────────────────────
print('\n[3] quota 충분 + 안전 메시지 → status=pending, ai=auto_pass')
status, j = _post('/api/facilities/1/notifications',
                  {'title': '쿠폰 도착', 'body': '10% 할인 쿠폰이 도착했어요',
                   'target_type': 'all_visited', 'scheduled_at': future12},
                  token=facility_token)
_ok('201 응답',                    status == 201, j)
_ok("status == 'pending'",         j['notification']['status'] == 'pending', j['notification'])
_ok("ai_review_status == 'auto_pass'",
    j['notification']['ai_review_status'] == 'auto_pass', j['notification'])
_ok('recipient_count == 2',        j['recipient_count'] == 2, j)
nid_pending = j['notification']['id']


# ── 4. 차단 단어 → review + blocked ──────────────────────────────────────
print('\n[4] 차단 단어 → status=review, ai=blocked')
status, j = _post('/api/facilities/1/notifications',
                  {'title': '특별 안내', 'body': '무이자 대출 가능합니다',
                   'target_type': 'all_visited', 'scheduled_at': future12},
                  token=facility_token)
_ok("status == 'review'",          j['notification']['status'] == 'review', j['notification'])
_ok("ai_review_status == 'blocked'",
    j['notification']['ai_review_status'] == 'blocked', j['notification'])
_ok('AI 사유 명시',                '대출' in j['notification']['ai_review_reason'], j['notification'])
nid_review = j['notification']['id']


# ── 5. quota 부족 → unpaid ────────────────────────────────────────────────
print('\n[5] quota 소진 후 신청 → status=unpaid')
db = _patched_get_db()
db.execute('UPDATE notification_quota SET quantity_used = quantity_purchased')
db.commit(); db.close()
status, j = _post('/api/facilities/1/notifications',
                  {'title': '안내', 'body': '쿠폰', 'target_type': 'all_visited',
                   'scheduled_at': future12},
                  token=facility_token)
_ok("status == 'unpaid'",          j['notification']['status'] == 'unpaid', j)
_ok('is_paid == False',            j['is_paid'] is False, j)
nid_unpaid = j['notification']['id']

# quota 복구 (이후 dispatch 검증 위해)
db = _patched_get_db()
db.execute('UPDATE notification_quota SET quantity_used = 0')
db.commit(); db.close()


# ── 6. 어드민 큐 조회 + 필터 ──────────────────────────────────────────────
print('\n[6] 어드민 큐: 3개 알림 + review 필터')
status, j = _get('/api/admin/notifications', token=admin_token)
_ok('count == 3',                  j['count'] == 3, j)
status, j = _get('/api/admin/notifications?status=review', token=admin_token)
_ok("status=review 필터 — 1건",      j['count'] == 1 and j['notifications'][0]['id'] == nid_review, j)


# ── 7. 어드민 approve (review → pending) ─────────────────────────────────
print('\n[7] review 큐 승인 — approved_by/at 기록')
status, j = _post(f'/api/admin/notifications/{nid_review}/approve',
                  token=admin_token)
_ok("review → pending",            j['notification']['status'] == 'pending', j)
_ok("approved_by_admin_id == 1",   j['notification']['approved_by_admin_id'] == 1, j)
_ok('approved_at 기록',            bool(j['notification']['approved_at']), j)


# ── 8. 어드민 reject (unpaid → canceled) ──────────────────────────────────
print('\n[8] unpaid 알림 거부')
status, j = _post(f'/api/admin/notifications/{nid_unpaid}/reject',
                  token=admin_token)
_ok('200 응답',                    status == 200, j)
db = _patched_get_db()
row = db.execute('SELECT status FROM notifications WHERE id=?', (nid_unpaid,)).fetchone()
db.close()
_ok("status == 'canceled'",        row['status'] == 'canceled', dict(row))


# ── 9. 어드민 즉시 dispatch (quota 차감 + push) ──────────────────────────
print('\n[9] 어드민 즉시 dispatch — pending → sent + quota 2 차감')
StubPushProvider.sent_log.clear()
status, j = _post(f'/api/admin/notifications/{nid_pending}/dispatch',
                  token=admin_token)
_ok("status == 'sent'",            j['notification']['status'] == 'sent', j)

db = _patched_get_db()
qu = db.execute('SELECT quantity_used FROM notification_quota WHERE id=1').fetchone()['quantity_used']
db.close()
_ok('quota_used == 2 (수신자 2명)', qu == 2, qu)


# ── 10. dispatch quota 부족 → 409 ────────────────────────────────────────
print('\n[10] quota 부족 시 dispatch → 409')
db = _patched_get_db()
db.execute('UPDATE notification_quota SET quantity_used = quantity_purchased')
db.commit(); db.close()
status, j = _post(f'/api/admin/notifications/{nid_review}/dispatch',
                  token=admin_token)
_ok('409 응답',                    status == 409, j)
_ok("error 메시지 'quota'",         'quota' in (j.get('message') or ''), j)


# ── 11. blocklist CRUD ───────────────────────────────────────────────────
print('\n[11] 금칙어 CRUD')
status, j = _get('/api/admin/notifications/blocklist', token=admin_token)
_ok('GET: 1건 (시드)',              j['count'] == 1, j)
status, j = _post('/api/admin/notifications/blocklist',
                  {'term': '도박', 'severity': 'block'}, token=admin_token)
_ok('POST 201',                    status == 201, j)
bid = j['blocklist']['id']
# 중복
status, j = _post('/api/admin/notifications/blocklist',
                  {'term': '도박', 'severity': 'flag'}, token=admin_token)
_ok('중복 → 409',                  status == 409, j)
status, j = _del(f'/api/admin/notifications/blocklist/{bid}', token=admin_token)
_ok('DELETE 200',                  status == 200, j)


# ── 12. 권한 — 사장 토큰으로 어드민 라우트 → 401/403 ─────────────────────
print('\n[12] 권한 분리')
status, j = _get('/api/admin/notifications', token=facility_token)
_ok('사장 → 어드민 라우트 401/403', status in (401, 403), (status, j))


# ── 13. 자동 배치 스케줄러 — 도래분 처리 ─────────────────────────────────
print('\n[13] 스케줄러 — 도래 pending 만 sent 로')
# quota 복구
db = _patched_get_db()
db.execute('UPDATE notification_quota SET quantity_used = 0')
# 도래 pending 1건 추가 (scheduled_at = 1시간 전)
past_iso = (datetime.utcnow() - timedelta(hours=1)).isoformat()
db.execute(
    "INSERT INTO notifications (facility_id,title,body,target_type,scheduled_at,status,recipient_count)"
    " VALUES (1,'스케줄러 도래','테스트','all_visited',?,'pending',2)",
    (past_iso,)
)
nid_due = db.execute("SELECT last_insert_rowid() AS id").fetchone()['id']
db.commit(); db.close()

from scripts.dispatch_due_notifications import dispatch_due
result = dispatch_due()
_ok(f'sent == 1 (실제: {result["sent"]})', result['sent'] == 1, result)

db = _patched_get_db()
status_after = db.execute('SELECT status FROM notifications WHERE id=?', (nid_due,)).fetchone()['status']
db.close()
_ok(f"#{nid_due} status == 'sent'", status_after == 'sent', status_after)


# ── 14. 스케줄러 quota 부족 → unpaid 자동 전환 ───────────────────────────
print('\n[14] 스케줄러 — quota 부족 시 pending → unpaid')
db = _patched_get_db()
db.execute('UPDATE notification_quota SET quantity_used = quantity_purchased')
# 도래 pending 1건 추가
db.execute(
    "INSERT INTO notifications (facility_id,title,body,target_type,scheduled_at,status,recipient_count)"
    " VALUES (1,'스케줄러 미결제','테스트','all_visited',?,'pending',2)",
    (past_iso,)
)
nid_due2 = db.execute("SELECT last_insert_rowid() AS id").fetchone()['id']
db.commit(); db.close()

result = dispatch_due()
_ok('failed >= 1',                 result['failed'] >= 1, result)

db = _patched_get_db()
status2 = db.execute('SELECT status FROM notifications WHERE id=?', (nid_due2,)).fetchone()['status']
db.close()
_ok(f"#{nid_due2} status == 'unpaid'", status2 == 'unpaid', status2)


# ── 15. 결제 → quota 자동 연동 (회귀) ────────────────────────────────────
print('\n[15] 결제 → quota 자동 생성 (회귀)')
db = _patched_get_db()
db.execute("INSERT INTO billing_keys (facility_account_id, pg_key, card_brand, masked_card) VALUES (1, 'sim-x', 'KB', '****-****-****-1234')")
db.commit(); db.close()
status, j = _post('/api/billing/subscriptions',
                  {'service_type': 'notification', 'quantity': 50, 'period_months': 1},
                  token=facility_token)
_ok('결제 201',                    status == 201, j)
db = _patched_get_db()
q_total = db.execute('SELECT COUNT(*) AS n FROM notification_quota WHERE facility_account_id=1').fetchone()['n']
db.close()
_ok(f'quota row 2개 이상 ({q_total})', q_total >= 2, q_total)


print('\n=== P11 알림 어드민 워크플로 — 전체 시나리오 PASS ===')
os.unlink(tmp.name)
