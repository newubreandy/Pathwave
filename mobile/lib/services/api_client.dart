import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

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
  static const _kToken = 'jwt_token';

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
    if (r.statusCode == 401) {
      await _storage.delete(key: _kToken);
      throw ApiException(401, body['message']?.toString() ?? '인증이 만료되었습니다.');
    }
    if (r.statusCode == 429) {
      throw ApiException(429, body['message']?.toString() ?? '요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.');
    }
    if (r.statusCode >= 400 || body['success'] == false) {
      throw ApiException(r.statusCode, body['message']?.toString() ?? '요청 실패 (${r.statusCode})', body);
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

  Future<Map<String, dynamic>> delete(String path) async {
    final r = await http.delete(_uri(path), headers: await _headers());
    return _decode(r);
  }
}
