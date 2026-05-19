import 'package:flutter/material.dart';

/// 3 콘솔 공통 AppBar — Material 표준 동작 위임형(simple) 래퍼.
///
/// 정책
/// ----
/// **모든 push 화면은 PwAppBar 사용 (raw `AppBar` 금지)** — 디자인 swap 시 한 곳만 교체.
///
/// 동작
/// ----
/// - `automaticallyImplyLeading=true` (기본): Material 표준대로 Navigator 가
///   pop 가능하면 자동으로 BackButton (`←`) 표시. iOS/Android 플랫폼 스타일 자동 적용.
/// - `leading` 직접 지정: 닫기 X 버튼 / 소셜 consent 단계처럼 직접 제어할 때 사용.
/// - 루트 탭(`HomeScreen` 의 bottom-nav tab) 처럼 백 버튼이 없어야 하는 경우엔
///   `automaticallyImplyLeading: false` 또는 raw `AppBar` 가 아닌 그 자체 위젯에서 처리.
///
/// 변경 이력
/// --------
/// - PR-J(2026-05-19) — 기존 `showBack` + `fallbackRoute='/home'` 자동 fallback 제거.
///   PR-G 에서 모든 진입 동선을 `context.push` 로 통일했고, Navigator.canPop=false 인 상태로
///   PwAppBar 가 노출되는 경우 = 라우팅 설계 오류이므로 호출부에서 명시적 처리.
class PwAppBar extends StatelessWidget implements PreferredSizeWidget {
  /// 타이틀 위젯 (보통 `Text`).
  final Widget? title;

  /// 명시적 leading. 지정되면 그대로 사용 (자동 추론보다 우선).
  final Widget? leading;

  /// Material 의 자동 BackButton 추론 사용 여부. 기본 true.
  final bool automaticallyImplyLeading;

  /// 우측 액션 버튼들.
  final List<Widget>? actions;

  /// 하단 위젯 (TabBar 등).
  final PreferredSizeWidget? bottom;

  /// title 중앙 정렬 여부 (iOS 스타일).
  final bool? centerTitle;

  /// 배경색 — 기본은 Theme.
  final Color? backgroundColor;

  /// elevation.
  final double? elevation;

  const PwAppBar({
    super.key,
    this.title,
    this.leading,
    this.automaticallyImplyLeading = true,
    this.actions,
    this.bottom,
    this.centerTitle,
    this.backgroundColor,
    this.elevation,
  });

  @override
  Size get preferredSize => Size.fromHeight(
    kToolbarHeight + (bottom?.preferredSize.height ?? 0),
  );

  @override
  Widget build(BuildContext context) {
    return AppBar(
      leading: leading,
      automaticallyImplyLeading: automaticallyImplyLeading,
      title: title,
      actions: actions,
      bottom: bottom,
      centerTitle: centerTitle,
      backgroundColor: backgroundColor,
      elevation: elevation,
    );
  }
}
