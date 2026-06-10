"""금지어 관리 라우트 (2026-06-09).

DB ``banned_words`` 테이블 — 슈퍼어드민이 욕설/성적/도박/불법/광고 등
금지어를 등록·삭제. PathWave (매장명/리뷰/채팅) + woorichat (프로필/채팅)
공통 사용.

- GET    /api/admin/banned-words           목록
- POST   /api/admin/banned-words           등록
- PATCH  /api/admin/banned-words/<id>      수정
- DELETE /api/admin/banned-words/<id>      삭제

severity: 'block' = 차단, 'warn' = 경고 노출
kind: 'profanity' | 'sexual' | 'gambling' | 'illegal' | 'ads' | 'general'
"""
from flask import Blueprint, request, jsonify, g

from models.database import get_db
from routes.auth import require_super_admin


banned_words_bp = Blueprint('banned_words', __name__)


def _row(r):
    return {
        'id': r['id'],
        'word': r['word'],
        'kind': r['kind'],
        'severity': r['severity'],
        'note': r['note'],
        'created_at': r['created_at'],
    }


@banned_words_bp.route('/api/admin/banned-words', methods=['GET'])
@require_super_admin()
def list_banned_words():
    """전체 금지어 목록 (검색 + kind 필터)."""
    q = (request.args.get('q') or '').strip()
    kind = (request.args.get('kind') or '').strip()
    sql = 'SELECT * FROM banned_words WHERE 1=1'
    params = []
    if q:
        sql += ' AND word LIKE ?'
        params.append(f'%{q}%')
    if kind:
        sql += ' AND kind = ?'
        params.append(kind)
    sql += ' ORDER BY kind, word'
    db = get_db()
    rows = db.execute(sql, params).fetchall()
    db.close()
    return jsonify({'success': True, 'count': len(rows),
                    'items': [_row(r) for r in rows]})


@banned_words_bp.route('/api/admin/banned-words', methods=['POST'])
@require_super_admin()
def create_banned_word():
    body = request.get_json(silent=True) or {}
    word = (body.get('word') or '').strip()
    if not word:
        return jsonify({'success': False, 'message': '금지어를 입력하세요.'}), 400
    kind = (body.get('kind') or 'general').strip()
    severity = (body.get('severity') or 'block').strip()
    note = (body.get('note') or '').strip() or None
    admin_id = g.auth.get('admin_id') if hasattr(g, 'auth') else None
    db = get_db()
    try:
        cur = db.execute(
            'INSERT INTO banned_words (word, kind, severity, note, created_by) '
            'VALUES (?, ?, ?, ?, ?)',
            (word, kind, severity, note, admin_id)
        )
        db.commit()
        new_id = cur.lastrowid
        r = db.execute('SELECT * FROM banned_words WHERE id=?', (new_id,)).fetchone()
        db.close()
        return jsonify({'success': True, 'item': _row(r)}), 201
    except Exception as e:
        db.close()
        msg = str(e)
        if 'UNIQUE' in msg.upper():
            return jsonify({'success': False, 'message': '이미 등록된 금지어입니다.'}), 409
        return jsonify({'success': False, 'message': msg}), 500


@banned_words_bp.route('/api/admin/banned-words/<int:wid>', methods=['PATCH'])
@require_super_admin()
def update_banned_word(wid):
    body = request.get_json(silent=True) or {}
    db = get_db()
    r = db.execute('SELECT * FROM banned_words WHERE id=?', (wid,)).fetchone()
    if not r:
        db.close()
        return jsonify({'success': False, 'message': '금지어를 찾을 수 없습니다.'}), 404
    word = (body.get('word') or r['word']).strip()
    kind = (body.get('kind') or r['kind']).strip()
    severity = (body.get('severity') or r['severity']).strip()
    note = body.get('note', r['note'])
    db.execute(
        'UPDATE banned_words SET word=?, kind=?, severity=?, note=? WHERE id=?',
        (word, kind, severity, note, wid)
    )
    db.commit()
    r = db.execute('SELECT * FROM banned_words WHERE id=?', (wid,)).fetchone()
    db.close()
    return jsonify({'success': True, 'item': _row(r)})


@banned_words_bp.route('/api/admin/banned-words/<int:wid>', methods=['DELETE'])
@require_super_admin()
def delete_banned_word(wid):
    db = get_db()
    cur = db.execute('DELETE FROM banned_words WHERE id=?', (wid,))
    db.commit()
    db.close()
    if cur.rowcount == 0:
        return jsonify({'success': False, 'message': '금지어를 찾을 수 없습니다.'}), 404
    return jsonify({'success': True})
