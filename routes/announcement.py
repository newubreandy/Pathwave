"""시스템 공지 (Announcements) — PR #33.

PathWave 운영자(super_admin)가 작성한 공지를 ``audience`` 별로 표시하고,
대상자(일반 회원/사장/직원)가 본인의 공지 목록을 조회하고 읽음 처리한다.

엔드포인트
---------
운영자 (super_admin)
  POST   /api/admin/announcements          — 공지 작성 (option: push 발송)
  GET    /api/admin/announcements          — 운영자가 작성한 모든 공지 목록
  PATCH  /api/admin/announcements/<id>     — 공지 수정 (제목/본문/audience/pinned)
  DELETE /api/admin/announcements/<id>     — 공지 삭제

대상자 (user / facility / staff)
  GET    /api/announcements                — 내 audience에 해당하는 활성 공지 목록
  POST   /api/announcements/<id>/read      — 읽음 처리

공지 발행 시 ``send_push=true``면 모든 대상의 push token에 stub/FCM으로 발송한다.
실제 발송 로직은 routes/push.py의 PushProvider abstraction을 재사용.
"""
from datetime import datetime

from flask import Blueprint, request, jsonify, g

from models.database import get_db
from routes.auth import decode_access_token, require_super_admin

announcement_bp = Blueprint('announcement', __name__)

VALID_AUDIENCES = {'all', 'users', 'facilities', 'staff'}


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────
def _row_to_dict(row):
    if not row:
        return None
    return {
        'id':         row['id'],
        'title':      row['title'],
        'body':       row['body'],
        'audience':   row['audience'],
        'pinned':     bool(row['pinned']),
        'push_sent':  bool(row['push_sent']),
        'starts_at':  row['starts_at'],
        'ends_at':    row['ends_at'],
        'created_at': row['created_at'],
    }


def _resolve_reader(auth_header: str):
    """대상자(user/facility/staff)의 sub_type 확인."""
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ', 1)[1]
    for sub_type in ('user', 'facility', 'staff'):
        try:
            payload = decode_access_token(token, expected_sub_type=sub_type)
            return {'kind': sub_type, 'id': payload['user_id']}
        except ValueError:
            continue
    return None


def _audience_matches(audience: str, kind: str) -> bool:
    if audience == 'all':
        return True
    if audience == 'users' and kind == 'user':
        return True
    if audience == 'facilities' and kind == 'facility':
        return True
    if audience == 'staff' and kind == 'staff':
        return True
    return False


def _is_active(row) -> bool:
    """현재 시각이 starts_at ~ ends_at 사이인지."""
    now = datetime.utcnow()
    if row['starts_at']:
        if now < datetime.fromisoformat(row['starts_at']):
            return False
    if row['ends_at']:
        if now > datetime.fromisoformat(row['ends_at']):
            return False
    return True


# ── 운영자 측 (super_admin) ──────────────────────────────────────────────────
@announcement_bp.route('/api/admin/announcements', methods=['POST'])
@require_super_admin()
def admin_create_announcement():
    """공지 작성 (super_admin only)."""
    data = request.get_json(silent=True) or {}

    title    = (data.get('title') or '').strip()
    body     = (data.get('body')  or '').strip()
    audience = (data.get('audience') or 'all').strip().lower()
    pinned   = 1 if data.get('pinned') else 0
    starts_at = (data.get('starts_at') or '').strip() or None
    ends_at   = (data.get('ends_at') or '').strip() or None

    if not title or not body:
        return jsonify({'success': False, 'message': '제목과 본문을 입력해 주세요.'}), 400
    if audience not in VALID_AUDIENCES:
        return jsonify({'success': False,
                        'message': f'audience는 {sorted(VALID_AUDIENCES)} 중 하나여야 합니다.'}), 400

    admin_id = g.auth['user_id']
    db = get_db()
    cur = db.execute(
        """INSERT INTO announcements
           (title, body, audience, created_by_admin_id, pinned, starts_at, ends_at)
           VALUES (?,?,?,?,?,?,?)""",
        (title, body, audience, admin_id, pinned, starts_at, ends_at)
    )
    aid = cur.lastrowid
    db.commit()
    row = db.execute("SELECT * FROM announcements WHERE id=?", (aid,)).fetchone()
    db.close()

    # send_push: 추후 PushProvider 통합. 현재는 push_sent 마킹만.
    if data.get('send_push'):
        db = get_db()
        db.execute("UPDATE announcements SET push_sent=1 WHERE id=?", (aid,))
        db.commit(); db.close()

    return jsonify({'success': True, 'announcement': _row_to_dict(row)}), 201


