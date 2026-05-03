"""시설(매장) CRUD API. SRS FR-STORE-001.

facility_accounts(사장님 계정) 1 : N facilities(매장) 관계.
모든 라우트는 시설 측 토큰(``sub_type='facility'`` 또는 ``'staff'``)을 요구하며,
``owner_account_id`` 범위로 격리된다. role 기반 분기:

- owner: 전체 (생성/수정/삭제, 이미지 CRUD)
- admin: 운영 (수정, 이미지 CRUD) — 매장 생성/삭제는 불가
- staff: 읽기만 (목록/상세/이미지 목록/비콘 목록)

엔드포인트
---------
- ``POST   /api/facilities``        새 매장 등록
- ``GET    /api/facilities``        내 매장 목록 (활성)
- ``GET    /api/facilities/<id>``   매장 상세
- ``PATCH  /api/facilities/<id>``   매장 정보 부분 수정
- ``DELETE /api/facilities/<id>``   매장 비활성화 (soft delete)
"""
import os

from flask import Blueprint, request, jsonify, g

from models.database import get_db
from models.translator import get_translator, TranslatorError
from routes.auth import require_facility_actor

store_bp = Blueprint('store', __name__, url_prefix='/api/facilities')

_UPDATABLE_FIELDS = {
    'name', 'address', 'phone', 'business_hours',
    'latitude', 'longitude', 'description', 'image_url',
    'welcome_coupon_title', 'welcome_coupon_benefit',
    'welcome_coupon_validity_days',
}

# SRS FR-I18N-001: ko/en/ja/zh + 추가 가능
_ALLOWED_LANGUAGES = {'ko', 'en', 'ja', 'zh', 'zh-CN', 'zh-TW', 'zh-HK', 'fr'}
_TRANSLATABLE_FIELDS = ('name', 'address', 'description')

_AUTO_ON_CREATE = os.environ.get('TRANSLATION_AUTO_ON_CREATE', 'true').lower() in ('1', 'true', 'yes')
_DEFAULT_SOURCE_LANG = os.environ.get('FACILITY_SOURCE_LANGUAGE', 'ko')


def _auto_translate_facility(db, fid: int, source_text: dict,
                              source_lang: str | None = None,
                              target_languages: list[str] | None = None,
                              force: bool = False) -> dict:
    """``source_text``는 {name, address, description} 중 일부 또는 전부.

    각 target 언어에 대해 캐시 미존재(또는 force) 시 번역해 upsert.
    실패한 언어는 ``errors``에 기록. (best-effort, 호출자가 무시 가능)
    """
    src = source_lang or _DEFAULT_SOURCE_LANG
    targets = target_languages or [
        l for l in _ALLOWED_LANGUAGES
        if l != src and not l.startswith(f'{src}-')
    ]
    translator = get_translator()
    translated, skipped, errors = [], [], []

    for lang in targets:
        if lang not in _ALLOWED_LANGUAGES:
            errors.append({'language': lang, 'error': 'unsupported_language'})
            continue
        if not force:
            existing = db.execute(
                "SELECT 1 FROM facility_translations WHERE facility_id=? AND language=?",
                (fid, lang)
            ).fetchone()
            if existing:
                skipped.append(lang)
                continue
        translated_fields = {}
        for field in _TRANSLATABLE_FIELDS:
            text = (source_text.get(field) or '').strip()
            if not text:
                continue
            try:
                translated_fields[field] = translator.translate(text, source=src, target=lang)
            except TranslatorError as e:
                errors.append({'language': lang, 'field': field, 'error': str(e)})
                translated_fields = None
                break
        if translated_fields is None:
            continue
        if not translated_fields:
            skipped.append(lang)
            continue
        db.execute(
            """INSERT INTO facility_translations
                 (facility_id, language, name, address, description, updated_at)
               VALUES (?, ?, ?, ?, ?, datetime('now'))
               ON CONFLICT (facility_id, language) DO UPDATE SET
                 name        = excluded.name,
                 address     = excluded.address,
                 description = excluded.description,
                 updated_at  = datetime('now')""",
            (fid, lang,
             translated_fields.get('name'),
             translated_fields.get('address'),
             translated_fields.get('description')),
        )
        translated.append(lang)
    return {'translated': translated, 'skipped': skipped, 'errors': errors,
            'provider': translator.name}


