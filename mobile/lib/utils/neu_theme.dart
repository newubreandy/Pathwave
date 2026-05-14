import 'package:flutter/material.dart';

/// PR #67 — Neumorphic 디자인 시스템 토큰.
///
/// 핵심 색상은 light gray base (`#E6E9EF`) + soft inner/outer shadow.
/// 모든 컴포넌트가 이 토큰만 참조해야 톤 통일 유지.
class NeuTheme {
  // ── 베이스 ────────────────────────────────────────────────────
  static const Color background = Color(0xFFE0E5EC);   // 메인 배경
  static const Color surface    = Color(0xFFE6E9EF);   // 카드 (= base 와 거의 같음)
  static const Color surfaceLight = Color(0xFFEDF1F7); // 살짝 밝은 카드
  static const Color border     = Color(0xFFD1D9E6);   // 경계선 (subtle)

  // ── 텍스트 ─────────────────────────────────────────────────────
  static const Color textPrimary   = Color(0xFF2D3748);   // 진한 회색
  static const Color textSecondary = Color(0xFF718096);
  static const Color textHint      = Color(0xFFA0AEC0);

  // ── 액센트 (선택적 컬러 강조) ──────────────────────────────────
  static const Color accent      = Color(0xFF22C55E);  // 토글 ON / 주요 CTA
  static const Color accentLight = Color(0xFF4ADE80);
  static const Color primary     = Color(0xFF7C3AED);  // 보라 (브랜드)
  static const Color error       = Color(0xFFEF4444);
  static const Color warning     = Color(0xFFF59E0B);

  // ── 그림자 (Neumorphism 핵심) ───────────────────────────────────
  /// 빛이 좌상단에서 들어오는 가정 — 좌상단 밝게, 우하단 어둡게
  static const Color shadowDark  = Color(0xFFA3B1C6);  // 우하단
  static const Color shadowLight = Color(0xFFFFFFFF);  // 좌상단

  // 외부로 튀어나온(Convex) 그림자
  static List<BoxShadow> outerShadow({double distance = 6, double blur = 12}) => [
    BoxShadow(
      color: shadowDark,
      offset: Offset(distance, distance),
      blurRadius: blur,
    ),
    BoxShadow(
      color: shadowLight,
      offset: Offset(-distance, -distance),
      blurRadius: blur,
    ),
  ];

  // 안으로 들어간(Concave / Pressed) 효과 — Container BoxShadow 로는 inset 직접 표현 불가
  // → Stack + ClipRRect + 그라디언트로 구현하거나 가벼운 outer shadow 절반만 사용
  static List<BoxShadow> pressedShadow({double distance = 2, double blur = 4}) => [
    BoxShadow(
      color: shadowDark.withValues(alpha: 0.3),
      offset: Offset(distance, distance),
      blurRadius: blur,
    ),
    BoxShadow(
      color: shadowLight.withValues(alpha: 0.6),
      offset: Offset(-distance, -distance),
      blurRadius: blur,
    ),
  ];

  static const BorderRadius radiusS  = BorderRadius.all(Radius.circular(12));
  static const BorderRadius radiusM  = BorderRadius.all(Radius.circular(20));
  static const BorderRadius radiusL  = BorderRadius.all(Radius.circular(28));
  static const BorderRadius radiusXL = BorderRadius.all(Radius.circular(40));

  // ── ThemeData (light) ──────────────────────────────────────────
  static ThemeData get themeData => ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    scaffoldBackgroundColor: background,
    colorScheme: const ColorScheme.light(
      primary: primary,
      secondary: accent,
      surface: surface,
      error: error,
      onPrimary: Colors.white,
      onSurface: textPrimary,
    ),
    fontFamily: 'Pretendard',
    textTheme: const TextTheme(
      displaySmall:    TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: textPrimary),
      headlineSmall:   TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: textPrimary),
      titleLarge:      TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: textPrimary),
      titleMedium:     TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: textPrimary),
      bodyLarge:       TextStyle(fontSize: 15, color: textPrimary),
      bodyMedium:      TextStyle(fontSize: 14, color: textPrimary),
      bodySmall:       TextStyle(fontSize: 12, color: textSecondary),
    ),
    iconTheme: const IconThemeData(color: textPrimary, size: 24),
    appBarTheme: const AppBarTheme(
      backgroundColor: background,
      foregroundColor: textPrimary,
      elevation: 0,
      centerTitle: false,
    ),
  );
}
