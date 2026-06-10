/// Feature Flag 클라이언트 (2026-06-08).
///
/// 사용
/// ----
/// 1) ``main.dart`` MultiProvider 에 ChangeNotifierProvider 로 등록.
/// 2) 앱 시작 시 ``await FeatureService.instance.init()`` 호출 (백그라운드 OK).
/// 3) UI 에서 ``Provider.of<FeatureService>(context)`` 또는
///    ``FeatureService.instance.isEnabled('chat')`` 으로 분기.
///
/// 정책
/// ----
/// - 서버 ``/api/me/features`` 의 응답을 SharedPreferences 에 캐시 (24h TTL).
/// - 네트워크 실패/오프라인 → 캐시 사용. 캐시도 없으면 ``_kDefault`` 사용.
/// - 어드민에서 모듈 ON/OFF 변경 시 다음 fetch 시점에 반영 (또는 사용자 refresh).
library;

import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api_client.dart';

class FeatureService extends ChangeNotifier {
  FeatureService._();
  static final FeatureService instance = FeatureService._();
  factory FeatureService() => instance;

  static const _kCacheJson = 'feature_flags.cache.v1.json';
  static const _kCacheTs   = 'feature_flags.cache.v1.ts';
  static const Duration _ttl = Duration(hours: 24);

  /// 백엔드 DEFAULT_FLAGS 와 동일 — 네트워크/캐시 모두 실패 시 fallback.
  static const Map<String, bool> _kDefault = {
    // 1차 활성 (12)
    'wifi_roaming':              true,
    'beacon':                    true,
    'stamp':                     true,
    'coupon':                    true,
    'chat':                      true,
    'chat_translate':            true,
    'menu_translate':            true,
    'menu_ocr_device':           true,
    'push':                      true,
    'email_notify':              true,
    'subscription_payment_toss': true,
    'season_theme':              true,
    // 1차 비활성 (2차 활성 후보)
    'store_payment':             false,
    'payment_zeropay':           false,
    'alipay_wechat':             false,
    'tax_refund':                false,
    'ai_chatbot':                false,
    'social_auto_post':          false,
    'voice_call_ai':             false,
    'crm_ads_auto':              false,
    'woorichat_translate_proxy': false,
    // P18·P19 (Phase 1 W1 WiFi 로밍 — flag 로 v1 비공개)
    'wifi_credential_managed':   false,
    'wifi_units_grant':          false,
    // IA 감사 2026-06-09 — UI 메뉴 가림 전용 flag
    'admin_extra_tools':         false,
    'parent_invite':             false,
  };

  Map<String, bool> _flags = Map.of(_kDefault);
  bool _loading = false;
  String? _lastError;

  /// 활성 여부 — 미정의 키는 false.
  bool isEnabled(String key) => _flags[key] ?? false;

  Map<String, bool> get all => Map.unmodifiable(_flags);
  bool get loading => _loading;
  String? get lastError => _lastError;

  /// 캐시 즉시 로드 + 백그라운드 fetch. 앱 시작 1회 호출.
  Future<void> init() async {
    await _loadFromCache();
    notifyListeners();
    unawaited(_fetchIfStale());
  }

  Future<void> refresh() async => _fetch();

  Future<void> _loadFromCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_kCacheJson);
      if (raw == null) return;
      final decoded = jsonDecode(raw) as Map<String, dynamic>;
      _flags = decoded.map((k, v) => MapEntry(k, v == true || v == 1));
    } catch (e) {
      debugPrint('[FeatureService] 캐시 로드 실패: $e');
    }
  }

  Future<void> _fetchIfStale() async {
    final prefs = await SharedPreferences.getInstance();
    final ts = prefs.getInt(_kCacheTs) ?? 0;
    final age = DateTime.now().millisecondsSinceEpoch - ts;
    if (age < _ttl.inMilliseconds && _flags.isNotEmpty) return;
    await _fetch();
  }

  Future<void> _fetch() async {
    if (_loading) return;
    _loading = true;
    _lastError = null;
    notifyListeners();
    try {
      final data = await ApiClient.instance.get('/api/me/features');
      final raw = data['features'];
      if (raw is Map) {
        final next = <String, bool>{};
        raw.forEach((k, v) {
          next[k.toString()] = v == true || v == 1;
        });
        // 백엔드에 없는 키도 DEFAULT 로 채워 안전성 확보.
        for (final e in _kDefault.entries) {
          next.putIfAbsent(e.key, () => e.value);
        }
        _flags = next;
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_kCacheJson, jsonEncode(_flags));
        await prefs.setInt(_kCacheTs,
            DateTime.now().millisecondsSinceEpoch);
      }
    } catch (e) {
      _lastError = e.toString();
      debugPrint('[FeatureService] fetch 실패: $e');
    } finally {
      _loading = false;
      notifyListeners();
    }
  }
}
