import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../services/ble_service.dart';
import '../../services/permission_service.dart';
import '../../utils/neu_theme.dart';
import '../../widgets/neu/neu_button.dart';
import '../../widgets/neu/neu_card.dart';
import '../../widgets/neu/neu_switch.dart';
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
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted) return;
      final auth = context.read<AuthService>();
      final ble  = context.read<BleService>();
      if (auth.user == null || ble.isScanning) return;

      final granted = await PermissionService.instance.ensureBluetoothScan(context);
      if (!granted || !mounted) return;
      await ble.startScan(userId: auth.user?['id']?.toString());
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
      backgroundColor: NeuTheme.background,
      body: SafeArea(child: tabs[_tab]),
      bottomNavigationBar: _NeuBottomNav(
        index: _tab,
        onTap: (i) => setState(() => _tab = i),
      ),
    );
  }
}

// ── 하단 네비게이션 (neumorphic) ──────────────────────────────────────────
class _NeuBottomNav extends StatelessWidget {
  final int index;
  final ValueChanged<int> onTap;
  const _NeuBottomNav({required this.index, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final items = [
      [Icons.home_outlined, Icons.home, '홈'],
      [Icons.search, Icons.search, '검색'],
      [Icons.person_outline, Icons.person, '마이'],
      [Icons.notifications_outlined, Icons.notifications, '알림'],
    ];
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
        child: Container(
          height: 70,
          decoration: BoxDecoration(
            color: NeuTheme.surface,
            borderRadius: BorderRadius.circular(36),
            gradient: const LinearGradient(
              begin: Alignment.topLeft, end: Alignment.bottomRight,
              colors: [NeuTheme.surfaceLight, NeuTheme.surface],
            ),
            boxShadow: NeuTheme.outerShadow(distance: 6, blur: 14),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: List.generate(items.length, (i) {
              final selected = index == i;
              final ic = items[i];
              return GestureDetector(
                onTap: () => onTap(i),
                behavior: HitTestBehavior.opaque,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: selected ? NeuTheme.surface : Colors.transparent,
                    borderRadius: BorderRadius.circular(24),
                    boxShadow: selected
                      ? NeuTheme.pressedShadow(distance: 1.5, blur: 4)
                      : null,
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        selected ? ic[1] as IconData : ic[0] as IconData,
                        color: selected ? NeuTheme.primary : NeuTheme.textSecondary,
                        size: 24,
                      ),
                      const SizedBox(height: 2),
                      Text(ic[2] as String,
                        style: TextStyle(
                          fontSize: 10,
                          color: selected ? NeuTheme.primary : NeuTheme.textSecondary,
                          fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                        )),
                    ],
                  ),
                ),
              );
            }),
          ),
        ),
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
        return SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 8),
              Text('PathWave', style: Theme.of(context).textTheme.displaySmall),
              const SizedBox(height: 6),
              const Text('비콘이 감지되면 자동으로 WiFi에 연결됩니다.',
                style: TextStyle(color: NeuTheme.textSecondary, fontSize: 14)),
              const SizedBox(height: 24),

              // BLE 스캔 상태 카드
              NeuCard(
                padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 18),
                child: Row(
                  children: [
                    Container(
                      width: 48, height: 48,
                      decoration: BoxDecoration(
                        color: NeuTheme.surface,
                        shape: BoxShape.circle,
                        boxShadow: NeuTheme.pressedShadow(distance: 1.5, blur: 4),
                      ),
                      child: Icon(
                        ble.isScanning ? Icons.bluetooth_searching : Icons.bluetooth_disabled,
                        color: ble.isScanning ? NeuTheme.accent : NeuTheme.textHint,
                        size: 22,
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            ble.isScanning ? '비콘 감지 중' : '비콘 감지 대기',
                            style: const TextStyle(
                              fontWeight: FontWeight.w700, fontSize: 15,
                              color: NeuTheme.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            ble.isScanning
                              ? '주변 비콘을 확인합니다.'
                              : '권한을 허용하면 자동 시작됩니다.',
                            style: const TextStyle(
                              color: NeuTheme.textSecondary, fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                    NeuSwitch(
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

              if (ble.pendingWifi != null) ...[
                _WifiBanner(
                  facility: ble.pendingWifi!['facility'],
                  wifi:     ble.pendingWifi!['wifi'],
                  onTap: () {
                    final f = ble.pendingWifi!['facility'] ?? {};
                    final w = ble.pendingWifi!['wifi'] ?? {};
                    context.push('/wifi-connect?'
                        'name=${Uri.encodeComponent(f['name']?.toString() ?? '')}'
                        '&ssid=${Uri.encodeComponent(w['ssid']?.toString() ?? '')}');
                  },
                  onDismiss: ble.clearPendingWifi,
                ),
              ] else
                NeuCard(
                  child: const Row(
                    children: [
                      Icon(Icons.wifi_off, color: NeuTheme.textHint),
                      SizedBox(width: 12),
                      Expanded(child: Text('아직 감지된 비콘이 없습니다.',
                        style: TextStyle(color: NeuTheme.textSecondary))),
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
    return NeuCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.wifi, color: NeuTheme.primary),
              const SizedBox(width: 8),
              Expanded(
                child: Text('${facility?['name'] ?? '매장'} WiFi 발견',
                  style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
              ),
              IconButton(
                icon: const Icon(Icons.close, size: 18),
                color: NeuTheme.textSecondary,
                onPressed: onDismiss),
            ],
          ),
          const SizedBox(height: 4),
          Text('SSID: ${wifi?['ssid'] ?? '—'}',
            style: const TextStyle(color: NeuTheme.textSecondary)),
          const SizedBox(height: 14),
          NeuButton(
            variant: NeuButtonVariant.primary,
            onPressed: onTap,
            child: const Center(child: Text('자동 연결하기')),
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

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('마이페이지', style: Theme.of(context).textTheme.displaySmall),
          const SizedBox(height: 18),

          NeuCard(
            child: Row(
              children: [
                Container(
                  width: 56, height: 56,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: const LinearGradient(
                      colors: [Color(0xFF8B5CF6), NeuTheme.primary],
                    ),
                    boxShadow: NeuTheme.outerShadow(distance: 4, blur: 8),
                  ),
                  child: const Icon(Icons.person, color: Colors.white, size: 28),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(email,
                        style: const TextStyle(
                          fontWeight: FontWeight.w700, fontSize: 15)),
                      const SizedBox(height: 2),
                      const Text('일반 회원',
                        style: TextStyle(color: NeuTheme.textSecondary, fontSize: 12)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),

          // PR #68 hotfix — 내부 메뉴는 push 로 (뒤로가기 히스토리 유지)
          _NeuMenuTile(icon: Icons.local_activity_outlined, title: '내 스탬프',
            onTap: () => context.push('/mypage/stamps')),
          const SizedBox(height: 10),
          _NeuMenuTile(icon: Icons.confirmation_number_outlined, title: '내 쿠폰',
            onTap: () => context.push('/mypage/coupons')),
          const SizedBox(height: 10),
          _NeuMenuTile(icon: Icons.family_restroom, title: '자녀 초대',
            onTap: () => context.push('/mypage/parent-invite')),
          const SizedBox(height: 10),
          _NeuMenuTile(icon: Icons.chat_bubble_outline, title: '매장 채팅',
            onTap: () => context.push('/chat')),
          const SizedBox(height: 10),
          _NeuMenuTile(icon: Icons.settings_outlined, title: '설정',
            onTap: () => context.push('/settings')),

          const SizedBox(height: 24),
          NeuButton(
            onPressed: () async {
              await context.read<AuthService>().logout();
              if (context.mounted) context.go('/auth/login');
            },
            child: const Center(
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.logout, color: NeuTheme.error, size: 18),
                  SizedBox(width: 8),
                  Text('로그아웃',
                    style: TextStyle(color: NeuTheme.error, fontWeight: FontWeight.w600)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}


class _NeuMenuTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final VoidCallback onTap;
  const _NeuMenuTile({
    required this.icon, required this.title, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: NeuCard(
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        child: Row(
          children: [
            Container(
              width: 38, height: 38,
              decoration: BoxDecoration(
                color: NeuTheme.surface,
                borderRadius: BorderRadius.circular(12),
                boxShadow: NeuTheme.pressedShadow(distance: 1, blur: 3),
              ),
              child: Icon(icon, size: 20, color: NeuTheme.primary),
            ),
            const SizedBox(width: 14),
            Expanded(child: Text(title,
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14))),
            const Icon(Icons.chevron_right, size: 20, color: NeuTheme.textHint),
          ],
        ),
      ),
    );
  }
}


// ── 알림 탭 ─────────────────────────────────────────────────────────────────
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
            style: TextStyle(color: NeuTheme.textSecondary)),
          const SizedBox(height: 24),
          Center(
            child: NeuButton(
              onPressed: () => context.push('/notifications'),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.open_in_new, size: 16),
                  SizedBox(width: 8),
                  Text('전체 알림 보기'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
