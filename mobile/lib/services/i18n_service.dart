import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../utils/api_config.dart';

/// 백엔드 DB 기반 i18n 서비스.
///
/// 부팅 시 `await I18nService.instance.init()` 를 호출하면
/// 디바이스 언어를 자동 감지 → 백엔드 fetch → SharedPreferences 24h 캐싱.
///
/// 지원 언어(23): ko, en, zh-CN, ja, zh-TW, vi, th, tl, id, ms, ru, hi,
///               es, de, fr, pt, it, nl, pl, ar, tr, he, sv
class I18nService {
  I18nService._();
  static final I18nService instance = I18nService._();

  static const cacheTtl = Duration(hours: 24);

  static const _supportedLangs = [
    'ko', 'en', 'zh-CN', 'ja', 'zh-TW', 'vi', 'th', 'tl', 'id', 'ms',
    'ru', 'hi', 'es', 'de', 'fr', 'pt', 'it', 'nl', 'pl', 'ar', 'tr', 'he', 'sv',
  ];

  // SharedPreferences 키 패턴: i18n.<lang>.payload / i18n.<lang>.cachedAt
  static String _keyPayload(String lang)   => 'i18n.$lang.payload';
  static String _keyCachedAt(String lang)  => 'i18n.$lang.cachedAt';

  Map<String, String> _strings = {};
  String _lang = 'ko';
  bool _initialized = false;

  /// 현재 로드된 언어 코드.
  String get currentLang => _lang;

  // ── 공개 API ──────────────────────────────────────────────────────────────

  /// 부팅 시 1회 호출. [deviceLanguageCode] 미전달 시 Flutter locale 자동 감지.
  Future<void> init({String? deviceLanguageCode}) async {
    final rawCode = deviceLanguageCode ?? _detectDeviceLang();
    _lang = _resolveLang(rawCode);

    final prefs = await SharedPreferences.getInstance();

    // 캐시 유효성 검사
    if (_isCacheValid(prefs, _lang)) {
      final payload = prefs.getString(_keyPayload(_lang));
      if (payload != null) {
        _strings = _parsePayload(payload);
        _initialized = true;
        debugPrint('[I18nService] 캐시 사용: $_lang (${_strings.length}개 키)');
        return;
      }
    }

    // 캐시 만료/없음 → fetch 시도
    final fetched = await _fetchFromBackend(_lang);
    if (fetched != null) {
      _strings = fetched;
      _saveCache(prefs, _lang, fetched);
      _initialized = true;
      debugPrint('[I18nService] fetch 완료: $_lang (${_strings.length}개 키)');
      return;
    }

    // 네트워크 실패 → 만료 캐시라도 사용
    final stalePayload = prefs.getString(_keyPayload(_lang));
    if (stalePayload != null) {
      _strings = _parsePayload(stalePayload);
      _initialized = true;
      debugPrint('[I18nService] 만료 캐시 fallback: $_lang');
      return;
    }

    // 캐시도 없음 → ARB fallback (빈 map — t() 에서 defaultValue/key 반환)
    _strings = {};
    _initialized = true;
    debugPrint('[I18nService] ARB fallback 모드: $_lang (DB/캐시 없음)');
  }

  /// 동기 번역 조회. 키가 없으면 [defaultValue] → key 자체 순으로 반환.
  String t(String key, {String? defaultValue}) {
    if (!_initialized) return defaultValue ?? key;
    return _strings[key] ?? defaultValue ?? key;
  }

  // ── 내부 ──────────────────────────────────────────────────────────────────

  /// Flutter 플랫폼 locale 에서 언어 코드 추출 (dart:ui 의존 없이 간단 처리).
  String _detectDeviceLang() {
    try {
      final locale = WidgetsBinding.instance.platformDispatcher.locale;
      final tag = locale.toLanguageTag(); // e.g. "zh-CN", "en", "ko"
      return tag;
    } catch (_) {
      return 'ko';
    }
  }

  /// 디바이스 언어 코드 → 지원 언어 코드 매핑.
  /// - 완전 일치 우선
  /// - `zh` prefix → `zh-CN`
  /// - 언어 코드만(예: `en-US` → `en`) 로 매칭
  /// - 없으면 `ko` (기본값)
  String _resolveLang(String code) {
    // 완전 일치
    if (_supportedLangs.contains(code)) return code;

    // zh 처리: zh-* → zh-CN, zh-TW 로 분기
    if (code.startsWith('zh')) {
      if (code.contains('TW') || code.contains('HK')) return 'zh-TW';
      return 'zh-CN';
    }

    // 언어 코드 앞 2자리 매칭 (예: en-US → en)
    final prefix = code.length >= 2 ? code.substring(0, 2) : code;
    if (_supportedLangs.contains(prefix)) return prefix;

    return 'ko';
  }

  bool _isCacheValid(SharedPreferences prefs, String lang) {
    final cachedAt = prefs.getString(_keyCachedAt(lang));
    if (cachedAt == null) return false;
    final ts = DateTime.tryParse(cachedAt);
    if (ts == null) return false;
    return DateTime.now().difference(ts) < cacheTtl;
  }

  Map<String, String> _parsePayload(String payload) {
    try {
      final decoded = jsonDecode(payload) as Map<String, dynamic>;
      return decoded.map((k, v) => MapEntry(k, v.toString()));
    } catch (_) {
      return {};
    }
  }

  Future<Map<String, String>?> _fetchFromBackend(String lang) async {
    try {
      final uri = Uri.parse('${ApiConfig.baseUrl}/api/i18n/$lang');
      final response = await http.get(uri, headers: {
        'Accept': 'application/json',
      }).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final decoded = jsonDecode(response.body) as Map<String, dynamic>;
        return decoded.map((k, v) => MapEntry(k, v.toString()));
      }
      debugPrint('[I18nService] fetch 실패: HTTP ${response.statusCode}');
      return null;
    } catch (e) {
      debugPrint('[I18nService] fetch 오류: $e');
      return null;
    }
  }

  void _saveCache(SharedPreferences prefs, String lang, Map<String, String> data) {
    prefs.setString(_keyPayload(lang), jsonEncode(data));
    prefs.setString(_keyCachedAt(lang), DateTime.now().toIso8601String());
  }
}
