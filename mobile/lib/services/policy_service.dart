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

  /// 정책 본문 조회 (markdown).
  Future<Map<String, dynamic>> body(String kind, {String lang = 'ko'}) async {
    return _api.get('/api/policies/$kind?lang=$lang');
  }
}
