import 'package:flutter/material.dart';

class AppTheme {
  // ── 색상 팔레트 ─────────────────────────────────────────────────
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
  static const Color textSecondary = Color(0xFFA1A1AA);
  static const Color textHint      = Color(0xFF71717A);
  static const Color border        = Color(0xFF3F3F5C);

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
