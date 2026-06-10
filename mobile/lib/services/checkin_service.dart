/// P22-a (2026-05-26): 회원 QR 체크인 클라이언트.
///
/// 백엔드 routes/checkin.py 호출 헬퍼.
/// - issueMemberQr() — 본인 회원 QR 토큰 발급 (60초 유효)
///
/// 2026-06-09: 토큰 저장소를 AuthService 와 일치시키기 위해 ApiClient 패턴으로 통일.
/// (기존 SharedPreferences 'access_token' 키는 AuthService 가 사용하지 않아 미스매치)
/// 점주 측 verify 는 provider-web 에서 호출 (mobile 미사용).
library;

import 'api_client.dart';

class CheckinService {
  /// 본인 회원 QR 토큰 발급. 60초 유효.
  ///
  /// 반환: { token, expiresIn }
  /// 실패 시 [Exception] throw.
  Future<({String token, int expiresIn})> issueMemberQr() async {
    final data = await ApiClient.instance.post('/api/checkin/member-qr');
    if (data['success'] != true) {
      throw Exception(data['message']?.toString() ?? '회원 QR 발급 실패');
    }
    final token = data['token']?.toString() ?? '';
    final exp = data['expires_in'];
    return (
      token:     token,
      expiresIn: exp is int ? exp : (exp is num ? exp.toInt() : 60),
    );
  }
}
