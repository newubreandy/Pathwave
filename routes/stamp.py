"""스탬프 정책/적립 API. SRS FR-STAMP-001/002.

엔드포인트
---------
- GET    /api/facilities/<fid>/stamp-policy      정책 조회 (all roles)
- PUT    /api/facilities/<fid>/stamp-policy      정책 upsert (owner+admin)
- DELETE /api/facilities/<fid>/stamp-policy      정책 비활성 (owner+admin)
- POST   /api/facilities/<fid>/stamps            스탬프 적립 (owner/admin/staff)
- GET    /api/facilities/<fid>/stamps            적립 이력 조회 (owner+admin)
- PATCH  /api/stamps/<id>                        수량 보정 (owner+admin)
- DELETE /api/stamps/<id>                        오적립 취소 (owner+admin)
- GET    /api/users/me/stamps                    앱 사용자 본인 현황 (sub_type='user')
"""
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, g

from models.database import get_db
from routes.auth import require_facility_actor, require_auth

stamp_bp = Blueprint('stamp', __name__)


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _owned_facility(db, fid: int, account_id: int) -> bool:
    return bool(db.execute(
        "SELECT 1 FROM facilities WHERE id=? AND owner_id=? AND active=1",
        (fid, account_id)
    ).fetchone())


def _row_to_policy(row) -> dict:
    return {
        'id':                 row['id'],
        'facility_id':        row['facility_id'],
        'reward_threshold':   row['reward_threshold'],
        'reward_description': row['reward_description'],
        'expires_days':       row['expires_days'],
        'design_image_url':   row['design_image_url'],
        'auto_stamp_enabled':           bool(row['auto_stamp_enabled']),
        'auto_stamp_cooldown_minutes':  row['auto_stamp_cooldown_minutes'],
        'reward_coupon_title':          row['reward_coupon_title'],
        'reward_coupon_benefit':        row['reward_coupon_benefit'],
        'reward_coupon_validity_days':  row['reward_coupon_validity_days'],
        'active':             bool(row['active']),
        'created_at':         row['created_at'],
        'updated_at':         row['updated_at'],
    }


def _row_to_stamp(row) -> dict:
    return {
        'id':           row['id'],
        'facility_id':  row['facility_id'],
        'user_id':      row['user_id'],
        'amount':       row['amount'],
        'note':         row['note'],
        'expires_at':   row['expires_at'],
        'granted_by': {
            'role':    row['granted_by_actor_role'],
            'actor_id': row['granted_by_actor_id'],
        },
        'created_at':   row['created_at'],
    }


# ── 정책 ──────────────────────────────────────────────────────────────────────