def _row_to_facility(row, *, translation: dict | None = None) -> dict:
    """매장 row → JSON. ``translation``이 주어지면 번역된 필드로 덮어씌움.

    번역 필드 중 NULL이면 원본 유지 (partial translation graceful)."""
    data = {
        'id':             row['id'],
        'name':           row['name'],
        'address':        row['address'],
        'phone':          row['phone'],
        'business_hours': row['business_hours'],
        'latitude':       row['latitude'],
        'longitude':      row['longitude'],
        'description':    row['description'],
        'image_url':      row['image_url'],
        'welcome_coupon_title':         row['welcome_coupon_title'],
        'welcome_coupon_benefit':       row['welcome_coupon_benefit'],
        'welcome_coupon_validity_days': row['welcome_coupon_validity_days'],
        'active':         bool(row['active']),
        'created_at':     row['created_at'],
    }
    if translation:
        for k in _TRANSLATABLE_FIELDS:
            v = translation.get(k)
            if v:
                data[k] = v
        data['language'] = translation.get('language')
    return data


def _fetch_translation(db, facility_id: int, lang: str | None) -> dict | None:
    """``(facility_id, lang)`` 캐시 조회. 없으면 None."""
    if not lang:
        return None
    row = db.execute(
        """SELECT language, name, address, description FROM facility_translations
           WHERE facility_id=? AND language=?""",
        (facility_id, lang)
    ).fetchone()
    return dict(row) if row else None


def _requested_lang() -> str | None:
    """``?lang=xx`` 쿼리 파라미터를 추출. 화이트리스트 외에는 None."""
    lang = (request.args.get('lang') or '').strip()
    return lang if lang in _ALLOWED_LANGUAGES else None


def _normalize_text(value, *, allow_empty=False) -> str | None:
    s = (value or '').strip() if isinstance(value, str) else value
    if isinstance(s, str):
        if not s:
            return None if not allow_empty else ''
        return s
    return value


# ── Create ────────────────────────────────────────────────────────────────────

@store_bp.route('', methods=['POST'])
@require_facility_actor(roles=['owner'])
def create_facility():
    """매장 등록."""
    account_id = g.auth['owner_account_id']
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': '매장명은 필수입니다.'}), 400

    db = get_db()
    cur = db.execute(
        """INSERT INTO facilities
           (name, address, phone, business_hours, latitude, longitude,
            description, image_url,
            welcome_coupon_title, welcome_coupon_benefit, welcome_coupon_validity_days,
            owner_id, active)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,1)""",
        (name,
         _normalize_text(data.get('address')),
         _normalize_text(data.get('phone')),
         _normalize_text(data.get('business_hours')),
         data.get('latitude'),
         data.get('longitude'),
         _normalize_text(data.get('description')),
         _normalize_text(data.get('image_url')),
         _normalize_text(data.get('welcome_coupon_title')),
         _normalize_text(data.get('welcome_coupon_benefit')),
         data.get('welcome_coupon_validity_days'),
         account_id),
    )
    fid = cur.lastrowid
    row = db.execute("SELECT * FROM facilities WHERE id=?", (fid,)).fetchone()

    auto_result = None
    if _AUTO_ON_CREATE:
        auto_result = _auto_translate_facility(db, fid, {
            'name':        row['name'],
            'address':     row['address'],
            'description': row['description'],
        })
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '매장이 등록되었습니다.',
                    'facility':         _row_to_facility(row),
                    'auto_translation': auto_result}), 201


# ── Read ──────────────────────────────────────────────────────────────────────

@store_bp.route('', methods=['GET'])
@require_facility_actor()
def list_my_facilities():
    """내 매장 목록 (활성만). ``?lang=xx``으로 번역된 필드 머지."""
    account_id = g.auth['owner_account_id']
    lang = _requested_lang()
    db = get_db()
    rows = db.execute(
        """SELECT * FROM facilities
           WHERE owner_id=? AND active=1
           ORDER BY id DESC""",
        (account_id,)
    ).fetchall()
    out = [_row_to_facility(r, translation=_fetch_translation(db, r['id'], lang))
           for r in rows]
    db.close()
    return jsonify({'success': True, 'facilities': out})


