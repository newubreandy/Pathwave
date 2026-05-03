"""쿠폰 발급/사용 API. SRS FR-COUPON-001/002.

엔드포인트
---------
- POST   /api/facilities/<fid>/coupons        쿠폰 발급 (owner+admin)
- GET    /api/facilities/<fid>/coupons        매장 쿠폰 이력 (owner+admin)
- PATCH  /api/coupons/<id>                    쿠폰 메타 수정 (owner+admin)
- DELETE /api/coupons/<id>                    쿠폰 회수 (owner+admin)
- POST   /api/coupons/<id>/use                사용 처리 (owner+admin+staff)
- GET    /api/users/me/coupons                앱 사용자 본인 쿠폰함

상태 (동적 계산):
- used=1                          → 'used'
- used=0 AND expires_at < now()   → 'expired'
- 그 외                            → 'active'
"""
from datetime import datetime

from flask import Blueprint, request, jsonify, g

from models.database import get_db
from routes.auth import require_facility_actor, require_auth

coupon_bp = Blueprint('coupon', __name__)


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _owned_facility(db, fid: int, account_id: int) -> bool:
    return bool(db.execute(
        "SELECT 1 FROM facilities WHERE id=? AND owner_id=? AND active=1",
        (fid, account_id)
    ).fetchone())


def _coupon_status(row) -> str:
    if row['used']:
        return 'used'
    exp = row['expires_at']
    if exp and datetime.utcnow() > datetime.fromisoformat(exp):
        return 'expired'
    return 'active'


def _row_to_coupon(row) -> dict:
    return {
        'id':          row['id'],
        'facility_id': row['facility_id'],
        'user_id':     row['user_id'],
        'title':       row['title'],
        'benefit':     row['benefit'],
        'status':      _coupon_status(row),
        'used':        bool(row['used']),
        'used_at':     row['used_at'],
        'used_by': {
            'role':     row['used_by_actor_role'],
            'actor_id': row['used_by_actor_id'],
        } if row['used'] else None,
        'issued_by': {
            'role':     row['issued_by_actor_role'],
            'actor_id': row['issued_by_actor_id'],
        },
        'expires_at': row['expires_at'],
        'created_at': row['created_at'],
    }


# ── 발급 ──────────────────────────────────────────────────────────────────────

@coupon_bp.route('/api/facilities/<int:fid>/coupons', methods=['POST'])
@require_facility_actor(roles=['owner', 'admin'])
def issue_coupon(fid):
    """쿠폰 발급. ``user_id`` (단일) 또는 ``user_ids`` (다중) 둘 중 하나 필수.

    body: {title, benefit?, expires_at?, user_id? | user_ids?: [...]}
    """
    account_id = g.auth['owner_account_id']
    actor_role = g.auth['actor_role']
    actor_id   = g.auth['user_id']
    data = request.get_json(silent=True) or {}

    title      = (data.get('title') or '').strip()
    benefit    = (data.get('benefit') or '').strip() or None
    expires_at = (data.get('expires_at') or '').strip() or None
    user_id    = data.get('user_id')
    user_ids   = data.get('user_ids') or ([] if user_id is None else [user_id])

    if not title:
        return jsonify({'success': False, 'message': 'title은 필수입니다.'}), 400
    if not isinstance(user_ids, list) or not user_ids:
        return jsonify({'success': False,
                        'message': 'user_id 또는 user_ids가 필요합니다.'}), 400
    if not all(isinstance(u, int) and u > 0 for u in user_ids):
        return jsonify({'success': False,
                        'message': 'user_ids는 양의 정수 배열이어야 합니다.'}), 400
    if expires_at:
        try:
            datetime.fromisoformat(expires_at)
        except ValueError:
            return jsonify({'success': False,
                            'message': 'expires_at은 ISO 8601 형식이어야 합니다.'}), 400

    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    # user 존재 일괄 확인
    placeholders = ','.join('?' * len(user_ids))
    found = {r['id'] for r in db.execute(
        f"SELECT id FROM users WHERE id IN ({placeholders}) AND deleted_at IS NULL",
        user_ids
    ).fetchall()}
    missing = [u for u in user_ids if u not in found]
    if missing:
        db.close()
        return jsonify({'success': False,
                        'message': f'존재하지 않는 사용자: {missing}'}), 404

    issued = []
    for uid in user_ids:
        cur = db.execute(
            """INSERT INTO coupons
                 (facility_id, user_id, title, benefit, expires_at,
                  issued_by_actor_role, issued_by_actor_id)
               VALUES (?,?,?,?,?,?,?)""",
            (fid, uid, title, benefit, expires_at, actor_role, actor_id)
        )
        issued.append(cur.lastrowid)
    rows = db.execute(
        f"SELECT * FROM coupons WHERE id IN ({','.join('?' * len(issued))})",
        issued
    ).fetchall()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': f'{len(issued)}건의 쿠폰이 발급되었습니다.',
                    'coupons': [_row_to_coupon(r) for r in rows]}), 201


