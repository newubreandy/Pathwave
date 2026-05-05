import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../services/ble_service.dart';
import '../../utils/app_theme.dart';
import '../search/search_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _tab = 0;

  @override
  void initState() {
    super.initState();
    // 앱 진입 시 BLE 자동 스캔 시작 (백그라운드에서 비콘 감지)
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final auth = context.read<AuthService>();
      final ble  = context.read<BleService>();
      if (auth.user != null && !ble.isScanning) {
        await ble.startScan(userId: auth.user?['id']?.toString());
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final tabs = [
      const _HomeTab(),
      const SearchScreen(),
      const _MyPageTab(),
      const _NotificationsTab(),
    ];

    return Scaffold(
      body: SafeArea(child: tabs[_tab]),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        backgroundColor: AppTheme.surface,
        indicatorColor: AppTheme.primary.withValues(alpha: 0.2),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: '홈'),
          NavigationDestination(icon: Icon(Icons.search), selectedIcon: Icon(Icons.search), label: '검색'),
          NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: '마이'),
          NavigationDestination(icon: Icon(Icons.notifications_outlined), selectedIcon: Icon(Icons.notifications), label: '알림'),
        ],
      ),
    );
  }
}


// ── 홈 탭: BLE 상태 + WiFi 자동 연결 트리거 ─────────────────────────────────
class _HomeTab extends StatelessWidget {
  const _HomeTab();

  @override
  Widget build(BuildContext context) {
    return Consumer<BleService>(
      builder: (context, ble, _) {
        return Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('PathWave', style: Theme.of(context).textTheme.displaySmall),
              const SizedBox(height: 4),
              const Text('비콘이 감지되면 자동으로 WiFi에 연결됩니다.',
                style: TextStyle(color: AppTheme.textSecondary)),
              const SizedBox(height: 20),

              // BLE 스캔 상태 카드
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.surface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppTheme.border),
                ),
                child: Row(
                  children: [
                    Icon(
                      ble.isScanning ? Icons.bluetooth_searching : Icons.bluetooth_disabled,
                      color: ble.isScanning ? AppTheme.success : AppTheme.textHint,
                      size: 28,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            ble.isScanning ? '비콘 감지 중' : '비콘 감지 대기',
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                          Text(
                            ble.isScanning
                              ? '주변에 비콘이 있는지 확인합니다.'
                              : '권한을 허용하면 자동으로 시작합니다.',
                            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                    Switch(
                      value: ble.isScanning,
                      onChanged: (v) async {
                        if (v) {
                          final uid = context.read<AuthService>().user?['id']?.toString();
                          await ble.startScan(userId: uid);
                        } else {
                          await ble.stopScan();
                        }
                      },
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 16),

              // WiFi 자동 연결 알림 (비콘 감지 시)
              if (ble.pendingWifi != null) ...[
                _WifiBanner(
                  facility: ble.pendingWifi!['facility'],
                  wifi:     ble.pendingWifi!['wifi'],
                  onTap: () {
                    final f = ble.pendingWifi!['facility'] ?? {};
                    final w = ble.pendingWifi!['wifi'] ?? {};
                    context.go('/wifi-connect?'
                        'name=${Uri.encodeComponent(f['name']?.toString() ?? '')}'
                        '&ssid=${Uri.encodeComponent(w['ssid']?.toString() ?? '')}');
                  },
                  onDismiss: ble.clearPendingWifi,
                ),
              ] else
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppTheme.surface,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppTheme.border),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.wifi_off, color: AppTheme.textHint),
                      SizedBox(width: 12),
                      Expanded(child: Text('아직 감지된 비콘이 없습니다.',
                        style: TextStyle(color: AppTheme.textSecondary))),
                    ],
                  ),
                ),
            ],
          ),
        );
      },
    );
  }
}


class _WifiBanner extends StatelessWidget {
  final Map<String, dynamic>? facility;
  final Map<String, dynamic>? wifi;
  final VoidCallback onTap;
  final VoidCallback onDismiss;
  const _WifiBanner({
    required this.facility,
    required this.wifi,
    required this.onTap,
    required this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [
          AppTheme.primary.withValues(alpha: 0.16),
          AppTheme.secondary.withValues(alpha: 0.12),
        ]),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.primary.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.wifi, color: AppTheme.primary),
              const SizedBox(width: 8),
              Expanded(
                child: Text('${facility?['name'] ?? '매장'} WiFi 발견',
                  style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
              ),
              IconButton(icon: const Icon(Icons.close, size: 18), onPressed: onDismiss),
            ],
          ),
          const SizedBox(height: 4),
          Text('SSID: ${wifi?['ssid'] ?? '—'}',
            style: const TextStyle(color: AppTheme.textSecondary)),
          const SizedBox(height: 12),
          ElevatedButton(
            onPressed: onTap,
            child: const Text('자동 연결하기'),
          ),
        ],
      ),
    );
  }
}


// ── 마이 탭 ─────────────────────────────────────────────────────────────────
class _MyPageTab extends StatelessWidget {
  const _MyPageTab();

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final email = auth.user?['email']?.toString() ?? '—';

    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('마이페이지', style: Theme.of(context).textTheme.displaySmall),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppTheme.border),
            ),
            child: Row(
              children: [
                const CircleAvatar(
                  radius: 24,
                  backgroundColor: AppTheme.primary,
                  child: Icon(Icons.person, color: Colors.white),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(email, style: const TextStyle(fontWeight: FontWeight.w600)),
                      const Text('일반 회원', style: TextStyle(color: AppTheme.textSecondary)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _MenuTile(icon: Icons.local_activity_outlined, title: '내 스탬프', onTap: () => context.go('/mypage/stamps')),
          _MenuTile(icon: Icons.confirmation_number_outlined, title: '내 쿠폰', onTap: () => context.go('/mypage/coupons')),
          _MenuTile(icon: Icons.family_restroom,            title: '자녀 초대', onTap: () => context.go('/mypage/parent-invite')),
          _MenuTile(icon: Icons.chat_bubble_outline,        title: '매장 채팅', onTap: () => context.go('/chat')),
          _MenuTile(icon: Icons.settings_outlined,          title: '설정', onTap: () => context.go('/settings')),
          const Spacer(),
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
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
        ],
      ),
    );
  }
}


class _MenuTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final VoidCallback onTap;
  const _MenuTile({required this.icon, required this.title, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppTheme.surface,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: [
              Icon(icon, size: 22, color: AppTheme.textSecondary),
              const SizedBox(width: 12),
              Expanded(child: Text(title)),
              const Icon(Icons.chevron_right, size: 20, color: AppTheme.textHint),
            ],
          ),
        ),
      ),
    );
  }
}


// ── 알림 탭 (목록 진입 라우트로 이동) ───────────────────────────────────────
class _NotificationsTab extends StatelessWidget {
  const _NotificationsTab();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('알림', style: Theme.of(context).textTheme.displaySmall),
          const SizedBox(height: 8),
          const Text('스탬프 적립 / 쿠폰 발급 / 시스템 공지가 표시됩니다.',
            style: TextStyle(color: AppTheme.textSecondary)),
          const SizedBox(height: 16),
          Center(
            child: TextButton.icon(
              onPressed: () => context.go('/notifications'),
              icon: const Icon(Icons.open_in_new),
              label: const Text('전체 알림 보기'),
            ),
          ),
        ],
      ),
    );
  }
}


