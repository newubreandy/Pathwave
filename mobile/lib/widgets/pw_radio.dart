import 'package:flutter/material.dart';

/// PathWave 표준 라디오 그룹 (단일 선택).
///
/// 화면마다 자작 라디오를 반복하지 말고 [PwRadioGroup] 을 사용한다.
/// 옵션 목록 + 현재 값 + onChanged 만 넘기면 그룹 전체를 렌더한다.
///
/// ```dart
/// PwRadioGroup<String>(
///   value: _gender,
///   onChanged: (v) => setState(() => _gender = v),
///   options: const [
///     PwRadioOption('m', '남성'),
///     PwRadioOption('f', '여성'),
///   ],
/// )
/// ```
class PwRadioGroup<T> extends StatelessWidget {
  final T? value;
  final ValueChanged<T?>? onChanged;
  final List<PwRadioOption<T>> options;

  const PwRadioGroup({
    super.key,
    required this.value,
    required this.onChanged,
    required this.options,
  });

  @override
  Widget build(BuildContext context) {
    final disabled = onChanged == null;
    return IgnorePointer(
      ignoring: disabled,
      child: Opacity(
        opacity: disabled ? 0.5 : 1,
        child: RadioGroup<T>(
          groupValue: value,
          onChanged: onChanged ?? (_) {},
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              for (final opt in options)
                InkWell(
                  onTap: () => onChanged?.call(opt.value),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(
                      children: [
                        Radio<T>(value: opt.value),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(opt.label,
                              style: const TextStyle(fontSize: 14)),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

/// [PwRadioGroup] 의 옵션 1개.
class PwRadioOption<T> {
  final T value;
  final String label;
  const PwRadioOption(this.value, this.label);
}
