/// 사용자 앱 시즌 배경 테마 — 서버 fetch + 캐시 + ChangeNotifier.
///
/// 1) 앱 시작 시 ``init()`` 호출 — SharedPreferences 의 캐시 즉시 로드 →
///    백그라운드로 fresh fetch (1시간 TTL).
/// 2) 화면은 ``Provider.of<ThemeService>(context)`` 로 listen 후
///    ``activeTheme`` 사용. null 이면 ``SeasonUtils.fallbackGradient`` 적용.
/// 3) pull-to-refresh 등에서 ``refresh()`` 호출 시 캐시 무시하고 즉시 fetch.
///
/// 무재배포 운영: 슈퍼어드민이 admin-web 에서 활성 테마 변경 → 다음 fetch
/// 시점(앱 재실행 / pull-to-refresh / 1h 경과)에 반영.
library;

import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api_client.dart';
import '../utils/season.dart';

class ThemeConfig {
  final int id;
  final String season;
  final String name;
  final String imageUrl;
  final double overlayAlpha;
  final bool textOnDark;
  final String? accentColor;

  ThemeConfig({
    required this.id,
    required this.season,
    required this.name,
    required this.imageUrl,
    required this.overlayAlpha,
    required this.textOnDark,
    this.accentColor,
  });

  factory ThemeConfig.fromJson(Map<String, dynamic> j) => ThemeConfig(
        id:           (j['id'] as num).toInt(),
        season:       j['season']?.toString() ?? '',
        name:         j['name']?.toString() ?? '',
        imageUrl:     j['image_url']?.toString() ?? '',
        overlayAlpha: (j['overlay_alpha'] as num?)?.toDouble() ?? 0.45,
        textOnDark:   j['text_on_dark'] == true || j['text_on_dark'] == 1,
        accentColor:  j['accent_color']?.toString(),
      );

  Map<String, dynamic> toJson() => {
        'id':            id,
        'season':        season,
        'name':          name,
        'image_url':     imageUrl,
        'overlay_alpha': overlayAlpha,
        'text_on_dark':  textOnDark,
        'accent_color':  accentColor,
      };
}

class ThemeService extends ChangeNotifier {
  ThemeService._();
  static final ThemeService instance = ThemeService._();
  factory ThemeService() => instance;

  static const _kCacheJson      = 'theme.cache.v1.json';
  static const _kCacheTimestamp = 'theme.cache.v1.ts';
  static const Duration _ttl    = Duration(hours: 1);

  ThemeConfig? _activeTheme;
  Season       _season  = SeasonUtils.currentKst();
  bool         _loading = false;
  String?      _lastError;

  ThemeConfig? get activeTheme => _activeTheme;
  // DEV_FORCE_SEASON 이 있으면 그 계절로 고정(QA), 없으면 서버/시간 기반 _season.
  Season       get season      => SeasonUtils.devForcedSeason ?? _season;
  bool         get loading     => _loading;
  String?      get lastError   => _lastError;

  /// 캐시 즉시 로드 + 백그라운드 fetch. 앱 시작 1회 호출.
  Future<void> init() async {
    await _loadFromCache();
    notifyListeners();
    // 개발 계절 강제(DEV_FORCE_SEASON) 시엔 캐시를 무시하고 항상 새로 fetch한다 —
    // 계절을 바꿔 재실행하면 즉시 해당 계절 테마가 반영되도록(캐시 1h 로 묶이지 않게).
    if (SeasonUtils.devForcedSeason != null) {
      unawaited(_fetch());
    } else {
      // 캐시 TTL 만료면 fetch — 만료 안 됐어도 백그라운드로 갱신
      unawaited(_fetchIfStale());
    }
  }

  Future<void> _loadFromCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_kCacheJson);
      if (raw == null) return;
      final decoded = jsonDecode(raw) as Map<String, dynamic>;
      _season = SeasonUtils.parse(decoded['season']?.toString());
      final t = decoded['theme'];
      if (t is Map<String, dynamic>) {
        _activeTheme = ThemeConfig.fromJson(t);
      } else {
        _activeTheme = null;
      }
    } catch (e) {
      debugPrint('[ThemeService] 캐시 로드 실패: $e');
    }
  }

  Future<void> _fetchIfStale() async {
    final prefs = await SharedPreferences.getInstance();
    final ts = prefs.getInt(_kCacheTimestamp) ?? 0;
    final age = DateTime.now().millisecondsSinceEpoch - ts;
    if (age < _ttl.inMilliseconds && _activeTheme != null) return;
    await _fetch();
  }

  /// 캐시 무시하고 즉시 fetch. pull-to-refresh 등에서 호출.
  Future<void> refresh() async => _fetch();

  Future<void> _fetch() async {
    if (_loading) return;
    _loading = true;
    _lastError = null;
    notifyListeners();
    try {
      // 개발 계절 강제(DEV_FORCE_SEASON) 시 같은 계절의 테마를 받도록 쿼리에 반영.
      // 운영은 미지정 → 백엔드가 KST 현재 계절을 자동 판정한다.
      final forced = SeasonUtils.devForcedSeason;
      final data = await ApiClient.instance.get(
        forced != null
            ? '/api/theme/current?season=${forced.code}'
            : '/api/theme/current',
      );
      _season = SeasonUtils.parse(data['season']?.toString());
      final t = data['theme'];
      if (t is Map<String, dynamic>) {
        _activeTheme = ThemeConfig.fromJson(t);
      } else {
        _activeTheme = null;   // fallback=true 응답 → 앱 기본 그라데이션
      }
      // 캐시 저장
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_kCacheJson, jsonEncode({
        'season': _season.code,
        'theme':  _activeTheme?.toJson(),
      }));
      await prefs.setInt(_kCacheTimestamp,
          DateTime.now().millisecondsSinceEpoch);
    } catch (e) {
      _lastError = e.toString();
      debugPrint('[ThemeService] fetch 실패: $e');
      // 실패해도 캐시는 유지. UI 는 캐시로 동작 + lastError 노출 가능.
    } finally {
      _loading = false;
      notifyListeners();
    }
  }
}
