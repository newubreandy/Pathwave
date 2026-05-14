import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../utils/api_config.dart';
import 'api_client.dart';

class AuthService extends ChangeNotifier {
  static String get _baseUrl => ApiConfig.baseUrl;
  static const _storage = FlutterSecureStorage();

  // 3 콘솔 토큰 키 통일 (provider-web localStorage 와 동일 명명).
  static const _kToken        = 'pathwave_token';
  static const _kRefreshToken = 'pathwave_refresh_token';
  static const _kUser         = 'pathwave_user';

  String? _token;
  Map<String, dynamic>? _user;

  bool get isLoggedIn => _token != null;
  String? get token => _token;
  Map<String, dynamic>? get user => _user;

  // 3 콘솔 공개 API 시그니처 통일 (provider-web AuthService 와 1:1).
  String? getToken() => _token;
  Map<String, dynamic>? getCurrentUser() => _user;
  bool isAuthenticated() => _token != null;

  AuthService() {
    // PR #60 — ApiClient 가 401 을 받으면 메모리 상태 비우고 redirect 트리거
    ApiClient.onUnauthorized = _handleUnauthorized;
    _loadToken();
  }

  void _handleUnauthorized() {
    if (_token == null) return;
    _token = null;
    _user  = null;
    // secure storage 는 ApiClient 가 이미 비웠음
    notifyListeners();
  }

  // ── 초기화: 저장된 토큰 로드 ────────────────────────────────────
  Future<void> _loadToken() async {
    _token = await _storage.read(key: _kToken);
    if (_token != null) {
      // user 캐시 hydrate — provider-web 의 localStorage('pathwave_user') 와 동일 패턴.
      final cachedUser = await _storage.read(key: _kUser);
      if (cachedUser != null) {
        try { _user = jsonDecode(cachedUser) as Map<String, dynamic>; } catch (_) {}
      }
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
      await _saveToken(data['token'], data['user'], refreshToken: data['refresh_token']);
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
      await _saveToken(data['token'], data['user'], refreshToken: data['refresh_token']);
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

  // ── Facebook / Kakao / Naver (PR #68) ───────────────────────────
  // 운영 활성화 절차 (각 Provider 별):
  //   Facebook: developers.facebook.com 앱 생성 → flutter_facebook_auth 패키지 추가
  //             + iOS Info.plist FacebookAppID, Android strings.xml facebook_app_id
  //   Kakao:    developers.kakao.com 앱 생성 → kakao_flutter_sdk 패키지 추가
  //             + iOS LSApplicationQueriesSchemes (kakaokompassauth, kakaolink)
  //             + Android NativeAppKey, AndroidManifest.xml 의 redirect scheme
  //   Naver:    developers.naver.com 애플리케이션 등록 → flutter_naver_login 패키지 추가
  //             + iOS Info.plist (CFBundleURLSchemes), Android AndroidManifest.xml
  // 백엔드는 `/api/auth/social` 의 provider 필드만 키 매칭하면 받음.
  Future<Map<String, dynamic>> signInWithFacebook() async {
    return _stubSocialNotice('facebook', 'Facebook');
  }

  Future<Map<String, dynamic>> signInWithKakao() async {
    return _stubSocialNotice('kakao', '카카오');
  }

  Future<Map<String, dynamic>> signInWithNaver() async {
    return _stubSocialNotice('naver', '네이버');
  }

  Future<Map<String, dynamic>> _stubSocialNotice(String key, String label) async {
    return {
      'success': false,
      'message': '$label 로그인은 Developer Console 에서 API 키 발급 + '
                 '네이티브 설정 (Info.plist / AndroidManifest.xml) 후 활성됩니다.\n'
                 '코드 흐름은 _socialLogin(idToken, "$key") 로 백엔드에 전달.',
    };
  }

  // ── 둘러보기 (PR #68) — 로그인 없이 화면 미리보기 ────────────
  /// 가짜 토큰 + 익명 사용자를 메모리에 주입.
  /// 실 API 호출은 401 로 실패하지만 UI 네비게이션/렌더링은 가능.
  Future<void> enterPreviewMode() async {
    _token = 'preview-mode-token';
    _user  = {
      'id': 0,
      'email': 'preview@dev.local',
      'name': '둘러보기',
      'provider': 'preview',
    };
    notifyListeners();
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
      await _saveToken(data['token'], data['user'], refreshToken: data['refresh_token']);
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

  // ── 비밀번호 변경 (PR #63) ──────────────────────────────────────
  Future<Map<String, dynamic>> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/auth/change-password'),
      headers: authHeaders,
      body: jsonEncode({
        'current_password': currentPassword,
        'new_password':     newPassword,
      }),
    );
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ── 회원 탈퇴 (PR #55) — Apple 5.1.1(v) / Google Play 정책 ─────
  Future<Map<String, dynamic>> deleteAccount({String? password}) async {
    final body = <String, dynamic>{};
    if (password != null && password.isNotEmpty) body['password'] = password;
    final res = await http.delete(
      Uri.parse('$_baseUrl/api/auth/me'),
      headers: authHeaders,
      body: jsonEncode(body),
    );
    final data = jsonDecode(res.body);
    if (data['success'] == true) {
      await logout();
    }
    return data;
  }

  // ── 로그아웃 ────────────────────────────────────────────────────
  Future<void> logout() async {
    await _storage.delete(key: _kToken);
    await _storage.delete(key: _kRefreshToken);
    await _storage.delete(key: _kUser);
    await GoogleSignIn().signOut();
    await FirebaseAuth.instance.signOut();
    _token = null;
    _user  = null;
    notifyListeners();
  }

  // ── 내부 헬퍼 ───────────────────────────────────────────────────
  Future<void> _saveToken(
    String token,
    Map<String, dynamic> user, {
    String? refreshToken,
  }) async {
    _token = token;
    _user  = user;
    await _storage.write(key: _kToken, value: token);
    await _storage.write(key: _kUser,  value: jsonEncode(user));
    if (refreshToken != null && refreshToken.isNotEmpty) {
      await _storage.write(key: _kRefreshToken, value: refreshToken);
    }
    notifyListeners();
  }

  Map<String, String> get authHeaders => {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer $_token',
  };
}
