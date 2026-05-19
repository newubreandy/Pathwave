import 'dart:io' show Platform;

/// 백엔드 베이스 URL 중앙 관리.
///
/// 우선순위:
///   1) --dart-define=API_BASE=...  (실 디바이스 / 운영 / 커스텀)
///   2) Android emulator     → http://10.0.2.2:8080   (호스트 머신 가상 IP)
///   3) iOS simulator / 그 외 → http://localhost:8080 (호스트와 네트워크 공유)
///
/// 예:
///   flutter run                                                    # 자동 분기
///   flutter run --dart-define=API_BASE=http://192.168.1.7:8080     # 실 디바이스
///   flutter build apk --dart-define=API_BASE=https://api.pathwave.kr  # 운영
class ApiConfig {
  static const String _envBase =
      String.fromEnvironment('API_BASE', defaultValue: '');

  /// 부팅 시점에 1회 계산되는 기본 base URL.
  ///
  /// Web/desktop 환경에서 ``Platform.is*`` 가 예외를 던질 수 있어 try/catch
  /// 로 감싸고 localhost 로 fallback.
  static final String baseUrl = _resolve();

  static String _resolve() {
    if (_envBase.isNotEmpty) return _envBase;
    try {
      if (Platform.isAndroid) return 'http://10.0.2.2:8080';
    } catch (_) { /* web / desktop fallback */ }
    return 'http://localhost:8080';
  }
}