@store_bp.route('/<int:fid>', methods=['GET'])
@require_facility_actor()
def get_facility(fid):
    """매장 상세 (소유). ``?lang=xx``으로 번역된 필드 머지."""
    account_id = g.auth['owner_account_id']
    lang = _requested_lang()
    db = get_db()
    row = db.execute(
        """SELECT * FROM facilities
           WHERE id=? AND owner_id=? AND active=1""",
        (fid, account_id)
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    translation = _fetch_translation(db, fid, lang)
    db.close()
    return jsonify({'success': True,
                    'facility': _row_to_facility(row, translation=translation)})


# ── Update ────────────────────────────────────────────────────────────────────

@store_bp.route('/<int:fid>', methods=['PATCH'])
@require_facility_actor(roles=['owner', 'admin'])
def update_facility(fid):
    """매장 정보 부분 수정 (소유). 보낸 필드만 갱신."""
    account_id = g.auth['owner_account_id']
    data = request.get_json(silent=True) or {}

    db = get_db()
    owned = db.execute(
        """SELECT 1 FROM facilities
           WHERE id=? AND owner_id=? AND active=1""",
        (fid, account_id)
    ).fetchone()
    if not owned:
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    sets, vals = [], []
    for key, raw in data.items():
        if key not in _UPDATABLE_FIELDS:
            continue
        if key == 'name':
            v = (raw or '').strip()
            if not v:
                db.close()
                return jsonify({'success': False,
                                'message': '매장명은 비울 수 없습니다.'}), 400
            vals.append(v)
        elif key in ('address', 'phone', 'business_hours',
                     'description', 'image_url',
                     'welcome_coupon_title', 'welcome_coupon_benefit'):
            vals.append(_normalize_text(raw))
        elif key == 'welcome_coupon_validity_days':
            if raw is not None and (not isinstance(raw, int) or raw < 1):
                db.close()
                return jsonify({'success': False,
                                'message': 'welcome_coupon_validity_days는 1 이상의 정수여야 합니다.'}), 400
            vals.append(raw)
        else:  # latitude, longitude
            vals.append(raw)
        sets.append(f'{key}=?')

    if not sets:
        db.close()
        return jsonify({'success': False,
                        'message': '수정할 필드가 없습니다.'}), 400

    vals.append(fid)
    db.execute(f"UPDATE facilities SET {', '.join(sets)} WHERE id=?", vals)
    row = db.execute("SELECT * FROM facilities WHERE id=?", (fid,)).fetchone()

    # 변경된 번역 가능 필드만 자동 재번역 (수동 캐시는 보존, force=False)
    auto_result = None
    if _AUTO_ON_CREATE:
        changed_translatable = {
            k: row[k] for k in _TRANSLATABLE_FIELDS if k in data
        }
        if changed_translatable:
            # 변경된 필드만 들고 들어가지만, 부분 번역 갱신은 복잡하므로
            # 캐시가 없는 언어만 새로 채움 (변경된 매장의 신규 언어 커버).
            auto_result = _auto_translate_facility(
                db, fid,
                {k: row[k] for k in _TRANSLATABLE_FIELDS},
            )
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '매장 정보가 수정되었습니다.',
                    'facility':         _row_to_facility(row),
                    'auto_translation': auto_result})


# ── Delete (soft) ─────────────────────────────────────────────────────────────

@store_bp.route('/<int:fid>', methods=['DELETE'])
@require_facility_actor(roles=['owner'])
def delete_facility(fid):
    """매장 비활성화 (soft delete; 데이터 보존, 조회에서 제외).

    cascade — 매장이 비활성화되면 그 매장에 묶인 비콘/WiFi도 운영 중단:
      * beacons.status='inactive'
      * wifi_profiles.active=0
    """
    account_id = g.auth['owner_account_id']
    db = get_db()
    cur = db.execute(
        """UPDATE facilities SET active=0
           WHERE id=? AND owner_id=? AND active=1""",
        (fid, account_id)
    )
    affected = cur.rowcount
    if affected == 0:
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    # cascade
    db.execute("UPDATE beacons       SET status='inactive' WHERE facility_id=?", (fid,))
    db.execute("UPDATE wifi_profiles SET active=0          WHERE facility_id=?", (fid,))
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': '매장이 비활성화되었습니다.'})


# ── 매장 이미지 헬퍼 ──────────────────────────────────────────────────────────

def _owned_facility(db, fid: int, account_id: int) -> bool:
    return bool(db.execute(
        "SELECT 1 FROM facilities WHERE id=? AND owner_id=? AND active=1",
        (fid, account_id)
    ).fetchone())


def _sync_primary_to_facility(db, fid: int) -> None:
    """현재 대표 이미지의 URL을 ``facilities.image_url``에 미러링한다.
    대표가 없으면 NULL로 비운다."""
    row = db.execute(
        "SELECT image_url FROM facility_images WHERE facility_id=? AND is_primary=1 LIMIT 1",
        (fid,)
    ).fetchone()
    db.execute("UPDATE facilities SET image_url=? WHERE id=?",
               (row['image_url'] if row else None, fid))


