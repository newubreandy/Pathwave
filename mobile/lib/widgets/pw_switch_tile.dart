import 'package:flutter/material.dart';

import '../theme/pw_theme.dart';
import 'pw_switch.dart';

/// 라벨 + (선택) 보조 설명 + PwSwitch 가 한 행에 들어가는 통일 컴포넌트.
///
/// raw [SwitchListTile] 사용 금지 — 이 위젯이 색/간격/폰트를 표준화한다.
///
/// 사용
/// ----
/// ```dart
/// PwSwitchTile(
///   title: '마케팅 정보 수신',
///   subtitle: '이벤트/쿠폰 안내 푸시·이메일',
///   leading: const Icon(Icons.campaign_outlined),
///   value: _value,
///   onChanged: _toggle,
/// )
/// ```
class PwSwitchTile extends StatelessWidget {
  /// 메인 라벨.
  final String title;

  /// 선택 — 보조 설명 (작은 글씨, hint 색).
  final String? subtitle;

  /// 선택 — 왼쪽 아이콘 (보통 [Icon]).
  final Widget? leading;

  /// 현재 상태.
  final bool value;

  /// 토글 핸들러. null 이면 비활성 (회색).
  final ValueChanged<bool>? onChanged;

  /// 좌우 패딩 — 기본 16/4. ListTile 표준과 동일.
  final EdgeInsetsGeometry contentPadding;

  const PwSwitchTile({
    super.key,
    required this.title,
    required this.value,
    required this.onChanged,
    this.subtitle,
    this.leading,
    this.contentPadding =
        const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
  });

  @override
  Widget build(BuildContext context) {
    final disabled = onChanged == null;
    return InkWell(
      onTap: disabled ? null : () => onChanged!(!value),
      child: Padding(
        padding: contentPadding,
        child: Row(
          children: [
            if (leading != null) ...[
              IconTheme.merge(
                data: const IconThemeData(
                  color: PwTheme.textSecondary, size: 20),
                child: leading!,
              ),
              const SizedBox(width: 16),
            ],
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    child: Text(
                      title,
                      style: const TextStyle(fontSize: 14),
                    ),
                  ),
                  if (subtitle != null) ...[
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Text(
                        subtitle!,
                        style: const TextStyle(
                          color: PwTheme.textHint, fontSize: 11),
                      ),
                    ),
                  ],
                ],
              ),
            ),
            PwSwitch(value: value, onChanged: onChanged),
          ],
        ),
      ),
    );
  }
}
