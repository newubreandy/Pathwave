from datetime import datetime
from flask import Blueprint, request, jsonify, g
from models.database import get_db
from models.crypto import encrypt_secret, decrypt_secret
from routes.auth import require_facility_actor

beacon_bp = Blueprint('beacon', __name__, url_prefix='/api/beacon')


def _ensure_facility_owned(db, facility_id: int, account_id: int) -> bool:
    """``facility_id``가 ``account_id``의 **활성** 소유 매장인지 확인."""
    row = db.execute(
        "SELECT owner_id FROM facilities WHERE id=? AND active=1", (facility_id,)
    ).fetchone()
    return bool(row and row['owner_id'] == account_id)


@beacon_bp.route('/handshake', methods=['POST'])
def handshake():
    """BLE 핸드셰이크 핵심 API
    Flutter 앱이 BLE로 감지한 UUID를 전송하면
    서버가 해당 시설의 암호화된 WiFi 프로필을 반환.
    """
    data = request.get_json(silent=True) or {}
    uuid = (data.get('uuid') or '').strip()
    rssi = data.get('rssi')       # 수신 신호 강도 (참고용 로깅)
    user_id = data.get('user_id') # 로그인된 사용자

    if not uuid:
        return jsonify({'success': False, 'message': 'UUID가 필요합니다.'}), 400

    db = get_db()

    # 비콘 조회
    beacon = db.execute(
        "SELECT id, facility_id, status FROM beacons WHERE uuid=?", (uuid,)
    ).fetchone()

    if not beacon:
        db.close()
        return jsonify({'success': False, 'message': '등록되지 않은 비콘입니다.'}), 404

    if beacon['status'] != 'active':
        db.close()
        return jsonify({'success': False, 'message': '현재 서비스 중인 비콘이 아닙니다.'}), 403

    facility_id = beacon['facility_id']

    # 시설 정보 조회
    facility = db.execute(
        "SELECT id, name, address, description, image_url FROM facilities WHERE id=? AND active=1",
        (facility_id,)
    ).fetchone()

    if not facility:
        db.close()
        return jsonify({'success': False, 'message': '시설 정보를 찾을 수 없습니다.'}), 404

    # WiFi 프로필 조회
    wifi = db.execute(
        "SELECT ssid, password FROM wifi_profiles WHERE facility_id=? AND active=1 LIMIT 1",
        (facility_id,)
    ).fetchone()

    if not wifi:
        db.close()
        return jsonify({'success': False, 'message': 'WiFi 프로필이 등록되지 않았습니다.'}), 404

    # 접속 로그 기록
    if user_id:
        db.execute(
            "INSERT INTO user_wifi_logs (user_id, facility_id) VALUES (?,?)",
            (user_id, facility_id)
        )
        db.commit()

    db.close()

    return jsonify({
        'success': True,
        'facility': {
            'id':          dict(facility)['id'],
            'name':        dict(facility)['name'],
            'address':     dict(facility)['address'],
            'description': dict(facility)['description'],
            'image_url':   dict(facility)['image_url'],
        },
        'wifi': {
            'ssid':     wifi['ssid'],
            'password': decrypt_secret(wifi['password']),  # AES-GCM 복호화
        }
    })


@beacon_bp.route('/wifi', methods=['POST'])
@require_facility_actor(roles=['owner', 'admin'])
def register_wifi():
    """시설 WiFi 프로필 등록/교체 (시설 사장님 전용). SRS FR-WIFI-001.

    비밀번호는 AES-256-GCM으로 암호화해 저장한다.
    """
    account_id  = g.auth['owner_account_id']
    data        = request.get_json(silent=True) or {}
    facility_id = data.get('facility_id')
    ssid        = (data.get('ssid')     or '').strip()
    password    = data.get('password')  or ''

    if not facility_id or not ssid or not password:
        return jsonify({'success': False, 'message': 'facility_id, ssid, password는 필수입니다.'}), 400

    db = get_db()
    if not _ensure_facility_owned(db, facility_id, account_id):
        db.close()
        return jsonify({'success': False, 'message': '해당 시설에 권한이 없습니다.'}), 403

    enc = encrypt_secret(password)
    db.execute('UPDATE wifi_profiles SET active=0 WHERE facility_id=?', (facility_id,))
    db.execute(
        """INSERT INTO wifi_profiles (facility_id, ssid, password, active)
           VALUES (?,?,?,1)""",
        (facility_id, ssid, enc),
    )
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': 'WiFi 프로필이 등록되었습니다.'})


@beacon_bp.route('/status', methods=['GET'])
@require_facility_actor(roles=['owner', 'admin'])
def beacon_status():
    """비콘 상태 목록 (시설 사장님 전용 — 본인 소유 비콘만)."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    beacons = db.execute("""
        SELECT b.id, b.serial_no, b.uuid, b.status, b.battery_pct,
               f.name as facility_name, f.id as facility_id
        FROM beacons b
        JOIN facilities f ON b.facility_id = f.id
        WHERE f.owner_id = ? AND f.active = 1
        ORDER BY b.id DESC
    """, (account_id,)).fetchall()
    db.close()

    return jsonify({
        'success': True,
        'beacons': [dict(row) for row in beacons]
    })


@beacon_bp.route('/register', methods=['POST'])
@require_facility_actor(roles=['owner', 'admin'])
def register_beacon():
    """비콘 등록 (시설 사장님 전용 — 본인 소유 시설만)."""
    account_id = g.auth['owner_account_id']
    data        = request.get_json(silent=True) or {}
    serial_no   = (data.get('serial_no')   or '').strip()
    uuid        = (data.get('uuid')        or '').strip()
    facility_id = data.get('facility_id')
    firmware    = (data.get('firmware_ver') or '').strip()

    if not serial_no or not uuid:
        return jsonify({'success': False, 'message': 'serial_no와 uuid는 필수입니다.'}), 400

    db = get_db()
    if facility_id and not _ensure_facility_owned(db, facility_id, account_id):
        db.close()
        return jsonify({'success': False, 'message': '해당 시설에 권한이 없습니다.'}), 403
    try:
        db.execute(
            """INSERT INTO beacons (serial_no, uuid, facility_id, firmware_ver, status)
               VALUES (?,?,?,?,?)""",
            (serial_no, uuid, facility_id, firmware,
             'active' if facility_id else 'inventory')
        )
        db.commit()
    except Exception as e:
        db.close()
        return jsonify({'success': False, 'message': f'등록 실패: {str(e)}'}), 409
    db.close()

    return jsonify({'success': True, 'message': '비콘이 등록되었습니다.'})
