"""결제/서비스 신청 API. SRS FR-PAY-001~005.

PG 호출은 시뮬레이션 — pg_key, pg_tid는 'sim-' + uuid. 실제 PG 통합은 별도 PR.

엔드포인트
---------
- POST /api/billing/cards                       카드 등록 (owner only)
- GET  /api/billing/cards                       카드 목록 (owner only)
- DELETE /api/billing/cards/<id>                카드 삭제 (owner only)
- POST /api/billing/subscriptions               서비스 신청 + 즉시 결제 (owner)
- GET  /api/billing/subscriptions               구독 목록 (owner+admin)
- POST /api/billing/subscriptions/<id>/cancel   서비스 종료 (owner only)
- POST /api/billing/subscriptions/<id>/extend   동일 조건 연장 + 결제 (owner only)
- GET  /api/billing/payments                    결제 내역 (owner+admin)
- POST /api/billing/receipt-email               영수증 이메일 등록 (owner only)
"""
import secrets
from datetime import datetime
from dateutil_shim import add_months  # local import
from flask import Blueprint, request, jsonify, g

from models.database import get_db
from models.payment_provider import get_payment_provider
from routes.auth import require_facility_actor

billing_bp = Blueprint('billing', __name__, url_prefix='/api/billing')

_SERVICE_TYPES = {'wifi', 'event', 'notification'}
_VAT_RATE = 0.10

# 단가표 (KRW, 월 기준) — 실제 운영 시 별도 테이블/관리 페이지로
_UNIT_PRICES = {
    'wifi':         5000,
    'event':        10000,
    'notification': 3000,
}


# ── 카드 ──────────────────────────────────────────────────────────────────────

def _row_to_card(row) -> dict:
    return {
        'id':          row['id'],
        'card_brand':  row['card_brand'],
        'masked_card': row['masked_card'],
        'active':      bool(row['active']),
        'created_at':  row['created_at'],
    }


@billing_bp.route('/cards', methods=['POST'])
@require_facility_actor(roles=['owner'])
def register_card():
    """카드 등록 — 시뮬: card_number 마지막 4자리만 받아 mask + 임의 PG key.

    실제 PG (토스/이니시스): 클라이언트가 직접 PG 위젯 호출 → 토큰 받아 우리에게 전달.
    이번 PR은 그 위젯 결과를 받는 형태로만 시뮬.
    """
    account_id = g.auth['owner_account_id']
    data = request.get_json(silent=True) or {}
    card_brand  = (data.get('card_brand') or '').strip()
    last4       = (data.get('last4') or '').strip()
    if not card_brand or not last4 or not last4.isdigit() or len(last4) != 4:
        return jsonify({'success': False,
                        'message': 'card_brand + last4(4자리 숫자) 필요.'}), 400

    masked = f'****-****-****-{last4}'
    pg_key = f'sim-{secrets.token_hex(8)}'
    db = get_db()
    # 기존 active 카드 비활성 (단일 active 카드)
    db.execute("UPDATE billing_keys SET active=0 WHERE facility_account_id=?", (account_id,))
    cur = db.execute(
        """INSERT INTO billing_keys (facility_account_id, pg_key, card_brand, masked_card)
           VALUES (?,?,?,?)""",
        (account_id, pg_key, card_brand, masked)
    )
    row = db.execute("SELECT * FROM billing_keys WHERE id=?", (cur.lastrowid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True, 'card': _row_to_card(row)}), 201


@billing_bp.route('/cards', methods=['GET'])
@require_facility_actor(roles=['owner'])
def list_cards():
    account_id = g.auth['owner_account_id']
    db = get_db()
    rows = db.execute(
        "SELECT * FROM billing_keys WHERE facility_account_id=? ORDER BY id DESC",
        (account_id,)
    ).fetchall()
    db.close()
    return jsonify({'success': True, 'cards': [_row_to_card(r) for r in rows]})


@billing_bp.route('/cards/<int:cid>', methods=['DELETE'])
@require_facility_actor(roles=['owner'])
def delete_card(cid):
    account_id = g.auth['owner_account_id']
    db = get_db()
    cur = db.execute(
        "DELETE FROM billing_keys WHERE id=? AND facility_account_id=?",
        (cid, account_id)
    )
    db.commit()
    affected = cur.rowcount
    db.close()
    if affected == 0:
        return jsonify({'success': False, 'message': '카드를 찾을 수 없습니다.'}), 404
    return jsonify({'success': True})


# ── 서비스 구독 + 결제 ───────────────────────────────────────────────────────

def _row_to_subscription(row) -> dict:
    return {
        'id':            row['id'],
        'service_type':  row['service_type'],
        'quantity':      row['quantity'],
        'period_months': row['period_months'],
        'unit_price':    row['unit_price'],
        'total_price':   row['total_price'],
        'started_at':    row['started_at'],
        'ends_at':       row['ends_at'],
        'status':        row['status'],
        'created_at':    row['created_at'],
    }


