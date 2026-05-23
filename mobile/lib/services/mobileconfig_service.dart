import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:url_launcher/url_launcher.dart';

import '../utils/api_config.dart';

/// P17/P16 — iOS .mobileconfig 다건 설치 트리거.
///
/// 매장의 모든 active WiFi 를 1개 Apple Configuration Profile 로 받아
/// iOS 1탭 설치 → 모든 WiFi 자동 추가 → AP 간 자동 핸드오프.
///
/// iOS Safari 가 외부 URL 을 받으면 Authorization 헤더를 못 붙이므로,
/// 백엔드는 ``?token=`` 쿼리도 받도록 했다(P16).
class MobileconfigService {
  MobileconfigService._();
  static final MobileconfigService instance = MobileconfigService._();
  factory MobileconfigService() => instance;

  static const _storage = FlutterSecureStorage();

  /// 매장 fid 의 .mobileconfig 다운로드 URL — Safari 가 자동으로 설치 UI 호출.
  Future<Uri?> buildVenueUrl(int facilityId) async {
    final token = await _storage.read(key: 'pathwave_token');
    if (token == null || token.isEmpty) {
      debugPrint('[mobileconfig] 토큰 없음 — 비로그인 상태');
      return null;
    }
    return Uri.parse(
      '${ApiConfig.baseUrl}/api/beacon/wifi/venue/$facilityId.mobileconfig'
      '?token=${Uri.encodeQueryComponent(token)}',
    );
  }

  /// iOS 외부 브라우저(Safari) 로 .mobileconfig URL 열기 →
  /// 시스템이 자동으로 "프로필 설치" UI 호출.
  ///
  /// Android 는 .mobileconfig 미지원이라 단순 fallback(다운로드만).
  ///
  /// Returns ``true`` if launch initiated.
  Future<bool> installVenueWifi(int facilityId) async {
    final uri = await buildVenueUrl(facilityId);
    if (uri == null) return false;
    try {
      // externalApplication = Safari (iOS) / Chrome (Android) 강제.
      return await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (e) {
      debugPrint('[mobileconfig] launchUrl 실패: $e');
      return false;
    }
  }
}
