import 'api_client.dart';

/// 스탬프 도메인 API.
class StampService {
  StampService._();
  static final StampService instance = StampService._();
  factory StampService() => instance;

  final _api = ApiClient.instance;

  /// 내 스탬프 목록 (시설별 그룹). 백엔드 stamp_bp.
  Future<List<Map<String, dynamic>>> myStamps() async {
    final data = await _api.get('/api/stamps');
    return (data['stamps'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  /// 시설별 스탬프 카드 정책 + 보유 카운트.
  Future<Map<String, dynamic>> cardForFacility(int facilityId) async {
    final data = await _api.get('/api/stamps/cards/$facilityId');
    return (data['card'] as Map?)?.cast<String, dynamic>() ?? {};
  }

  /// 사용자 측 스탬프 적립 (BLE 자동 적립과는 별도, 수동 트리거 시).
  Future<Map<String, dynamic>> issue(int facilityId) async {
    return _api.post('/api/stamps/issue', {'facility_id': facilityId});
  }
}
