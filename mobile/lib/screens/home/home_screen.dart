import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../services/ble_service.dart';
import '../../services/i18n_service.dart';
import '../../services/permission_service.dart';
import '../../theme/pw_theme.dart';
import '../../widgets/notification_permission_dialog.dart';
import '../../widgets/pw.dart';
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
    // PR #58 — 권한 사전 안내 다이얼로그를 먼저 표시
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted) return;
      final auth = context.read<AuthService>();
      final ble  = context.read<BleService>();
      if (auth.user == null || ble.isScanning) return;

      final granted = await PermissionService.instance.ensureBluetoothScan(context);
      if (!granted || !mounted) return;
      await ble.startScan(userId: auth.user?['id']?.toString());

      // 정보통신망법 §50 — 푸시 알림 수신 동의 (마케팅 분리). BLE 흐름 완료 후 1회.
      if (!mounted) return;
      await NotificationPermissionDialog.showIfNeeded(context);
    });
  }

  @override
  Widget build(BuildContext context) {
    final t = I18nService.instance;
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
        backgroundColor: PwTheme.surface,
        indicatorColor: PwTheme.primary.withValues(alpha: 0.2),
        destinations: [
          NavigationDestination(icon: const Icon(Icons.home_outlined), selectedIcon: const Icon(Icons.home), label: t.t('nav.home', defaultValue: '홈')),
          NavigationDestination(icon: const Icon(Icons.search), selectedIcon: const Icon(Icons.search), label: t.t('nav.search', defaultValue: '검색')),
          NavigationDestination(icon: const Icon(Icons.person_outline), selectedIcon: const Icon(Icons.person), label: t.t('nav.my', defaultValue: '마이')),
          NavigationDestination(icon: const Icon(Icons.notifications_outlined), selectedIcon: const Icon(Icons.notifications), label: t.t('nav.notifications', defaultValue: '알림')),
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
    final t = I18nService.instance;
    return Consumer<BleService>(
      builder: (context, ble, _) {
        return Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('PathWave', style: Theme.of(context).textTheme.displaySmall),
              const SizedBox(height: 4),
              Text(
                t.t('home.subtitle',
                  defaultValue: '비콘이 감지되면 자동으로 WiFi에 연결됩니다.'),
                style: const TextStyle(color: PwTheme.textSecondary)),
              const SizedBox(height: 20),

              // BLE 스캔 상태 카드
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: PwTheme.surface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: PwTheme.border),
                ),
                child: Row(
                  children: [
                    Icon(
                      ble.isScanning ? Icons.bluetooth_searching : Icons.bluetooth_disabled,
                      color: ble.isScanning ? PwTheme.success : PwTheme.textHint,
                      size: 28,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            ble.isScanning
                              ? t.t('home.ble_scanning', defaultValue: '비콘 감지 중')
                              : t.t('home.ble_idle', defaultValue: '비콘 감지 대기'),
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                          Text(
                            ble.isScanning
                              ? t.t('home.ble_scanning_desc',
                                  defaultValue: '주변에 비콘이 있는지 확인합니다.')
                              : t.t('home.ble_idle_desc',
                                  defaultValue: '권한을 허용하면 자동으로 시작합니다.'),
                            style: const TextStyle(color: PwTheme.textSecondary, fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                    PwSwitch(
                      value: ble.isScanning,
                      onChanged: (v) async {
                        if (v) {
                          final granted = await PermissionService.instance
                              .ensureBluetoothScan(context);
                          if (!granted) return;
                          if (!context.mounted) return;
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
                    // push 사용 — wifi-connect 에서 시스템 백 제스처로 홈 복귀.
                    context.push('/wifi-connect?'
                        'name=${Uri.encodeComponent(f['name']?.toString() ?? '')}'
                        '&ssid=${Uri.encodeComponent(w['ssid']?.toString() ?? '')}');
                  },
                  onDismiss: ble.clearPendingWifi,
                ),
              ] else
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: PwTheme.surface,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: PwTheme.border),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.wifi_off, color: PwTheme.textHint),
                      const SizedBox(width: 12),
                      Expanded(child: Text(
                        t.t('home.no_beacon', defaultValue: '아직 감지된 비콘이 없습니다.'),
                        style: const TextStyle(color: PwTheme.textSecondary))),
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
    final t = I18nService.instance;
    final name = facility?['name']?.toString().trim();
    final store = (name == null || name.isEmpty)
      ? t.t('common.store', defaultValue: '매장')
      : name;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [
          PwTheme.primary.withValues(alpha: 0.16),
          PwTheme.primaryLight.withValues(alpha: 0.12),
        ]),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: PwTheme.primary.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.wifi, color: PwTheme.primary),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  '$store ${t.t('home.wifi_found', defaultValue: 'WiFi 발견')}',
                  style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
              ),
              PwIconButton(icon: Icons.close, size: 18, onPressed: onDismiss),
            ],
          ),
          const SizedBox(height: 4),
          Text('SSID: ${wifi?['ssid'] ?? '—'}',
            style: const TextStyle(color: PwTheme.textSecondary)),
          const SizedBox(height: 12),
          PwButton(
            onPressed: onTap,
            child: Text(t.t('wifi.btn_connect', defaultValue: '자동 연결하기')),
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
    final t = I18nService.instance;
    final auth = context.watch<AuthService>();
    final email = auth.user?['email']?.toString() ?? '—';

    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(t.t('mypage.title', defaultValue: '마이페이지'),
            style: Theme.of(context).textTheme.displaySmall),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: PwTheme.surface,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: PwTheme.border),
            ),
            child: Row(
              children: [
                const CircleAvatar(
                  radius: 24,
                  backgroundColor: PwTheme.primary,
                  child: Icon(Icons.person, color: Colors.white),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(email, style: const TextStyle(fontWeight: FontWeight.w600)),
                      Text(t.t('mypage.member_general', defaultValue: '일반 회원'),
                        style: const TextStyle(color: PwTheme.textSecondary)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // context.push 사용 — 스택 보존으로 시스템 백 제스처 + AppBar back arrow 동작 보장 (iOS HIG / Material 3).
          _MenuTile(icon: Icons.local_activity_outlined, title: t.t('mypage.menu_stamps', defaultValue: '내 스탬프'), onTap: () => context.push('/mypage/stamps')),
          _MenuTile(icon: Icons.confirmation_number_outlined, title: t.t('mypage.menu_coupons', defaultValue: '내 쿠폰'), onTap: () => context.push('/mypage/coupons')),
          _MenuTile(icon: Icons.favorite_outline, title: t.t('mypage.menu_favorites', defaultValue: '즐겨찾기'), onTap: () => context.push('/mypage/favorites')),
          _MenuTile(icon: Icons.family_restroom, title: t.t('mypage.menu_parent_invite', defaultValue: '자녀 초대'), onTap: () => context.push('/mypage/parent-invite')),
          _MenuTile(icon: Icons.chat_bubble_outline, title: t.t('mypage.menu_chat', defaultValue: '매장 채팅'), onTap: () => context.push('/chat')),
          _MenuTile(icon: Icons.headset_mic_outlined, title: t.t('mypage.menu_support', defaultValue: '고객센터'), onTap: () => context.push('/support')),
          _MenuTile(icon: Icons.settings_outlined, title: t.t('mypage.menu_settings', defaultValue: '설정'), onTap: () => context.push('/settings')),
          const Spacer(),
          PwButton(
            variant: PwButtonVariant.danger,
            icon: Icons.logout,
            onPressed: () async {
              await context.read<AuthService>().logout();
              if (context.mounted) context.go('/auth/login');
            },
            child: Text(t.t('auth.logout', defaultValue: '로그아웃')),
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
      color: PwTheme.surface,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: [
              Icon(icon, size: 22, color: PwTheme.textSecondary),
              const SizedBox(width: 12),
              Expanded(child: Text(title)),
              const Icon(Icons.chevron_right, size: 20, color: PwTheme.textHint),
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
    final t = I18nService.instance;
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(t.t('nav.notifications', defaultValue: '알림'),
            style: Theme.of(context).textTheme.displaySmall),
          const SizedBox(height: 8),
          Text(
            t.t('home.notif_desc',
              defaultValue: '스탬프 적립 / 쿠폰 발급 / 시스템 공지가 표시됩니다.'),
            style: const TextStyle(color: PwTheme.textSecondary)),
          const SizedBox(height: 16),
          Center(
            child: TextButton.icon(
              // push 사용 — 알림 화면에서 시스템 백 제스처로 홈 복귀.
              onPressed: () => context.push('/notifications'),
              icon: const Icon(Icons.open_in_new),
              label: Text(t.t('home.btn_all_notif', defaultValue: '전체 알림 보기')),
            ),
          ),
        ],
      ),
    );
  }
}
