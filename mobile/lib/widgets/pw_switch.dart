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
    // Material 3 Switch (raw `Switch`) — NeuTheme.switchTheme 글로벌 정책 자동 적용.
    // ※ Switch.adaptive 는 iOS 에서 CupertinoSwitch 로 fallback 되어
    //   switchTheme 가 무시되므로 사용 금지(녹색 ON 색이 강제됨).
    return Switch(
      value: value,
      onChanged: onChanged,
    );
  }
}
