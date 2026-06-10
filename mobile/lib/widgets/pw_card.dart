import 'dart:ui';

import 'package:flutter/material.dart';

import '../utils/app_theme.dart';

/// PathWave 표준 Card (Material 3 [Card] 추상화).
///
/// 화면은 raw [Card] 또는 [Container] + decoration 대신 [PwCard] 를 사용한다.
/// padding/onTap/색상 톤을 일관되게 잡아주고, 2차 톤앤매너 교체 시 이 클래스만
/// 바꾸면 화면 코드는 그대로다.
///
/// 디폴트 = 글래스모피즘 (반투명 흰 + backdrop blur). 시즌 배경 위에서
/// 자연스럽게 떠 보인다. 다크 단색 배경 위에서도 그냥 반투명 패널로 동작
/// (시각적 손상 없음).
///
/// 글래스가 어울리지 않는 화면(예: 모달 내부 인풋 카드)은 ``glass: false``
/// 로 기존 surface 단색 카드로 회귀할 수 있다. ``color`` 가 명시되면
/// 자동으로 단색 모드.
class PwCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final VoidCallback? onTap;
  final BorderRadius borderRadius;
  final Color? color;
  final BoxBorder? border;
  final bool glass;

  const PwCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.onTap,
    this.borderRadius = const BorderRadius.all(Radius.circular(AppTheme.rLg)),
    this.color,
    this.border,
    this.glass = true,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    // ── 글래스 모드 (디폴트) ─────────────────────────────────────────────
    if (glass && color == null) {
      final fill = Colors.white.withValues(alpha: 0.12);
      final borderColor = Colors.white.withValues(alpha: 0.18);
      final inner = Container(
        padding: padding,
        decoration: BoxDecoration(
          color: fill,
          borderRadius: borderRadius,
          border: border ?? Border.all(color: borderColor, width: 1),
        ),
        child: child,
      );
      Widget body = ClipRRect(
        borderRadius: borderRadius,
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
          child: inner,
        ),
      );
      if (onTap != null) {
        body = Material(
          color: Colors.transparent,
          borderRadius: borderRadius,
          child: InkWell(
            onTap: onTap,
            borderRadius: borderRadius,
            child: body,
          ),
        );
      }
      return body;
    }

    // ── 단색 모드 (기존 호환) ─────────────────────────────────────────────
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