def _row_to_image(row) -> dict:
    return {
        'id':         row['id'],
        'image_url':  row['image_url'],
        'is_primary': bool(row['is_primary']),
        'sort_order': row['sort_order'],
        'created_at': row['created_at'],
    }


# ── 매장 이미지 CRUD ──────────────────────────────────────────────────────────

@store_bp.route('/<int:fid>/images', methods=['POST'])
@require_facility_actor(roles=['owner', 'admin'])
def add_image(fid):
    """매장 이미지 추가. 첫 이미지면 자동으로 대표 지정."""
    account_id = g.auth['owner_account_id']
    data       = request.get_json(silent=True) or {}
    image_url  = (data.get('image_url') or '').strip()
    if not image_url:
        return jsonify({'success': False, 'message': 'image_url은 필수입니다.'}), 400

    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    has_any = db.execute(
        "SELECT 1 FROM facility_images WHERE facility_id=? LIMIT 1", (fid,)
    ).fetchone() is not None
    auto_primary = not has_any
    requested_primary = bool(data.get('is_primary'))
    is_primary = 1 if (auto_primary or requested_primary) else 0

    sort_order = data.get('sort_order')
    if sort_order is None:
        max_row = db.execute(
            "SELECT COALESCE(MAX(sort_order), -1) AS m FROM facility_images WHERE facility_id=?",
            (fid,)
        ).fetchone()
        sort_order = max_row['m'] + 1

    if is_primary:
        db.execute("UPDATE facility_images SET is_primary=0 WHERE facility_id=?", (fid,))

    cur = db.execute(
        """INSERT INTO facility_images (facility_id, image_url, is_primary, sort_order)
           VALUES (?,?,?,?)""",
        (fid, image_url, is_primary, sort_order),
    )
    iid = cur.lastrowid
    if is_primary:
        _sync_primary_to_facility(db, fid)

    row = db.execute("SELECT * FROM facility_images WHERE id=?", (iid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '이미지가 추가되었습니다.',
                    'image': _row_to_image(row)}), 201


@store_bp.route('/<int:fid>/images', methods=['GET'])
@require_facility_actor()
def list_images(fid):
    """매장 이미지 목록 (sort_order ASC, id ASC)."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    rows = db.execute(
        """SELECT * FROM facility_images WHERE facility_id=?
           ORDER BY sort_order ASC, id ASC""",
        (fid,)
    ).fetchall()
    db.close()
    return jsonify({'success': True,
                    'facility_id': fid,
                    'images': [_row_to_image(r) for r in rows]})


@store_bp.route('/<int:fid>/images/<int:iid>', methods=['PATCH'])
@require_facility_actor(roles=['owner', 'admin'])
def update_image(fid, iid):
    """이미지 메타 수정 (is_primary / sort_order / image_url)."""
    account_id = g.auth['owner_account_id']
    data       = request.get_json(silent=True) or {}

    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    img = db.execute(
        "SELECT * FROM facility_images WHERE id=? AND facility_id=?",
        (iid, fid)
    ).fetchone()
    if not img:
        db.close()
        return jsonify({'success': False, 'message': '이미지를 찾을 수 없습니다.'}), 404

    sets, vals = [], []
    if 'image_url' in data:
        v = (data.get('image_url') or '').strip()
        if not v:
            db.close()
            return jsonify({'success': False,
                            'message': 'image_url은 비울 수 없습니다.'}), 400
        sets.append('image_url=?'); vals.append(v)
    if 'sort_order' in data:
        sets.append('sort_order=?'); vals.append(data.get('sort_order'))

    set_primary = bool(data.get('is_primary')) if 'is_primary' in data else None
    if set_primary is True:
        # 다른 모든 이미지 대표 해제 후 본인을 대표로
        db.execute("UPDATE facility_images SET is_primary=0 WHERE facility_id=?", (fid,))
        sets.append('is_primary=?'); vals.append(1)
    elif set_primary is False and img['is_primary']:
        # 본인을 대표 해제 (수동으로 해제)
        sets.append('is_primary=?'); vals.append(0)

    if not sets:
        db.close()
        return jsonify({'success': False, 'message': '수정할 필드가 없습니다.'}), 400

    vals.append(iid)
    db.execute(f"UPDATE facility_images SET {', '.join(sets)} WHERE id=?", vals)
    _sync_primary_to_facility(db, fid)
    row = db.execute("SELECT * FROM facility_images WHERE id=?", (iid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '이미지가 수정되었습니다.',
                    'image': _row_to_image(row)})


@store_bp.route('/<int:fid>/images/<int:iid>', methods=['DELETE'])
@require_facility_actor(roles=['owner', 'admin'])
def delete_image(fid, iid):
    """이미지 삭제. 대표를 지우면 남은 첫 이미지로 대표 승계."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    img = db.execute(
        "SELECT is_primary FROM facility_images WHERE id=? AND facility_id=?",
        (iid, fid)
    ).fetchone()
    if not img:
        db.close()
        return jsonify({'success': False, 'message': '이미지를 찾을 수 없습니다.'}), 404

    db.execute("DELETE FROM facility_images WHERE id=?", (iid,))

    if img['is_primary']:
        successor = db.execute(
            """SELECT id FROM facility_images WHERE facility_id=?
               ORDER BY sort_order ASC, id ASC LIMIT 1""",
            (fid,)
        ).fetchone()
        if successor:
            db.execute("UPDATE facility_images SET is_primary=1 WHERE id=?",
                       (successor['id'],))

    _sync_primary_to_facility(db, fid)
    db.commit()
    db.close()
    return jsonify({'success': True, 'message': '이미지가 삭제되었습니다.'})


