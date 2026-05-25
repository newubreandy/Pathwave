"""C-4 USP — 매장 메뉴 OCR + 자동 번역 (D-4-a).

엔드포인트
---------
- POST   /api/facilities/<fid>/menu/upload    (owner/admin) — 이미지 업로드+OCR
- GET    /api/facilities/<fid>/menu           — 메뉴 항목 (lang 별 자동 번역+캐시)
- POST   /api/facilities/<fid>/menu/items     (owner/admin) — 수동 신규/교체
- PATCH  /api/facility-menu-items/<id>        (owner/admin) — 항목 수정
- DELETE /api/facility-menu-items/<id>        (owner/admin) — 항목 삭제

원칙
----
- 가격 단위 = KRW 강제 (외국 통화 거부)
- 자동 번역 대상 = name / description. price 는 절대 번역 X
- OCR / 번역 호출 시 ai_usage_logs 자동 기록 → 임계점 도달 시 차단
"""
from __future__ import annotations

import base64
import json
import logging
from flask import Blueprint, request, jsonify, g

from models.database import get_db
from routes.auth import require_facility_actor, require_auth  # noqa: F401
from models.menu_ocr_provider import (
    get_menu_ocr_provider, normalize_krw_price,
)
from models.ai_cost import is_translation_blocked, month_total_usd, record_usage

logger = logging.getLogger('pathwave')
menu_bp = Blueprint('menu', __name__)


# ─── 헬퍼 ─────────────────────────────────────────────────────────────────
def _owned_facility(db, fid: int, account_id: int) -> bool:
    row = db.execute(
        "SELECT id FROM facilities WHERE id=? AND owner_id=?",
        (fid, account_id)
    ).fetchone()
    return row is not None


def _row_to_item(r) -> dict:
    return {
        'id':           r['id'],
        'facility_id':  r['facility_id'],
        'language':     r['language'],
        'name':         r['name'],
        'price':        r['price'],
        'description':  r['description'],
        'sort_order':   r['sort_order'],
        'source':       r['source'],
        'upload_id':    r['upload_id'],
        'base_item_id': r['base_item_id'],
        'active':       bool(r['active']),
        'updated_at':   r['updated_at'],
    }


def _decode_image_payload(data: dict) -> bytes:
    """body 의 image_b64 또는 image_url 에서 bytes 추출.

    이번 단계는 b64 만 지원. R2 단계에서 multipart/S3 추가.
    """
    b64 = (data.get('image_b64') or '').strip()
    if not b64:
        raise ValueError('image_b64 (base64 인코딩 이미지) 가 필요합니다.')
    # data URL prefix 제거
    if ',' in b64 and b64.startswith('data:'):
        b64 = b64.split(',', 1)[1]
    try:
        return base64.b64decode(b64)
    except Exception:
        raise ValueError('image_b64 디코딩 실패')


# ─── POST /menu/upload — 이미지 업로드 + OCR ──────────────────────────────
@menu_bp.route('/api/facilities/<int:fid>/menu/upload', methods=['POST'])
@require_facility_actor(roles=['owner', 'admin'])
def upload_menu_image(fid: int):
    """이미지 업로드 → OCR → items 추출.

    body: {image_b64: str, replace: bool=false}
      - replace=True 면 기존 ko items 비활성화 후 신규 등록
    """
    account_id = g.auth['owner_account_id']
    actor_id   = g.auth['user_id']
    data = request.get_json(silent=True) or {}
    replace = bool(data.get('replace'))

    try:
        image_bytes = _decode_image_payload(data)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404

    # OCR 실행
    provider = get_menu_ocr_provider()
    try:
        items = provider.extract(image_bytes, db=db, facility_id=fid,
                                 actor_id=actor_id, source_lang='ko')
    except ValueError as e:
        # 가격에 외국 통화 등 검증 오류
        db.close()
        return jsonify({'success': False, 'message': str(e)}), 422
    except Exception as e:
        logger.exception('[menu/upload] OCR 실패: %s', e)
        db.close()
        return jsonify({'success': False,
                        'message': f'OCR 실패: {e}'}), 502

    # upload row 기록
    cur = db.execute(
        """INSERT INTO facility_menu_uploads
             (facility_id, image_url, ocr_status, ocr_provider, ocr_result,
              uploaded_by_actor_role, uploaded_by_actor_id)
           VALUES (?, '(inline)', 'success', ?, ?, ?, ?)""",
        (fid, provider.name, json.dumps(items, ensure_ascii=False),
         g.auth.get('actor_role'), actor_id),
    )
    upload_id = cur.lastrowid

    # replace 옵션
    if replace:
        db.execute(
            "UPDATE facility_menu_items SET active=0 WHERE facility_id=? AND language='ko'",
            (fid,))

    # ko items 저장 (가격 정규화 한 번 더)
    saved_ids = []
    for it in items:
        try:
            price = normalize_krw_price(it.get('price') or '')
        except ValueError as e:
            db.close()
            return jsonify({'success': False, 'message': str(e)}), 422
        cur = db.execute(
            """INSERT INTO facility_menu_items
                 (facility_id, language, name, price, description, sort_order,
                  source, upload_id)
               VALUES (?, 'ko', ?, ?, ?, ?, 'ocr', ?)""",
            (fid, (it.get('name') or '').strip(), price,
             (it.get('description') or '').strip(),
             int(it.get('sort_order') or 0),
             upload_id),
        )
        saved_ids.append(cur.lastrowid)
    db.commit()

    # 응답
    rows = db.execute(
        f"SELECT * FROM facility_menu_items WHERE id IN "
        f"({','.join('?' * len(saved_ids))})",
        saved_ids,
    ).fetchall() if saved_ids else []
    db.close()
    return jsonify({
        'success':     True,
        'upload_id':   upload_id,
        'provider':    provider.name,
        'item_count':  len(saved_ids),
        'items':       [_row_to_item(r) for r in rows],
    }), 201


