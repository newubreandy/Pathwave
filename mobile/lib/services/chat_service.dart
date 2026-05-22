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

  /// 메시지 전송. 백엔드 스키마: `{body: <text>}`.
  Future<Map<String, dynamic>> send(int roomId, String text) async {
    final data = await _api.post('/api/chat/rooms/$roomId/messages', {'body': text});
    return (data['message'] as Map?)?.cast<String, dynamic>() ?? {};
  }

  /// SSE 스트림 — 새 메시지 push (지수 backoff 자동 재연결 포함).
  ///
  /// - 사용: `chatService.streamMessages(roomId).listen((msg) {...})`
  /// - 종료: stream subscription cancel → 재연결 루프도 즉시 중단됨.
  /// - 재연결: 끊김(정상 종료·오류) 시 1→2→4→8→16→30초 간격으로 재연결.
  ///           재연결 시 마지막으로 받은 메시지 id 를 `after_id` 로 전달해
  ///           누락 없이 이어받음.
  Stream<Map<String, dynamic>> streamMessages(int roomId) {
    // StreamController 로 감싸 cancel 시 재연결 루프를 확실히 중단한다.
    late StreamController<Map<String, dynamic>> controller;
    bool cancelled = false;
    int lastId = 0;

    Future<void> connect() async {
      int backoff = 1; // 초

      while (!cancelled) {
        final token = await _storage.read(key: 'pathwave_token');
        final uri = Uri.parse(
          '${ApiConfig.baseUrl}/api/chat/rooms/$roomId/stream'
          '${lastId > 0 ? '?after_id=$lastId' : ''}',
        );
        final req = http.Request('GET', uri);
        req.headers['Accept'] = 'text/event-stream';
        if (token != null) req.headers['Authorization'] = 'Bearer $token';

        final client = http.Client();
        try {
          final resp = await client.send(req);
          if (resp.statusCode != 200) {
            // 401/403 등 — 재연결해도 의미 없으므로 error 전파 후 중단.
            if (resp.statusCode == 401 || resp.statusCode == 403) {
              if (!cancelled) {
                controller.addError(
                    Exception('SSE 인증 오류 (${resp.statusCode})'));
                await controller.close();
              }
              return;
            }
            // 그 외 서버 오류 — backoff 후 재시도.
            throw Exception('SSE 연결 실패 (${resp.statusCode})');
          }

          // 연결 성공 → backoff 리셋.
          backoff = 1;

          // SSE 라인 파싱: 'event: message\ndata: {json}\n\n' 블록 단위.
          String buffer = '';
          await for (final chunk in resp.stream.transform(utf8.decoder)) {
            if (cancelled) break;
            buffer += chunk;
            while (true) {
              final idx = buffer.indexOf('\n\n');
              if (idx < 0) break;
              final block = buffer.substring(0, idx);
              buffer = buffer.substring(idx + 2);
              String? dataLine;
              for (final line in block.split('\n')) {
                // 'event: message' 블록의 data 줄만 처리
                // (': keepalive', 'retry:' 등은 건너뜀)
                if (line.startsWith('data:')) {
                  dataLine = line.substring(5).trim();
                }
              }
              if (dataLine == null || dataLine.isEmpty) continue;
              try {
                final obj = jsonDecode(dataLine);
                if (obj is Map<String, dynamic>) {
                  if (!cancelled) controller.add(obj);
                  final id = obj['id'];
                  if (id is int && id > lastId) lastId = id;
                }
              } catch (_) {/* 비-JSON (heartbeat 등) 무시 */}
            }
          }
          // 정상 종료(5분 서버 의도 종료 포함) → 즉시 재연결(backoff 없이).
        } catch (_) {
          // 오류 → backoff 후 재연결.
          if (!cancelled) {
            await Future.delayed(Duration(seconds: backoff));
            backoff = (backoff * 2).clamp(1, 30);
          }
        } finally {
          client.close();
        }
      }
    }

    controller = StreamController<Map<String, dynamic>>(
      onListen: () => connect(),
      onCancel: () { cancelled = true; },
    );

    return controller.stream;
  }
}
