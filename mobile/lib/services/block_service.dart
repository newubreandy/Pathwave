import 'api_client.dart';

/// 채팅 차단(block) 도메인 API — 손님이 매장을 차단/해지.
///
/// 백엔드: routes/block.py
/// - `POST   /api/blocks`         매장 차단
/// - `DELETE /api/blocks/{fid}`   차단 해지
/// - `GET    /api/blocks`         내 차단 목록
class BlockService {
  BlockService._();
  static final BlockService instance = BlockService._();
  factory BlockService() => instance;

  final _api = ApiClient.instance;

  /// 매장 차단. 이미 차단돼 있어도 멱등.
  Future<void> blockFacility(int facilityId) async {
    await _api.post('/api/blocks', {'facility_id': facilityId});
  }

  /// 차단 해지. 차단돼 있지 않아도 멱등.
  Future<void> unblockFacility(int facilityId) async {
    await _api.delete('/api/blocks/$facilityId');
  }

  /// 내가 차단한 매장 목록.
  /// 각 항목: {facility_id:int, facility_name:String, created_at:String}
  Future<List<Map<String, dynamic>>> listBlocks() async {
    final data = await _api.get('/api/blocks');
    final raw = data['blocks'] as List? ?? const [];
    return raw.cast<Map<String, dynamic>>();
  }
}
