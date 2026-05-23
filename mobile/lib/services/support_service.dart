import 'api_client.dart';
import 'i18n_service.dart';

/// 고객센터 문의 (support tickets) + FAQ 도메인 API.
class SupportService {
  SupportService._();
  static final SupportService instance = SupportService._();
  factory SupportService() => instance;

  final _api = ApiClient.instance;

  // ── 문의 ──────────────────────────────────────────────────────────

  /// 새 문의 작성. ``lang_hint`` (P8b) — 작성자 단말 언어를 같이 보내
  /// 백엔드가 ``body_lang`` 으로 저장 (운영자 인박스에서 한국어로 번역됨).
  Future<Map<String, dynamic>> createTicket({
    required String subject,
    required String body,
    String? category,
  }) async {
    final payload = <String, dynamic>{
      'subject':   subject,
      'body':      body,
      'lang_hint': I18nService.instance.currentLang,
    };
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
  /// ``?lang`` (P8b) — viewer 언어. 백엔드가 메시지에 ``translated_text`` 머지.
  /// 응답 구조: ``{ticket, messages, viewer_lang}`` — 전체를 그대로 반환한다.
  Future<Map<String, dynamic>> getTicket(int tid) async {
    final lang = I18nService.instance.currentLang;
    final data = await _api.get('/api/support/tickets/me/$tid?lang=$lang');
    // ticket 안에 messages 가 같이 들어가도록 일반화 — 호출부 호환성 유지.
    final ticket = (data['ticket'] as Map?)?.cast<String, dynamic>() ?? {};
    ticket['messages']    = data['messages'] ?? [];
    ticket['viewer_lang'] = data['viewer_lang'];
    return ticket;
  }

  /// 추가 메시지 전송. ``lang_hint`` 동봉 (P8b).
  Future<void> addMessage(int tid, String body) async {
    await _api.post('/api/support/tickets/me/$tid/messages', {
      'body':      body,
      'lang_hint': I18nService.instance.currentLang,
    });
  }

  // ── FAQ ───────────────────────────────────────────────────────────

  /// 공개 FAQ 목록. kind=user 고정, lang 기본 ko.
  Future<List<Map<String, dynamic>>> listFaqs({String lang = 'ko'}) async {
    final data = await _api.get('/api/faqs?kind=user&lang=$lang');
    return (data['faqs'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }
}
