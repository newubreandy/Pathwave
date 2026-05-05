import 'api_client.dart';

/// 부모 → 자녀(미성년자) 초대 발급 (PR #47).
class ParentInviteService {
  ParentInviteService._();
  static final ParentInviteService instance = ParentInviteService._();
  factory ParentInviteService() => instance;

  final _api = ApiClient.instance;

  /// liability_accepted: 보호자가 자녀 이용에 대한 법적 책임 부담 동의 (필수).
  Future<Map<String, dynamic>> create({
    required bool liabilityAccepted,
    String? inviteeEmail,
  }) async {
    final body = <String, dynamic>{'liability_accepted': liabilityAccepted};
    if (inviteeEmail != null && inviteeEmail.isNotEmpty) {
      body['invitee_email'] = inviteeEmail;
    }
    final data = await _api.post('/api/invitations/parent', body);
    return (data['invitation'] as Map?)?.cast<String, dynamic>() ?? {};
  }
}
