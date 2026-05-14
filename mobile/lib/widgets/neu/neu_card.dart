import 'package:flutter/material.dart';
import '../../utils/neu_theme.dart';

/// PR #67 — Neumorphic Card.
///
/// 외부로 살짝 튀어나온 부드러운 카드. 그라디언트 + 이중 그림자로 입체감.
class NeuCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final BorderRadius borderRadius;
  final double shadowDistance;
  final double shadowBlur;
  final bool inset; // true 면 안으로 들어간(pressed) 느낌

  const NeuCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.borderRadius = NeuTheme.radiusM,
    this.shadowDistance = 6,
    this.shadowBlur = 14,
    this.inset = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: padding,
      decoration: BoxDecoration(
        color: NeuTheme.surface,
        borderRadius: borderRadius,
        gradient: inset
          ? null
          : const LinearGradient(
              begin: Alignment.topLeft,
              end:   Alignment.bottomRight,
              colors: [NeuTheme.surfaceLight, NeuTheme.surface],
            ),
        boxShadow: inset
          ? NeuTheme.pressedShadow(distance: shadowDistance / 3, blur: shadowBlur / 2)
          : NeuTheme.outerShadow(distance: shadowDistance, blur: shadowBlur),
      ),
      child: child,
    );
  }
}
