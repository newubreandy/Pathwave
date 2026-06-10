/// PathWave 공통 팝업 — 흰 글래스 카드 + 항상 블러 처리된 딤 배경.
///
/// 사용자 정책(2026-06-04): "팝업은 흰색 투명한 바탕 + 딤 위에 항상 블러".
///
/// 사용 방법
/// --------
/// 1) **간단한 텍스트 다이얼로그** — [showPwDialog] 헬퍼 사용:
///       showPwDialog(context: c, title: Text('제목'),
///         content: Text('본문'), actions: [...]);
///
/// 2) **상태가 있는 다이얼로그** (체크박스/입력 등) — [PwDialog] 위젯을 직접 사용:
///       showPwDialogWidget(context: c, child: const MyStatefulDialog());
///    내부에서 MyStatefulDialog.build() 가 `PwDialog(title, content, actions)` 반환.
library;

import 'dart:ui';

import 'package:flutter/material.dart';

/// 텍스트형 다이얼로그 헬퍼 (state 없음).
Future<T?> showPwDialog<T>({
  required BuildContext context,
  required Widget title,
  required Widget content,
  required List<Widget> actions,
  bool barrierDismissible = true,
}) {
  return showPwDialogWidget<T>(
    context: context,
    barrierDismissible: barrierDismissible,
    child: PwDialog(title: title, content: content, actions: actions),
  );
}

/// 위젯형 다이얼로그 헬퍼 — child 가 자체적으로 [PwDialog] 를 build 하는 경우.
Future<T?> showPwDialogWidget<T>({
  required BuildContext context,
  required Widget child,
  bool barrierDismissible = true,
}) {
  return showGeneralDialog<T>(
    context: context,
    barrierDismissible: barrierDismissible,
    barrierLabel: 'dialog',
    barrierColor: Colors.transparent,
    transitionDuration: const Duration(milliseconds: 180),
    pageBuilder: (ctx, a1, a2) => _DialogBarrier(
      barrierDismissible: barrierDismissible,
      child: child,
    ),
    transitionBuilder: (ctx, a1, a2, child) {
      return FadeTransition(
        opacity: a1,
        child: ScaleTransition(
          scale: Tween<double>(begin: 0.96, end: 1.0).animate(
            CurvedAnimation(parent: a1, curve: Curves.easeOutCubic),
          ),
          child: child,
        ),
      );
    },
  );
}

class _DialogBarrier extends StatelessWidget {
  final Widget child;
  final bool barrierDismissible;
  const _DialogBarrier({required this.child, required this.barrierDismissible});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // 블러 처리된 딤 (사용자 정책 — barrier 위에 backdrop blur 강제)
        Positioned.fill(
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTap: barrierDismissible
                ? () => Navigator.of(context).maybePop()
                : null,
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
              child: ColoredBox(color: Colors.black.withValues(alpha: 0.45)),
            ),
          ),
        ),
        Center(child: child),
      ],
    );
  }
}

/// 흰 글래스 카드 (다이얼로그 본체) — Material/border/blur/padding 표준화.
///
/// 다이얼로그 콘텐츠에 상태가 있으면(StatefulWidget) 그 widget 의 build() 가
/// 이 [PwDialog] 를 반환하도록 한다. [showPwDialogWidget] 으로 띄운다.
class PwDialog extends StatelessWidget {
  final Widget title;
  final Widget content;
  final List<Widget> actions;
  final EdgeInsetsGeometry padding;

  const PwDialog({
    super.key,
    required this.title,
    required this.content,
    this.actions = const [],
    this.padding = const EdgeInsets.fromLTRB(20, 20, 20, 12),
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 28),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 380),
        child: Material(
          color: Colors.transparent,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(20),
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 24, sigmaY: 24),
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.22),
                    width: 1,
                  ),
                ),
                padding: padding,
                // 가이드 — title 중앙, content 좌측(긴 본문 가독성), actions 중앙 (iOS HIG)
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Center(
                      child: DefaultTextStyle(
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                        ),
                        child: title,
                      ),
                    ),
                    const SizedBox(height: 12),
                    DefaultTextStyle(
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        height: 1.5,
                      ),
                      child: content,
                    ),
                    if (actions.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          for (int i = 0; i < actions.length; i++) ...[
                            if (i != 0) const SizedBox(width: 8),
                            actions[i],
                          ],
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
