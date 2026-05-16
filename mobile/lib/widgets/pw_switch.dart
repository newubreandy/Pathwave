import 'package:flutter/material.dart';

/// PathWave 표준 Switch (Material 3 [Switch] 추상화).
///
/// 화면은 raw [Switch] 대신 [PwSwitch] 를 사용해 ON/OFF 색을 통일한다.
class PwSwitch extends StatelessWidget {
  final bool value;
  final ValueChanged<bool>? onChanged;

  const PwSwitch({
    super.key,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Switch.adaptive(
      value: value,
      onChanged: onChanged,
    );
  }
}
