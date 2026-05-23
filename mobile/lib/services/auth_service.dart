import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:kakao_flutter_sdk_user/kakao_flutter_sdk_user.dart' as kakao;
import 'package:flutter_naver_login/flutter_naver_login.dart';

import '../utils/api_config.dart';
import 'api_client.dart';
import 'i18n_service.dart';

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

  // ── 이메일 인증 코드 발송 (P8d — 디바이스 lang 동봉) ──────────────
  Future<Map<String, dynamic>> sendCode(String email) async {
    // P8d — 가입 전이라 users.language 없음. 디바이스 lang 을 body 에 동봉.
    //       백엔드가 ko/en 자동 분기 (P12 정책과 일관).
    final res = await http.post(
      Uri.parse('$_baseUrl/api/auth/send-code'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'lang':  I18nService.instance.currentLang,
      }),
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
    // KAKAO_NATIVE_APP_KEY 가 주입되면 native SDK 로 authorization_code 획득,
    // 없으면 (dev/CI) 백엔드 stub 흐름으로만 검증.
    const kakaoKey = String.fromEnvironment('KAKAO_NATIVE_APP_KEY', defaultValue: '');
    if (kakaoKey.isEmpty) {
      return _stubSocialNotice('kakao', '카카오');
    }
    try {
      kakao.KakaoSdk.init(nativeAppKey: kakaoKey);
      final token = await kakao.UserApi.instance.loginWithKakaoAccount();
      return await _socialExchange(token.accessToken, 'kakao');
    } catch (e) {
      return {'success': false, 'message': '카카오 로그인 실패: $e'};
    }
  }

  Future<Map<String, dynamic>> signInWithNaver() async {
    // NAVER_CONSUMER_KEY 가 주입되면 native SDK 로 access token 획득,
    // 없으면 (dev/CI) 백엔드 stub 흐름으로만 검증.
    const naverKey = String.fromEnvironment('NAVER_CONSUMER_KEY', defaultValue: '');
    if (naverKey.isEmpty) {
      return _stubSocialNotice('naver', '네이버');
    }
    try {
      final result = await FlutterNaverLogin.logIn();
      // flutter_naver_login 응답 형태는 버전에 따라 다름 — accessToken.accessToken
      // 또는 account.accessToken. 두 케이스 모두 안전하게 시도.
      final token = result.accessToken?.accessToken ?? '';
      if (token.isEmpty) {
        return {'success': false, 'message': '네이버 로그인 취소 또는 실패'};
      }
      return await _socialExchange(token, 'naver');
    } catch (e) {
      return {'success': false, 'message': '네이버 로그인 실패: $e'};
    }
  }

  Future<Map<String, dynamic>> _stubSocialNotice(String key, String label) async {
    return {
      'success': false,
      'message': '$label 로그인은 Developer Console 에서 API 키 발급 + '
                 '네이티브 설정 (Info.plist / AndroidManifest.xml) 후 활성됩니다.\n'
                 '코드 흐름은 _socialExchange(accessToken, "$key") 로 백엔드에 전달.',
    };
  }

  // ── 카카오/네이버 authorization_code → 백엔드 exchange ─────────
  Future<Map<String, dynamic>> _socialExchange(
      String accessToken, String provider) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/social/$provider/exchange'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'access_token': accessToken, 'provider': provider}),
    );
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    if (data['success'] == true) {
      await _saveToken(data['token'], data['user'],
          refreshToken: data['refresh_token']);
    }
    return data;
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

  /// 소셜 신규 가입 후 동의 항목 기록 (PIPC §22 / 정보통신망법 §50).
  /// `/api/auth/social` 응답에 `is_new_user=true` 가 포함되면 호출.
  Future<Map<String, dynamic>> submitConsents(
      List<Map<String, dynamic>> consents) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/auth/consents'),
      headers: authHeaders,
      body: jsonEncode({'consents': consents}),
    );
    return jsonDecode(res.body) as Map<String, dynamic>;
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
    // Firebase 가 미초기화된 dev 모드에서도 안전하게 동작 — 토큰 만료/서버
    // 실패 시 _fetchMe → logout 체인이 [core/no-app] 으로 throw 되어 콘솔
    // 빨간 에러 + AuthService 가 사용자 상태 정리 못 하던 문제 차단.
    try { await GoogleSignIn().signOut(); } catch (_) {}
    try { await FirebaseAuth.instance.signOut(); } catch (_) {}
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
