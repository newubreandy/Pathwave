import 'api_client.dart';

/// 즐겨찾기 도메인 API.
class FavoriteService {
  FavoriteService._();
  static final FavoriteService instance = FavoriteService._();
  factory FavoriteService() => instance;

  final _api = ApiClient.instance;

  /// 즐겨찾기 목록. [{id, name, address, description, image_url, latitude, longitude, favorited_at}]
  Future<List<Map<String, dynamic>>> list() async {
    final data = await _api.get('/api/users/me/favorites');
    return (data['favorites'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  /// 즐겨찾기 추가. 성공 시 true.
  Future<bool> add(int facilityId) async {
    try {
      await _api.post('/api/users/me/favorites', {'facility_id': facilityId});
      return true;
    } catch (_) {
      return false;
    }
  }

  /// 즐겨찾기 해제. 성공 시 true.
  Future<bool> remove(int facilityId) async {
    try {
      await _api.delete('/api/users/me/favorites/$facilityId');
      return true;
    } catch (_) {
      return false;
    }
  }
}