@stamp_bp.route('/api/facilities/<int:fid>/stamp-policy', methods=['GET'])
@require_facility_actor()
def get_policy(fid):
    """현재 활성 정책 조회. 없으면 null 반환."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    row = db.execute(
        "SELECT * FROM stamp_policies WHERE facility_id=? AND active=1",
        (fid,)
    ).fetchone()
    db.close()
    return jsonify({'success': True,
                    'facility_id': fid,
                    'policy': _row_to_policy(row) if row else None})


@stamp_bp.route('/api/facilities/<int:fid>/stamp-policy', methods=['PUT'])
@require_facility_actor(roles=['owner', 'admin'])
def upsert_policy(fid):
    """정책 upsert (active=1 row가 존재하면 갱신, 없으면 생성).

    body: {reward_threshold, reward_description, expires_days?, design_image_url?}
    """
    account_id = g.auth['owner_account_id']
    data = request.get_json(silent=True) or {}
    threshold = data.get('reward_threshold')
    description = (data.get('reward_description') or '').strip()
    expires_days = data.get('expires_days')
    design_url = (data.get('design_image_url') or '').strip() or None
    auto_stamp_enabled = bool(data.get('auto_stamp_enabled'))
    cooldown = data.get('auto_stamp_cooldown_minutes', 60)
    reward_coupon_title    = (data.get('reward_coupon_title')   or '').strip() or None
    reward_coupon_benefit  = (data.get('reward_coupon_benefit') or '').strip() or None
    reward_coupon_validity = data.get('reward_coupon_validity_days')
    if reward_coupon_validity is not None:
        if not isinstance(reward_coupon_validity, int) or reward_coupon_validity < 1:
            return jsonify({'success': False,
                            'message': 'reward_coupon_validity_days는 1 이상의 정수여야 합니다.'}), 400

    if not isinstance(threshold, int) or threshold < 1:
        return jsonify({'success': False,
                        'message': 'reward_threshold는 1 이상의 정수여야 합니다.'}), 400
    if not description:
        return jsonify({'success': False,
                        'message': 'reward_description은 필수입니다.'}), 400
    if expires_days is not None:
        if not isinstance(expires_days, int) or expires_days < 1:
            return jsonify({'success': False,
                            'message': 'expires_days는 1 이상의 정수여야 합니다.'}), 400
    if not isinstance(cooldown, int) or cooldown < 1:
        return jsonify({'success': False,
                        'message': 'auto_stamp_cooldown_minutes는 1 이상의 정수여야 합니다.'}), 400

    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    existing = db.execute(
        "SELECT id FROM stamp_policies WHERE facility_id=? AND active=1",
        (fid,)
    ).fetchone()
    if existing:
        db.execute(
            """UPDATE stamp_policies SET
                 reward_threshold=?, reward_description=?,
                 expires_days=?, design_image_url=?,
                 auto_stamp_enabled=?, auto_stamp_cooldown_minutes=?,
                 reward_coupon_title=?, reward_coupon_benefit=?,
                 reward_coupon_validity_days=?,
                 updated_at=datetime('now')
               WHERE id=?""",
            (threshold, description, expires_days, design_url,
             1 if auto_stamp_enabled else 0, cooldown,
             reward_coupon_title, reward_coupon_benefit, reward_coupon_validity,
             existing['id'])
        )
        pid = existing['id']
    else:
        cur = db.execute(
            """INSERT INTO stamp_policies
                 (facility_id, reward_threshold, reward_description,
                  expires_days, design_image_url,
                  auto_stamp_enabled, auto_stamp_cooldown_minutes,
                  reward_coupon_title, reward_coupon_benefit,
                  reward_coupon_validity_days, active)
               VALUES (?,?,?,?,?,?,?,?,?,?,1)""",
            (fid, threshold, description, expires_days, design_url,
             1 if auto_stamp_enabled else 0, cooldown,
             reward_coupon_title, reward_coupon_benefit, reward_coupon_validity)
        )
        pid = cur.lastrowid
    row = db.execute("SELECT * FROM stamp_policies WHERE id=?", (pid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '스탬프 정책이 저장되었습니다.',
                    'policy': _row_to_policy(row)})


@stamp_bp.route('/api/facilities/<int:fid>/stamp-policy', methods=['DELETE'])
@require_facility_actor(roles=['owner', 'admin'])
def deactivate_policy(fid):
    """정책 비활성화 (active=0). 기존 적립은 보존."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    cur = db.execute(
        "UPDATE stamp_policies SET active=0 WHERE facility_id=? AND active=1",
        (fid,)
    )
    db.commit()
    affected = cur.rowcount
    db.close()
    if affected == 0:
        return jsonify({'success': False, 'message': '활성 정책이 없습니다.'}), 404
    return jsonify({'success': True, 'message': '정책이 비활성화되었습니다.'})


# ── 적립 ──────────────────────────────────────────────────────────────────────

def _calc_expires_at(db, fid: int) -> str | None:
    row = db.execute(
        "SELECT expires_days FROM stamp_policies WHERE facility_id=? AND active=1",
        (fid,)
    ).fetchone()
    days = row['expires_days'] if row else None
    if not days:
        return None
    return (datetime.utcnow() + timedelta(days=days)).isoformat()