# ─── GET /menu — lang 별 항목 (자동 번역 + 캐시) ──────────────────────────
@menu_bp.route('/api/facilities/<int:fid>/menu', methods=['GET'])
def get_menu(fid: int):
    """매장 메뉴 (lang 별).

    ?lang=ko|en|ja|...  (기본=ko)
    동작:
    - 해당 lang items 가 active 면 그대로 반환
    - 없으면 ko 원본 fetch → 자동 번역 폴백 (translation_blocked 면 ko 그대로)

    공개 API — 인증 없음. 외국인 사용자 mobile 에서 호출.
    """
    lang = (request.args.get('lang') or 'ko').strip().lower()
    db = get_db()
    try:
        # 1) 요청한 lang 에 active items 있는지 확인
        rows = db.execute(
            """SELECT * FROM facility_menu_items
                WHERE facility_id=? AND language=? AND active=1
                ORDER BY sort_order ASC, id ASC""",
            (fid, lang)
        ).fetchall()
        if rows:
            return jsonify({
                'success':  True,
                'facility_id': fid,
                'language': lang,
                'source':   'cache',
                'items':    [_row_to_item(r) for r in rows],
            })

        # 2) 없으면 ko 가져옴
        ko_rows = db.execute(
            """SELECT * FROM facility_menu_items
                WHERE facility_id=? AND language='ko' AND active=1
                ORDER BY sort_order ASC, id ASC""",
            (fid,)
        ).fetchall()
        if not ko_rows:
            return jsonify({'success': True,
                            'facility_id': fid,
                            'language':    lang,
                            'source':      'empty',
                            'items':       []})

        # 3) ko == lang 이면 ko 그대로 반환
        if lang == 'ko':
            return jsonify({'success': True,
                            'facility_id': fid,
                            'language': 'ko',
                            'source':   'cache',
                            'items':    [_row_to_item(r) for r in ko_rows]})

        # 4) 자동 번역 (translation_blocked 면 ko 그대로)
        import datetime as _dt
        now = _dt.datetime.utcnow()
        agg = month_total_usd(db, now.year, now.month)
        if is_translation_blocked(agg['total_usd']):
            return jsonify({'success': True,
                            'facility_id': fid,
                            'language':    lang,
                            'source':      'fallback_blocked',
                            'items':       [_row_to_item(r) for r in ko_rows]})

        # 5) 자동 번역 + 캐시
        translated = _translate_items(db, ko_rows, target_lang=lang)
        return jsonify({'success': True,
                        'facility_id': fid,
                        'language': lang,
                        'source':   'translated',
                        'items':    translated})
    finally:
        db.close()


def _translate_items(db, ko_rows, *, target_lang: str) -> list[dict]:
    """ko items → target_lang 로 번역 + 캐시 + 비용 기록.

    번역 대상 = name / description 만. price 는 원본 유지 (KRW).
    """
    out = []
    for r in ko_rows:
        # 간이 번역 (실 DeepL 호출은 routes/store.py 자동번역과 패턴 통일 — 단순 fallback 우선)
        # 이번 단계는 ko 원본 그대로 반환 (price KRW 보존 핵심).
        # 실 번역은 향후 store.py 의 trigger_auto_translate 와 통합.
        new_name = r['name']
        new_desc = r['description']
        cur = db.execute(
            """INSERT INTO facility_menu_items
                 (facility_id, language, name, price, description,
                  sort_order, source, base_item_id)
               VALUES (?, ?, ?, ?, ?, ?, 'translated', ?)""",
            (r['facility_id'], target_lang, new_name, r['price'], new_desc,
             r['sort_order'], r['id']),
        )
        # 캐시 항목 cost record (0 USD — 실제 번역 호출 시 deepl record 별도)
        record_usage(db, provider='stub', operation='translate',
                     units=len(new_name) + len(new_desc),
                     facility_id=r['facility_id'])
        row = db.execute(
            "SELECT * FROM facility_menu_items WHERE id=?",
            (cur.lastrowid,)
        ).fetchone()
        out.append(_row_to_item(row))
    db.commit()
    return out


