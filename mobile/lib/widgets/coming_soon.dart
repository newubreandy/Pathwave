import 'package:flutter/material.dart';

import '../utils/app_theme.dart';

/// 후속 PR 에서 구현 예정인 화면용 공통 placeholder.
class ComingSoon extends StatelessWidget {
  final String title;
  final IconData icon;
  final String? subtitle;
  final String? prNote;
  const ComingSoon({
    super.key,
    required this.title,
    required this.icon,
    this.subtitle,
    this.prNote,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 88, height: 88,
              decoration: BoxDecoration(
                color: AppTheme.surface,
                borderRadius: BorderRadius.circular(22),
                border: Border.all(color: AppTheme.border),
              ),
              child: Icon(icon, size: 40, color: AppTheme.textSecondary),
            ),
            const SizedBox(height: 16),
            Text(title,
              style: Theme.of(context).textTheme.headlineMedium,
              textAlign: TextAlign.center),
            if (subtitle != null) ...[
              const SizedBox(height: 8),
              Text(subtitle!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppTheme.textSecondary)),
            ],
            const SizedBox(height: 12),
            const Text('UI 구현 예정',
              style: TextStyle(color: AppTheme.textHint, fontSize: 13)),
            if (prNote != null) ...[
              const SizedBox(height: 4),
              Text(prNote!, style: const TextStyle(color: AppTheme.primary, fontSize: 13)),
            ],
          ],
        ),
      ),
    );
  }
}
