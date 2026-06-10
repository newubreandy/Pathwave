import 'dart:ui';

import 'package:flutter/material.dart';

/// 3 콘솔 공통 AppBar — Material 표준 동작 위임형 + 글래스 톤 가이드.
///
/// 정책
/// ----
/// **모든 push 화면은 PwAppBar 사용 (raw `AppBar` 금지)** — 디자인 swap 시 한 곳만 교체.
///
/// 디자인 가이드 (시즌 배경 위 글래스 톤)
/// ------------------------------------
/// - 배경: 흰 글래스 6% + backdrop blur 14
/// - 하단: 흰 1px 보더 (콘텐츠 영역과 시각적 구분)
/// - 타이틀/back arrow: 흰 (NeuTheme.appBarTheme)
/// - flexibleSpace 로 글래스 fill — backgroundColor 는 transparent 유지
///
/// 동작
/// ----
/// - `automaticallyImplyLeading=true` (기본): Material 표준대로 Navigator 가
///   pop 가능하면 자동으로 BackButton (`←`) 표시.
/// - `leading` 직접 지정: 닫기 X 버튼 / 소셜 consent 단계처럼 직접 제어할 때 사용.
/// - 루트 탭(`HomeScreen` bottom-nav tab) 처럼 백 버튼이 없어야 하는 경우엔
///   `automaticallyImplyLeading: false`.
class PwAppBar extends StatelessWidget implements PreferredSizeWidget {
  final Widget? title;
  final Widget? leading;
  final bool automaticallyImplyLeading;
  final List<Widget>? actions;
  final PreferredSizeWidget? bottom;
  final bool? centerTitle;

  /// 배경색 — 명시되면 글래스 fill 대신 사용 (특수 페이지).
  final Color? backgroundColor;

  /// elevation. 글래스 톤은 0 유지.
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
      // 글래스 톤 영역 구분 — backdrop blur + 흰 fill + 하단 1px 보더.
      // 시즌 배경 위에 자연스럽게 떠 보이면서 콘텐츠 영역과 명확히 분리.
      flexibleSpace: backgroundColor != null
          ? null
          : ClipRect(
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
                child: Container(
                  // 2026-06-09 — 흰 글래스 톤 (사용자 가이드: 다른 화면처럼 흰 투명).
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.12),
                    border: Border(
                      bottom: BorderSide(
                        color: Colors.white.withValues(alpha: 0.22),
                        width: 1,
                      ),
                    ),
                  ),
                ),
              ),
            ),
    );
  }
}
