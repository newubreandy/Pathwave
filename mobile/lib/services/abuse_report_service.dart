import 'api_client.dart';

/// 신고 도메인 API.
class AbuseReportService {
  AbuseReportService._();
  static final AbuseReportService instance = AbuseReportService._();
  factory AbuseReportService() => instance;

  final _api = ApiClient.instance;

  /// 신고 제출.
  /// [targetKind] : 'facility' | 'user' 등
  /// [targetId]   : 대상 ID (정수)
  /// [reasonCode] : 'spam' | 'abuse' | 'illegal' | 'inappropriate' | 'other'
  /// [detail]     : 선택 상세 사유
  Future<void> report({
    required String targetKind,
    required int targetId,
    required String reasonCode,
    String? detail,
  }) async {
    final payload = <String, dynamic>{
      'target_kind': targetKind,
      'target_id': targetId,
      'reason_code': reasonCode,
    };
    if (detail != null && detail.isNotEmpty) payload['reason_detail'] = detail;
    await _api.post('/api/abuse-reports', payload);
  }
}