@stamp_bp.route('/api/facilities/<int:fid>/stamps', methods=['POST'])
@require_facility_actor(roles=['owner', 'admin', 'staff'])
def grant_stamp(fid):
    """매장이 사용자에게 스탬프 적립. 직원도 가능 (FR-STAMP-002).

    body: {user_id, amount?(=1), note?}
    """
    account_id = g.auth['owner_account_id']
    actor_role = g.auth['actor_role']
    actor_id   = g.auth['user_id']
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    amount  = data.get('amount', 1)
    note    = (data.get('note') or '').strip() or None

    if not isinstance(user_id, int) or user_id < 1:
        return jsonify({'success': False, 'message': 'user_id가 필요합니다.'}), 400
    if not isinstance(amount, int) or amount < 1:
        return jsonify({'success': False,
                        'message': 'amount는 1 이상의 정수여야 합니다.'}), 400

    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    # user 존재 확인 (deleted 제외)
    if not db.execute(
        "SELECT 1 FROM users WHERE id=? AND deleted_at IS NULL", (user_id,)
    ).fetchone():
        db.close()
        return jsonify({'success': False, 'message': '대상 사용자를 찾을 수 없습니다.'}), 404

    expires_at = _calc_expires_at(db, fid)
    cur = db.execute(
        """INSERT INTO stamps
             (facility_id, user_id, amount, note,
              granted_by_account_id, granted_by_actor_role, granted_by_actor_id,
              expires_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (fid, user_id, amount, note,
         account_id, actor_role, actor_id, expires_at)
    )
    row = db.execute("SELECT * FROM stamps WHERE id=?", (cur.lastrowid,)).fetchone()

    # 임계치 도달 시 보상 쿠폰 자동 발급 (best-effort)
    from routes.beacon import _maybe_issue_reward_coupon
    granted_reward = _maybe_issue_reward_coupon(db, fid, user_id)
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '스탬프가 적립되었습니다.',
                    'stamp': _row_to_stamp(row),
                    'granted_reward_coupon': granted_reward}), 201


@stamp_bp.route('/api/facilities/<int:fid>/stamps', methods=['GET'])
@require_facility_actor(roles=['owner', 'admin'])
def list_stamps(fid):
    """매장의 스탬프 적립 이력 (필터: ?user_id=N)."""
    account_id = g.auth['owner_account_id']
    user_id = request.args.get('user_id', type=int)
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    if user_id:
        rows = db.execute(
            """SELECT * FROM stamps WHERE facility_id=? AND user_id=?
               ORDER BY id DESC""", (fid, user_id)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM stamps WHERE facility_id=? ORDER BY id DESC", (fid,)
        ).fetchall()
    db.close()
    return jsonify({'success': True,
                    'facility_id': fid,
                    'stamps': [_row_to_stamp(r) for r in rows]})


@stamp_bp.route('/api/stamps/<int:sid>', methods=['PATCH'])
@require_facility_actor(roles=['owner', 'admin'])
def adjust_stamp(sid):
    """스탬프 수량 보정 (note도 함께 수정 가능)."""
    account_id = g.auth['owner_account_id']
    data = request.get_json(silent=True) or {}
    db = get_db()
    row = db.execute(
        """SELECT s.* FROM stamps s
           JOIN facilities f ON s.facility_id = f.id
           WHERE s.id=? AND f.owner_id=?""",
        (sid, account_id)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False, 'message': '스탬프를 찾을 수 없습니다.'}), 404

    sets, vals = [], []
    if 'amount' in data:
        amt = data.get('amount')
        if not isinstance(amt, int) or amt < 1:
            db.close()
            return jsonify({'success': False,
                            'message': 'amount는 1 이상의 정수여야 합니다.'}), 400
        sets.append('amount=?'); vals.append(amt)
    if 'note' in data:
        sets.append('note=?')
        vals.append((data.get('note') or '').strip() or None)
    if not sets:
        db.close()
        return jsonify({'success': False, 'message': '수정할 필드가 없습니다.'}), 400

    vals.append(sid)
    db.execute(f"UPDATE stamps SET {', '.join(sets)} WHERE id=?", vals)
    new_row = db.execute("SELECT * FROM stamps WHERE id=?", (sid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '스탬프가 수정되었습니다.',
                    'stamp': _row_to_stamp(new_row)})


@stamp_bp.route('/api/stamps/<int:sid>', methods=['DELETE'])
@require_facility_actor(roles=['owner', 'admin'])
def delete_stamp(sid):
    """오적립 취소 (hard delete)."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    cur = db.execute(
        """DELETE FROM stamps
           WHERE id=? AND facility_id IN (SELECT id FROM facilities WHERE owner_id=?)""",
        (sid, account_id)
    )
    db.commit()
    affected = cur.rowcount
    db.close()
    if affected == 0:
        return jsonify({'success': False, 'message': '스탬프를 찾을 수 없습니다.'}), 404
    return jsonify({'success': True, 'message': '스탬프가 삭제되었습니다.'})


# ── 사용자 본인 현황 ──────────────────────────────────────────────────────────

@stamp_bp.route('/api/users/me/stamps', methods=['GET'])
@require_auth(sub_type='user')
def my_stamps():
    """앱 사용자 본인의 매장별 스탬프 합계 + 정책 정보."""
    user_id = g.auth['user_id']
    db = get_db()
    rows = db.execute("""
        SELECT s.facility_id, f.name AS facility_name,
               SUM(s.amount) AS total,
               p.reward_threshold, p.reward_description, p.expires_days
        FROM stamps s
        JOIN facilities f ON s.facility_id = f.id
        LEFT JOIN stamp_policies p
          ON p.facility_id = s.facility_id AND p.active = 1
        WHERE s.user_id=?
          AND (s.expires_at IS NULL OR s.expires_at > datetime('now'))
        GROUP BY s.facility_id
        ORDER BY total DESC
    """, (user_id,)).fetchall()
    db.close()
    out = []
    for r in rows:
        threshold = r['reward_threshold']
        total = r['total']
        out.append({
            'facility_id':        r['facility_id'],
            'facility_name':      r['facility_name'],
            'total_stamps':       total,
            'reward_threshold':   threshold,
            'reward_description': r['reward_description'],
            'expires_days':       r['expires_days'],
            'reward_available':   bool(threshold and total >= threshold),
        })
    return jsonify({'success': True, 'stamps_by_facility': out})
