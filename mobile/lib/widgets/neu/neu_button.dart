import 'package:flutter/material.dart';
import '../../utils/neu_theme.dart';

/// PR #67 — Neumorphic Button.
///
/// 누르면 살짝 들어가는 효과. variant 별 테마:
/// - default: 회색 톤 raised
/// - primary: 보라 그라디언트 + 흰 텍스트
/// - accent : 초록 (CTA / 토글 ON 같은 강조)
/// - icon   : 둥근 사각형 아이콘 단독 버튼
enum NeuButtonVariant { defaultStyle, primary, accent, icon }

class NeuButton extends StatefulWidget {
  final VoidCallback? onPressed;
  final Widget child;
  final NeuButtonVariant variant;
  final EdgeInsetsGeometry padding;
  final BorderRadius borderRadius;
  final double? width;
  final double? height;

  const NeuButton({
    super.key,
    required this.child,
    this.onPressed,
    this.variant = NeuButtonVariant.defaultStyle,
    this.padding = const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
    this.borderRadius = NeuTheme.radiusXL,
    this.width,
    this.height,
  });

  factory NeuButton.icon({
    required Widget icon,
    VoidCallback? onPressed,
    double size = 56,
  }) => NeuButton(
    onPressed: onPressed,
    variant: NeuButtonVariant.icon,
    padding: EdgeInsets.zero,
    borderRadius: BorderRadius.circular(size / 2),
    width: size, height: size,
    child: Center(child: icon),
  );

  @override
  State<NeuButton> createState() => _NeuButtonState();
}

class _NeuButtonState extends State<NeuButton> {
  bool _pressed = false;

  Color get _bg {
    switch (widget.variant) {
      case NeuButtonVariant.primary:
        return NeuTheme.primary;
      case NeuButtonVariant.accent:
        return NeuTheme.accent;
      default:
        return NeuTheme.surface;
    }
  }

  Color get _fg {
    switch (widget.variant) {
      case NeuButtonVariant.primary:
      case NeuButtonVariant.accent:
        return Colors.white;
      default:
        return NeuTheme.textPrimary;
    }
  }

  LinearGradient? get _gradient {
    if (_pressed) return null;
    switch (widget.variant) {
      case NeuButtonVariant.primary:
        return const LinearGradient(
          begin: Alignment.topLeft, end: Alignment.bottomRight,
          colors: [NeuTheme.accentLight, NeuTheme.primary],
        );
      case NeuButtonVariant.accent:
        return const LinearGradient(
          begin: Alignment.topLeft, end: Alignment.bottomRight,
          colors: [NeuTheme.accentLight, NeuTheme.accent],
        );
      default:
        return const LinearGradient(
          begin: Alignment.topLeft, end: Alignment.bottomRight,
          colors: [NeuTheme.surfaceLight, NeuTheme.surface],
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final disabled = widget.onPressed == null;
    return GestureDetector(
      onTapDown:   (_) { if (!disabled) setState(() => _pressed = true); },
      onTapUp:     (_) { setState(() => _pressed = false); },
      onTapCancel: ()  { setState(() => _pressed = false); },
      onTap: widget.onPressed,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 90),
        width:   widget.width,
        height:  widget.height,
        padding: widget.padding,
        decoration: BoxDecoration(
          color: _bg,
          borderRadius: widget.borderRadius,
          gradient: _gradient,
          boxShadow: _pressed
            ? NeuTheme.pressedShadow(distance: 1.5, blur: 4)
            : NeuTheme.outerShadow(distance: 4, blur: 10),
        ),
        child: DefaultTextStyle.merge(
          style: TextStyle(
            color: disabled ? NeuTheme.textHint : _fg,
            fontSize: 15, fontWeight: FontWeight.w600,
          ),
          child: IconTheme.merge(
            data: IconThemeData(color: disabled ? NeuTheme.textHint : _fg),
            child: widget.child,
          ),
        ),
      ),
    );
  }
}