def _row_to_payment(row) -> dict:
    return {
        'id':              row['id'],
        'subscription_id': row['subscription_id'],
        'order_no':        row['order_no'],
        'amount':          row['amount'],
        'vat':             row['vat'],
        'total':           row['total'],
        'pg_tid':          row['pg_tid'],
        'status':          row['status'],
        'receipt_email':   row['receipt_email'],
        'paid_at':         row['paid_at'],
        'created_at':      row['created_at'],
    }


def _ensure_active_card(db, account_id: int):
    return db.execute(
        "SELECT * FROM billing_keys WHERE facility_account_id=? AND active=1",
        (account_id,)
    ).fetchone()


def _charge(card_pg_key: str, total: int, order_no: str,
            customer_email: str | None = None) -> tuple[bool, str | None, str | None]:
    """현재 ENV 의 PG provider 로 결제. (success, pg_tid, payment_key)."""
    provider = get_payment_provider()
    res = provider.charge(
        billing_key=card_pg_key, total=total,
        order_no=order_no, customer_email=customer_email,
    )
    if res.get('success'):
        return True, res.get('pg_tid'), res.get('payment_key')
    return False, None, None


@billing_bp.route('/subscriptions', methods=['POST'])
@require_facility_actor(roles=['owner'])
def create_subscription():
    """서비스 신청 5단계의 최종 단계 통합 — body: service_type, quantity, period_months."""
    account_id = g.auth['owner_account_id']
    data = request.get_json(silent=True) or {}
    service_type = (data.get('service_type') or '').strip()
    quantity     = data.get('quantity')
    period       = data.get('period_months')

    if service_type not in _SERVICE_TYPES:
        return jsonify({'success': False,
                        'message': f"service_type은 {sorted(_SERVICE_TYPES)} 중 하나여야 합니다."}), 400
    if not isinstance(quantity, int) or quantity < 1:
        return jsonify({'success': False, 'message': 'quantity는 1 이상의 정수여야 합니다.'}), 400
    if period not in (1, 12):
        return jsonify({'success': False, 'message': 'period_months는 1 또는 12.'}), 400

    db = get_db()
    card = _ensure_active_card(db, account_id)
    if not card:
        db.close()
        return jsonify({'success': False,
                        'message': '등록된 카드가 없습니다. 먼저 카드를 등록해 주세요.'}), 400

    unit  = _UNIT_PRICES[service_type]
    base  = unit * quantity * period
    # 연간 10% 할인
    if period == 12:
        base = int(base * 0.90)
    vat   = int(base * _VAT_RATE)
    total = base + vat

    ends_at = add_months(datetime.utcnow(), period).isoformat()
    cur = db.execute(
        """INSERT INTO service_subscriptions
             (facility_account_id, service_type, quantity, period_months,
              unit_price, total_price, ends_at)
           VALUES (?,?,?,?,?,?,?)""",
        (account_id, service_type, quantity, period, unit, total, ends_at)
    )
    sid = cur.lastrowid

    # PG 결제 — provider 추상화 (sim / toss)
    order_no = f'ORD-{datetime.utcnow().strftime("%Y%m%d")}-{secrets.token_hex(4)}'
    receipt_email = data.get('receipt_email') or db.execute(
        "SELECT email FROM facility_accounts WHERE id=?", (account_id,)
    ).fetchone()['email']
    ok, pg_tid, _payment_key = _charge(card['pg_key'], total, order_no, receipt_email)

    cur2 = db.execute(
        """INSERT INTO payments
             (facility_account_id, subscription_id, order_no, amount, vat, total,
              pg_tid, status, receipt_email, paid_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (account_id, sid, order_no, base, vat, total,
         pg_tid if ok else None,
         'paid' if ok else 'failed',
         receipt_email,
         datetime.utcnow().isoformat() if ok else None)
    )

    sub_row = db.execute("SELECT * FROM service_subscriptions WHERE id=?", (sid,)).fetchone()
    pay_row = db.execute("SELECT * FROM payments WHERE id=?", (cur2.lastrowid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'subscription': _row_to_subscription(sub_row),
                    'payment': _row_to_payment(pay_row)}), 201


@billing_bp.route('/subscriptions', methods=['GET'])
@require_facility_actor(roles=['owner', 'admin'])
def list_subscriptions():
    account_id = g.auth['owner_account_id']
    db = get_db()
    rows = db.execute(
        "SELECT * FROM service_subscriptions WHERE facility_account_id=? ORDER BY id DESC",
        (account_id,)
    ).fetchall()
    db.close()
    return jsonify({'success': True,
                    'subscriptions': [_row_to_subscription(r) for r in rows]})


@billing_bp.route('/subscriptions/<int:sid>/cancel', methods=['POST'])
@require_facility_actor(roles=['owner'])
def cancel_subscription(sid):
    account_id = g.auth['owner_account_id']
    db = get_db()
    row = db.execute(
        """SELECT status FROM service_subscriptions
           WHERE id=? AND facility_account_id=?""",
        (sid, account_id)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '구독을 찾을 수 없습니다.'}), 404
    if row['status'] != 'active':
        db.close()
        return jsonify({'success': False,
                        'message': f"이미 '{row['status']}' 상태입니다."}), 409
    db.execute(
        "UPDATE service_subscriptions SET status='canceled' WHERE id=?", (sid,)
    )
    db.commit()
    db.close()
    return jsonify({'success': True})


@billing_bp.route('/subscriptions/<int:sid>/extend', methods=['POST'])
@require_facility_actor(roles=['owner'])
def extend_subscription(sid):
    """동일 조건으로 연장 — 새 결제 row 생성."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    row = db.execute(
        """SELECT * FROM service_subscriptions
           WHERE id=? AND facility_account_id=?""",
        (sid, account_id)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '구독을 찾을 수 없습니다.'}), 404
    if row['status'] not in ('active', 'expired'):
        db.close()
        return jsonify({'success': False,
                        'message': f"'{row['status']}' 상태에서는 연장할 수 없습니다."}), 409

    card = _ensure_active_card(db, account_id)
    if not card:
        db.close()
        return jsonify({'success': False, 'message': '등록된 카드가 없습니다.'}), 400

    base = row['total_price'] * 100 // 110   # vat 역산
    vat  = row['total_price'] - base
    total = row['total_price']
    order_no = f'ORD-{datetime.utcnow().strftime("%Y%m%d")}-{secrets.token_hex(4)}'
    receipt_email = db.execute(
        "SELECT email FROM facility_accounts WHERE id=?", (account_id,)
    ).fetchone()['email']
    ok, pg_tid, _payment_key = _charge(card['pg_key'], total, order_no, receipt_email)

    new_ends = add_months(datetime.utcnow(), row['period_months']).isoformat()
    db.execute(
        """UPDATE service_subscriptions
             SET ends_at=?, status='active'
           WHERE id=?""",
        (new_ends, sid)
    )
    cur = db.execute(
        """INSERT INTO payments
             (facility_account_id, subscription_id, order_no, amount, vat, total,
              pg_tid, status, receipt_email, paid_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (account_id, sid, order_no, base, vat, total,
         pg_tid, 'paid' if ok else 'failed',
         row['facility_account_id'] and db.execute(
             "SELECT email FROM facility_accounts WHERE id=?", (account_id,)
         ).fetchone()['email'],
         datetime.utcnow().isoformat() if ok else None)
    )
    pay_row = db.execute("SELECT * FROM payments WHERE id=?", (cur.lastrowid,)).fetchone()
    sub_row = db.execute("SELECT * FROM service_subscriptions WHERE id=?", (sid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'subscription': _row_to_subscription(sub_row),
                    'payment': _row_to_payment(pay_row)})


# ── 결제 내역 ─────────────────────────────────────────────────────────────────

@billing_bp.route('/payments', methods=['GET'])
@require_facility_actor(roles=['owner', 'admin'])
def list_payments():
    account_id = g.auth['owner_account_id']
    db = get_db()
    rows = db.execute(
        """SELECT * FROM payments WHERE facility_account_id=?
           ORDER BY id DESC LIMIT 200""",
        (account_id,)
    ).fetchall()
    db.close()
    return jsonify({'success': True, 'payments': [_row_to_payment(r) for r in rows]})


# ── 영수증 이메일 (전역 설정으로 facility_account에 보관) ───────────────────

@billing_bp.route('/receipt-email', methods=['POST'])
@require_facility_actor(roles=['owner'])
def set_receipt_email():
    """이후 결제의 기본 영수증 이메일. 단일성 — facility_accounts.email 자체는 로그인 이메일이라 별도 보관."""
    account_id = g.auth['owner_account_id']
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    if not email or '@' not in email:
        return jsonify({'success': False, 'message': '유효한 이메일 필요.'}), 400
    db = get_db()
    # facility_accounts에 receipt_email 컬럼 없으면 미들 ALTER (마이그레이션은 기존 헬퍼)
    cols = [r['name'] for r in db.execute('PRAGMA table_info(facility_accounts)').fetchall()]
    if 'receipt_email' not in cols:
        db.execute("ALTER TABLE facility_accounts ADD COLUMN receipt_email TEXT")
    db.execute(
        "UPDATE facility_accounts SET receipt_email=? WHERE id=?",
        (email, account_id)
    )
    db.commit()
    db.close()
    return jsonify({'success': True, 'receipt_email': email})
