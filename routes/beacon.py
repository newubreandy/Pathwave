from datetime import datetime
from flask import Blueprint, request, jsonify
from models.database import get_db

beacon_bp = Blueprint('beacon', __name__, url_prefix='/api/beacon')


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
            'password': wifi['password'],  # TODO: AES 복호화 후 전송
        }
    })


@beacon_bp.route('/status', methods=['GET'])
def beacon_status():
    """비콘 상태 목록 (Admin용)"""
    db = get_db()
    beacons = db.execute("""
        SELECT b.id, b.serial_no, b.uuid, b.status, b.battery_pct,
               f.name as facility_name
        FROM beacons b
        LEFT JOIN facilities f ON b.facility_id = f.id
        ORDER BY b.id DESC
    """).fetchall()
    db.close()

    return jsonify({
        'success': True,
        'beacons': [dict(row) for row in beacons]
    })


@beacon_bp.route('/register', methods=['POST'])
def register_beacon():
    """비콘 등록 (Admin용)"""
    data        = request.get_json(silent=True) or {}
    serial_no   = (data.get('serial_no')   or '').strip()
    uuid        = (data.get('uuid')        or '').strip()
    facility_id = data.get('facility_id')
    firmware    = (data.get('firmware_ver') or '').strip()

    if not serial_no or not uuid:
        return jsonify({'success': False, 'message': 'serial_no와 uuid는 필수입니다.'}), 400

    db = get_db()
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