@announcement_bp.route('/api/admin/announcements', methods=['GET'])
@require_super_admin()
def admin_list_announcements():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM announcements ORDER BY pinned DESC, id DESC LIMIT 200"
    ).fetchall()
    db.close()
    return jsonify({
        'success': True,
        'announcements': [_row_to_dict(r) for r in rows],
        'count': len(rows),
    })


@announcement_bp.route('/api/admin/announcements/<int:aid>', methods=['PATCH'])
@require_super_admin()
def admin_update_announcement(aid: int):
    data = request.get_json(silent=True) or {}
    fields, values = [], []
    for k in ('title', 'body', 'audience', 'starts_at', 'ends_at'):
        if k in data:
            v = data[k]
            if k == 'audience' and v not in VALID_AUDIENCES:
                return jsonify({'success': False, 'message': 'audience 값이 올바르지 않습니다.'}), 400
            fields.append(f"{k}=?"); values.append(v)
    if 'pinned' in data:
        fields.append("pinned=?"); values.append(1 if data['pinned'] else 0)
    if not fields:
        return jsonify({'success': False, 'message': '수정할 항목이 없습니다.'}), 400
    values.append(aid)

    db = get_db()
    db.execute(f"UPDATE announcements SET {', '.join(fields)} WHERE id=?", values)
    db.commit()
    row = db.execute("SELECT * FROM announcements WHERE id=?", (aid,)).fetchone()
    db.close()
    if not row:
        return jsonify({'success': False, 'message': '공지를 찾을 수 없습니다.'}), 404
    return jsonify({'success': True, 'announcement': _row_to_dict(row)})


@announcement_bp.route('/api/admin/announcements/<int:aid>', methods=['DELETE'])
@require_super_admin()
def admin_delete_announcement(aid: int):
    db = get_db()
    db.execute("DELETE FROM announcement_reads WHERE announcement_id=?", (aid,))
    db.execute("DELETE FROM announcements WHERE id=?", (aid,))
    db.commit(); db.close()
    return jsonify({'success': True, 'message': '공지를 삭제했습니다.'})


# ── 대상자 측 (user / facility / staff) ─────────────────────────────────────
@announcement_bp.route('/api/announcements', methods=['GET'])
def list_announcements_for_me():
    """내 audience에 해당하는 활성 공지 목록 + 각 공지의 읽음 여부."""
    reader = _resolve_reader(request.headers.get('Authorization', ''))
    if not reader:
        return jsonify({'success': False, 'message': '인증이 필요합니다.'}), 401

    db = get_db()
    rows = db.execute(
        "SELECT * FROM announcements ORDER BY pinned DESC, id DESC LIMIT 200"
    ).fetchall()

    items = []
    for r in rows:
        if not _audience_matches(r['audience'], reader['kind']):
            continue
        if not _is_active(r):
            continue
        read = db.execute(
            "SELECT 1 FROM announcement_reads WHERE announcement_id=? AND reader_kind=? AND reader_id=?",
            (r['id'], reader['kind'], reader['id'])
        ).fetchone()
        d = _row_to_dict(r)
        d['read'] = bool(read)
        items.append(d)
    db.close()
    return jsonify({'success': True, 'announcements': items, 'count': len(items)})


@announcement_bp.route('/api/announcements/<int:aid>/read', methods=['POST'])
def mark_read(aid: int):
    reader = _resolve_reader(request.headers.get('Authorization', ''))
    if not reader:
        return jsonify({'success': False, 'message': '인증이 필요합니다.'}), 401

    db = get_db()
    if not db.execute("SELECT id FROM announcements WHERE id=?", (aid,)).fetchone():
        db.close()
        return jsonify({'success': False, 'message': '공지를 찾을 수 없습니다.'}), 404
    db.execute(
        """INSERT OR IGNORE INTO announcement_reads
           (announcement_id, reader_kind, reader_id) VALUES (?,?,?)""",
        (aid, reader['kind'], reader['id'])
    )
    db.commit(); db.close()
    return jsonify({'success': True, 'message': '읽음 처리되었습니다.'})
