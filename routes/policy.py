"""정책 본문 + 동의 메타데이터 + 운영자 약관 관리 (PR #46).

본문 우선순위: DB ``policies`` 테이블 → ``static/policies/{kind}.{lang}.md`` 파일.
운영자(super_admin) 가 admin-web 에서 새 버전 발행/예약 → 적용일 도달 시
회원에게 자동 메일 공지.

엔드포인트
---------
공개:
  GET  /api/policies                      — 동의 항목 메타 + 현재 버전
  GET  /api/policies/<kind>               — 현재 시행 본문
  GET  /api/policies/<kind>/versions      — 모든 버전 목록 (이전 버전 보기)
  GET  /api/policies/<kind>/versions/<v>  — 특정 버전 본문

운영자 (super_admin):
  GET    /api/admin/policies                       — 모든 kind 의 현재 버전 + pending
  POST   /api/admin/policies                       — 새 버전 작성/예약
  PATCH  /api/admin/policies/<id>                  — 미시행 버전 수정
  DELETE /api/admin/policies/<id>                  — 미시행 버전 삭제
  POST   /api/admin/policies/<id>/notify           — 적용일 도달 시 이메일 공지 1회 발송
"""
from datetime import datetime

from flask import Blueprint, g, jsonify, request

from models.consent import CONSENT_KINDS, VALID_KINDS
from models.database import get_db
from models.email_provider import get_email_provider
from models.policy_store import (
    delete as policy_delete,
    get_active,
    get_by_id,
    insert as policy_insert,
    list_all_active_kinds,
    list_pending,
    list_versions,
    mark_email_notified,
    update as policy_update,
)
from routes.auth import require_super_admin

policy_bp = Blueprint('policy', __name__)

KIND_LABELS = {
    'age14':       '만 14세 이상입니다',
    'terms':       '서비스 이용약관 동의',
    'privacy':     '개인정보 수집·이용 동의',
    'location':    '위치 정보 이용 동의',
    'camera':      '카메라 접근 동의',
    'storage':     '저장공간 접근 동의',
    'push':        '푸시 알림 수신 동의',
    'marketing':   '마케팅 정보 수신 동의',
    'third_party': '제3자 정보 제공 동의',
}


# ════════════════════════════════════════════════════════════════════════════
#                          공개 (가입/조회)
# ════════════════════════════════════════════════════════════════════════════

@policy_bp.route('/api/policies', methods=['GET'])
def list_policies():
    """전체 동의 항목 메타 + 현재 시행 버전. 가입 동의 화면용."""
    sub_type = (request.args.get('sub_type') or 'user').strip().lower()
    lang = (request.args.get('lang') or 'ko').strip().lower()
    db = get_db()
    try:
        items = []
        for kind, meta in CONSENT_KINDS.items():
            active = get_active(db, kind, lang)
            items.append({
                'kind':     kind,
                'label':    KIND_LABELS.get(kind, kind),
                'required': sub_type in meta['required_for'],
                'version':  active['version'],
                'effective_at': active.get('effective_at'),
            })
        return jsonify({'success': True, 'sub_type': sub_type, 'items': items})
    finally:
        db.close()


@policy_bp.route('/api/policies/<kind>', methods=['GET'])
def get_policy(kind: str):
    """현재 시행 정책 본문."""
    if kind not in VALID_KINDS:
        return jsonify({'success': False, 'message': '알 수 없는 정책 항목입니다.'}), 404
    lang = (request.args.get('lang') or 'ko').strip().lower()
    db = get_db()
    try:
        active = get_active(db, kind, lang)
        return jsonify({
            'success': True,
            'kind':    kind,
            'label':   KIND_LABELS.get(kind, kind),
            'lang':    lang,
            'version': active['version'],
            'title':   active.get('title'),
            'body':    active['body'],
            'effective_at': active.get('effective_at'),
            'change_log':   active.get('change_log'),
            'needs_content': active.get('needs_content', False),
            'source':  active.get('source', 'db'),
        })
    finally:
        db.close()


