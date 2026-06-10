/// KST 기준 계절 판정 + 기본 그라데이션 팔레트.
///
/// 백엔드(routes/theme.py)와 경계 정의 통일:
///   봄 3-5 · 여름 6-8 · 가을 9-11 · 겨울 12-2 (기상학적)
///
/// 서버 테마가 없을 때(fallback) 사용자 앱이 자체적으로 그릴 그라데이션.
library;

import 'package:flutter/material.dart';

enum Season { spring, summer, autumn, winter }

extension SeasonCode on Season {
  String get code {
    switch (this) {
      case Season.spring: return 'spring';
      case Season.summer: return 'summer';
      case Season.autumn: return 'autumn';
      case Season.winter: return 'winter';
    }
  }
}

class SeasonUtils {
  /// 개발/QA 용 계절 강제 — ``--dart-define=DEV_FORCE_SEASON=spring|summer|autumn|winter``.
  /// 지정 시 서버 응답·디바이스 시간과 무관하게 해당 계절로 고정한다(4계절 미리보기).
  /// 미지정(빈 문자열)이면 ``null`` → 평소처럼 서버/시간 기반으로 동작.
  /// 출시 빌드는 define 을 주지 않으므로 영향 없음.
  static const String _devForceRaw = String.fromEnvironment('DEV_FORCE_SEASON');
  static Season? get devForcedSeason =>
      _devForceRaw.isEmpty ? null : parse(_devForceRaw);

  /// KST 기준 현재 계절. ``at`` 미지정 시 ``DateTime.now()`` (디바이스 시간)
  /// 을 KST(+9) 로 변환해서 판정한다.
  static Season currentKst([DateTime? at]) {
    final now = (at ?? DateTime.now()).toUtc().add(const Duration(hours: 9));
    final m = now.month;
    if (m >= 3 && m <= 5)   return Season.spring;
    if (m >= 6 && m <= 8)   return Season.summer;
    if (m >= 9 && m <= 11)  return Season.autumn;
    return Season.winter;
  }

  /// 서버 응답의 ``season`` 문자열 → enum. 알 수 없으면 KST 현재.
  static Season parse(String? raw) {
    switch ((raw ?? '').toLowerCase()) {
      case 'spring': return Season.spring;
      case 'summer': return Season.summer;
      case 'autumn': return Season.autumn;
      case 'winter': return Season.winter;
      default:       return currentKst();
    }
  }

  /// fallback 그라데이션 (서버 테마 미설정 시) — 계절 톤 반영.
  /// 보라(브랜드) 를 항상 살짝 섞어서 PathWave 정체성 유지.
  ///
  /// ⚠️ 채도·명도 가이드: 디바이스에서 어두운 톤이 묻혀 보이지 않도록
  /// 최소 명도 50% 이상 유지. 너무 진한 보라(#4C1D95, #6D28D9)는 노치/베젤과
  /// 구분이 안 되어 "검은 화면" 처럼 보이므로 금지.
  static LinearGradient fallbackGradient(Season s) {
    switch (s) {
      case Season.spring:
        return const LinearGradient(
          begin: Alignment.topLeft,
          end:   Alignment.bottomRight,
          colors: [Color(0xFFA78BFA), Color(0xFFF472B6)],     // 라벤더 → 분홍 (벚꽃)
        );
      case Season.summer:
        return const LinearGradient(
          begin: Alignment.topLeft,
          end:   Alignment.bottomRight,
          colors: [Color(0xFF8B5CF6), Color(0xFF22D3EE)],     // 보라 → 청록 (바다/수국)
        );
      case Season.autumn:
        return const LinearGradient(
          begin: Alignment.topLeft,
          end:   Alignment.bottomRight,
          colors: [Color(0xFFA78BFA), Color(0xFFFB923C)],     // 라벤더 → 오렌지 (단풍)
        );
      case Season.winter:
        return const LinearGradient(
          begin: Alignment.topLeft,
          end:   Alignment.bottomRight,
          colors: [Color(0xFF818CF8), Color(0xFF67E8F9)],     // 인디고 → 청록 (얼음)
        );
    }
  }
}
