import 'api_client.dart';

/// 시설(매장) 도메인 API. 백엔드 store_bp / search_bp 호출.
class StoreService {
  StoreService._();
  static final StoreService instance = StoreService._();
  factory StoreService() => instance;

  final _api = ApiClient.instance;

  // ── 검색 ────────────────────────────────────────────────────────────────
  /// 키워드 / 거리 / 다국어 매장 검색.
  /// query: q, lat, lng, radius_m, lang
  Future<List<Map<String, dynamic>>> search({
    String? q, double? lat, double? lng, int? radiusM, String? lang,
  }) async {
    final params = <String, String>{};
    if (q != null && q.isNotEmpty) params['q'] = q;
    if (lat != null) params['lat'] = lat.toString();
    if (lng != null) params['lng'] = lng.toString();
    if (radiusM != null) params['radius_m'] = radiusM.toString();
    if (lang != null) params['lang'] = lang;
    final qs = params.entries.map((e) => '${e.key}=${Uri.encodeComponent(e.value)}').join('&');
    final data = await _api.get('/api/search/facilities${qs.isEmpty ? '' : '?$qs'}');
    return (data['facilities'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  // ── 시설 상세 ────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> get(int facilityId) async {
    final data = await _api.get('/api/facilities/$facilityId');
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
