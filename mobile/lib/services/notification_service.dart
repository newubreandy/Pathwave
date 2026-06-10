import 'api_client.dart';

/// 알림 인박스 도메인 API.
///
/// 백엔드 분리:
///   - notification_bp  → 개인 인박스 (스탬프 적립, 쿠폰 발급 등 트랜잭션 기반)
///   - announcement_bp  → 시스템 공지 (super_admin 작성, audience 필터)
///
/// 게스트 모드(미로그인) 안전성:
///   read 류 (`inbox` / `announcements` / `getSettings`) 는 401 발생 시
///   throw 대신 빈 결과를 반환 — 게스트 화면(둘러보기)에서 진입해도 콘솔에
///   빨간 ApiException 안 띄움. UI 는 자연스레 PwEmptyState 로 떨어진다.
///   mutation (`markRead` 등) 은 그대로 throw — 호출 측이 처리.
class NotificationService {
  NotificationService._();
  static final NotificationService instance = NotificationService._();
  factory NotificationService() => instance;

  final _api = ApiClient.instance;

  /// 401 (미인증) 응답을 null 로 안전 변환 — 게스트 모드 진입 시 흔히 발생.
  Future<Map<String, dynamic>?> _getSafe(String path) async {
    try {
      return await _api.get(path);
    } on ApiException catch (e) {
      if (e.statusCode == 401) return null;
      rethrow;
    }
  }

  /// 미읽음 알림 개수 (2026-06-08). 실패 시 0 반환.
  Future<int> unreadCount() async {
    final data = await _getSafe('/api/users/me/notifications/unread-count');
    if (data == null) return 0;
    final v = data['count'];
    if (v is int) return v;
    if (v is num) return v.toInt();
    return 0;
  }

  // ── 개인 인박스 ─────────────────────────────────────────────────────────
  /// 내 알림 목록 (최신 순). 게스트 / 401 → 빈 리스트.
  Future<List<Map<String, dynamic>>> inbox() async {
    final data = await _getSafe('/api/notifications');
    if (data == null) return [];
    return (data['notifications'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  Future<void> markRead(int notificationId) async {
    await _api.post('/api/notifications/$notificationId/read');
  }

  /// 설정 조회. 게스트 / 401 → 빈 맵.
  Future<Map<String, dynamic>> getSettings() async {
    final data = await _getSafe('/api/notifications/settings');
    if (data == null) return {};
    return (data['settings'] as Map?)?.cast<String, dynamic>() ?? {};
  }

  Future<Map<String, dynamic>> updateSettings(Map<String, dynamic> body) {
    return _api.patch('/api/notifications/settings', body);
  }

  // ── 시스템 공지 ─────────────────────────────────────────────────────────
  /// 게스트 / 401 → 빈 리스트.
  Future<List<Map<String, dynamic>>> announcements() async {
    final data = await _getSafe('/api/announcements');
    if (data == null) return [];
    return (data['announcements'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  Future<void> markAnnouncementRead(int aid) async {
    await _api.post('/api/announcements/$aid/read');
  }
}
