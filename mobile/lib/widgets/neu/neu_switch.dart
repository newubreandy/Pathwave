import 'package:flutter/material.dart';
import '../../utils/neu_theme.dart';

/// PR #67 — Neumorphic Switch (ON/OFF 토글).
///
/// 레퍼런스 이미지의 초록 ON / 흰 손잡이 + 그림자 스타일.
class NeuSwitch extends StatelessWidget {
  final bool value;
  final ValueChanged<bool>? onChanged;
  final double width;
  final double height;

  const NeuSwitch({
    super.key,
    required this.value,
    this.onChanged,
    this.width  = 64,
    this.height = 32,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onChanged == null ? null : () => onChanged!(!value),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOut,
        width: width,
        height: height,
        padding: const EdgeInsets.all(3),
        decoration: BoxDecoration(
          color: value ? NeuTheme.accent : NeuTheme.surface,
          gradient: value
            ? const LinearGradient(
                begin: Alignment.topLeft, end: Alignment.bottomRight,
                colors: [NeuTheme.accentLight, NeuTheme.accent],
              )
            : null,
          borderRadius: BorderRadius.circular(height / 2),
          boxShadow: value
            ? NeuTheme.outerShadow(distance: 2, blur: 6)
            : NeuTheme.pressedShadow(distance: 1.5, blur: 3),
        ),
        child: Stack(
          children: [
            AnimatedAlign(
              duration: const Duration(milliseconds: 220),
              curve: Curves.easeOut,
              alignment: value ? Alignment.centerRight : Alignment.centerLeft,
              child: Container(
                width: height - 6,
                height: height - 6,
                decoration: BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: NeuTheme.shadowDark.withValues(alpha: 0.4),
                      blurRadius: 4,
                      offset: const Offset(1, 2),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
