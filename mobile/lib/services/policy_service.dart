import 'api_client.dart';
import 'i18n_service.dart';

/// 정책/동의 도메인 — `/api/policies` 호출.
///
/// P12 — 약관은 ko/en 두 언어만 노출. 디바이스 언어가 ko 면 ko, 그 외 모두 en.
/// 호출자가 ``lang`` 을 명시하면 그대로 보냄(어드민/디버깅용).
class PolicyService {
  PolicyService._();
  static final PolicyService instance = PolicyService._();
  factory PolicyService() => instance;

  final _api = ApiClient.instance;

  /// 디바이스 언어 → ko/en 매핑 (P12). 한국어 단말만 ko, 그 외 모두 en.
  String _policyLang() =>
      I18nService.instance.currentLang == 'ko' ? 'ko' : 'en';

  /// 회원가입 시 표시할 동의 항목 메타.
  /// sub_type: 'user' (앱 사용자) | 'facility' (사장)
  Future<List<Map<String, dynamic>>> listItems(String subType,
      {String? lang}) async {
    final l = lang ?? _policyLang();
    final data = await _api.get('/api/policies?sub_type=$subType&lang=$l');
    return (data['items'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  /// 현재 시행 정책 본문 (markdown).
  Future<Map<String, dynamic>> body(String kind, {String? lang}) async {
    final l = lang ?? _policyLang();
    return _api.get('/api/policies/$kind?lang=$l');
  }

  /// 이전 버전 보기 — 모든 버전 목록 (가벼움, 본문 미포함).
  Future<List<Map<String, dynamic>>> versions(String kind,
      {String? lang}) async {
    final l = lang ?? _policyLang();
    final data = await _api.get('/api/policies/$kind/versions?lang=$l');
    return (data['versions'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  /// 특정 버전 본문 (이전 버전 클릭 시). 본문 자체에 lang 정보가 row 에 같이 있어 별도 lang 인자 불필요.
  Future<Map<String, dynamic>> versionBody(String kind, int versionId) async {
    return _api.get('/api/policies/$kind/versions/$versionId');
  }
}
