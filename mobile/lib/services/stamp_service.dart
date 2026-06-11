import 'api_client.dart';

/// 스탬프 도메인 API.
class StampService {
  StampService._();
  static final StampService instance = StampService._();
  factory StampService() => instance;

  final _api = ApiClient.instance;

  /// 내 스탬프 목록 (시설별 그룹). 백엔드 stamp_bp.
  Future<List<Map<String, dynamic>>> myStamps() async {
    // 2026-06-09 — 백엔드 라우트 정합: /api/users/me/stamps + stamps_by_facility
    final data = await _api.get('/api/users/me/stamps');
    return (data['stamps_by_facility'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  // 2026-06-11 — cardForFacility / issue 제거.
  // 두 메서드 모두 backend 에 대응 라우트가 없는 dead code 였음 (404 → HTML 파싱 실패).
  // · 시설별 정책+카운트 = /api/users/me/stamps 의 stamps_by_facility 에 포함
  // · 적립 = BLE 자동 (provider 측 /api/facilities/<fid>/stamps POST), 사용자 수동 적립 정책 없음
}