# ── 매장별 비콘 목록 ──────────────────────────────────────────────────────────

@store_bp.route('/<int:fid>/beacons', methods=['GET'])
@require_facility_actor()
def list_facility_beacons(fid):
    """특정 매장의 비콘 목록 (소유 매장만)."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    owned = db.execute(
        "SELECT 1 FROM facilities WHERE id=? AND owner_id=? AND active=1",
        (fid, account_id)
    ).fetchone()
    if not owned:
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    rows = db.execute(
        """SELECT id, serial_no, uuid, status, battery_pct, firmware_ver, created_at
           FROM beacons WHERE facility_id=?
           ORDER BY id DESC""",
        (fid,)
    ).fetchall()
    db.close()
    return jsonify({
        'success': True,
        'facility_id': fid,
        'beacons': [dict(r) for r in rows],
    })


# ── 매장에 인벤토리 비콘 claim ────────────────────────────────────────────────

@store_bp.route('/<int:fid>/claim-beacon', methods=['POST'])
@require_facility_actor(roles=['owner', 'admin'])
def claim_beacon(fid):
    """사장님이 SN을 입력해 인벤토리 비콘을 자기 매장에 claim.

    body: ``{serial_no}``. 비콘은 ``status='inventory'``여야 함. 성공 시
    ``status='active'`` + facility_id 할당.
    """
    account_id = g.auth['owner_account_id']
    data = request.get_json(silent=True) or {}
    serial_no = (data.get('serial_no') or '').strip()
    if not serial_no:
        return jsonify({'success': False, 'message': 'serial_no가 필요합니다.'}), 400

    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    beacon = db.execute(
        "SELECT id, status, facility_id FROM beacons WHERE serial_no=?",
        (serial_no,)
    ).fetchone()
    if not beacon:
        db.close()
        return jsonify({'success': False,
                        'message': '해당 SN의 비콘을 찾을 수 없습니다. Super Admin에 문의해 주세요.'}), 404
    if beacon['status'] != 'inventory':
        db.close()
        if beacon['facility_id']:
            return jsonify({'success': False,
                            'message': '이미 다른 매장에 할당된 비콘입니다.'}), 409
        return jsonify({'success': False,
                        'message': f"비콘 상태가 '{beacon['status']}'이어서 claim할 수 없습니다."}), 409

    db.execute(
        "UPDATE beacons SET facility_id=?, status='active' WHERE id=?",
        (fid, beacon['id'])
    )
    new_row = db.execute(
        """SELECT id, serial_no, uuid, status, battery_pct, firmware_ver, created_at
           FROM beacons WHERE id=?""", (beacon['id'],)
    ).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '비콘이 매장에 할당되었습니다.',
                    'beacon': dict(new_row)})


# ── 매장 다국어 캐시 (SRS FR-I18N-002) ────────────────────────────────────────

def _row_to_translation(row) -> dict:
    return {
        'language':    row['language'],
        'name':        row['name'],
        'address':     row['address'],
        'description': row['description'],
        'created_at':  row['created_at'],
        'updated_at':  row['updated_at'],
    }


@store_bp.route('/<int:fid>/translations', methods=['GET'])
@require_facility_actor()
def list_translations(fid):
    """매장의 모든 캐시된 번역 목록 (소유 매장)."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    rows = db.execute(
        """SELECT * FROM facility_translations
           WHERE facility_id=? ORDER BY language ASC""",
        (fid,)
    ).fetchall()
    db.close()
    return jsonify({'success': True,
                    'facility_id': fid,
                    'translations': [_row_to_translation(r) for r in rows]})


