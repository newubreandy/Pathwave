/// P22-c (2026-05-27): 친구초대 QR 서비스.
///
/// 기존 invitations API (routes/invitation.py) 활용. channel='qr' 로 발급.
/// 가입 추적은 users.invited_via_code 컬럼에 저장 (백엔드가 처리).
///
/// 초대보상 구조는 v1 hook 만 (rewarded=0 으로 발급, 후속 PR 에서 보상 지급).
import 'api_client.dart';

class FriendInviteService {
  FriendInviteService([ApiClient? api]) : _api = api ?? ApiClient.instance;
  final ApiClient _api;

  /// 친구초대 QR 코드 발급. channel='qr'.
  ///
  /// @returns {code, channel, expires_at, ...}  (invitations 응답)
  Future<Map<String, dynamic>> createQrInvite() async {
    final data = await _api.post('/api/invitations', {
      'channel': 'qr',
    });
    return Map<String, dynamic>.from(data);
  }

  /// 본인이 발급한 초대 목록 (가입 완료 여부 포함).
  Future<List<Map<String, dynamic>>> listMyInvites() async {
    final data = await _api.get('/api/invitations');
    final list = (data['invitations'] as List?) ?? [];
    return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }
}
