import 'dart:io' show Platform;

import 'package:package_info_plus/package_info_plus.dart';

import 'api_client.dart';

/// 앱 버전 강제/권장 업데이트 체크 — 부팅 시 1회 호출.
///
/// 백엔드 GET /api/version/check?platform=ios|android&current=X.Y.Z
/// 응답:
///   {
///     success: true,
///     platform: 'ios',
///     current: '1.0.0',
///     force_update: false,
///     recommend_update: true,
///     min_supported: '1.0.0',
///     latest: '1.2.0',
///     store_url: '...',
///     force_message: '...',
///   }
///
/// 네트워크 실패 / DB 미등록 platform 의 경우 [VersionCheckResult.skip] 반환.
class VersionCheckResult {
  final bool forceUpdate;
  final bool recommendUpdate;
  final String? minSupported;
  final String? latest;
  final String? current;
  final String? storeUrl;
  final String? forceMessage;

  const VersionCheckResult({
    required this.forceUpdate,
    required this.recommendUpdate,
    this.minSupported,
    this.latest,
    this.current,
    this.storeUrl,
    this.forceMessage,
  });

  /// 네트워크 실패 등으로 체크 못 한 경우 — 통과 처리.
  factory VersionCheckResult.skip() => const VersionCheckResult(
        forceUpdate: false,
        recommendUpdate: false,
      );

  bool get needsAction => forceUpdate || recommendUpdate;
}

class VersionService {
  VersionService._();
  static final VersionService instance = VersionService._();
  factory VersionService() => instance;

  /// 현재 플랫폼 코드 ('ios' | 'android'). 그 외 (web/desktop) 는 null.
  String? get _platform {
    if (Platform.isIOS) return 'ios';
    if (Platform.isAndroid) return 'android';
    return null;
  }

  /// 부팅 시 호출. 네트워크 실패 / 비지원 플랫폼 시 [VersionCheckResult.skip].
  Future<VersionCheckResult> check() async {
    final platform = _platform;
    if (platform == null) return VersionCheckResult.skip();
    final info = await PackageInfo.fromPlatform();
    final current = info.version; // 'X.Y.Z'
    try {
      final res = await ApiClient.instance.get(
        '/api/version/check?platform=$platform&current=$current',
      );
      return VersionCheckResult(
        forceUpdate:      res['force_update']     == true,
        recommendUpdate:  res['recommend_update'] == true,
        minSupported:     res['min_supported'] as String?,
        latest:           res['latest']        as String?,
        current:          current,
        storeUrl:         res['store_url']     as String?,
        forceMessage:     res['force_message'] as String?,
      );
    } catch (_) {
      // 네트워크 실패 등은 통과 (출시 직후 백엔드 미응답 상황에서 앱이 막히는 것 방지).
      return VersionCheckResult.skip();
    }
  }
}