# ─── POST /menu/items — 수동 신규 ─────────────────────────────────────────
@menu_bp.route('/api/facilities/<int:fid>/menu/items', methods=['POST'])
@require_facility_actor(roles=['owner', 'admin'])
def create_menu_item(fid: int):
    """수동으로 메뉴 1건 신규 등록.

    body: {name, price?, description?, sort_order?, language? (기본 ko)}
    """
    account_id = g.auth['owner_account_id']
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'name 필수.'}), 400
    try:
        price = normalize_krw_price(data.get('price') or '')
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 422
    description = (data.get('description') or '').strip()
    sort_order  = int(data.get('sort_order') or 0)
    language    = (data.get('language') or 'ko').strip().lower()

    db = get_db()
    if not _owned_facility(db, fid, account_id):
        db.close()
        return jsonify({'success': False,
                        'message': '매장을 찾을 수 없거나 권한이 없습니다.'}), 404
    cur = db.execute(
        """INSERT INTO facility_menu_items
             (facility_id, language, name, price, description, sort_order,
              source)
           VALUES (?, ?, ?, ?, ?, ?, 'manual')""",
        (fid, language, name, price, description, sort_order),
    )
    row = db.execute(
        "SELECT * FROM facility_menu_items WHERE id=?", (cur.lastrowid,)
    ).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True, 'item': _row_to_item(row)}), 201


# ─── PATCH /facility-menu-items/<id> — 수정 ───────────────────────────────
@menu_bp.route('/api/facility-menu-items/<int:iid>', methods=['PATCH'])
@require_facility_actor(roles=['owner', 'admin'])
def update_menu_item(iid: int):
    """항목 수정. 보낸 필드만 변경. 가격은 KRW 강제 정규화."""
    account_id = g.auth['owner_account_id']
    data = request.get_json(silent=True) or {}
    db = get_db()
    row = db.execute(
        """SELECT m.* FROM facility_menu_items m
             JOIN facilities f ON m.facility_id = f.id
            WHERE m.id=? AND f.owner_id=?""",
        (iid, account_id),
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False,
                        'message': '항목을 찾을 수 없거나 권한이 없습니다.'}), 404

    fields, params = [], []
    if 'name' in data:
        fields.append('name=?'); params.append((data.get('name') or '').strip())
    if 'price' in data:
        try:
            params.append(normalize_krw_price(data.get('price') or ''))
        except ValueError as e:
            db.close()
            return jsonify({'success': False, 'message': str(e)}), 422
        fields.append('price=?')
    if 'description' in data:
        fields.append('description=?'); params.append((data.get('description') or '').strip())
    if 'sort_order' in data:
        fields.append('sort_order=?'); params.append(int(data.get('sort_order') or 0))
    if 'active' in data:
        fields.append('active=?'); params.append(1 if data.get('active') else 0)

    if not fields:
        db.close()
        return jsonify({'success': False, 'message': '변경할 필드가 없습니다.'}), 400

    fields.append("updated_at=datetime('now')")
    db.execute(f"UPDATE facility_menu_items SET {', '.join(fields)} WHERE id=?",
               (*params, iid))
    new_row = db.execute("SELECT * FROM facility_menu_items WHERE id=?", (iid,)).fetchone()
    db.commit()
    db.close()
    return jsonify({'success': True, 'item': _row_to_item(new_row)})


# ─── DELETE /facility-menu-items/<id> ─────────────────────────────────────
@menu_bp.route('/api/facility-menu-items/<int:iid>', methods=['DELETE'])
@require_facility_actor(roles=['owner', 'admin'])
def delete_menu_item(iid: int):
    """항목 삭제 (실제 DELETE — base item 삭제 시 종속 번역도 cascade 안 됨,
    별도로 base_item_id=? 정리)."""
    account_id = g.auth['owner_account_id']
    db = get_db()
    row = db.execute(
        """SELECT m.id FROM facility_menu_items m
             JOIN facilities f ON m.facility_id = f.id
            WHERE m.id=? AND f.owner_id=?""",
        (iid, account_id),
    ).fetchone()
    if not row:
        db.close()
        return jsonify({'success': False,
                        'message': '항목을 찾을 수 없거나 권한이 없습니다.'}), 404
    # 종속 번역 정리
    db.execute("DELETE FROM facility_menu_items WHERE base_item_id=?", (iid,))
    db.execute("DELETE FROM facility_menu_items WHERE id=?", (iid,))
    db.commit()
    db.close()
    return jsonify({'success': True})
