import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../utils/api_config.dart';

class AuthService extends ChangeNotifier {
  static String get _baseUrl => ApiConfig.baseUrl;
  static const _storage = FlutterSecureStorage();

  String? _token;
  Map<String, dynamic>? _user;

  bool get isLoggedIn => _token != null;
  String? get token => _token;
  Map<String, dynamic>? get user => _user;

  AuthService() {
    _loadToken();
  }

  // ── 초기화: 저장된 토큰 로드 ────────────────────────────────────
  Future<void> _loadToken() async {
    _token = await _storage.read(key: 'jwt_token');
    if (_token != null) {
      await _fetchMe();
    }
    notifyListeners();
  }

  Future<void> _fetchMe() async {
    try {
      final res = await http.get(
        Uri.parse('$_baseUrl/api/auth/me'),
        headers: {'Authorization': 'Bearer $_token'},
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _user = data['user'];
      } else {
        await logout();
      }
    } catch (_) {
      await logout();
    }
  }

  // ── 이메일 인증 코드 발송 ────────────────────────────────────────
  Future<Map<String, dynamic>> sendCode(String email) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/auth/send-code'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email}),
    );
    return jsonDecode(res.body);
  }

  // ── 인증 코드 검증 ──────────────────────────────────────────────
  Future<Map<String, dynamic>> verifyCode(String email, String code) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/auth/verify-code'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'code': code}),
    );
    return jsonDecode(res.body);
  }

  // ── 회원가입 ────────────────────────────────────────────────────
  /// consents: [{kind, version, accepted}, ...] — PR #45
  /// birthYear / invitationCode (미성년자) — PR #47
  Future<Map<String, dynamic>> register(
      String email, String code, String password,
      {List<Map<String, dynamic>>? consents,
       int? birthYear,
       String? invitationCode}) async {
    final body = <String, dynamic>{
      'email': email, 'code': code, 'password': password,
    };
    if (consents != null) body['consents'] = consents;
    if (birthYear != null) body['birth_year'] = birthYear;
    if (invitationCode != null && invitationCode.isNotEmpty) {
      body['invitation_code'] = invitationCode;
    }
    final res = await http.post(
      Uri.parse('$_baseUrl/api/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    final data = jsonDecode(res.body);
    if (data['success'] == true) {
      await _saveToken(data['token'], data['user']);
    }
    return data;
  }

  // ── 이메일 로그인 ────────────────────────────────────────────────
  Future<Map<String, dynamic>> login(String email, String password) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    final data = jsonDecode(res.body);
    if (data['success'] == true) {
      await _saveToken(data['token'], data['user']);
    }
    return data;
  }

  // ── Google 로그인 ────────────────────────────────────────────────
  Future<Map<String, dynamic>> signInWithGoogle() async {
    try {
      final googleUser = await GoogleSignIn().signIn();
      if (googleUser == null) return {'success': false, 'message': '취소됨'};

      final googleAuth = await googleUser.authentication;
      final credential  = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken:     googleAuth.idToken,
      );

      final userCred = await FirebaseAuth.instance.signInWithCredential(credential);
      final idToken  = await userCred.user!.getIdToken();

      return await _socialLogin(idToken!, 'google');
    } catch (e) {
      return {'success': false, 'message': e.toString()};
    }
  }

  // ── Apple 로그인 ────────────────────────────────────────────────
  Future<Map<String, dynamic>> signInWithApple() async {
    try {
      final provider = AppleAuthProvider();
      final userCred = await FirebaseAuth.instance.signInWithProvider(provider);
      final idToken  = await userCred.user!.getIdToken();

      return await _socialLogin(idToken!, 'apple');
    } catch (e) {
      return {'success': false, 'message': e.toString()};
    }
  }

  // ── 소셜 로그인 → 백엔드 ─────────────────────────────────────────
  Future<Map<String, dynamic>> _socialLogin(String idToken, String provider) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/auth/social'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'id_token': idToken, 'provider': provider}),
    );
    final data = jsonDecode(res.body);
    if (data['success'] == true) {
      await _saveToken(data['token'], data['user']);
    }
    return data;
  }

  // ── 비밀번호 찾기 ────────────────────────────────────────────────
  Future<Map<String, dynamic>> forgotPassword(String email) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/auth/forgot-password'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email}),
    );
    return jsonDecode(res.body);
  }

  // ── 비밀번호 재설정 ──────────────────────────────────────────────
  Future<Map<String, dynamic>> resetPassword(
      String email, String code, String password) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/auth/reset-password'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'code': code, 'password': password}),
    );
    return jsonDecode(res.body);
  }

  // ── 로그아웃 ────────────────────────────────────────────────────
  Future<void> logout() async {
    await _storage.delete(key: 'jwt_token');
    await GoogleSignIn().signOut();
    await FirebaseAuth.instance.signOut();
    _token = null;
    _user  = null;
    notifyListeners();
  }

  // ── 내부 헬퍼 ───────────────────────────────────────────────────
  Future<void> _saveToken(String token, Map<String, dynamic> user) async {
    _token = token;
    _user  = user;
    await _storage.write(key: 'jwt_token', value: token);
    notifyListeners();
  }

  Map<String, String> get authHeaders => {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer $_token',
  };
}
