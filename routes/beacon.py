from datetime import datetime, timedelta
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

    # 접속 로그 기록 + 자동 스탬프 적립 시도
    granted_stamp = None
    auto_stamp_skipped_reason = None
    if user_id:
        db.execute(
            "INSERT INTO user_wifi_logs (user_id, facility_id) VALUES (?,?)",
            (user_id, facility_id)
        )
        granted_stamp, auto_stamp_skipped_reason = _maybe_grant_auto_stamp(
            db, facility_id, int(user_id)
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
        },
        'granted_stamp': granted_stamp,
        'auto_stamp_skipped_reason': auto_stamp_skipped_reason,
    })


def _maybe_grant_auto_stamp(db, facility_id: int, user_id: int):
    """``stamp_policies.auto_stamp_enabled``가 켜져 있고 쿨다운 안 지났으면
    스탬프 1개 자동 적립. (granted_stamp, skipped_reason) 둘 중 하나만 채워짐.

    skipped_reason 값:
      - 'no_active_policy'        활성 정책 없음
      - 'auto_stamp_disabled'     정책에서 자동 적립 OFF
      - 'cooldown'                직전 적립 후 쿨다운 미경과
    """
    policy = db.execute(
        "SELECT * FROM stamp_policies WHERE facility_id=? AND active=1",
        (facility_id,)
    ).fetchone()
    if not policy:
        return None, 'no_active_policy'
    if not policy['auto_stamp_enabled']:
        return None, 'auto_stamp_disabled'

    cooldown_min = policy['auto_stamp_cooldown_minutes']
    cooldown_threshold = (datetime.utcnow()
                          - timedelta(minutes=cooldown_min)).strftime('%Y-%m-%d %H:%M:%S')
    last = db.execute(
        """SELECT created_at FROM stamps
           WHERE facility_id=? AND user_id=? AND granted_by_actor_role='system'
           ORDER BY id DESC LIMIT 1""",
        (facility_id, user_id)
    ).fetchone()
    if last and last['created_at'] >= cooldown_threshold:
        return None, 'cooldown'

    expires_at = None
    if policy['expires_days']:
        expires_at = (datetime.utcnow()
                      + timedelta(days=policy['expires_days'])).isoformat()
    owner_id = db.execute(
        "SELECT owner_id FROM facilities WHERE id=?", (facility_id,)
    ).fetchone()['owner_id']

    cur = db.execute(
        """INSERT INTO stamps
             (facility_id, user_id, amount, note,
              granted_by_account_id, granted_by_actor_role, granted_by_actor_id,
              expires_at)
           VALUES (?,?,1,?,?,?,?,?)""",
        (facility_id, user_id, 'BLE 자동 적립',
         owner_id, 'system', None, expires_at)
    )
    return {'id': cur.lastrowid, 'amount': 1, 'expires_at': expires_at}, None


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
