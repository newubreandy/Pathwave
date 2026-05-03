import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../services/auth_service.dart';
import '../../utils/app_theme.dart';

/// 마이페이지 화면
class MyPageScreen extends StatelessWidget {
  const MyPageScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();

    return Scaffold(
      backgroundColor: AppTheme.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('마이페이지',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary)),
              const SizedBox(height: 24),

              // ── 프로필 카드 ────────────────────────────────────
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF0F172A), Color(0xFF1E293B)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 56, height: 56,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [AppTheme.primary, AppTheme.secondary],
                        ),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Center(
                        child: Text(
                          (auth.user?['email'] ?? 'U')[0].toUpperCase(),
                          style: const TextStyle(
                            color: Colors.white, fontSize: 22,
                            fontWeight: FontWeight.w700),
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            auth.user?['email'] ?? '사용자',
                            style: const TextStyle(color: Colors.white,
                              fontSize: 16, fontWeight: FontWeight.w600),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '가입일: 2025.04.01',
                            style: TextStyle(color: Colors.white.withOpacity(0.6),
                              fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                    GestureDetector(
                      onTap: () {},
                      child: Container(
                        width: 36, height: 36,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(Icons.edit_rounded,
                          color: Colors.white, size: 18),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // ── 통계 카드 ──────────────────────────────────────
              Row(
                children: [
                  _StatCard(
                    icon: Icons.star_rounded,
                    label: '스탬프',
                    value: '24',
                    color: AppTheme.warning,
                  ),
                  const SizedBox(width: 12),
                  _StatCard(
                    icon: Icons.card_giftcard_rounded,
                    label: '쿠폰',
                    value: '5',
                    color: const Color(0xFFEC4899),
                  ),
                  const SizedBox(width: 12),
                  _StatCard(
                    icon: Icons.wifi_rounded,
                    label: '접속',
                    value: '38',
                    color: AppTheme.primary,
                  ),
                ],
              ),
              const SizedBox(height: 28),

              // ── 메뉴 섹션 1: 내 활동 ───────────────────────────
              const _SectionTitle('내 활동'),
              const SizedBox(height: 10),
              _MenuGroup(
                children: [
                  _MenuItem(
                    icon: Icons.star_rounded,
                    label: '스탬프',
                    color: AppTheme.warning,
                    onTap: () => context.push('/mypage/stamps'),
                  ),
                  _MenuItem(
                    icon: Icons.card_giftcard_rounded,
                    label: '쿠폰',
                    color: const Color(0xFFEC4899),
                    onTap: () => context.push('/mypage/coupons'),
                  ),
                  _MenuItem(
                    icon: Icons.history_rounded,
                    label: '접속 이력',
                    color: AppTheme.secondary,
                    onTap: () {},
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // ── 메뉴 섹션 2: 설정 ──────────────────────────────
              const _SectionTitle('설정'),
              const SizedBox(height: 10),
              _MenuGroup(
                children: [
                  _MenuItem(
                    icon: Icons.person_outline_rounded,
                    label: '프로필 수정',
                    color: AppTheme.textSecondary,
                    onTap: () {},
                  ),
                  _MenuItem(
                    icon: Icons.language_rounded,
                    label: '언어 설정',
                    color: AppTheme.primary,
                    subtitle: '한국어',
                    onTap: () {},
                  ),
                  _MenuItem(
                    icon: Icons.notifications_outlined,
                    label: '알림 설정',
                    color: AppTheme.warning,
                    onTap: () {},
                  ),
                  _MenuItem(
                    icon: Icons.settings_outlined,
                    label: '앱 설정',
                    color: AppTheme.textHint,
                    onTap: () => context.push('/settings'),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // ── 기타 ──────────────────────────────────────────
              const _SectionTitle('기타'),
              const SizedBox(height: 10),
              _MenuGroup(
                children: [
                  _MenuItem(
                    icon: Icons.help_outline_rounded,
                    label: '고객센터',
                    color: AppTheme.secondary,
                    onTap: () {},
                  ),
                  _MenuItem(
                    icon: Icons.info_outline_rounded,
                    label: '앱 정보',
                    color: AppTheme.textHint,
                    subtitle: 'v1.0.0',
                    onTap: () {},
                  ),
                  _MenuItem(
                    icon: Icons.logout_rounded,
                    label: '로그아웃',
                    color: AppTheme.error,
                    isDestructive: true,
                    onTap: () async {
                      final confirmed = await _showLogoutDialog(context);
                      if (confirmed && context.mounted) {
                        await context.read<AuthService>().logout();
                        if (context.mounted) context.go('/auth/login');
                      }
                    },
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<bool> _showLogoutDialog(BuildContext context) async {
    return await showDialog<bool>(
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
    ) ?? false;
  }
}

// ── 통계 카드 ────────────────────────────────────────────────────────────
class _StatCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _StatCard({
    required this.icon, required this.label,
    required this.value, required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color.withOpacity(0.06),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withOpacity(0.12)),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 8),
            Text(value, style: TextStyle(
              fontSize: 22, fontWeight: FontWeight.w700, color: color)),
            const SizedBox(height: 2),
            Text(label, style: const TextStyle(
              fontSize: 12, color: AppTheme.textHint)),
          ],
        ),
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

// ── 메뉴 그룹 ────────────────────────────────────────────────────────────
class _MenuGroup extends StatelessWidget {
  final List<Widget> children;
  const _MenuGroup({required this.children});

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
                indent: 56),
          ],
        ],
      ),
    );
  }
}

// ── 메뉴 아이템 ──────────────────────────────────────────────────────────
class _MenuItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final String? subtitle;
  final bool isDestructive;
  final VoidCallback onTap;

  const _MenuItem({
    required this.icon, required this.label, required this.color,
    required this.onTap, this.subtitle, this.isDestructive = false,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            Container(
              width: 32, height: 32,
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(9),
              ),
              child: Icon(icon, color: color, size: 17),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Text(label, style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w500,
                color: isDestructive ? AppTheme.error : AppTheme.textPrimary,
              )),
            ),
            if (subtitle != null)
              Text(subtitle!, style: const TextStyle(
                fontSize: 13, color: AppTheme.textHint)),
            if (!isDestructive)
              const SizedBox(width: 4),
            if (!isDestructive)
              const Icon(Icons.chevron_right_rounded,
                color: AppTheme.textHint, size: 20),
          ],
        ),
      ),
    );
  }
}
