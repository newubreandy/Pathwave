import 'api_client.dart';

/// 정책/동의 도메인 — `/api/policies` 호출.
class PolicyService {
  PolicyService._();
  static final PolicyService instance = PolicyService._();
  factory PolicyService() => instance;

  final _api = ApiClient.instance;

  /// 회원가입 시 표시할 동의 항목 메타.
  /// sub_type: 'user' (앱 사용자) | 'facility' (사장)
  Future<List<Map<String, dynamic>>> listItems(String subType) async {
    final data = await _api.get('/api/policies?sub_type=$subType');
    return (data['items'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  /// 현재 시행 정책 본문 (markdown).
  Future<Map<String, dynamic>> body(String kind, {String lang = 'ko'}) async {
    return _api.get('/api/policies/$kind?lang=$lang');
  }

  /// 이전 버전 보기 — 모든 버전 목록 (가벼움, 본문 미포함).
  Future<List<Map<String, dynamic>>> versions(String kind, {String lang = 'ko'}) async {
    final data = await _api.get('/api/policies/$kind/versions?lang=$lang');
    return (data['versions'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  /// 특정 버전 본문 (이전 버전 클릭 시).
  Future<Map<String, dynamic>> versionBody(String kind, int versionId) async {
    return _api.get('/api/policies/$kind/versions/$versionId');
  }
}
