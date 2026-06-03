/// 글래스모피즘 카드 — 반투명 + backdrop blur + 흰색 1px 보더.
///
/// 사용:
///   GlassCard(
///     padding: EdgeInsets.all(16),
///     child: ...
///   )
///
/// 디자인 토큰 (AppTheme/Material 3 일관):
/// - radius:   AppTheme.rLg (20px)
/// - blur:     sigma 20
/// - bg fill:  white α 0.12 (어두운 배경 위) / black α 0.06 (밝은 배경 위)
/// - border:   white α 0.18, 1px
///
/// ``onDarkBackground`` 가 false 면 fill/border 색을 검정 톤으로 자동 전환.
library;

import 'dart:ui';

import 'package:flutter/material.dart';

import '../utils/app_theme.dart';

class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final double radius;
  final double sigma;
  final bool   onDarkBackground;

  /// 강조 보더(활성 카드 등) — null 이면 기본 흰색 alpha.
  final Color? borderHighlight;

  /// 카드 자체에 그림자(soft) 표시. 글래스 위에 살짝 떠 보이게.
  final bool elevated;

  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(AppTheme.s4),
    this.radius = AppTheme.rLg,
    this.sigma = 20.0,
    this.onDarkBackground = true,
    this.borderHighlight,
    this.elevated = false,
  });

  @override
  Widget build(BuildContext context) {
    final fill = onDarkBackground
        ? Colors.white.withValues(alpha: 0.12)
        : Colors.black.withValues(alpha: 0.06);
    final border = borderHighlight ??
        (onDarkBackground
            ? Colors.white.withValues(alpha: 0.18)
            : Colors.black.withValues(alpha: 0.12));

    final rect = BorderRadius.circular(radius);
    return Container(
      decoration: elevated
          ? BoxDecoration(
              borderRadius: rect,
              boxShadow: AppTheme.softShadowSm,
            )
          : null,
      child: ClipRRect(
        borderRadius: rect,
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: sigma, sigmaY: sigma),
          child: Container(
            padding: padding,
            decoration: BoxDecoration(
              color: fill,
              borderRadius: rect,
              border: Border.all(color: border, width: 1),
            ),
            child: child,
          ),
        ),
      ),
    );
  }
}

/// 작은 알약형 칩 (예: "NEW FEATURE"). 글래스 위에 자연스럽게 얹힌다.
class GlassPill extends StatelessWidget {
  final String label;
  final Color? color;
  final bool onDarkBackground;

  const GlassPill({
    super.key,
    required this.label,
    this.color,
    this.onDarkBackground = true,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color ??
            (onDarkBackground
                ? Colors.white.withValues(alpha: 0.18)
                : Colors.black.withValues(alpha: 0.10)),
        borderRadius: BorderRadius.circular(AppTheme.rPill),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.6,
          color: onDarkBackground ? Colors.white : Colors.black87,
        ),
      ),
    );
  }
}