# ── 매장 이력 ─────────────────────────────────────────────────────────────────

@coupon_bp.route('/api/facilities/<int:fid>/coupons', methods=['GET'])
@require_facility_actor(roles=['owner', 'admin'])
def list_facility_coupons(fid):
    """매장 쿠폰 이력. 필터: ``?user_id=N``, ``?status=active|used|expired``."""
    account_id = g.auth['owner_account_id']
    user_id  = request.args.get('user_id', type=int)
    status   = request.args.get('status')
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    if user_id:
        rows = db.execute(
            "SELECT * FROM coupons WHERE facility_id=? AND user_id=? ORDER BY id DESC",
            (fid, user_id)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM coupons WHERE facility_id=? ORDER BY id DESC", (fid,)
        ).fetchall()
    db.close()

    out = [_row_to_coupon(r) for r in rows]
    if status in ('active', 'used', 'expired'):
        out = [c for c in out if c['status'] == status]
    return jsonify({'success': True, 'facility_id': fid, 'coupons': out})


# ── 수정 / 회수 ───────────────────────────────────────────────────────────────

@coupon_bp.route('/api/coupons/<int:cid>', methods=['PATCH'])
@require_facility_actor(roles=['owner', 'admin'])
def update_coupon(cid):
    """쿠폰 메타 수정 (title/benefit/expires_at). 사용 완료된 쿠폰은 변경 불가."""
    account_id = g.auth['owner_account_id']
    data = request.get_json(silent=True) or {}
    db = get_db()
    row = db.execute(
        """SELECT c.* FROM coupons c
           JOIN facilities f ON c.facility_id = f.id
           WHERE c.id=? AND f.owner_id=?""",
        (cid, account_id)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '쿠폰을 찾을 수 없습니다.'}), 404
    if row['used']:
        db.close()
        return jsonify({'success': False, 'message': '이미 사용된 쿠폰은 수정할 수 없습니다.'}), 409

    sets, vals = [], []
    if 'title' in data:
        v = (data['title'] or '').strip()
        if not v:
            db.close()
            return jsonify({'success': False,
                            'message': 'title은 비울 수 없습니다.'}), 400
        sets.append('title=?'); vals.append(v)
    if 'benefit' in data:
        sets.append('benefit=?')
        vals.append((data['benefit'] or '').strip() or None)
    if 'expires_at' in data:
        exp = (data['expires_at'] or '').strip() or None
        if exp:
            try:
                datetime.fromisoformat(exp)
            except ValueError:
                db.close()
                return jsonify({'success': False,
                                'message': 'expires_at은 ISO 8601 형식이어야 합니다.'}), 400
        sets.append('expires_at=?'); vals.append(exp)
    if not sets:
        db.close()
        return jsonify({'success': False, 'message': '수정할 필드가 없습니다.'}), 400

    vals.append(cid)
    db.execute(f"UPDATE coupons SET {', '.join(sets)} WHERE id=?", vals)
    new_row = db.execute("SELECT * FROM coupons WHERE id=?", (cid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '쿠폰이 수정되었습니다.',
                    'coupon': _row_to_coupon(new_row)})


