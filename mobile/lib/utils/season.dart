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
  static LinearGradient fallbackGradient(Season s) {
    switch (s) {
      case Season.spring:
        return const LinearGradient(
          begin: Alignment.topLeft,
          end:   Alignment.bottomRight,
          colors: [Color(0xFF7C3AED), Color(0xFFEC4899)],     // 보라 → 핑크 (벚꽃)
        );
      case Season.summer:
        return const LinearGradient(
          begin: Alignment.topLeft,
          end:   Alignment.bottomRight,
          colors: [Color(0xFF6D28D9), Color(0xFF06B6D4)],     // 진보라 → 시안 (물)
        );
      case Season.autumn:
        return const LinearGradient(
          begin: Alignment.topLeft,
          end:   Alignment.bottomRight,
          colors: [Color(0xFF7C3AED), Color(0xFFF59E0B)],     // 보라 → 호박 (단풍)
        );
      case Season.winter:
        return const LinearGradient(
          begin: Alignment.topLeft,
          end:   Alignment.bottomRight,
          colors: [Color(0xFF4C1D95), Color(0xFF38BDF8)],     // 깊은 보라 → 하늘색 (눈)
        );
    }
  }
}
