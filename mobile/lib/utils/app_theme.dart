import 'package:flutter/material.dart';

/// PathWave mobile 디자인 토큰 단일 소스.
///
/// ⚠️ 규칙: 화면/위젯에서 라운드·여백·그림자·폰트를 **하드코딩 금지**.
///         반드시 아래 토큰(rSm/rMd/rLg·s1~s6·softShadow·textTheme)을 참조한다.
///         → 디자인 변경 시 이 파일 한 곳만 고치면 전체 반영.
/// 가이드: docs/DESIGN_SYSTEM.md "10. Mobile (Flutter)" 섹션.
class AppTheme {
  // ── 색상 팔레트 (확정 정책색 — 변경 금지) ─────────────────────────
  static const Color primary       = Color(0xFF7C3AED); // 보라
  static const Color primaryLight  = Color(0xFFA78BFA);
  static const Color secondary     = Color(0xFF06B6D4); // 시안
  static const Color background    = Color(0xFF0F0F1A); // 배경
  static const Color surface       = Color(0xFF1E1E2E); // 카드
  static const Color surfaceLight  = Color(0xFF2A2A3E);
  static const Color error         = Color(0xFFEF4444);
  static const Color success       = Color(0xFF10B981);
  static const Color warning       = Color(0xFFF59E0B);
  static const Color textPrimary   = Color(0xFFFFFFFF);
  // 그라데이션 위 가독성 — 흰톤(alpha). NeuTheme 와 동일 정책.
  static const Color textSecondary = Color(0xC8FFFFFF);   // white 78%
  static const Color textHint      = Color(0x8AFFFFFF);   // white 54%
  static const Color border        = Color(0xFF3F3F5C);

  // ── 라운드 토큰 (DesignCode 톤 — 둥근 카드 계열) ──────────────────
  static const double rSm   = 12;  // 칩/태그/작은 요소
  static const double rMd   = 16;  // 버튼/입력필드
  static const double rLg   = 20;  // 카드/시트
  static const double rXl   = 28;  // 큰 컨테이너/모달
  static const double rPill = 999; // 알약형

  // ── 여백 스케일 (4 배수) ──────────────────────────────────────────
  static const double s1 = 4;
  static const double s2 = 8;
  static const double s3 = 12;
  static const double s4 = 16;
  static const double s5 = 20;
  static const double s6 = 24;

  // ── soft shadow (다크 적정 강도 — 미묘한 depth) ───────────────────
  static const List<BoxShadow> softShadow = [
    BoxShadow(color: Color(0x33000000), blurRadius: 16, offset: Offset(0, 6)),
  ];
  static const List<BoxShadow> softShadowSm = [
    BoxShadow(color: Color(0x26000000), blurRadius: 8, offset: Offset(0, 2)),
  ];

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: const ColorScheme.dark(
        primary:          primary,
        secondary:        secondary,
        surface:          surface,
        error:            error,
        onPrimary:        Colors.white,
        onSecondary:      Colors.white,
        onSurface:        textPrimary,
      ),
      // 글로벌 시즌 배경(SeasonalBackground) 이 MaterialApp.builder 에서
      // 모든 화면 뒤를 깔기 때문에, Scaffold 는 투명이어야 그라데이션이 비친다.
      scaffoldBackgroundColor: Colors.transparent,

      // 폰트 — DesignCode 톤: heading letterSpacing 좁힘 + line-height 정제.
      textTheme: TextTheme(
        displayLarge:  _ts(32, FontWeight.bold,   ls: -0.5, h: 1.2),
        displayMedium: _ts(28, FontWeight.bold,   ls: -0.4, h: 1.2),
        displaySmall:  _ts(24, FontWeight.bold,   ls: -0.3, h: 1.25),
        headlineLarge: _ts(22, FontWeight.w700,   ls: -0.3, h: 1.25),
        headlineMedium:_ts(20, FontWeight.w600,   ls: -0.2, h: 1.3),
        headlineSmall: _ts(18, FontWeight.w600,   ls: -0.2, h: 1.3),
        titleLarge:    _ts(16, FontWeight.w600,   ls: -0.1, h: 1.35),
        titleMedium:   _ts(14, FontWeight.w500,             h: 1.4),
        bodyLarge:     _ts(16, FontWeight.normal,           h: 1.5),
        bodyMedium:    _ts(14, FontWeight.normal,           h: 1.5),
        bodySmall:     _ts(12, FontWeight.normal,           h: 1.45),
        labelLarge:    _ts(14, FontWeight.w600,             h: 1.35),
      ),

      // AppBar — 시즌 배경 위에 자연스럽게 얹히도록 투명. 그림자로 깊이만 표현.
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: textPrimary,
          fontSize: 18,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.2,
          shadows: [
            Shadow(color: Colors.black54, blurRadius: 6, offset: Offset(0, 1)),
          ],
        ),
        iconTheme: IconThemeData(color: textPrimary),
      ),

      // 버튼 — rMd 통일
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          minimumSize: const Size(double.infinity, 54),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(rMd),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: -0.1,
          ),
        ),
      ),

      // 텍스트필드 — rMd 통일
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surface,
        hintStyle: const TextStyle(color: textHint),
        contentPadding: const EdgeInsets.symmetric(horizontal: s4, vertical: s4),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(rMd),
          borderSide: const BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(rMd),
          borderSide: const BorderSide(color: border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(rMd),
          borderSide: const BorderSide(color: primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(rMd),
          borderSide: const BorderSide(color: error),
        ),
      ),

      // 카드 — rLg 둥근 카드
      cardTheme: CardThemeData(
        color: surface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(rLg),
          side: const BorderSide(color: border, width: 1),
        ),
      ),
    );
  }

  static TextStyle _ts(double size, FontWeight weight,
          {double? ls, double? h}) =>
      TextStyle(
        fontSize: size,
        fontWeight: weight,
        color: textPrimary,
        letterSpacing: ls,
        height: h,
      );
}
