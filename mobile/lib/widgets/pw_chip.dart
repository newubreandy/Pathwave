import 'package:flutter/material.dart';

/// PathWave 표준 칩 — 선택 가능한 태그/필터.
///
/// raw [ChoiceChip] / [FilterChip] 직접 사용 대신 [PwChip] 으로 톤을 통일한다.
///
/// ```dart
/// PwChip(
///   label: '카페',
///   selected: _selected == 'cafe',
///   onSelected: () => setState(() => _selected = 'cafe'),
/// )
/// ```
class PwChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback? onSelected;

  const PwChip({
    super.key,
    required this.label,
    this.selected = false,
    this.onSelected,
  });

  @override
  Widget build(BuildContext context) {
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      onSelected: onSelected == null ? null : (_) => onSelected!(),
    );
  }
}
