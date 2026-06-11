import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import 'i18n_service.dart';
import '../utils/api_config.dart';

/// 공통 HTTP 클라이언트 — JWT 자동 주입 + JSON 직렬화 + 에러 매핑.
///
/// 사용:
///   final api = ApiClient();
///   final data = await api.get('/api/notifications');
class ApiException implements Exception {
  final int statusCode;
  final String message;
  final dynamic payload;
  ApiException(this.statusCode, this.message, [this.payload]);
  @override
  String toString() => 'ApiException($statusCode): $message';
}

class ApiClient {
  ApiClient._();
  static final ApiClient instance = ApiClient._();
  factory ApiClient() => instance;

  static const _storage = FlutterSecureStorage();
  // PR — 3 콘솔 토큰 키 통일 (mobile/provider-web 공통).
  static const _kToken        = 'pathwave_token';
  static const _kRefreshToken = 'pathwave_refresh_token';
  static const _kUser         = 'pathwave_user';

  /// PR #60 — 401 발생 시 호출되는 글로벌 콜백.
  /// AuthService 가 등록하면 메모리 토큰/유저를 비우고 notifyListeners() —
  /// 그러면 go_router redirect 가 자동으로 /auth/login 으로 보냄.
  static void Function()? onUnauthorized;

  Future<String?> _token() => _storage.read(key: _kToken);

  Future<Map<String, String>> _headers({Map<String, String>? extra}) async {
    final h = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    final t = await _token();
    if (t != null && t.isNotEmpty) h['Authorization'] = 'Bearer $t';
    if (extra != null) h.addAll(extra);
    return h;
  }

  Uri _uri(String path) {
    final base = ApiConfig.baseUrl;
    return Uri.parse(base + path);
  }

  Future<Map<String, dynamic>> _decode(http.Response r) async {
    Map<String, dynamic> body;
    try {
      body = jsonDecode(r.body) as Map<String, dynamic>;
    } catch (_) {
      body = {};
    }
    final t = I18nService.instance;
    if (r.statusCode == 401) {
      await _storage.delete(key: _kToken);
      await _storage.delete(key: _kRefreshToken);
      await _storage.delete(key: _kUser);
      onUnauthorized?.call();
      throw ApiException(401, body['message']?.toString() ??
          t.t('mobile.api.auth_expired', defaultValue: '인증이 만료되었습니다.'));
    }
    if (r.statusCode == 429) {
      throw ApiException(429, body['message']?.toString() ??
          t.t('mobile.api.too_many_requests', defaultValue: '요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.'));
    }
    if (r.statusCode >= 400 || body['success'] == false) {
      throw ApiException(r.statusCode, body['message']?.toString() ??
          '${t.t('mobile.api.request_failed', defaultValue: '요청 실패')} (${r.statusCode})', body);
    }
    return body;
  }

  Future<Map<String, dynamic>> get(String path) async {
    final r = await http.get(_uri(path), headers: await _headers());
    return _decode(r);
  }

  Future<Map<String, dynamic>> post(String path, [Map<String, dynamic>? body]) async {
    final r = await http.post(
      _uri(path),
      headers: await _headers(),
      body: body == null ? null : jsonEncode(body),
    );
    return _decode(r);
  }

  Future<Map<String, dynamic>> patch(String path, Map<String, dynamic> body) async {
    final r = await http.patch(
      _uri(path),
      headers: await _headers(),
      body: jsonEncode(body),
    );
    return _decode(r);
  }

  Future<Map<String, dynamic>> put(String path, {Map<String, dynamic>? body}) async {
    final r = await http.put(
      _uri(path),
      headers: await _headers(),
      body: body == null ? null : jsonEncode(body),
    );
    return _decode(r);
  }

  /// Multipart 업로드 (사진 첨부 등). 2026-06-08 추가.
  ///
  /// - [fields]  : 일반 form 필드 (문자열).
  /// - [files]   : (필드명, 로컬 경로) 튜플 리스트. 같은 필드명 여러 번 가능.
  Future<Map<String, dynamic>> postMultipart(
    String path, {
    Map<String, String>? fields,
    List<MapEntry<String, String>>? files,
  }) async {
    final req = http.MultipartRequest('POST', _uri(path));
    final t = await _token();
    if (t != null && t.isNotEmpty) req.headers['Authorization'] = 'Bearer $t';
    if (fields != null) req.fields.addAll(fields);
    if (files != null) {
      for (final e in files) {
        req.files.add(await http.MultipartFile.fromPath(e.key, e.value));
      }
    }
    final streamed = await req.send();
    final r = await http.Response.fromStream(streamed);
    return _decode(r);
  }

  Future<Map<String, dynamic>> delete(String path,
      [Map<String, dynamic>? body]) async {
    // 2026-06-11 — 일부 라우트(푸시 토큰 해제 등)는 DELETE 에 JSON body 요구.
    final r = await http.delete(
      _uri(path),
      headers: await _headers(),
      body: body != null ? jsonEncode(body) : null,
    );
    return _decode(r);
  }
}
