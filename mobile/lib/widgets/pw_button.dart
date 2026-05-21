import 'package:flutter/material.dart';

import '../theme/pw_theme.dart';

/// PathWave 표준 버튼 (Material 3 기반 추상화).
///
/// 화면은 raw [ElevatedButton] / [OutlinedButton] / [TextButton] 대신 항상
/// [PwButton] 을 사용한다. variant 만 바꿔서 톤을 통일하고, loading 상태와
/// leadingIcon 패턴을 한 곳에 모은다.
///
/// 2차 톤앤매너 교체 시(Neu*) 이 위젯 내부 구현만 바꾸면 화면 코드는 그대로다.
enum PwButtonVariant {
  /// 메인 CTA — 보라 배경 + 흰 텍스트.
  primary,

  /// 보조 — 표면 톤 채움 + 텍스트 색.
  secondary,

  /// 외곽선만.
  outlined,

  /// 텍스트만 (링크 톤).
  text,

  /// 위험 액션 — 빨간 외곽선/텍스트.
  danger,
}

class PwButton extends StatelessWidget {
  final VoidCallback? onPressed;
  final Widget child;
  final PwButtonVariant variant;
  final IconData? icon;
  final bool loading;
  final bool fullWidth;
  final EdgeInsetsGeometry? padding;

  const PwButton({
    super.key,
    required this.onPressed,
    required this.child,
    this.variant = PwButtonVariant.primary,
    this.icon,
    this.loading = false,
    this.fullWidth = true,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final disabled = onPressed == null || loading;
    final content = _content(context, scheme);
    final minSize = fullWidth ? const Size(double.infinity, 50) : const Size(0, 44);

    switch (variant) {
      case PwButtonVariant.primary:
        return ElevatedButton(
          onPressed: disabled ? null : onPressed,
          style: ElevatedButton.styleFrom(
            minimumSize: minSize,
            padding: padding,
          ),
          child: content,
        );
      case PwButtonVariant.secondary:
        return FilledButton(
          onPressed: disabled ? null : onPressed,
          style: FilledButton.styleFrom(
            minimumSize: minSize,
            padding: padding,
            backgroundColor: PwTheme.surfaceLight,
            foregroundColor: PwTheme.textPrimary,
            side: const BorderSide(color: PwTheme.border),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
          ),
          child: content,
        );
      case PwButtonVariant.outlined:
        return OutlinedButton(
          onPressed: disabled ? null : onPressed,
          style: OutlinedButton.styleFrom(
            minimumSize: minSize,
            padding: padding,
            side: BorderSide(color: scheme.outline),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
          ),
          child: content,
        );
      case PwButtonVariant.text:
        return TextButton(
          onPressed: disabled ? null : onPressed,
          style: TextButton.styleFrom(
            minimumSize: fullWidth ? minSize : null,
            padding: padding,
          ),
          child: content,
        );
      case PwButtonVariant.danger:
        return OutlinedButton(
          onPressed: disabled ? null : onPressed,
          style: OutlinedButton.styleFrom(
            minimumSize: minSize,
            padding: padding,
            foregroundColor: scheme.error,
            side: BorderSide(color: scheme.error),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
          ),
          child: content,
        );
    }
  }

  Widget _content(BuildContext context, ColorScheme scheme) {
    if (loading) {
      return SizedBox(
        width: 20,
        height: 20,
        child: CircularProgressIndicator(
          strokeWidth: 2,
          color: variant == PwButtonVariant.primary ? Colors.white : scheme.primary,
        ),
      );
    }
    if (icon == null) return child;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 18),
        const SizedBox(width: 8),
        child,
      ],
    );
  }
}
