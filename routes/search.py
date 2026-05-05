"""매장 검색 API. SRS FR-STORE-002 (지도 연동) — 좌표 기반 거리 계산.

엔드포인트
---------
- GET /api/search/facilities
    Query params:
      - q          (선택) 매장명/주소 부분 일치
      - lat, lng   (선택) 거리순 정렬 + 결과에 distance_km 포함
      - radius_km  (선택, lat/lng 함께) 반경 내 필터 (기본 무제한)
      - lang       (선택) 캐시된 번역 머지 (기존 ?lang= 패턴 재사용)
      - limit      (선택, 기본 20, 최대 100)

공개 라우트 — 누구나 사용 가능 (앱 사용자가 주변 매장 발견에 사용).
``facilities.active=1``인 매장만 노출.
"""
import math
from flask import Blueprint, request, jsonify

from models.database import get_db
from routes.auth import decode_access_token

search_bp = Blueprint('search', __name__, url_prefix='/api/search')


def _is_minor_caller() -> bool:
    """Authorization 헤더에서 user 토큰을 디코드 → age_group 이 minor 인지 확인.

    토큰 없거나 user 가 아니면 False (성인/공개 호출 취급).
    """
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return False
    payload = decode_access_token(auth.split(' ', 1)[1])
    if not payload or payload.get('sub_type') not in (None, 'user'):
        return False
    user_id = payload.get('user_id')
    if not user_id:
        return False
    db = get_db()
    try:
        row = db.execute(
            "SELECT age_group FROM users WHERE id=? AND deleted_at IS NULL",
            (user_id,)
        ).fetchone()
    finally:
        db.close()
    return bool(row and row['age_group'] == 'minor_14_18')


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """두 좌표 간 거리(km). Haversine."""
    R = 6371.0  # 지구 반지름
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp/2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def _row_to_search_result(row) -> dict:
    return {
        'id':          row['id'],
        'name':        row['name'],
        'address':     row['address'],
        'phone':       row['phone'],
        'description': row['description'],
        'image_url':   row['image_url'],
        'latitude':    row['latitude'],
        'longitude':   row['longitude'],
        'adult_only':  bool(row['adult_only']) if 'adult_only' in row.keys() else False,
    }


@search_bp.route('/facilities', methods=['GET'])
def search_facilities():
    q          = (request.args.get('q') or '').strip()
    lat        = request.args.get('lat',       type=float)
    lng        = request.args.get('lng',       type=float)
    radius_km  = request.args.get('radius_km', type=float)
    lang       = (request.args.get('lang') or '').strip() or None
    limit      = request.args.get('limit', default=20, type=int)
    if limit < 1: limit = 20
    if limit > 100: limit = 100

    if (lat is None) ^ (lng is None):
        return jsonify({'success': False,
                        'message': 'lat과 lng는 함께 지정해야 합니다.'}), 400
    has_geo = lat is not None and lng is not None

    db = get_db()
    sql = "SELECT * FROM facilities WHERE active=1"
    params: list = []
    # PR #47 — 미성년자 토큰이면 adult_only 시설 자동 필터
    if _is_minor_caller():
        sql += " AND COALESCE(adult_only, 0) = 0"
    if q:
        sql += " AND (name LIKE ? OR address LIKE ? OR description LIKE ?)"
        like = f'%{q}%'
        params.extend([like, like, like])
    rows = db.execute(sql, params).fetchall()

    results = []
    for r in rows:
        item = _row_to_search_result(r)
        if has_geo and r['latitude'] is not None and r['longitude'] is not None:
            dist = _haversine_km(lat, lng, r['latitude'], r['longitude'])
            if radius_km is not None and dist > radius_km:
                continue
            item['distance_km'] = round(dist, 3)
        elif radius_km is not None and has_geo:
            # 좌표 미설정 매장은 반경 필터 들어오면 제외
            continue
        # 번역 머지
        if lang:
            t = db.execute(
                """SELECT name, address, description FROM facility_translations
                   WHERE facility_id=? AND language=?""",
                (r['id'], lang)
            ).fetchone()
            if t:
                if t['name']:        item['name']        = t['name']
                if t['address']:     item['address']     = t['address']
                if t['description']: item['description'] = t['description']
                item['language'] = lang
        results.append(item)

    if has_geo:
        results.sort(key=lambda x: x.get('distance_km', float('inf')))
    else:
        results.sort(key=lambda x: x['id'], reverse=True)
    results = results[:limit]
    db.close()
    return jsonify({'success': True,
                    'count': len(results),
                    'results': results})
