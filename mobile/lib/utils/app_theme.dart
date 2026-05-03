import 'package:flutter/material.dart';
// import 'package:google_fonts/google_fonts.dart'; // 일단 기본 폰트 사용

class AppTheme {
  // ── 색상 팔레트 ─────────────────────────────────────────────────
  static const Color primary       = Color(0xFF10B981); // 에메랄드 그린
  static const Color primaryLight  = Color(0xFF34D399);
  static const Color secondary     = Color(0xFF06B6D4); // 시안
  static const Color background    = Color(0xFFFFFFFF); // 배경 (흰색)
  static const Color surface       = Color(0xFFF8FAFC); // 입력창, 카드 배경
  static const Color surfaceLight  = Color(0xFFF1F5F9);
  static const Color error         = Color(0xFFEF4444);
  static const Color success       = Color(0xFF10B981);
  static const Color warning       = Color(0xFFF59E0B);
  static const Color textPrimary   = Color(0xFF0F172A); // 진한 텍스트
  static const Color textSecondary = Color(0xFF64748B); // 보조 텍스트
  static const Color textHint      = Color(0xFF94A3B8); // 힌트 텍스트
  static const Color border        = Color(0xFFE2E8F0); // 테두리

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: const ColorScheme.light(
        primary:          primary,
        secondary:        secondary,
        surface:          surface,
        error:            error,
        onPrimary:        Colors.white,
        onSecondary:      Colors.white,
        onSurface:        textPrimary,
      ),
      scaffoldBackgroundColor: background,

      // 폰트
      textTheme: TextTheme(
        displayLarge:  _ts(32, FontWeight.bold),
        displayMedium: _ts(28, FontWeight.bold),
        displaySmall:  _ts(24, FontWeight.bold),
        headlineLarge: _ts(22, FontWeight.w700),
        headlineMedium:_ts(20, FontWeight.w600),
        headlineSmall: _ts(18, FontWeight.w600),
        titleLarge:    _ts(16, FontWeight.w600),
        titleMedium:   _ts(14, FontWeight.w500),
        bodyLarge:     _ts(16, FontWeight.normal),
        bodyMedium:    _ts(14, FontWeight.normal),
        bodySmall:     _ts(12, FontWeight.normal),
        labelLarge:    _ts(14, FontWeight.w600),
      ),

      // AppBar
      appBarTheme: const AppBarTheme(
        backgroundColor: background,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: textPrimary,
          fontSize: 18,
          fontWeight: FontWeight.w600,
        ),
        iconTheme: IconThemeData(color: textPrimary),
      ),

      // 버튼
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          minimumSize: const Size(double.infinity, 54),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),

      // 텍스트필드
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surface,
        hintStyle: const TextStyle(color: textHint),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: error),
        ),
      ),

      // 카드
      cardTheme: CardThemeData(
        color: surface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: border, width: 1),
        ),
      ),
    );
  }

  static TextStyle _ts(double size, FontWeight weight) => TextStyle(
    fontSize: size,
    fontWeight: weight,
    color: textPrimary,
  );
}
