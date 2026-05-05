import 'dart:io' show Platform;
import 'package:firebase_messaging/firebase_messaging.dart';

import 'api_client.dart';

/// 푸시 토큰 등록 + FCM/APNs 통합.
///
/// 사용:
///   await PushService().init();   // 권한 + 토큰 백엔드 등록
class PushService {
  PushService._();
  static final PushService instance = PushService._();
  factory PushService() => instance;

  final _api = ApiClient.instance;
  String? _token;

  String? get token => _token;

  /// 초기화 — 권한 요청 + 토큰 발급 + 백엔드 등록.
  Future<void> init() async {
    final messaging = FirebaseMessaging.instance;

    // iOS: 권한 명시적 요청. Android 13+ 도 POST_NOTIFICATIONS 필요.
    final perm = await messaging.requestPermission(
      alert: true, badge: true, sound: true,
    );
    if (perm.authorizationStatus == AuthorizationStatus.denied) return;

    // FCM 토큰 (Android: 기본 / iOS: APNs 위에 wrap).
    _token = await messaging.getToken();
    if (_token == null) return;

    final platform = Platform.isIOS ? 'apns' : 'fcm';
    try {
      await _api.post('/api/push/register-token', {
        'token': _token,
        'platform': platform,
      });
    } catch (_) {/* 회원 미인증 등은 무시, 추후 로그인 시 재등록 */}

    // 토큰 회전 시 자동 재등록.
    messaging.onTokenRefresh.listen((newToken) async {
      _token = newToken;
      try {
        await _api.post('/api/push/register-token', {
          'token': newToken, 'platform': platform,
        });
      } catch (_) {}
    });
  }

  Future<void> unregister() async {
    if (_token == null) return;
    try {
      await _api.delete('/api/push/register-token?token=$_token');
    } catch (_) {}
    _token = null;
  }
}
