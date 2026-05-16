import 'package:flutter/material.dart';

/// PathWave 표준 IconButton (Material 3 기반).
///
/// 화면은 raw [IconButton] 대신 [PwIconButton] 을 사용해 색/툴팁 톤을 통일한다.
class PwIconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback? onPressed;
  final String? tooltip;
  final double size;
  final Color? color;

  const PwIconButton({
    super.key,
    required this.icon,
    required this.onPressed,
    this.tooltip,
    this.size = 22,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return IconButton(
      tooltip: tooltip,
      onPressed: onPressed,
      icon: Icon(
        icon,
        size: size,
        color: color ?? scheme.onSurface,
      ),
    );
  }
}
