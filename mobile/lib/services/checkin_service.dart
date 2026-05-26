/// P22-a (2026-05-26): 회원 QR 체크인 클라이언트.
///
/// 백엔드 routes/checkin.py 호출 헬퍼.
/// - issueMemberQr() — 본인 회원 QR 토큰 발급 (60초 유효)
///
/// 점주 측 verify 는 provider-web 에서 호출 (mobile 미사용).
library;

import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../utils/api_config.dart';

class CheckinService {
  /// 본인 회원 QR 토큰 발급. 60초 유효.
  ///
  /// 반환: { token, expiresIn }
  /// 실패 시 [Exception] throw.
  Future<({String token, int expiresIn})> issueMemberQr() async {
    final prefs = await SharedPreferences.getInstance();
    final access = prefs.getString('access_token');
    if (access == null || access.isEmpty) {
      throw Exception('로그인이 필요합니다.');
    }

    final uri = Uri.parse('${ApiConfig.baseUrl}/api/checkin/member-qr');
    final res = await http.post(
      uri,
      headers: {
        'Content-Type':  'application/json',
        'Authorization': 'Bearer $access',
      },
    );

    if (res.statusCode != 200) {
      throw Exception('회원 QR 발급 실패 (${res.statusCode}): ${res.body}');
    }

    final body = jsonDecode(res.body) as Map<String, dynamic>;
    if (body['success'] != true) {
      throw Exception(body['message']?.toString() ?? '회원 QR 발급 실패');
    }

    return (
      token:     body['token'] as String,
      expiresIn: body['expires_in'] as int,
    );
  }
}