@store_bp.route('/<int:fid>/translations/<lang>', methods=['PUT'])
@require_facility_actor(roles=['owner', 'admin'])
def upsert_translation(fid, lang):
    """``(facility_id, language)`` 캐시 upsert. 모든 필드 선택."""
    if lang not in _ALLOWED_LANGUAGES:
        return jsonify({'success': False,
                        'message': f'지원하지 않는 언어입니다. 허용: {sorted(_ALLOWED_LANGUAGES)}'}), 400
    account_id = g.auth['owner_account_id']
    data = request.get_json(silent=True) or {}
    name        = _normalize_text(data.get('name'))
    address     = _normalize_text(data.get('address'))
    description = _normalize_text(data.get('description'))

    if not any([name, address, description]):
        return jsonify({'success': False,
                        'message': 'name, address, description 중 적어도 하나는 필수입니다.'}), 400

    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    db.execute(
        """INSERT INTO facility_translations
             (facility_id, language, name, address, description, updated_at)
           VALUES (?, ?, ?, ?, ?, datetime('now'))
           ON CONFLICT (facility_id, language) DO UPDATE SET
             name        = excluded.name,
             address     = excluded.address,
             description = excluded.description,
             updated_at  = datetime('now')""",
        (fid, lang, name, address, description),
    )
    row = db.execute(
        "SELECT * FROM facility_translations WHERE facility_id=? AND language=?",
        (fid, lang)
    ).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True,
                    'message': '번역이 저장되었습니다.',
                    'translation': _row_to_translation(row)})


@store_bp.route('/<int:fid>/translations/<lang>', methods=['DELETE'])
@require_facility_actor(roles=['owner', 'admin'])
def delete_translation(fid, lang):
    """캐시된 번역 제거."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    cur = db.execute(
        "DELETE FROM facility_translations WHERE facility_id=? AND language=?",
        (fid, lang)
    )
    db.commit()
    affected = cur.rowcount
    db.close()
    if affected == 0:
        return jsonify({'success': False, 'message': '해당 언어 번역이 없습니다.'}), 404
    return jsonify({'success': True, 'message': '번역이 삭제되었습니다.'})


@store_bp.route('/<int:fid>/translations/auto', methods=['POST'])
@require_facility_actor(roles=['owner', 'admin'])
def trigger_auto_translate(fid):
    """수동으로 자동 번역 트리거. 외부 provider 호출.

    body (모두 옵션):
    - source_language: 기본 ``ko`` (env FACILITY_SOURCE_LANGUAGE 가능)
    - target_languages: 미지정 시 supported \\ source 전체
    - force: true이면 기존 캐시 덮어쓰기 (수동 캐시 포함)
    """
    account_id = g.auth['owner_account_id']
    data = request.get_json(silent=True) or {}
    source_lang   = (data.get('source_language') or '').strip() or None
    target_langs  = data.get('target_languages')
    force         = bool(data.get('force'))

    if source_lang and source_lang not in _ALLOWED_LANGUAGES:
        return jsonify({'success': False,
                        'message': f'지원하지 않는 source_language: {source_lang}'}), 400
    if target_langs is not None:
        if not isinstance(target_langs, list) or not target_langs:
            return jsonify({'success': False,
                            'message': 'target_languages는 비어 있지 않은 배열이어야 합니다.'}), 400
        bad = [l for l in target_langs if l not in _ALLOWED_LANGUAGES]
        if bad:
            return jsonify({'success': False,
                            'message': f'지원하지 않는 언어: {bad}'}), 400

    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    row = db.execute(
        "SELECT name, address, description FROM facilities WHERE id=?", (fid,)
    ).fetchone()
    result = _auto_translate_facility(
        db, fid,
        {'name': row['name'], 'address': row['address'], 'description': row['description']},
        source_lang=source_lang,
        target_languages=target_langs,
        force=force,
    )
    db.commit()
    db.close()
    return jsonify({'success': True, 'auto_translation': result})
