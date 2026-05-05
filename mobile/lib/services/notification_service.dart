import 'api_client.dart';

/// 알림 인박스 도메인 API.
///
/// 백엔드 분리:
///   - notification_bp  → 개인 인박스 (스탬프 적립, 쿠폰 발급 등 트랜잭션 기반)
///   - announcement_bp  → 시스템 공지 (super_admin 작성, audience 필터)
class NotificationService {
  NotificationService._();
  static final NotificationService instance = NotificationService._();
  factory NotificationService() => instance;

  final _api = ApiClient.instance;

  // ── 개인 인박스 ─────────────────────────────────────────────────────────
  /// 내 알림 목록 (최신 순).
  Future<List<Map<String, dynamic>>> inbox() async {
    final data = await _api.get('/api/notifications');
    return (data['notifications'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  Future<void> markRead(int notificationId) async {
    await _api.post('/api/notifications/$notificationId/read');
  }

  Future<Map<String, dynamic>> getSettings() async {
    final data = await _api.get('/api/notifications/settings');
    return (data['settings'] as Map?)?.cast<String, dynamic>() ?? {};
  }

  Future<Map<String, dynamic>> updateSettings(Map<String, dynamic> body) {
    return _api.patch('/api/notifications/settings', body);
  }

  // ── 시스템 공지 ─────────────────────────────────────────────────────────
  Future<List<Map<String, dynamic>>> announcements() async {
    final data = await _api.get('/api/announcements');
    return (data['announcements'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  Future<void> markAnnouncementRead(int aid) async {
    await _api.post('/api/announcements/$aid/read');
  }
}
