import 'package:flutter/material.dart';

import '../services/i18n_service.dart';
import '../theme/pw_theme.dart';
import 'pw_button.dart';

/// 목록 화면 공통 빈 상태 위젯 (구 `EmptyState` 의 Pw* 통일판).
///
/// 사용
/// ----
/// ```dart
/// const PwEmptyState(
///   icon: Icons.inbox_outlined,
///   title: '받은 알림이 없습니다',
///   subtitle: '스탬프 / 쿠폰 / 채팅 알림이 표시됩니다.',
/// )
/// ```
class PwEmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? subtitle;

  /// (선택) 액션 버튼. null 이면 표시 안 함.
  final String? actionLabel;
  final VoidCallback? onAction;

  const PwEmptyState({
    super.key,
    required this.icon,
    required this.title,
    this.subtitle,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 56, color: PwTheme.textHint),
            const SizedBox(height: 12),
            Text(title,
              textAlign: TextAlign.center,
              style: const TextStyle(color: PwTheme.textSecondary, fontSize: 15)),
            if (subtitle != null) ...[
              const SizedBox(height: 4),
              Text(subtitle!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: PwTheme.textHint, fontSize: 13)),
            ],
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 16),
              PwButton(
                variant: PwButtonVariant.outlined,
                fullWidth: false,
                onPressed: onAction,
                child: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// 에러 상태 위젯 + 재시도 버튼 (구 `ErrorState` 의 Pw* 통일판).
///
/// 사용
/// ----
/// ```dart
/// PwErrorState(
///   message: '알림을 불러오지 못했어요.',
///   onRetry: _reload,
/// )
/// ```
class PwErrorState extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;

  const PwErrorState({super.key, required this.message, this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 48, color: PwTheme.error),
            const SizedBox(height: 12),
            Text(message,
              textAlign: TextAlign.center,
              style: const TextStyle(color: PwTheme.textSecondary)),
            if (onRetry != null) ...[
              const SizedBox(height: 16),
              PwButton(
                variant: PwButtonVariant.outlined,
                fullWidth: false,
                icon: Icons.refresh,
                onPressed: onRetry,
                child: Text(I18nService.instance
                    .t('common.retry', defaultValue: '다시 시도')),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
