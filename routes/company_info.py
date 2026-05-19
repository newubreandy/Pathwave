"""법인 정보 — 3 콘솔 footer 자동 동기 (Phase M).

엔드포인트
---------
공개:
  GET  /api/company-info
       → {company_name, ceo, biz_number, commerce_number, address,
          phone, email, hosting, updated_at}
       값이 없으면 모두 null. 호출자는 적당한 fallback 표시.

운영자 (super_admin):
  PUT  /api/admin/company-info
       body 의 키 중 _EDITABLE_FIELDS 만 upsert.
       단일 행 (id=1) 패턴 — 첫 PUT 에서 INSERT, 이후 UPDATE.

note
----
이메일은 일단 admin UI 에서 노출 안 함 (DNS/MX 연결 후 별도 적용).
백엔드는 받기는 한다 — 추후 admin UI 가 노출하면 즉시 동작.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from models.database import get_db
from routes.auth import require_super_admin

company_info_bp = Blueprint('company_info', __name__)

_EDITABLE_FIELDS = (
    'company_name', 'ceo', 'biz_number', 'commerce_number',
    'address', 'phone', 'email', 'hosting',
)


def _row_to_dict(row) -> dict:
    if row is None:
        return {f: None for f in _EDITABLE_FIELDS} | {'updated_at': None}
    return {f: row[f] for f in _EDITABLE_FIELDS} | {'updated_at': row['updated_at']}


# ════════════════════════════════════════════════════════════════════════════
#                                  공개
# ════════════════════════════════════════════════════════════════════════════

@company_info_bp.route('/api/company-info', methods=['GET'])
def get_company_info():
    db = get_db()
    try:
        row = db.execute("SELECT * FROM company_info WHERE id=1").fetchone()
        return jsonify({'success': True, 'company_info': _row_to_dict(row)})
    finally:
        db.close()


# ════════════════════════════════════════════════════════════════════════════
#                          운영자 (super_admin)
# ════════════════════════════════════════════════════════════════════════════

@company_info_bp.route('/api/admin/company-info', methods=['PUT'])
@require_super_admin()
def upsert_company_info():
    """단일 행 upsert. body 의 _EDITABLE_FIELDS 중 포함된 키만 갱신.

    빈 문자열은 NULL 로 저장 — "지움" 처리.
    """
    data = request.get_json(silent=True) or {}
    values = {}
    for f in _EDITABLE_FIELDS:
        if f in data:
            v = data[f]
            if v is None:
                values[f] = None
            elif isinstance(v, str):
                values[f] = v.strip() or None
            else:
                return jsonify({'success': False,
                                'message': f"{f} 는 문자열이어야 합니다."}), 400
    if not values:
        return jsonify({'success': False, 'message': '변경할 필드가 없습니다.'}), 400

    db = get_db()
    try:
        existing = db.execute(
            "SELECT id FROM company_info WHERE id=1"
        ).fetchone()
        if existing:
            sets = ', '.join(f"{k}=?" for k in values) + ", updated_at=datetime('now')"
            db.execute(
                f"UPDATE company_info SET {sets} WHERE id=1",
                list(values.values())
            )
        else:
            cols = ['id'] + list(values.keys())
            placeholders = ', '.join(['?'] * len(cols))
            db.execute(
                f"INSERT INTO company_info ({', '.join(cols)}) "
                f"VALUES ({placeholders})",
                [1] + list(values.values())
            )
        db.commit()
        new_row = db.execute(
            "SELECT * FROM company_info WHERE id=1"
        ).fetchone()
        return jsonify({'success': True,
                        'company_info': _row_to_dict(new_row)})
    finally:
        db.close()
