import 'dart:io' show Platform;

import 'package:flutter/services.dart';

/// 매장 WiFi 자동 가입을 OS 에 요청 (PR #49).
///
/// 백엔드 BLE 핸드셰이크에서 받은 SSID/password 를 native (Kotlin/Swift) 측에
/// 전달 → OS API 가 사용자에게 가입 동의를 표시 후 등록.
///
/// 플랫폼:
///   - Android 10+: WifiNetworkSuggestion (백그라운드 자동 연결, 1회 알림)
///   - Android  9-: 미지원 (`unsupported_os` 에러)
///   - iOS 11+:    NEHotspotConfiguration (capability 활성화 필수)
class WifiConnector {
  WifiConnector._();
  static final WifiConnector instance = WifiConnector._();
  factory WifiConnector() => instance;

  static const _channel = MethodChannel('pathwave/wifi');

  /// SSID/비밀번호로 WiFi 가입 요청. 결과 dict:
  ///   { ok: true, method: 'suggestion'|'applied'|'alreadyAssociated' }
  /// 실패 시 [PlatformException] 던짐.
  Future<Map<String, Object?>> connect({
    required String ssid,
    required String password,
  }) async {
    if (!_isSupportedPlatform()) {
      throw _unsupported();
    }
    final res = await _channel.invokeMethod<Map<Object?, Object?>>(
      'connect', {'ssid': ssid, 'password': password},
    );
    return (res ?? <Object?, Object?>{}).map(
      (k, v) => MapEntry(k.toString(), v),
    );
  }

  Future<void> remove({required String ssid}) async {
    if (!_isSupportedPlatform()) return;
    try {
      await _channel.invokeMethod('remove', {'ssid': ssid});
    } catch (_) {/* 정리 실패는 무시 */}
  }

  bool _isSupportedPlatform() => Platform.isAndroid || Platform.isIOS;

  PlatformException _unsupported() => PlatformException(
    code: 'unsupported_platform',
    message: '본 기능은 Android / iOS 에서만 지원됩니다.',
  );
}