@policy_bp.route('/api/policies/<kind>/versions', methods=['GET'])
def list_policy_versions(kind: str):
    """이전 버전 보기 — 모든 버전 (시행/예약 모두)."""
    if kind not in VALID_KINDS:
        return jsonify({'success': False, 'message': '알 수 없는 정책 항목입니다.'}), 404
    lang = (request.args.get('lang') or 'ko').strip().lower()
    db = get_db()
    try:
        rows = list_versions(db, kind, lang)
        # 본문 미포함 (목록은 가벼워야 함)
        items = [{
            'id':           r['id'],
            'version':      r['version'],
            'title':        r['title'],
            'effective_at': r['effective_at'],
            'change_log':   r['change_log'],
        } for r in rows]
        return jsonify({'success': True, 'kind': kind, 'lang': lang, 'versions': items})
    finally:
        db.close()


@policy_bp.route('/api/policies/<kind>/versions/<int:pid>', methods=['GET'])
def get_policy_version(kind: str, pid: int):
    """특정 버전 본문 (이전 버전 보기 클릭 시)."""
    db = get_db()
    try:
        row = get_by_id(db, pid)
        if not row or row['kind'] != kind:
            return jsonify({'success': False, 'message': '해당 버전이 없습니다.'}), 404
        return jsonify({'success': True, **row})
    finally:
        db.close()


# ════════════════════════════════════════════════════════════════════════════
#                          운영자 (super_admin)
# ════════════════════════════════════════════════════════════════════════════

@policy_bp.route('/api/admin/policies', methods=['GET'])
@require_super_admin()
def admin_list_policies():
    """모든 kind 의 현재 시행 버전 + 예약(pending) 버전."""
    lang = (request.args.get('lang') or 'ko').strip().lower()
    db = get_db()
    try:
        active = list_all_active_kinds(db, lang)
        pending = list_pending(db)
        return jsonify({
            'success': True,
            'lang': lang,
            'active': [{**a, 'label': KIND_LABELS.get(a['kind'], a['kind'])} for a in active],
            'pending': pending,
        })
    finally:
        db.close()


@policy_bp.route('/api/admin/policies', methods=['POST'])
@require_super_admin()
def admin_create_policy():
    """새 정책 버전 작성 또는 예약.

    body: {kind, lang?, version, title?, body, change_log?, effective_at}
      effective_at: ISO 8601. 과거 시각이면 즉시 시행.
    """
    data = request.get_json(silent=True) or {}
    kind = (data.get('kind') or '').strip()
    if kind not in VALID_KINDS:
        return jsonify({'success': False,
                        'message': f"kind 는 {sorted(VALID_KINDS)} 중 하나여야 합니다."}), 400
    lang = (data.get('lang') or 'ko').strip().lower()
    version = (data.get('version') or '').strip()
    title = (data.get('title') or '').strip() or None
    body = data.get('body') or ''
    change_log = (data.get('change_log') or '').strip() or None
    effective_at = (data.get('effective_at') or '').strip()

    if not version:
        return jsonify({'success': False, 'message': 'version 이 필요합니다.'}), 400
    if not body or not body.strip():
        return jsonify({'success': False, 'message': '본문을 입력해 주세요.'}), 400
    if not effective_at:
        return jsonify({'success': False, 'message': 'effective_at (시행 일시) 이 필요합니다.'}), 400

    db = get_db()
    try:
        # 같은 (kind, lang, version) 중복 검사
        if db.execute(
            "SELECT 1 FROM policies WHERE kind=? AND lang=? AND version=?",
            (kind, lang, version)
        ).fetchone():
            return jsonify({'success': False,
                            'message': '같은 버전이 이미 존재합니다.'}), 409

        pid = policy_insert(
            db, kind=kind, lang=lang, version=version, title=title,
            body=body, change_log=change_log, effective_at=effective_at,
            admin_id=g.auth['user_id'],
        )
        db.commit()
        row = get_by_id(db, pid)
        return jsonify({'success': True, 'policy': row}), 201
    finally:
        db.close()


