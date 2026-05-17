import 'api_client.dart';

/// 고객센터 문의 (support tickets) + FAQ 도메인 API.
class SupportService {
  SupportService._();
  static final SupportService instance = SupportService._();
  factory SupportService() => instance;

  final _api = ApiClient.instance;

  // ── 문의 ──────────────────────────────────────────────────────────

  /// 새 문의 작성.
  Future<Map<String, dynamic>> createTicket({
    required String subject,
    required String body,
    String? category,
  }) async {
    final payload = <String, dynamic>{'subject': subject, 'body': body};
    if (category != null && category.isNotEmpty) payload['category'] = category;
    final data = await _api.post('/api/support/tickets', payload);
    return (data['ticket'] as Map?)?.cast<String, dynamic>() ?? {};
  }

  /// 내 문의 목록.
  Future<List<Map<String, dynamic>>> listMyTickets() async {
    final data = await _api.get('/api/support/tickets/me');
    return (data['tickets'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  /// 문의 상세 + 대화 thread.
  Future<Map<String, dynamic>> getTicket(int tid) async {
    final data = await _api.get('/api/support/tickets/me/$tid');
    return (data['ticket'] as Map?)?.cast<String, dynamic>() ?? {};
  }

  /// 추가 메시지 전송.
  Future<void> addMessage(int tid, String body) async {
    await _api.post('/api/support/tickets/me/$tid/messages', {'body': body});
  }

  // ── FAQ ───────────────────────────────────────────────────────────

  /// 공개 FAQ 목록. kind=user 고정, lang 기본 ko.
  Future<List<Map<String, dynamic>>> listFaqs({String lang = 'ko'}) async {
    final data = await _api.get('/api/faqs?kind=user&lang=$lang');
    return (data['faqs'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }
}
