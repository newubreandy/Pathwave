import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// 3 콘솔 공통 AppBar — back button 정책 통일.
///
/// 정책
/// ----
/// **모든 push 화면은 반드시 PwAppBar 사용 (raw `AppBar` 금지)**.
/// 사유: GoRouter `go()` 가 stack 을 replace 해서 자동 back arrow 가
/// 안 떠 사용자 동선이 막히는 사고가 반복.
///
/// 동작
/// ----
/// - `showBack=true` (기본): leading 자동으로 ←
///   - `Navigator.canPop()` true → pop
///   - false → `context.go(fallbackRoute)` (기본 `/home`)
/// - `showBack=false`: 진짜 root 탭 / splash 등에서 명시적으로 끄기
/// - `leading` 을 직접 넘기면 그게 우선 (예: 닫기 X 버튼이 필요한 모달성 화면)
///
/// 사용
/// ----
/// ```dart
/// Scaffold(
///   appBar: const PwAppBar(title: Text('고객센터')),
///   // bottom 이 있는 경우:
///   // appBar: PwAppBar(title: const Text('고객센터'), bottom: TabBar(...)),
/// )
/// ```
class PwAppBar extends StatelessWidget implements PreferredSizeWidget {
  /// 타이틀 위젯 (보통 `Text`).
  final Widget? title;

  /// leading 자동 ← 표시 여부. false 면 leading 미지정 (root tab/splash 용).
  final bool showBack;

  /// `Navigator.canPop()` 이 false 일 때 이동할 경로.
  final String fallbackRoute;

  /// 명시적 leading. 넘기면 showBack 무시.
  final Widget? leading;

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
    this.showBack = true,
    this.fallbackRoute = '/home',
    this.leading,
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

  Widget? _resolveLeading(BuildContext context) {
    if (leading != null) return leading;
    if (!showBack) return null;
    return IconButton(
      icon: const Icon(Icons.arrow_back),
      tooltip: '뒤로',
      onPressed: () {
        if (Navigator.of(context).canPop()) {
          Navigator.of(context).pop();
        } else {
          context.go(fallbackRoute);
        }
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return AppBar(
      leading: _resolveLeading(context),
      automaticallyImplyLeading: false, // 우리가 직접 결정 — Material 자동 추론 비활성
      title: title,
      actions: actions,
      bottom: bottom,
      centerTitle: centerTitle,
      backgroundColor: backgroundColor,
      elevation: elevation,
    );
  }
}
