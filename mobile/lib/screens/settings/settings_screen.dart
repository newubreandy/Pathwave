import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../utils/api_config.dart';
import '../../utils/app_theme.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final email = auth.user?['email']?.toString() ?? '—';

    return Scaffold(
      appBar: AppBar(title: const Text('설정')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _section(context, '계정', [
            _tile(context, Icons.email_outlined, '이메일', email),
          ]),
          _section(context, '서버', [
            _tile(context, Icons.cloud_outlined, 'API Base URL', ApiConfig.baseUrl,
              subtitle: 'flutter run 시 --dart-define=API_BASE=... 로 변경'),
          ]),
          _section(context, '앱 정보', [
            _tile(context, Icons.info_outline, '버전', '1.0.0+1'),
            _tile(context, Icons.privacy_tip_outlined, '개인정보 처리방침', '후속 PR 예정'),
          ]),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: () async {
              await context.read<AuthService>().logout();
              if (context.mounted) context.go('/auth/login');
            },
            icon: const Icon(Icons.logout, color: AppTheme.error),
            label: const Text('로그아웃', style: TextStyle(color: AppTheme.error)),
            style: OutlinedButton.styleFrom(
              minimumSize: const Size(double.infinity, 50),
              side: const BorderSide(color: AppTheme.error),
            ),
          ),
        ],
      ),
    );
  }

  Widget _section(BuildContext context, String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          child: Text(title,
            style: const TextStyle(color: AppTheme.textHint, fontSize: 12, letterSpacing: 0.5)),
        ),
        Container(
          decoration: BoxDecoration(
            color: AppTheme.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppTheme.border),
          ),
          child: Column(children: children),
        ),
        const SizedBox(height: 8),
      ],
    );
  }

  Widget _tile(BuildContext _, IconData icon, String title, String value, {String? subtitle}) {
    return ListTile(
      leading: Icon(icon, color: AppTheme.textSecondary, size: 20),
      title: Text(title, style: const TextStyle(fontSize: 14)),
      subtitle: subtitle != null
        ? Text(subtitle, style: const TextStyle(color: AppTheme.textHint, fontSize: 11))
        : null,
      trailing: SizedBox(
        width: 180,
        child: Text(value,
          textAlign: TextAlign.right,
          style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
          overflow: TextOverflow.ellipsis),
      ),
    );
  }
}
