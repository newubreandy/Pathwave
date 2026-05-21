import 'package:flutter/material.dart';

/// PathWave 모바일 통합 디자인 토큰 (P1, 2026-05-21).
///
/// 구 `AppTheme`(utils/app_theme.dart) + `NeuTheme`(utils/neu_theme.dart) 를
/// 하나로 통합. 화면·위젯은 색·폰트·라운드를 자체 정의하지 말고 이 클래스의
/// 토큰만 참조한다.
///
/// 색 정책: mobile = 보라(#8B5CF6). provider-web = 녹색, admin-web = 블루.
/// 상태색(error/warning/success)은 3콘솔 공통 의미색 — provider design-tokens.css 기준.
///
/// 1차(v1) = Material 3 표준 톤. 2차 톤앤매너(뉴모피즘) 교체 시 `Pw*` 위젯
/// 내부 구현만 바꾸면 화면 코드는 무영향.
class PwTheme {
  PwTheme._();

  // ── 베이스 (다크 4단계) ────────────────────────────────────────
  static const Color background   = Color(0xFF0B0B12); // 페이지 배경
  static const Color surface      = Color(0xFF14141C); // 카드
  static const Color surfaceLight = Color(0xFF1A1A24); // 카드 inset / 살짝 밝게
  static const Color border       = Color(0xFF1F1F2B); // 경계선

  // ── 텍스트 (3단계) ─────────────────────────────────────────────
  static const Color textPrimary   = Color(0xFFF2F3F7);
  static const Color textSecondary = Color(0xFF8A91A3);
  static const Color textHint      = Color(0xFF5A6072);

  // ── 브랜드 포인트 (mobile = 보라) ──────────────────────────────
  static const Color primary      = Color(0xFF8B5CF6);
  static const Color primaryLight = Color(0xFFA78BFA);

  // ── 상태색 (3콘솔 공통 의미색) ─────────────────────────────────
  static const Color error   = Color(0xFFEF4444); // 오류
  static const Color warning = Color(0xFFF59E0B); // 경고
  static const Color success = Color(0xFF22C55E); // 성공·완료

  // ── 라운드 ─────────────────────────────────────────────────────
  static const BorderRadius radiusS  = BorderRadius.all(Radius.circular(12));
  static const BorderRadius radiusM  = BorderRadius.all(Radius.circular(20));
  static const BorderRadius radiusL  = BorderRadius.all(Radius.circular(28));
  static const BorderRadius radiusXL = BorderRadius.all(Radius.circular(40));

  // ── 폰트 ───────────────────────────────────────────────────────
  // OS 시스템 폰트 사용 — iOS: San Francisco·Apple SD Gothic·Hiragino·PingFang /
  // Android: Roboto·Noto Sans CJK. ThemeData 에 fontFamily 미지정 → 플랫폼 기본.
  // 결정 2026-05-21: 모바일 UI 는 시스템 폰트 (성능·배터리·네이티브 느낌, 앱 용량 0).

  // ── ThemeData (Material 3 다크) ────────────────────────────────
  static ThemeData get theme => ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: background,
        colorScheme: const ColorScheme.dark(
          primary: primary,
          secondary: primary,
          surface: surface,
          error: error,
          onPrimary: Colors.white,
          onSecondary: Colors.white,
          onSurface: textPrimary,
          onError: Colors.white,
        ),
        textTheme: _textTheme,
        iconTheme: const IconThemeData(color: textPrimary, size: 24),
        dividerColor: border,
        appBarTheme: const AppBarTheme(
          backgroundColor: background,
          foregroundColor: textPrimary,
          elevation: 0,
          centerTitle: true,
          titleTextStyle: TextStyle(
            color: textPrimary,
            fontSize: 18,
            fontWeight: FontWeight.w600,
          ),
          iconTheme: IconThemeData(color: textPrimary),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: primary,
            foregroundColor: Colors.white,
            minimumSize: const Size(double.infinity, 54),
            shape: const RoundedRectangleBorder(borderRadius: radiusS),
            textStyle: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        inputDecorationTheme: const InputDecorationTheme(
          filled: true,
          fillColor: surface,
          hintStyle: TextStyle(color: textHint),
          contentPadding:
              EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          border: OutlineInputBorder(
            borderRadius: radiusS,
            borderSide: BorderSide(color: border),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: radiusS,
            borderSide: BorderSide(color: border),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: radiusS,
            borderSide: BorderSide(color: primary, width: 2),
          ),
          errorBorder: OutlineInputBorder(
            borderRadius: radiusS,
            borderSide: BorderSide(color: error),
          ),
        ),
        cardTheme: const CardThemeData(
          color: surface,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: radiusM,
            side: BorderSide(color: border, width: 1),
          ),
        ),
      );

  static const TextTheme _textTheme = TextTheme(
    displayLarge:
        TextStyle(fontSize: 32, fontWeight: FontWeight.w800, color: textPrimary),
    displayMedium:
        TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: textPrimary),
    displaySmall:
        TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: textPrimary),
    headlineMedium:
        TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: textPrimary),
    headlineSmall:
        TextStyle(fontSize: 20, fontWeight: FontWeight.w600, color: textPrimary),
    titleLarge:
        TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: textPrimary),
    titleMedium:
        TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: textPrimary),
    bodyLarge: TextStyle(fontSize: 15, color: textPrimary),
    bodyMedium: TextStyle(fontSize: 14, color: textPrimary),
    bodySmall: TextStyle(fontSize: 12, color: textSecondary),
    labelLarge:
        TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: textPrimary),
  );
}
