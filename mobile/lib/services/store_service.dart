import 'api_client.dart';

/// 시설(매장) 도메인 API. 백엔드 store_bp / search_bp 호출.
class StoreService {
  StoreService._();
  static final StoreService instance = StoreService._();
  factory StoreService() => instance;

  final _api = ApiClient.instance;

  // ── 검색 ────────────────────────────────────────────────────────────────
  /// 키워드 / 거리 / 다국어 매장 검색.
  /// query: q, lat, lng, radius_km, lang, limit
  /// 응답: results 배열 + 각 row 에 distance_km 포함 (lat/lng 지정 시).
  Future<List<Map<String, dynamic>>> search({
    String? q, double? lat, double? lng, double? radiusKm, String? lang,
    int? limit,
  }) async {
    final params = <String, String>{};
    if (q != null && q.isNotEmpty) params['q'] = q;
    if (lat != null) params['lat'] = lat.toString();
    if (lng != null) params['lng'] = lng.toString();
    if (radiusKm != null) params['radius_km'] = radiusKm.toString();
    if (lang != null) params['lang'] = lang;
    if (limit != null) params['limit'] = limit.toString();
    final qs = params.entries.map((e) => '${e.key}=${Uri.encodeComponent(e.value)}').join('&');
    final data = await _api.get('/api/search/facilities${qs.isEmpty ? '' : '?$qs'}');
    return (data['results'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  // ── 시설 상세 ────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> get(int facilityId, {String? lang}) async {
    final qs = (lang != null && lang.isNotEmpty) ? '?lang=$lang' : '';
    final data = await _api.get('/api/facilities/$facilityId$qs');
    return (data['facility'] as Map?)?.cast<String, dynamic>() ?? {};
  }

  // ── 시설 이미지 목록 ─────────────────────────────────────────────────────
  Future<List<Map<String, dynamic>>> images(int facilityId) async {
    final data = await _api.get('/api/facilities/$facilityId/images');
    return (data['images'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  // ── 다국어 번역 ─────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> translate(int facilityId, String lang) async {
    return _api.get('/api/facilities/$facilityId/translate?lang=$lang');
  }
}