@coupon_bp.route('/api/coupons/<int:cid>', methods=['DELETE'])
@require_facility_actor(roles=['owner', 'admin'])
def revoke_coupon(cid):
    """쿠폰 회수 (hard delete). 사용된 쿠폰도 삭제 가능 (이력 보존이 필요하면
    delete 대신 별도 archive 테이블 — 향후)."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    cur = db.execute(
        """DELETE FROM coupons
           WHERE id=? AND facility_id IN (SELECT id FROM facilities WHERE owner_id=?)""",
        (cid, account_id)
    )
    db.commit()
    affected = cur.rowcount
    db.close()
    if affected == 0:
        return jsonify({'success': False, 'message': '쿠폰을 찾을 수 없습니다.'}), 404
    return jsonify({'success': True, 'message': '쿠폰이 회수되었습니다.'})


# ── 사용 처리 ─────────────────────────────────────────────────────────────────

@coupon_bp.route('/api/coupons/<int:cid>/use', methods=['POST'])
@require_facility_actor(roles=['owner', 'admin', 'staff'])
def use_coupon(cid):
    """쿠폰 사용 처리. 직원도 가능 (QR 스캔 / 수동 처리).

    멱등하지 않음 — 재호출 시 409. 이미 만료된 쿠폰은 410.
    """
    account_id = g.auth['owner_account_id']
    actor_role = g.auth['actor_role']
    actor_id   = g.auth['user_id']
    db = get_db()
    row = db.execute(
        """SELECT c.* FROM coupons c
           JOIN facilities f ON c.facility_id = f.id
           WHERE c.id=? AND f.owner_id=?""",
        (cid, account_id)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '쿠폰을 찾을 수 없습니다.'}), 404
    if row['used']:
        db.close()
        return jsonify({'success': False, 'message': '이미 사용된 쿠폰입니다.'}), 409
    if row['expires_at'] and datetime.utcnow() > datetime.fromisoformat(row['expires_at']):
        db.close()
        return jsonify({'success': False, 'message': '만료된 쿠폰입니다.'}), 410

    db.execute(
        """UPDATE coupons SET
             used=1, used_at=datetime('now'),
             used_by_actor_role=?, used_by_actor_id=?
           WHERE id=?""",
        (actor_role, actor_id, cid)
    )
    new_row = db.execute("SELECT * FROM coupons WHERE id=?", (cid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '쿠폰이 사용되었습니다.',
                    'coupon': _row_to_coupon(new_row)})


# ── 사용자 본인 쿠폰함 ────────────────────────────────────────────────────────

@coupon_bp.route('/api/users/me/coupons', methods=['GET'])
@require_auth(sub_type='user')
def my_coupons():
    """본인 쿠폰함. ``?status=active|used|expired|all`` (기본=active)."""
    user_id = g.auth['user_id']
    status  = request.args.get('status', 'active')
    db = get_db()
    rows = db.execute(
        """SELECT c.*, f.name AS facility_name
           FROM coupons c
           JOIN facilities f ON c.facility_id = f.id
           WHERE c.user_id=?
           ORDER BY c.id DESC""",
        (user_id,)
    ).fetchall()
    db.close()
    out = []
    for r in rows:
        c = _row_to_coupon(r)
        c['facility_name'] = r['facility_name']
        out.append(c)
    if status != 'all':
        if status not in ('active', 'used', 'expired'):
            return jsonify({'success': False,
                            'message': "status는 'active'/'used'/'expired'/'all' 중 하나여야 합니다."}), 400
        out = [c for c in out if c['status'] == status]
    return jsonify({'success': True, 'coupons': out})
