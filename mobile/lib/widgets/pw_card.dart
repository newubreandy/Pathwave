import 'package:flutter/material.dart';

import '../utils/app_theme.dart';

/// PathWave 표준 Card (Material 3 [Card] 추상화).
///
/// 화면은 raw [Card] 또는 [Container] + decoration 대신 [PwCard] 를 사용한다.
/// padding/onTap/색상 톤을 일관되게 잡아주고, 2차 톤앤매너 교체 시 이 클래스만
/// 바꾸면 화면 코드는 그대로다.
class PwCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final VoidCallback? onTap;
  final BorderRadius borderRadius;
  final Color? color;
  final BoxBorder? border;

  const PwCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.onTap,
    this.borderRadius = const BorderRadius.all(Radius.circular(AppTheme.rLg)),
    this.color,
    this.border,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final box = Container(
      decoration: BoxDecoration(
        color: color ?? scheme.surface,
        borderRadius: borderRadius,
        border: border ?? Border.all(color: scheme.outlineVariant, width: 1),
      ),
      padding: padding,
      child: child,
    );
    if (onTap == null) return box;
    return Material(
      color: Colors.transparent,
      borderRadius: borderRadius,
      child: InkWell(
        onTap: onTap,
        borderRadius: borderRadius,
        child: box,
      ),
    );
  }
}
