import 'api_client.dart';

/// SupportService — mobile(B2C) 의 고객센터/FAQ/신고 API 래퍼.
///
/// - listFaqs / listCategories: 공개 GET (인증 불필요)
/// - createTicket / listMyTickets / getTicket / replyToTicket / createReport:
///   사용자 토큰 필요 (ApiClient 가 자동 주입).
class SupportService {
  SupportService._();
  static final SupportService instance = SupportService._();

  final _api = ApiClient();

  /// FAQ 목록 (B2C). category 미지정 시 전체.
  Future<List<dynamic>> listFaqs({String? category, String lang = 'ko'}) async {
    final qp = StringBuffer('kind=user&lang=$lang');
    if (category != null && category.isNotEmpty) {
      qp.write('&category=$category');
    }
    final res = await _api.get('/api/faqs?$qp');
    return (res['faqs'] as List?) ?? const [];
  }

  Future<List<dynamic>> listCategories() async {
    final res = await _api.get('/api/support/categories?kind=user');
    return (res['categories'] as List?) ?? const [];
  }

  Future<int> createTicket({
    required String category,
    required String subject,
    required String body,
    String priority = 'normal',
  }) async {
    final res = await _api.post('/api/support/tickets', {
      'category': category,
      'subject':  subject,
      'body':     body,
      'priority': priority,
    });
    return (res['ticket_id'] as num).toInt();
  }

  Future<List<dynamic>> listMyTickets() async {
    final res = await _api.get('/api/support/tickets/me');
    return (res['tickets'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> getTicket(int tid) async {
    return _api.get('/api/support/tickets/$tid');
  }

  Future<void> replyToTicket(int tid, String body) async {
    await _api.post('/api/support/tickets/$tid/messages', {'body': body});
  }

  Future<int> createReport({
    required String targetKind,        // 'facility'|'user'|'review'|'chat'
    required int    targetId,
    required String reasonCode,        // 'spam'|'inappropriate'|'fraud'|'etc'
    String? reasonText,
  }) async {
    final res = await _api.post('/api/reports', {
      'target_kind': targetKind,
      'target_id':   targetId,
      'reason_code': reasonCode,
      if (reasonText != null && reasonText.isNotEmpty)
        'reason_text': reasonText,
    });
    return (res['report_id'] as num).toInt();
  }
}
