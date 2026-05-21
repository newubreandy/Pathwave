import 'package:flutter/material.dart';

/// PathWave 표준 드롭다운 (Material 3 [DropdownButtonFormField] 추상화).
///
/// raw `DropdownButton` 직접 사용 금지 — label/hint/항목을 1줄 API 로 받는다.
///
/// ```dart
/// PwDropdown<String>(
///   value: _category,
///   label: '업종',
///   items: const [
///     PwDropdownItem('cafe', '카페'),
///     PwDropdownItem('food', '음식점'),
///   ],
///   onChanged: (v) => setState(() => _category = v),
/// )
/// ```
class PwDropdown<T> extends StatelessWidget {
  final T? value;
  final List<PwDropdownItem<T>> items;
  final ValueChanged<T?>? onChanged;
  final String? label;
  final String? hint;

  const PwDropdown({
    super.key,
    required this.value,
    required this.items,
    required this.onChanged,
    this.label,
    this.hint,
  });

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<T>(
      initialValue: value,
      items: [
        for (final it in items)
          DropdownMenuItem<T>(value: it.value, child: Text(it.label)),
      ],
      onChanged: onChanged,
      decoration: InputDecoration(labelText: label, hintText: hint),
    );
  }
}

/// [PwDropdown] 의 항목 1개.
class PwDropdownItem<T> {
  final T value;
  final String label;
  const PwDropdownItem(this.value, this.label);
}
