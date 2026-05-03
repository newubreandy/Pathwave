import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../services/auth_service.dart';
import '../../utils/app_theme.dart';

/// 설정 화면
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _pushEnabled = true;
  bool _bleAutoScan = true;
  String _selectedLanguage = '한국어';

  final _languages = ['한국어', 'English', '日本語', '中文(简体)', '中文(繁體)', '中文(廣東話)', 'Français'];

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('설정'),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── 계정 정보 ────────────────────────────────────────
            const _SectionTitle('계정'),
            const SizedBox(height: 10),
            _SettingsGroup(
              children: [
                _SettingsItem(
                  icon: Icons.email_outlined,
                  label: '이메일',
                  trailing: Text(auth.user?['email'] ?? '-',
                    style: const TextStyle(fontSize: 13, color: AppTheme.textHint)),
                ),
                _SettingsItem(
                  icon: Icons.lock_outline_rounded,
                  label: '비밀번호 변경',
                  onTap: () {},
                ),
                _SettingsItem(
                  icon: Icons.shield_outlined,
                  label: '개인정보 보호',
                  onTap: () {},
                ),
              ],
            ),
            const SizedBox(height: 24),

            // ── 알림 설정 ────────────────────────────────────────
            const _SectionTitle('알림'),
            const SizedBox(height: 10),
            _SettingsGroup(
              children: [
                _SettingsItem(
                  icon: Icons.notifications_outlined,
                  label: '푸시 알림',
                  trailing: Switch.adaptive(
                    value: _pushEnabled,
                    onChanged: (v) => setState(() => _pushEnabled = v),
                    activeColor: AppTheme.primary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // ── WiFi / BLE ──────────────────────────────────────
            const _SectionTitle('WiFi & BLE'),
            const SizedBox(height: 10),
            _SettingsGroup(
              children: [
                _SettingsItem(
                  icon: Icons.bluetooth_rounded,
                  label: 'BLE 자동 스캔',
                  trailing: Switch.adaptive(
                    value: _bleAutoScan,
                    onChanged: (v) => setState(() => _bleAutoScan = v),
                    activeColor: AppTheme.primary,
                  ),
                ),
                _SettingsItem(
                  icon: Icons.wifi_rounded,
                  label: 'WiFi 자동 연결',
                  trailing: Switch.adaptive(
                    value: true,
                    onChanged: (v) {},
                    activeColor: AppTheme.primary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // ── 언어 설정 ────────────────────────────────────────
            const _SectionTitle('언어'),
            const SizedBox(height: 10),
            _SettingsGroup(
              children: [
                _SettingsItem(
                  icon: Icons.language_rounded,
                  label: '앱 언어',
                  trailing: Text(_selectedLanguage,
                    style: const TextStyle(fontSize: 13, color: AppTheme.primary,
                      fontWeight: FontWeight.w500)),
                  onTap: () => _showLanguagePicker(),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // ── 정보 ────────────────────────────────────────────
            const _SectionTitle('정보'),
            const SizedBox(height: 10),
            _SettingsGroup(
              children: [
                _SettingsItem(
                  icon: Icons.info_outline_rounded,
                  label: '앱 버전',
                  trailing: const Text('1.0.0',
                    style: TextStyle(fontSize: 13, color: AppTheme.textHint)),
                ),
                _SettingsItem(
                  icon: Icons.description_outlined,
                  label: '이용약관',
                  onTap: () {},
                ),
                _SettingsItem(
                  icon: Icons.privacy_tip_outlined,
                  label: '개인정보 처리방침',
                  onTap: () {},
                ),
                _SettingsItem(
                  icon: Icons.open_in_new_rounded,
                  label: '오픈소스 라이선스',
                  onTap: () {},
                ),
              ],
            ),
            const SizedBox(height: 24),

            // ── 계정 관리 ────────────────────────────────────────
            const _SectionTitle('계정 관리'),
            const SizedBox(height: 10),
            _SettingsGroup(
              children: [
                _SettingsItem(
                  icon: Icons.logout_rounded,
                  label: '로그아웃',
                  labelColor: AppTheme.error,
                  onTap: () => _confirmLogout(context, auth),
                ),
                _SettingsItem(
                  icon: Icons.delete_forever_outlined,
                  label: '회원탈퇴',
                  labelColor: AppTheme.textHint,
                  onTap: () => _confirmDeleteAccount(context),
                ),
              ],
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  void _showLanguagePicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (_) => Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 12),
            Container(width: 40, height: 4,
              decoration: BoxDecoration(color: AppTheme.border,
                borderRadius: BorderRadius.circular(2))),
            const SizedBox(height: 20),
            const Text('언어 선택', style: TextStyle(
              fontSize: 17, fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
            const SizedBox(height: 16),
            ..._languages.map((lang) => ListTile(
              title: Text(lang),
              trailing: _selectedLanguage == lang
                ? const Icon(Icons.check_rounded, color: AppTheme.primary)
                : null,
              onTap: () {
                setState(() => _selectedLanguage = lang);
                Navigator.pop(context);
              },
            )),
            SizedBox(height: MediaQuery.of(context).padding.bottom + 16),
          ],
        ),
      ),
    );
  }

  Future<void> _confirmLogout(BuildContext context, AuthService auth) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('로그아웃', style: TextStyle(fontWeight: FontWeight.w600)),
        content: const Text('정말 로그아웃 하시겠어요?',
          style: TextStyle(color: AppTheme.textSecondary)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소', style: TextStyle(color: AppTheme.textHint)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('로그아웃', style: TextStyle(color: AppTheme.error)),
          ),
        ],
      ),
    );
    if (confirmed == true && context.mounted) {
      await auth.logout();
      if (context.mounted) context.go('/auth/login');
    }
  }

  Future<void> _confirmDeleteAccount(BuildContext context) async {
    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('회원탈퇴', style: TextStyle(fontWeight: FontWeight.w600)),
        content: const Text('탈퇴 시 모든 데이터가 삭제되며,\n7일 이내 재가입이 불가합니다.',
          style: TextStyle(color: AppTheme.textSecondary, height: 1.5)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('취소', style: TextStyle(color: AppTheme.textHint)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('탈퇴하기', style: TextStyle(color: AppTheme.error)),
          ),
        ],
      ),
    );
  }
}

// ── 섹션 타이틀 ──────────────────────────────────────────────────────────
class _SectionTitle extends StatelessWidget {
  final String title;
  const _SectionTitle(this.title);
  @override
  Widget build(BuildContext context) {
    return Text(title, style: const TextStyle(
      fontSize: 14, fontWeight: FontWeight.w600, color: AppTheme.textHint));
  }
}

// ── 설정 그룹 ────────────────────────────────────────────────────────────
class _SettingsGroup extends StatelessWidget {
  final List<Widget> children;
  const _SettingsGroup({required this.children});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.border.withOpacity(0.5)),
      ),
      child: Column(
        children: [
          for (int i = 0; i < children.length; i++) ...[
            children[i],
            if (i < children.length - 1)
              Divider(height: 1, color: AppTheme.border.withOpacity(0.5),
                indent: 52),
          ],
        ],
      ),
    );
  }
}

// ── 설정 아이템 ──────────────────────────────────────────────────────────
class _SettingsItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color? labelColor;
  final Widget? trailing;
  final VoidCallback? onTap;

  const _SettingsItem({
    required this.icon, required this.label,
    this.labelColor, this.trailing, this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
        child: Row(
          children: [
            Icon(icon, size: 20,
              color: labelColor ?? AppTheme.textSecondary),
            const SizedBox(width: 14),
            Expanded(
              child: Text(label, style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w500,
                color: labelColor ?? AppTheme.textPrimary,
              )),
            ),
            if (trailing != null) trailing!
            else if (onTap != null)
              const Icon(Icons.chevron_right_rounded,
                color: AppTheme.textHint, size: 20),
          ],
        ),
      ),
    );
  }
}
