"""P-A (2026-05-29): 점주 서비스 신청 저장 — 비콘 프로비저닝 워크플로우.

점주가 설치위치 + WiFi(SSID/PW) + 기간을 신청 → service_requests + units 저장.
슈퍼어드민이 이후 인벤토리 비콘을 매칭·할당한다 (P-B).
설계: docs/pathwave_beacon_provisioning_design_2026-05-29.md

엔드포인트
---------
- POST /api/service-requests   (점주 owner) — 신청 생성 (units 포함)
- GET  /api/service-requests   (점주 owner) — 내 신청 목록 (WiFi 비번은 응답 제외)
"""
from __future__ import annotations

from flask import Blueprint, request, jsonify, g

from models.crypto import encrypt_secret
from models.database import get_db
from routes.auth import require_facility_actor

service_request_bp = Blueprint('service_request', __name__,
                               url_prefix='/api/service-requests')

_SERVICE_TYPES = {'wifi', 'event', 'notification', 'stamp'}


@service_request_bp.route('', methods=['POST'])
@require_facility_actor(roles=['owner'])
def create_request():
    """서비스 신청 생성. body: {service_type, note?, units:[{location_label, ssid,
    wifi_password, period_start, period_end}]}. WiFi 비번은 AES-GCM 암호화 저장."""
    account_id = g.auth['owner_account_id']
    data = request.get_json(silent=True) or {}
    service_type = (data.get('service_type') or 'wifi').strip().lower()
    if service_type not in _SERVICE_TYPES:
        return jsonify({'success': False,
                        'message': f'service_type 은 {sorted(_SERVICE_TYPES)} 중 하나여야 합니다.'}), 400
    note  = (data.get('note') or '').strip()
    units = data.get('units') or []
    if not isinstance(units, list):
        return jsonify({'success': False, 'message': 'units 는 배열이어야 합니다.'}), 400

    db = get_db()
    try:
        # 소유 매장 (1계정=1매장)
        fac = db.execute(
            "SELECT id FROM facilities WHERE owner_id=? AND active=1 ORDER BY id LIMIT 1",
            (account_id,)
        ).fetchone()
        facility_id = fac['id'] if fac else None

        cur = db.execute(
            """INSERT INTO service_requests
                 (facility_id, facility_account_id, service_type, status, note)
               VALUES (?,?,?,'pending',?)""",
            (facility_id, account_id, service_type, note or None)
        )
        rid = cur.lastrowid

        for u in units:
            if not isinstance(u, dict):
                continue
            loc  = (u.get('location_label') or '').strip() or None
            ssid = (u.get('ssid') or '').strip() or None
            pw   = u.get('wifi_password') or ''
            pw_enc = encrypt_secret(pw) if pw else None
            db.execute(
                """INSERT INTO service_request_units
                     (request_id, location_label, ssid, wifi_password_enc,
                      period_start, period_end, status)
                   VALUES (?,?,?,?,?,?, 'pending')""",
                (rid, loc, ssid, pw_enc,
                 (u.get('period_start') or None), (u.get('period_end') or None))
            )
        db.commit()
    finally:
        db.close()

    return jsonify({'success': True, 'request_id': rid,
                    'message': '서비스 신청이 접수되었습니다. 운영팀 검토 후 연락드립니다.'}), 201


def _row_to_request(db, r) -> dict:
    units = db.execute(
        """SELECT id, location_label, ssid, period_start, period_end, beacon_id, status
           FROM service_request_units WHERE request_id=? ORDER BY id""",
        (r['id'],)
    ).fetchall()
    # 보안: wifi_password_enc 는 응답에 포함하지 않는다 (슈퍼어드민 매칭 시 별도 복호화).
    return {
        'id':           r['id'],
        'facility_id':  r['facility_id'],
        'service_type': r['service_type'],
        'status':       r['status'],
        'note':         r['note'],
        'created_at':   r['created_at'],
        'units':        [dict(u) for u in units],
    }


@service_request_bp.route('', methods=['GET'])
@require_facility_actor(roles=['owner'])
def list_requests():
    """내(점주) 서비스 신청 목록."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    try:
        rows = db.execute(
            "SELECT * FROM service_requests WHERE facility_account_id=? ORDER BY id DESC",
            (account_id,)
        ).fetchall()
        out = [_row_to_request(db, r) for r in rows]
    finally:
        db.close()
    return jsonify({'success': True, 'requests': out})
