import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../utils/api_config.dart';
import 'api_client.dart';

/// 1:1 채팅 + SSE 실시간 스트림.
///
/// 백엔드: chat_bp (PR #16) + SSE 스트림(PR #21) — `/api/chat/rooms/<id>/stream`
class ChatService {
  ChatService._();
  static final ChatService instance = ChatService._();
  factory ChatService() => instance;

  final _api = ApiClient.instance;
  static const _storage = FlutterSecureStorage();

  Future<List<Map<String, dynamic>>> rooms() async {
    final data = await _api.get('/api/chat/rooms');
    return (data['rooms'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  /// 시설 ID 기반 채팅방 진입 (없으면 생성).
  Future<Map<String, dynamic>> openRoom(int facilityId) async {
    final data = await _api.post('/api/facilities/$facilityId/chat/rooms');
    return (data['room'] as Map?)?.cast<String, dynamic>() ?? {};
  }

  Future<Map<String, dynamic>> roomDetail(int roomId) async {
    final data = await _api.get('/api/chat/rooms/$roomId');
    return (data['room'] as Map?)?.cast<String, dynamic>() ?? {};
  }

  Future<void> markRead(int roomId) async {
    await _api.post('/api/chat/rooms/$roomId/read');
  }

  /// 메시지 페이지 로드 (?before_id=, ?limit=).
  Future<List<Map<String, dynamic>>> messages(
    int roomId, {int? beforeId, int limit = 50}
  ) async {
    final params = <String, String>{'limit': limit.toString()};
    if (beforeId != null) params['before_id'] = beforeId.toString();
    final qs = params.entries.map((e) => '${e.key}=${e.value}').join('&');
    final data = await _api.get('/api/chat/rooms/$roomId/messages?$qs');
    return (data['messages'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  Future<Map<String, dynamic>> send(int roomId, String text) async {
    final data = await _api.post('/api/chat/rooms/$roomId/messages', {'text': text});
    return (data['message'] as Map?)?.cast<String, dynamic>() ?? {};
  }

  /// SSE 스트림 — 새 메시지 push.
  /// - 사용: `chatService.streamMessages(roomId).listen((msg) {...})`
  /// - 종료: stream subscription cancel
  Stream<Map<String, dynamic>> streamMessages(int roomId) async* {
    final token = await _storage.read(key: 'jwt_token');
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/chat/rooms/$roomId/stream');
    final req = http.Request('GET', uri);
    req.headers['Accept'] = 'text/event-stream';
    if (token != null) req.headers['Authorization'] = 'Bearer $token';

    final client = http.Client();
    try {
      final resp = await client.send(req);
      if (resp.statusCode != 200) {
        throw Exception('SSE 연결 실패 (${resp.statusCode})');
      }
      // SSE 라인 파싱: 'data: {json}\n\n' 단위로 잘라서 emit.
      String buffer = '';
      await for (final chunk in resp.stream.transform(utf8.decoder)) {
        buffer += chunk;
        while (true) {
          final idx = buffer.indexOf('\n\n');
          if (idx < 0) break;
          final block = buffer.substring(0, idx);
          buffer = buffer.substring(idx + 2);
          for (final line in block.split('\n')) {
            if (!line.startsWith('data:')) continue;
            final payload = line.substring(5).trim();
            if (payload.isEmpty) continue;
            try {
              final obj = jsonDecode(payload);
              if (obj is Map<String, dynamic>) yield obj;
            } catch (_) {/* heartbeat / 비-JSON */}
          }
        }
      }
    } finally {
      client.close();
    }
  }
}
