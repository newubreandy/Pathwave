"""WiFi 프로필 + 비콘↔WiFi 매핑 통합 테스트.

라우트
------
- POST   /api/beacon/wifi                            (생성/교체, 비번 AES 암호화)
- GET    /api/facilities/<fid>/wifis                 (목록, ?include_password=1 평문 복호화)
- PATCH  /api/facilities/<fid>/wifis/<wid>           (부분 수정)
- DELETE /api/facilities/<fid>/wifis/<wid>           (삭제)
- GET    /api/facilities/<fid>/beacons/<bid>/wifis   (매핑 조회)
- PUT    /api/facilities/<fid>/beacons/<bid>/wifis   (매핑 일괄 교체)
- DELETE /api/facilities/<fid>/beacons/<bid>/wifis/<wpid>  (단일 매핑 해제)

검증 목적
---------
- 신규 DB 환경 회귀 방지
- 비번 AES-256-GCM 암호화 저장 + 복호화 응답
- legacy single-mode vs multi=true 토글
- 소유권 가드 (다른 매장 wifi 매핑 차단)
- 비콘 ↔ WiFi 매핑 일괄 교체 + priority
"""
import os
import sqlite3
import tempfile

import bcrypt

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name

import models.database as _dbmod  # noqa: E402


def _patched_get_db():
    conn = sqlite3.connect(os.environ['PATHWAVE_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


_dbmod.get_db = _patched_get_db

from app import app  # noqa: E402
from models.crypto import decrypt_secret  # noqa: E402
from models.rate_limit import limiter  # noqa: E402
from routes.auth import make_jwt  # noqa: E402

limiter.enabled = False
c = app.test_client()


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


# ── 픽스처 ──────────────────────────────────────────────────────────────────
def _seed_baseline() -> dict:
    """점주 + 매장 + 인벤토리 비콘 2개 (P-B 매칭 안 됨 상태)."""
    db = _dbmod.get_db(); cur = db.cursor()
    pw = bcrypt.hashpw(b'X!23456789', bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO facility_accounts
             (business_no, company_name, email, password, manager_name,
              verified, status, created_at)
           VALUES ('111-11-11111', 'Cafe', 'o@t.test', ?, 'Mgr', 1, 'verified',
                   datetime('now'))""",
        (pw,),
    )
    aid = cur.lastrowid
    cur.execute(
        """INSERT INTO facilities (name, owner_id, active, created_at)
           VALUES ('Cafe One', ?, 1, datetime('now'))""",
        (aid,),
    )
    fid = cur.lastrowid

    # 비콘은 facility 에 직접 활성 매핑 (테스트 단순화)
    cur.execute(
        """INSERT INTO beacons (serial_no, uuid, facility_id, status, battery_pct, firmware_ver)
           VALUES ('SN-1', 'AAAA0000000000000000000000000001', ?, 'active', 100, '1.0')""",
        (fid,),
    )
    bid1 = cur.lastrowid
    cur.execute(
        """INSERT INTO beacons (serial_no, uuid, facility_id, status, battery_pct, firmware_ver)
           VALUES ('SN-2', 'BBBB0000000000000000000000000001', ?, 'active', 100, '1.0')""",
        (fid,),
    )
    bid2 = cur.lastrowid

    # 다른 매장(소유 검증용)
    pw2 = bcrypt.hashpw(b'Y!23456789', bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO facility_accounts
             (business_no, company_name, email, password, manager_name,
              verified, status, created_at)
           VALUES ('999-99-99999', 'Other', 'x@t.test', ?, 'Mgr', 1, 'verified',
                   datetime('now'))""",
        (pw2,),
    )
    aid_other = cur.lastrowid
    cur.execute(
        """INSERT INTO facilities (name, owner_id, active, created_at)
           VALUES ('Other Cafe', ?, 1, datetime('now'))""",
        (aid_other,),
    )
    fid_other = cur.lastrowid

    db.commit(); db.close()
    return {'aid': aid, 'fid': fid, 'bid1': bid1, 'bid2': bid2,
            'aid_other': aid_other, 'fid_other': fid_other}


def _h(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _owner_token(account_id: int, facility_id: int) -> str:
    return make_jwt(account_id, 'o@t.test', 'access', 'facility',
                    {'facility_id': facility_id, 'role': 'owner',
                     'owner_account_id': account_id})


def _truncate_all():
    db = _dbmod.get_db()
    for t in (
        'beacon_wifi', 'wifi_profiles', 'beacons',
        'facilities', 'facility_accounts',
    ):
        try:
            db.execute(f'DELETE FROM {t}')
        except sqlite3.OperationalError:
            pass
    db.commit(); db.close()


# ══════════════════════════════════════════════════════════════════════════════
# A. WiFi 프로필 등록 + 암호화 + 목록
# ══════════════════════════════════════════════════════════════════════════════
def test_a_wifi_create_encrypt_list():
    print('\n── A. WiFi 등록 + 암호화 저장 + 목록 ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['aid'], ids['fid']))

    # 등록
    r = c.post('/api/beacon/wifi', headers=OH, json={
        'facility_id': ids['fid'],
        'ssid': 'PathWave_Cafe',
        'password': 'WiFiPass!23',
    })
    body = r.get_json()
    _ok('① 등록 200 + wifi_profile_id', r.status_code == 200 and 'wifi_profile_id' in body, body)
    wid = body['wifi_profile_id']

    # DB password 평문 아님 + 복호화 라운드트립
    db = _dbmod.get_db()
    row = db.execute("SELECT password FROM wifi_profiles WHERE id=?", (wid,)).fetchone()
    db.close()
    enc = row['password']
    _ok('② DB password 평문 아님 (암호화 저장)', enc != 'WiFiPass!23')
    _ok('③ 복호화 → 원문', decrypt_secret(enc) == 'WiFiPass!23')

    # 목록 (기본 — password 미포함)
    r = c.get(f"/api/facilities/{ids['fid']}/wifis", headers=OH)
    j = r.get_json()
    _ok('④ 목록 200 + 1건', r.status_code == 200 and len(j['wifis']) == 1, j)
    _ok('⑤ 기본 응답에 password 없음 (보안)', 'password' not in j['wifis'][0],
        j['wifis'][0])

    # 목록 — include_password=1 (owner)
    r = c.get(f"/api/facilities/{ids['fid']}/wifis?include_password=1", headers=OH)
    j = r.get_json()
    pw = j['wifis'][0].get('password')
    _ok('⑥ include_password=1 → 복호화 평문 반환',
        pw == 'WiFiPass!23', f'got password={pw!r}')


def test_a_wifi_multi_mode():
    print('\n── A2. multi=false vs true ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['aid'], ids['fid']))

    # 첫 등록
    c.post('/api/beacon/wifi', headers=OH, json={
        'facility_id': ids['fid'], 'ssid': 'A', 'password': 'p1XXXXXXX',
    })

    # multi=false → 기존 active 비활성
    c.post('/api/beacon/wifi', headers=OH, json={
        'facility_id': ids['fid'], 'ssid': 'B', 'password': 'p2XXXXXXX',
    })
    r = c.get(f"/api/facilities/{ids['fid']}/wifis", headers=OH)
    actives = [w for w in r.get_json()['wifis'] if w.get('active')]
    _ok('① multi 기본(false) — active=1 단 1건', len(actives) == 1)

    # multi=true → 기존 active 유지
    c.post('/api/beacon/wifi', headers=OH, json={
        'facility_id': ids['fid'], 'ssid': 'C', 'password': 'p3XXXXXXX',
        'multi': True,
    })
    r = c.get(f"/api/facilities/{ids['fid']}/wifis", headers=OH)
    actives = [w for w in r.get_json()['wifis'] if w.get('active')]
    _ok('② multi=true — 기존 + 신규 = active 2건', len(actives) == 2)


# ══════════════════════════════════════════════════════════════════════════════
# B. PATCH / DELETE
# ══════════════════════════════════════════════════════════════════════════════
def test_b_wifi_patch_delete():
    print('\n── B. WiFi PATCH (ssid/password 갱신) + DELETE ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['aid'], ids['fid']))

    wid = c.post('/api/beacon/wifi', headers=OH, json={
        'facility_id': ids['fid'], 'ssid': 'OldName', 'password': 'old!1234',
    }).get_json()['wifi_profile_id']

    # PATCH ssid
    r = c.patch(f"/api/facilities/{ids['fid']}/wifis/{wid}", headers=OH,
                json={'ssid': 'NewName'})
    _ok('① PATCH ssid 200', r.status_code == 200, r.get_json())

    # PATCH password 갱신 → DB 재암호화 확인
    r = c.patch(f"/api/facilities/{ids['fid']}/wifis/{wid}", headers=OH,
                json={'password': 'new!5678'})
    _ok('② PATCH password 200', r.status_code == 200)
    db = _dbmod.get_db()
    enc = db.execute("SELECT password FROM wifi_profiles WHERE id=?", (wid,)).fetchone()['password']
    db.close()
    _ok('③ 새 password 복호화 = new!5678', decrypt_secret(enc) == 'new!5678')

    # DELETE (soft — active=0, 비콘 매핑 보존)
    r = c.delete(f"/api/facilities/{ids['fid']}/wifis/{wid}", headers=OH)
    _ok('④ DELETE 200 (soft delete)', r.status_code == 200, r.get_json())
    r = c.get(f"/api/facilities/{ids['fid']}/wifis", headers=OH)
    wifis = r.get_json()['wifis']
    _ok('⑤ 삭제 후 row 보존 + active=False',
        len(wifis) == 1 and not wifis[0].get('active'), wifis)


# ══════════════════════════════════════════════════════════════════════════════
# C. 등록 검증 가드
# ══════════════════════════════════════════════════════════════════════════════
def test_c_wifi_create_guards():
    print('\n── C. 등록 검증 가드 ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['aid'], ids['fid']))

    # 필수 필드 누락
    r = c.post('/api/beacon/wifi', headers=OH,
               json={'facility_id': ids['fid'], 'ssid': 'X'})
    _ok('① password 누락 → 400', r.status_code == 400, r.get_json())

    # 잘못된 scope
    r = c.post('/api/beacon/wifi', headers=OH, json={
        'facility_id': ids['fid'], 'ssid': 'X', 'password': 'p!XXXXXXX',
        'scope': 'global',
    })
    _ok('② 잘못된 scope → 400', r.status_code == 400)

    # 잘못된 credential_mode
    r = c.post('/api/beacon/wifi', headers=OH, json={
        'facility_id': ids['fid'], 'ssid': 'X', 'password': 'p!XXXXXXX',
        'credential_mode': 'magic',
    })
    _ok('③ 잘못된 credential_mode → 400', r.status_code == 400)

    # 다른 매장에 등록 시도 (소유권 위반)
    r = c.post('/api/beacon/wifi', headers=OH, json={
        'facility_id': ids['fid_other'], 'ssid': 'X', 'password': 'p!XXXXXXX',
    })
    _ok('④ 다른 매장 fid → 403', r.status_code == 403, r.get_json())


# ══════════════════════════════════════════════════════════════════════════════
# D. 비콘 ↔ WiFi 매핑
# ══════════════════════════════════════════════════════════════════════════════
def test_d_beacon_wifi_mapping():
    print('\n── D. 비콘 ↔ WiFi 매핑 PUT/GET/DELETE ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['aid'], ids['fid']))

    # WiFi 2개 만들기 (multi=true)
    w1 = c.post('/api/beacon/wifi', headers=OH, json={
        'facility_id': ids['fid'], 'ssid': 'W1', 'password': 'p!1XXXXXXX',
        'multi': True,
    }).get_json()['wifi_profile_id']
    w2 = c.post('/api/beacon/wifi', headers=OH, json={
        'facility_id': ids['fid'], 'ssid': 'W2', 'password': 'p!2XXXXXXX',
        'multi': True,
    }).get_json()['wifi_profile_id']

    # 비콘1 → [w1, w2] PUT (set)
    r = c.put(f"/api/facilities/{ids['fid']}/beacons/{ids['bid1']}/wifis",
              headers=OH, json={'wifi_profile_ids': [w1, w2]})
    body = r.get_json()
    _ok('① PUT 매핑 200 + 2건', r.status_code == 200 and body['wifi_profile_ids'] == [w1, w2],
        body)

    # GET 매핑 — priority 순서
    r = c.get(f"/api/facilities/{ids['fid']}/beacons/{ids['bid1']}/wifis",
              headers=OH)
    j = r.get_json()
    _ok('② GET 매핑 — 2건', r.status_code == 200 and len(j.get('wifis', [])) == 2, j)

    # DELETE 단일 매핑
    r = c.delete(f"/api/facilities/{ids['fid']}/beacons/{ids['bid1']}/wifis/{w1}",
                 headers=OH)
    _ok('③ DELETE 단일 매핑 200', r.status_code == 200)
    r = c.get(f"/api/facilities/{ids['fid']}/beacons/{ids['bid1']}/wifis",
              headers=OH)
    _ok('④ 매핑 1건 남음', len(r.get_json().get('wifis', [])) == 1)


def test_d_beacon_wifi_mapping_guards():
    print('\n── D-guards. 매핑 PUT 가드 ──')
    ids = _seed_baseline()
    OH = _h(_owner_token(ids['aid'], ids['fid']))

    # 다른 매장 WiFi 만들고 우리 비콘에 매핑 시도 (소유권 검증)
    OH_other = _h(_owner_token(ids['aid_other'], ids['fid_other']))
    w_other = c.post('/api/beacon/wifi', headers=OH_other, json={
        'facility_id': ids['fid_other'], 'ssid': 'OtherW', 'password': 'p!XXXXXXX',
    }).get_json()['wifi_profile_id']

    r = c.put(f"/api/facilities/{ids['fid']}/beacons/{ids['bid1']}/wifis",
              headers=OH, json={'wifi_profile_ids': [w_other]})
    _ok('① 다른 매장 wifi 매핑 → 400', r.status_code == 400, r.get_json())

    # 존재하지 않는 비콘
    r = c.put(f"/api/facilities/{ids['fid']}/beacons/999999/wifis",
              headers=OH, json={'wifi_profile_ids': []})
    _ok('② 존재하지 않는 비콘 → 404', r.status_code == 404)

    # wifi_profile_ids 형식 오류
    r = c.put(f"/api/facilities/{ids['fid']}/beacons/{ids['bid1']}/wifis",
              headers=OH, json={'wifi_profile_ids': 'not-a-list'})
    _ok('③ wifi_profile_ids 비배열 → 400', r.status_code == 400)


# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    print('═══ WiFi 프로필 + 비콘↔WiFi 매핑 통합 테스트 ═══')
    for fn in (
        test_a_wifi_create_encrypt_list,
        test_a_wifi_multi_mode,
        test_b_wifi_patch_delete,
        test_c_wifi_create_guards,
        test_d_beacon_wifi_mapping,
        test_d_beacon_wifi_mapping_guards,
    ):
        _truncate_all()
        fn()
    print('\n✅ 모든 테스트 통과')


if __name__ == '__main__':
    main()
