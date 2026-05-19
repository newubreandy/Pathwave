import 'api_client.dart';

/// 알림 카테고리별 on/off (mobile = 사용자 측).
///
/// 백엔드 (Phase L):
///   GET  /api/users/me/notification-preferences
///   PUT  /api/users/me/notification-preferences/{category}
class NotificationPreference {
  final String category;
  final String label;
  final bool enabled;

  const NotificationPreference({
    required this.category,
    required this.label,
    required this.enabled,
  });

  factory NotificationPreference.fromJson(Map<String, dynamic> j) =>
      NotificationPreference(
        category: j['category'] as String,
        label:    j['label']    as String,
        enabled:  j['enabled']  as bool,
      );
}

class NotificationPreferencesService {
  NotificationPreferencesService._();
  static final NotificationPreferencesService instance =
      NotificationPreferencesService._();
  factory NotificationPreferencesService() => instance;

  /// 카탈로그 + 현재 enabled 상태.
  Future<List<NotificationPreference>> list() async {
    final res = await ApiClient.instance
        .get('/api/users/me/notification-preferences');
    final list = (res['preferences'] as List? ?? []);
    return list
        .map((e) => NotificationPreference.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// 특정 카테고리 on/off.
  Future<void> set(String category, bool enabled) async {
    await ApiClient.instance.put(
      '/api/users/me/notification-preferences/$category',
      body: {'enabled': enabled},
    );
  }
}
