import 'api_client.dart';

/// 신고 도메인 API.
class AbuseReportService {
  AbuseReportService._();
  static final AbuseReportService instance = AbuseReportService._();
  factory AbuseReportService() => instance;

  final _api = ApiClient.instance;

  /// 신고 제출.
  /// [attachments] 가 비어있으면 JSON, 있으면 multipart 로 전송한다 (2026-06-08).
  Future<void> report({
    required String targetKind,
    required int targetId,
    required String reasonCode,
    String? detail,
    List<String>? attachments,
  }) async {
    final hasFiles = attachments != null && attachments.isNotEmpty;
    if (!hasFiles) {
      final payload = <String, dynamic>{
        'target_kind': targetKind,
        'target_id': targetId,
        'reason_code': reasonCode,
      };
      if (detail != null && detail.isNotEmpty) payload['reason_detail'] = detail;
      await _api.post('/api/abuse-reports', payload);
      return;
    }
    // 첨부 사진 — multipart (백엔드 routes/abuse_report.py 가 attachments[] 받음).
    final fields = <String, String>{
      'target_kind': targetKind,
      'target_id': targetId.toString(),
      'reason_code': reasonCode,
    };
    if (detail != null && detail.isNotEmpty) fields['reason_detail'] = detail;
    final files = <MapEntry<String, String>>[
      for (final p in attachments.take(3)) MapEntry('attachments', p),
    ];
    await _api.postMultipart('/api/abuse-reports', fields: fields, files: files);
  }
}
