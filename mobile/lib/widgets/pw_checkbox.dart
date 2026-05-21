import 'package:flutter/material.dart';

/// PathWave 표준 체크박스 — 라벨 + Checkbox 한 행, 행 전체 탭 가능.
///
/// raw [Checkbox] 직접 사용 금지 — 화면마다 자작 체크박스 반복을 막는다.
///
/// ```dart
/// PwCheckbox(
///   value: _agreed,
///   onChanged: (v) => setState(() => _agreed = v),
///   label: '약관에 동의합니다',
/// )
/// ```
class PwCheckbox extends StatelessWidget {
  final bool value;
  final ValueChanged<bool>? onChanged;
  final String label;

  const PwCheckbox({
    super.key,
    required this.value,
    required this.onChanged,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    final disabled = onChanged == null;
    return InkWell(
      onTap: disabled ? null : () => onChanged!(!value),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          children: [
            Checkbox(
              value: value,
              onChanged: disabled ? null : (v) => onChanged!(v ?? false),
            ),
            const SizedBox(width: 4),
            Expanded(
              child: Text(label, style: const TextStyle(fontSize: 14)),
            ),
          ],
        ),
      ),
    );
  }
}
