/// 백엔드 베이스 URL 중앙 관리.
///
/// 개발: `flutter run --dart-define=API_BASE=http://192.168.1.x:8080`
/// 운영: `flutter build apk --dart-define=API_BASE=https://api.pathwave.kr`
///
/// 미설정 시 안드로이드 에뮬레이터(10.0.2.2) + iOS 시뮬레이터(localhost) 호환 기본값.
class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE',
    defaultValue: 'http://10.0.2.2:8080',
  );
}
