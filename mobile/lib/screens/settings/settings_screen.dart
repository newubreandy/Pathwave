import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../services/policy_service.dart';
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
          _section(context, '약관 및 정책', [
            _linkTile(context, Icons.description_outlined,
              '서비스 이용약관', () => _showPolicy(context, 'terms')),
            _linkTile(context, Icons.privacy_tip_outlined,
              '개인정보 처리방침', () => _showPolicy(context, 'privacy')),
            _linkTile(context, Icons.location_on_outlined,
              '위치 정보 이용 약관', () => _showPolicy(context, 'location')),
            _linkTile(context, Icons.share_outlined,
              '제3자 정보 제공', () => _showPolicy(context, 'third_party')),
            _linkTile(context, Icons.campaign_outlined,
              '마케팅 정보 수신', () => _showPolicy(context, 'marketing')),
          ]),
          _section(context, '앱 정보', [
            _tile(context, Icons.info_outline, '버전', '1.0.0+1'),
            _tile(context, Icons.business_outlined, '사업자',
              '주식회사 트리거소프트 (triggersoft)'),
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
          const SizedBox(height: 8),
          TextButton(
            onPressed: () => context.push('/mypage/delete-account'),
            child: const Text('회원 탈퇴',
              style: TextStyle(
                color: AppTheme.error,
                decoration: TextDecoration.underline,
                fontSize: 13,
              )),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Future<void> _showPolicy(BuildContext context, String kind) async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(child: CircularProgressIndicator()),
    );
    try {
      final data = await PolicyService.instance.body(kind);
      if (!context.mounted) return;
      Navigator.of(context, rootNavigator: true).pop();
      await showModalBottomSheet(
        context: context,
        isScrollControlled: true,
        backgroundColor: AppTheme.surface,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
        ),
        builder: (ctx) => _PolicySheet(data: data),
      );
    } catch (e) {
      if (!context.mounted) return;
      Navigator.of(context, rootNavigator: true).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('약관을 불러오지 못했습니다: $e')),
      );
    }
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

  Widget _linkTile(BuildContext _, IconData icon, String title, VoidCallback onTap) {
    return ListTile(
      leading: Icon(icon, color: AppTheme.textSecondary, size: 20),
      title: Text(title, style: const TextStyle(fontSize: 14)),
      trailing: const Icon(Icons.chevron_right,
        color: AppTheme.textHint, size: 20),
      onTap: onTap,
    );
  }
}

class _PolicySheet extends StatelessWidget {
  final Map<String, dynamic> data;
  const _PolicySheet({required this.data});

  @override
  Widget build(BuildContext context) {
    final title = data['label']?.toString() ?? data['kind']?.toString() ?? '약관';
    final version = data['version']?.toString() ?? '';
    final body = data['body']?.toString() ?? '본문이 등록되어 있지 않습니다.';
    final effective = data['effective_at']?.toString();

    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.85,
      maxChildSize: 0.95,
      minChildSize: 0.5,
      builder: (_, scrollCtrl) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40, height: 4,
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(
                  color: AppTheme.border,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            Row(
              children: [
                Expanded(
                  child: Text(title,
                    style: Theme.of(context).textTheme.titleLarge),
                ),
                if (version.isNotEmpty)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.primary.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text('v$version',
                      style: const TextStyle(
                        color: AppTheme.primary,
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                      )),
                  ),
              ],
            ),
            if (effective != null && effective.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text('시행일: ${effective.split("T").first}',
                style: const TextStyle(color: AppTheme.textHint, fontSize: 12)),
            ],
            const Divider(height: 24),
            Expanded(
              child: SingleChildScrollView(
                controller: scrollCtrl,
                child: SelectableText(body,
                  style: const TextStyle(fontSize: 14, height: 1.6)),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('닫기'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
