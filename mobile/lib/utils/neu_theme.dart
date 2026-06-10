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
  // 그라데이션 배경 위에서도 가독성 확보 — 흰톤 (alpha) 기반.
  // Color(0xC8FFFFFF) = white 78% / Color(0x8AFFFFFF) = white 54%.
  // WCAG AA 4.5:1 통과 (보라/시안 그라데이션 + 0.15 오버레이 기준).
  static const Color textSecondary = Color(0xC8FFFFFF);
  static const Color textHint      = Color(0x8AFFFFFF);

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
    // 글로벌 SeasonalBackground 가 모든 화면 뒤를 깐다 — Scaffold 는 투명.
    scaffoldBackgroundColor: Colors.transparent,
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
    // 페이지 전환 — 글로벌 SeasonalBackground 위에서 콘텐츠만 페이드.
    // (2026-06-09) iOS 슬라이드 시 글래스 카드가 겹쳐 보이는 어색함 제거.
    pageTransitionsTheme: const PageTransitionsTheme(builders: {
      TargetPlatform.iOS:      _FadePageTransitionsBuilder(),
      TargetPlatform.android:  _FadePageTransitionsBuilder(),
      TargetPlatform.macOS:    _FadePageTransitionsBuilder(),
      TargetPlatform.windows:  _FadePageTransitionsBuilder(),
      TargetPlatform.linux:    _FadePageTransitionsBuilder(),
      TargetPlatform.fuchsia:  _FadePageTransitionsBuilder(),
    }),
    appBarTheme: const AppBarTheme(
      backgroundColor: Colors.transparent,
      surfaceTintColor: Colors.transparent,
      foregroundColor: textPrimary,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
    ),
    // 체크박스 — 보라 ON + 흰 보더 OFF (공통 가이드).
    checkboxTheme: CheckboxThemeData(
      fillColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.disabled)) {
          return Colors.white.withValues(alpha: 0.10);
        }
        if (states.contains(WidgetState.selected)) {
          return primary;                                   // ON 보라 fill
        }
        return Colors.transparent;                          // OFF 투명 (보더만)
      }),
      checkColor: WidgetStateProperty.all(Colors.white),    // ✓ 흰
      side: BorderSide(color: Colors.white.withValues(alpha: 0.55), width: 1.5),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
    ),
    // 토글(Switch) — 브랜드 보라 ON + 어두운 OFF 강제.
    //   iOS 디폴트 ActivateColor(녹색) 무력화 + Material 3 톤 통일.
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.disabled)) {
          return Colors.white.withValues(alpha: 0.30);
        }
        if (states.contains(WidgetState.selected)) {
          return Colors.white;                          // ON thumb 흰
        }
        return Colors.white.withValues(alpha: 0.85);    // OFF thumb 회색흰
      }),
      trackColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.disabled)) {
          return Colors.white.withValues(alpha: 0.08);
        }
        if (states.contains(WidgetState.selected)) {
          return primary;                               // ON track 보라
        }
        return Colors.black.withValues(alpha: 0.40);    // OFF track 어두운
      }),
      trackOutlineColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return Colors.transparent;
        }
        return Colors.white.withValues(alpha: 0.20);    // OFF 외곽 살짝 보임
      }),
      trackOutlineWidth: WidgetStateProperty.all(1),
    ),
    // 모달 시트 — 글래스 다크 + 흰 보더 (DialogTheme 와 동일 톤).
    bottomSheetTheme: BottomSheetThemeData(
      backgroundColor: const Color(0xE61A1A24),
      surfaceTintColor: Colors.transparent,
      modalBackgroundColor: const Color(0xE61A1A24),
      modalBarrierColor: const Color(0x99000000),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        side: BorderSide(color: Colors.white.withValues(alpha: 0.12), width: 1),
      ),
    ),
    // 구분선 — 모든 raw Divider 자동 흰 톤.
    dividerTheme: DividerThemeData(
      color: Colors.white.withValues(alpha: 0.14),
      thickness: 1,
      space: 1,
    ),
    // 다이얼로그 — 글래스 톤 통일 (모든 raw AlertDialog 자동 적용).
    dialogTheme: DialogThemeData(
      backgroundColor: const Color(0xE61A1A24),    // 거의 불투명한 다크 (글래스 위 가독성)
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(color: Colors.white.withValues(alpha: 0.12), width: 1),
      ),
      titleTextStyle: const TextStyle(
        color: textPrimary, fontSize: 18, fontWeight: FontWeight.w700,
      ),
      contentTextStyle: const TextStyle(
        color: textSecondary, fontSize: 14, height: 1.5,
      ),
    ),
    // 하단 NavigationBar — 흰색 floating pill (시즌 배경 위에 떠 있는 둥근 바).
    // 컨테이너(흰 배경·radius·그림자)는 home_screen 에서, 색/크기/라벨은 여기서.
    // 선택=보라 채움 + 라벨 / 미선택=진회색 라인(라벨 숨김, onlyShowSelected).
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: Colors.transparent,   // pill 컨테이너가 흰색을 담당
      surfaceTintColor: Colors.transparent,
      indicatorColor: Colors.transparent,    // 선택 알약 배경 없음 — 아이콘 색으로만 강조
      elevation: 0,
      height: 68,
      // 색은 흰색 통일 — 선택/미선택 구분은 라인(미선택)/채움(선택) 모양으로.
      labelTextStyle: const WidgetStatePropertyAll(
        TextStyle(fontSize: 11.5, fontWeight: FontWeight.w700, color: Colors.white),
      ),
      iconTheme: const WidgetStatePropertyAll(
        IconThemeData(color: Colors.white, size: 28), // 24→28 키움
      ),
    ),
    // 탭바 — 흰 톤 통일 (모든 raw TabBar 자동 적용).
    // 정책: 활성/비활성 모두 흰색(가독성 우선) + 두꺼운 흰 인디케이터로 활성 강조.
    tabBarTheme: TabBarThemeData(
      labelColor: Colors.white,
      unselectedLabelColor: Colors.white.withValues(alpha: 0.70),
      labelStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
      unselectedLabelStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
      // 두꺼운 흰 underline — 라벨 색이 같아도 활성 탭이 한눈에 보인다.
      indicator: const UnderlineTabIndicator(
        borderSide: BorderSide(color: Colors.white, width: 4),
        insets: EdgeInsets.symmetric(horizontal: 12),
      ),
      indicatorSize: TabBarIndicatorSize.tab,
      dividerColor: Colors.white.withValues(alpha: 0.22),
      dividerHeight: 1,
    ),
    // 글래스 톤 입력 필드 — 그라데이션 위에 자연스럽게 떠 보이고 가독성 OK.
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: const Color(0x1FFFFFFF),                  // white 12%
      hintStyle:    const TextStyle(color: textHint),
      labelStyle:   const TextStyle(color: textSecondary),
      helperStyle:  const TextStyle(color: textHint, fontSize: 12),
      prefixIconColor: textSecondary,
      suffixIconColor: textSecondary,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: Color(0x2EFFFFFF), width: 1),  // 18%
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: Color(0x2EFFFFFF), width: 1),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: primary, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: error, width: 1),
      ),
    ),
  );
}


/// 모든 플랫폼에서 페이지 전환을 부드러운 페이드로 통일.
/// 글래스 카드 + 시즌 배경 가이드에 맞춰 콘텐츠만 자연스럽게 이어진다.
class _FadePageTransitionsBuilder extends PageTransitionsBuilder {
  const _FadePageTransitionsBuilder();

  @override
  Widget buildTransitions<T>(
    PageRoute<T> route,
    BuildContext context,
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  ) {
    return FadeTransition(opacity: animation, child: child);
  }
}