@policy_bp.route('/api/admin/policies/<int:pid>', methods=['PATCH'])
@require_super_admin()
def admin_update_policy(pid: int):
    """미시행(effective_at > now) 버전만 수정 가능."""
    data = request.get_json(silent=True) or {}
    db = get_db()
    try:
        row = get_by_id(db, pid)
        if not row:
            return jsonify({'success': False, 'message': '정책을 찾을 수 없습니다.'}), 404
        if row['effective_at'] and row['effective_at'] <= datetime.utcnow().isoformat():
            return jsonify({'success': False,
                            'message': '이미 시행된 버전은 수정할 수 없습니다. 새 버전을 발행해 주세요.'}), 409

        ok = policy_update(
            db, pid,
            title=data.get('title'),
            body=data.get('body'),
            change_log=data.get('change_log'),
            effective_at=data.get('effective_at'),
        )
        if not ok:
            return jsonify({'success': False, 'message': '수정할 항목이 없습니다.'}), 400
        db.commit()
        return jsonify({'success': True, 'policy': get_by_id(db, pid)})
    finally:
        db.close()


@policy_bp.route('/api/admin/policies/<int:pid>', methods=['DELETE'])
@require_super_admin()
def admin_delete_policy(pid: int):
    """미시행 버전 삭제 (시행된 버전은 감사 보존을 위해 삭제 불가)."""
    db = get_db()
    try:
        row = get_by_id(db, pid)
        if not row:
            return jsonify({'success': False, 'message': '정책을 찾을 수 없습니다.'}), 404
        if row['effective_at'] and row['effective_at'] <= datetime.utcnow().isoformat():
            return jsonify({'success': False,
                            'message': '이미 시행된 버전은 삭제할 수 없습니다.'}), 409
        policy_delete(db, pid)
        db.commit()
        return jsonify({'success': True})
    finally:
        db.close()


@policy_bp.route('/api/admin/policies/<int:pid>/notify', methods=['POST'])
@require_super_admin()
def admin_notify_policy(pid: int):
    """정책 변경을 회원에게 메일로 일괄 공지.

    sub_type 필터:
      - 'user' / 'facility' / 'all'
    """
    data = request.get_json(silent=True) or {}
    target = (data.get('sub_type') or 'all').strip().lower()
    db = get_db()
    try:
        row = get_by_id(db, pid)
        if not row:
            return jsonify({'success': False, 'message': '정책을 찾을 수 없습니다.'}), 404
        if row['email_notified']:
            return jsonify({'success': False,
                            'message': '이미 공지 메일이 발송되었습니다.'}), 409

        # 대상 이메일 모집
        emails: list[str] = []
        if target in ('user', 'all'):
            user_rows = db.execute(
                "SELECT email FROM users WHERE deleted_at IS NULL"
            ).fetchall()
            emails.extend([r['email'] for r in user_rows if r['email']])
        if target in ('facility', 'all'):
            fac_rows = db.execute(
                "SELECT email FROM facility_accounts WHERE status='verified'"
            ).fetchall()
            emails.extend([r['email'] for r in fac_rows if r['email']])

        # 본문 — change_log 우선, 없으면 본문 첫 200자.
        kind_label = KIND_LABELS.get(row['kind'], row['kind'])
        summary = row.get('change_log') or (row['body'][:200] + '...')
        subject = f'[PathWave] {kind_label} 변경 안내 ({row["version"]})'
        html = (
            f'<h2>{kind_label} 변경 안내</h2>'
            f'<p>적용일: {row["effective_at"]}</p>'
            f'<p>변경 내역:</p>'
            f'<pre style="white-space:pre-wrap">{summary}</pre>'
            f'<p>자세한 본문은 앱 내 [설정 > 약관 보기] 또는 사장님 콘솔에서 확인하실 수 있습니다.</p>'
            f'<hr><p style="color:#888">트리거소프트 (triggersoft) PathWave 운영팀</p>'
        )
        text = f'{kind_label} 변경 안내 ({row["version"]})\n적용일: {row["effective_at"]}\n\n{summary}'

        provider = get_email_provider()
        sent, failed = 0, 0
        for to in emails:
            res = provider.send(to=to, subject=subject, html=html, text=text)
            if res.get('success'):
                sent += 1
            else:
                failed += 1

        mark_email_notified(db, pid)
        db.commit()
        return jsonify({
            'success': True,
            'message': f'{sent}건 발송, {failed}건 실패.',
            'sent': sent, 'failed': failed,
            'recipient_count': len(emails),
            'provider': provider.name,
        })
    finally:
        db.close()
