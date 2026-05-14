import 'package:flutter/material.dart';
import '../../utils/neu_theme.dart';

/// PR #67 — Neumorphic Text Field (안으로 살짝 들어간 입력 필드).
class NeuTextField extends StatelessWidget {
  final TextEditingController? controller;
  final String? hintText;
  final IconData? prefixIcon;
  final bool obscureText;
  final TextInputType? keyboardType;
  final ValueChanged<String>? onChanged;
  final String? Function(String?)? validator;
  final TextInputAction? textInputAction;

  const NeuTextField({
    super.key,
    this.controller,
    this.hintText,
    this.prefixIcon,
    this.obscureText = false,
    this.keyboardType,
    this.onChanged,
    this.validator,
    this.textInputAction,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: NeuTheme.surface,
        borderRadius: NeuTheme.radiusXL,
        boxShadow: NeuTheme.pressedShadow(distance: 2, blur: 6),
      ),
      child: TextFormField(
        controller: controller,
        obscureText: obscureText,
        keyboardType: keyboardType,
        onChanged: onChanged,
        validator: validator,
        textInputAction: textInputAction,
        style: const TextStyle(color: NeuTheme.textPrimary, fontSize: 15),
        cursorColor: NeuTheme.primary,
        decoration: InputDecoration(
          hintText: hintText,
          hintStyle: const TextStyle(color: NeuTheme.textHint),
          border: InputBorder.none,
          enabledBorder: InputBorder.none,
          focusedBorder: InputBorder.none,
          errorBorder: InputBorder.none,
          focusedErrorBorder: InputBorder.none,
          prefixIcon: prefixIcon == null
            ? null
            : Icon(prefixIcon, size: 20, color: NeuTheme.textSecondary),
          contentPadding: const EdgeInsets.symmetric(vertical: 16),
        ),
      ),
    );
  }
}
