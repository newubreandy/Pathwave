import 'package:flutter/material.dart';

/// PR #67 / 디자인 1차 통일 — Dark + 보라 (#8B5CF6) 단일 포인트.
///
/// PathWave 3 콘솔 색 분리:
/// - mobile (사용자) = 보라 #8B5CF6
/// - provider-web (시설관리자) = 그린 #22C55E
/// - admin-web (슈퍼어드민) = 블루 #2563EB
///
/// 모든 컴포넌트가 이 토큰만 참조해야 톤 통일 유지.
/// 1차 단계: 색만 다크 + 보라로 정렬. 구조/네이밍은 유지.
class NeuTheme {
  // ── 베이스 (다크 4단계 — provider/admin 토큰과 정렬) ───────────
  static const Color background   = Color(0xFF0B0B12);   // 페이지 배경
  static const Color surface      = Color(0xFF14141C);   // 카드
  static const Color surfaceLight = Color(0xFF1A1A24);   // 카드 inset / 살짝 밝게
  static const Color border       = Color(0xFF1F1F2B);   // 경계선 (subtle)

  // ── 텍스트 ─────────────────────────────────────────────────────
  static const Color textPrimary   = Color(0xFFF2F3F7);  // 밝은 메인
  static const Color textSecondary = Color(0xFF8A91A3);
  static const Color textHint      = Color(0xFF5A6072);

  // ── 액센트 (mobile = 보라 포인트) ──────────────────────────────
  static const Color accent      = Color(0xFF8B5CF6);   // 주요 CTA / 토글 ON
  static const Color accentLight = Color(0xFFA78BFA);
  static const Color primary     = Color(0xFF8B5CF6);   // 보라 (브랜드) — accent 와 동일 톤
  static const Color error       = Color(0xFFEF4444);
  static const Color warning     = Color(0xFFF59E0B);

  // ── 그림자 (Dark Neumorphism — 좌상단 살짝 밝은 회색, 우하단 검정) ─
  static const Color shadowDark  = Color(0xFF000000);
  static const Color shadowLight = Color(0xFF2A2A38);

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

  static List<BoxShadow> pressedShadow({double distance = 2, double blur = 4}) => [
    BoxShadow(
      color: shadowDark.withValues(alpha: 0.45),
      offset: Offset(distance, distance),
      blurRadius: blur,
    ),
    BoxShadow(
      color: shadowLight.withValues(alpha: 0.55),
      offset: Offset(-distance, -distance),
      blurRadius: blur,
    ),
  ];

  static const BorderRadius radiusS  = BorderRadius.all(Radius.circular(12));
  static const BorderRadius radiusM  = BorderRadius.all(Radius.circular(20));
  static const BorderRadius radiusL  = BorderRadius.all(Radius.circular(28));
  static const BorderRadius radiusXL = BorderRadius.all(Radius.circular(40));

  // ── ThemeData (dark) ───────────────────────────────────────────
  static ThemeData get themeData => ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: background,
    colorScheme: const ColorScheme.dark(
      primary: primary,
      secondary: accent,
      surface: surface,
      error: error,
      onPrimary: Colors.white,
      onSecondary: Colors.white,
      onSurface: textPrimary,
      onError: Colors.white,
    ),
    fontFamily: 'Noto Sans KR',
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
