/// PathWave 공통 하단 시트(BottomSheet) — 흰 글래스 + 블러 처리된 딤.
///
/// 사용자 가이드(2026-06-04):
///   - **작성 / 긴 입력 / 약관 보기** → [showPwSheet] (하단에서 올라옴)
///   - **안내 / 컨펌 (Yes/No, OK)**   → [showPwDialog] (가운데 카드)
///   - 두 경우 모두 뒷 화면은 **블러 처리된 딤** (흰 글래스 톤 통일)
///
/// raw [showModalBottomSheet] 대신 [showPwSheet] 사용.
library;

import 'dart:ui';

import 'package:flutter/material.dart';

Future<T?> showPwSheet<T>({
  required BuildContext context,
  required Widget child,
  bool barrierDismissible = true,
}) {
  return showGeneralDialog<T>(
    context: context,
    barrierDismissible: barrierDismissible,
    barrierLabel: 'sheet',
    barrierColor: Colors.transparent,
    transitionDuration: const Duration(milliseconds: 220),
    pageBuilder: (ctx, a1, a2) => _SheetBarrier(
      barrierDismissible: barrierDismissible,
      child: PwSheet(child: child),
    ),
    transitionBuilder: (ctx, a1, a2, sheet) => SlideTransition(
      position: Tween<Offset>(begin: const Offset(0, 1), end: Offset.zero)
          .animate(CurvedAnimation(parent: a1, curve: Curves.easeOutCubic)),
      child: FadeTransition(opacity: a1, child: sheet),
    ),
  );
}

class _SheetBarrier extends StatelessWidget {
  final Widget child;
  final bool barrierDismissible;
  const _SheetBarrier({required this.child, required this.barrierDismissible});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
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
        Align(
          alignment: Alignment.bottomCenter,
          child: AnimatedPadding(
            duration: const Duration(milliseconds: 180),
            padding: EdgeInsets.only(bottom: MediaQuery.viewInsetsOf(context).bottom),
            child: child,
          ),
        ),
      ],
    );
  }
}

/// 흰 글래스 하단 시트 본체 (드래그 핸들 + blur + 흰 보더).
class PwSheet extends StatelessWidget {
  final Widget child;
  final EdgeInsets padding;
  const PwSheet({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.fromLTRB(20, 12, 20, 20),
  });

  @override
  Widget build(BuildContext context) {
    // 2026-06-10 — 최대 높이 = 화면 90% (status bar / safe area 위 자른 후).
    // 본문이 짧으면 mainAxisSize.min 으로 자연 크기, 길면 최대 높이까지만 + 스크롤.
    final mq = MediaQuery.of(context);
    final maxHeight = (mq.size.height - mq.padding.top) * 0.92;
    return Material(
      color: Colors.transparent,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxHeight: maxHeight),
        child: ClipRRect(
          borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 24, sigmaY: 24),
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.16),
                borderRadius:
                    const BorderRadius.vertical(top: Radius.circular(24)),
                border: Border(
                  top: BorderSide(
                    color: Colors.white.withValues(alpha: 0.22),
                    width: 1,
                  ),
                ),
              ),
              padding: padding,
              child: SafeArea(
                top: false,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // 드래그 핸들 — 흰 30%
                    Container(
                      width: 40,
                      height: 4,
                      margin: const EdgeInsets.only(bottom: 12),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.30),
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                    Flexible(child: child),
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
