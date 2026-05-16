import 'package:flutter/material.dart';

/// PathWave 표준 텍스트 필드 (Material 3 [TextFormField] 추상화).
///
/// 화면은 raw [TextField] / [TextFormField] + [InputDecoration] 대신
/// [PwTextField] 를 사용한다. label/hint/prefix-icon/obscure/keyboardType/
/// validator/maxLength/helperText 같은 흔한 옵션을 1줄 API 로 받는다.
class PwTextField extends StatelessWidget {
  final TextEditingController? controller;
  final String? label;
  final String? hint;
  final String? helperText;
  final IconData? prefixIcon;
  final Widget? suffix;
  final bool obscureText;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onSubmitted;
  final String? Function(String?)? validator;
  final int? maxLength;
  final bool counter;
  final TextStyle? style;
  final TextAlign textAlign;
  final bool autofocus;
  final bool enabled;

  const PwTextField({
    super.key,
    this.controller,
    this.label,
    this.hint,
    this.helperText,
    this.prefixIcon,
    this.suffix,
    this.obscureText = false,
    this.keyboardType,
    this.textInputAction,
    this.onChanged,
    this.onSubmitted,
    this.validator,
    this.maxLength,
    this.counter = false,
    this.style,
    this.textAlign = TextAlign.start,
    this.autofocus = false,
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      obscureText: obscureText,
      keyboardType: keyboardType,
      textInputAction: textInputAction,
      onChanged: onChanged,
      onFieldSubmitted: onSubmitted,
      validator: validator,
      maxLength: maxLength,
      style: style,
      textAlign: textAlign,
      autofocus: autofocus,
      enabled: enabled,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        helperText: helperText,
        prefixIcon: prefixIcon == null ? null : Icon(prefixIcon),
        suffixIcon: suffix,
        counterText: counter ? null : '',
      ),
    );
  }
}
