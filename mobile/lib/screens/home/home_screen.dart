import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../services/auth_service.dart';
import '../../services/ble_service.dart';
import '../../utils/app_theme.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    // BLE 스캔 시작
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final auth = context.read<AuthService>();
      context.read<BleService>().startScan(
        userId: auth.user?['id']?.toString(),
      );
    });
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final ble  = context.watch<BleService>();

    // WiFi 감지 알림
    if (ble.pendingWifi != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _showWifiAlert(context, ble);
      });
    }

    return Scaffold(
      backgroundColor: AppTheme.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── 상단 헤더 ────────────────────────────────────────
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('안녕하세요 👋',
                          style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
                        const SizedBox(height: 2),
                        Text(auth.user?['email'] ?? 'PathWave',
                          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700,
                            color: AppTheme.textPrimary)),
                      ],
                    ),
                  ),
                  GestureDetector(
                    onTap: () => context.push('/notifications'),
                    child: Container(
                      width: 44, height: 44,
                      decoration: BoxDecoration(
                        color: AppTheme.surface,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppTheme.border),
                      ),
                      child: const Icon(Icons.notifications_outlined,
                        color: AppTheme.textPrimary, size: 22),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // ── WiFi 감지 카드 ──────────────────────────────────
              GestureDetector(
                onTap: () => ble.simulateBeaconDetection(),
                child: AnimatedBuilder(
                  animation: _pulseController,
                  builder: (context, child) {
                    return Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [
                            AppTheme.primary,
                            Color.lerp(AppTheme.primary, const Color(0xFF065F46),
                              _pulseController.value * 0.3)!,
                          ],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: [
                          BoxShadow(
                            color: AppTheme.primary.withOpacity(0.25),
                            blurRadius: 20,
                            offset: const Offset(0, 8),
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Container(
                                width: 40, height: 40,
                                decoration: BoxDecoration(
                                  color: Colors.white.withOpacity(0.2),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: const Icon(Icons.wifi_rounded,
                                  color: Colors.white, size: 22),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text('스마트 WiFi',
                                      style: TextStyle(color: Colors.white,
                                        fontSize: 16, fontWeight: FontWeight.w600)),
                                    const SizedBox(height: 2),
                                    Text(
                                      ble.isScanning
                                        ? '주변 WiFi를 감지하고 있어요...'
                                        : 'BLE 스캔 대기 중',
                                      style: TextStyle(
                                        color: Colors.white.withOpacity(0.8),
                                        fontSize: 13),
                                    ),
                                  ],
                                ),
                              ),
                              if (ble.isScanning)
                                SizedBox(width: 18, height: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white.withOpacity(0.8),
                                  ),
                                ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.15),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.touch_app_rounded,
                                  color: Colors.white.withOpacity(0.8), size: 16),
                                const SizedBox(width: 6),
                                Text('터치하여 WiFi 감지 테스트',
                                  style: TextStyle(color: Colors.white.withOpacity(0.9),
                                    fontSize: 12, fontWeight: FontWeight.w500)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(height: 28),

              // ── 빠른 서비스 ─────────────────────────────────────
              const Text('서비스',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary)),
              const SizedBox(height: 14),
              GridView.count(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisCount: 2,
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 1.35,
                children: [
                  _ServiceCard(
                    icon: Icons.store_rounded,
                    label: '시설 안내',
                    subtitle: '주변 시설 보기',
                    gradient: const [Color(0xFF10B981), Color(0xFF059669)],
                    onTap: () {},
                  ),
                  _ServiceCard(
                    icon: Icons.card_giftcard_rounded,
                    label: '쿠폰',
                    subtitle: '할인 혜택',
                    gradient: const [Color(0xFFEC4899), Color(0xFFDB2777)],
                    onTap: () => context.push('/mypage/coupons'),
                  ),
                  _ServiceCard(
                    icon: Icons.star_rounded,
                    label: '스탬프',
                    subtitle: '적립 현황',
                    gradient: const [Color(0xFFF59E0B), Color(0xFFD97706)],
                    onTap: () => context.push('/mypage/stamps'),
                  ),
                  _ServiceCard(
                    icon: Icons.chat_bubble_outline_rounded,
                    label: '문의',
                    subtitle: '실시간 채팅',
                    gradient: const [Color(0xFF06B6D4), Color(0xFF0891B2)],
                    onTap: () => context.push('/chat'),
                  ),
                ],
              ),
              const SizedBox(height: 28),

              // ── 최근 접속 이력 ──────────────────────────────────
              Row(
                children: [
                  const Text('최근 접속',
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700,
                      color: AppTheme.textPrimary)),
                  const Spacer(),
                  TextButton(
                    onPressed: () => context.push('/mypage'),
                    child: const Text('전체 보기',
                      style: TextStyle(color: AppTheme.primary, fontSize: 13)),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              _RecentCard(
                name: '스타벅스 강남점',
                ssid: 'Starbucks_WiFi_5G',
                time: '오늘 10:30',
                icon: Icons.coffee_rounded,
              ),
              const SizedBox(height: 10),
              _RecentCard(
                name: '투썸플레이스 역삼점',
                ssid: 'A_Twosome_Place',
                time: '어제 14:20',
                icon: Icons.local_cafe_rounded,
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showWifiAlert(BuildContext context, BleService ble) {
    final facility = ble.pendingWifi!['facility'];
    final wifi     = ble.pendingWifi!['wifi'];
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (_) => Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
        ),
        padding: const EdgeInsets.all(28),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Container(width: 40, height: 4,
            decoration: BoxDecoration(color: AppTheme.border,
              borderRadius: BorderRadius.circular(2))),
          const SizedBox(height: 24),
          Container(
            width: 64, height: 64,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [AppTheme.primary, Color(0xFF059669)],
              ),
              borderRadius: BorderRadius.circular(18),
            ),
            child: const Icon(Icons.wifi_rounded, color: Colors.white, size: 32),
          ),
          const SizedBox(height: 16),
          Text('${facility['name']}', style: const TextStyle(
            fontSize: 20, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
          const SizedBox(height: 6),
          Text('${wifi['ssid']} WiFi에 연결할까요?',
            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 14)),
          const SizedBox(height: 28),
          SizedBox(
            width: double.infinity,
            height: 52,
            child: ElevatedButton(
              onPressed: () {
                Navigator.pop(context);
                ble.clearPendingWifi();
                context.push('/wifi-connect?name=${facility['name']}&ssid=${wifi['ssid']}');
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primary,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              ),
              child: const Text('연결하기',
                style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
            ),
          ),
          const SizedBox(height: 10),
          TextButton(
            onPressed: () { Navigator.pop(context); ble.clearPendingWifi(); },
            child: const Text('나중에',
              style: TextStyle(color: AppTheme.textHint, fontSize: 14)),
          ),
        ]),
      ),
    );
  }
}

// ── 서비스 카드 ──────────────────────────────────────────────────────────
class _ServiceCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final List<Color> gradient;
  final VoidCallback onTap;

  const _ServiceCard({
    required this.icon, required this.label, required this.subtitle,
    required this.gradient, required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AppTheme.border.withOpacity(0.5)),
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 40, height: 40,
              decoration: BoxDecoration(
                gradient: LinearGradient(colors: gradient),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: Colors.white, size: 20),
            ),
            const SizedBox(height: 12),
            Text(label, style: const TextStyle(
              color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w600)),
            const SizedBox(height: 2),
            Text(subtitle, style: const TextStyle(
              color: AppTheme.textHint, fontSize: 11)),
          ],
        ),
      ),
    );
  }
}

// ── 최근 접속 카드 ──────────────────────────────────────────────────────
class _RecentCard extends StatelessWidget {
  final String name;
  final String ssid;
  final String time;
  final IconData icon;

  const _RecentCard({
    required this.name, required this.ssid,
    required this.time, required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.border.withOpacity(0.5)),
      ),
      child: Row(
        children: [
          Container(
            width: 44, height: 44,
            decoration: BoxDecoration(
              color: AppTheme.primary.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: AppTheme.primary, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, style: const TextStyle(
                  fontSize: 15, fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
                const SizedBox(height: 3),
                Text(ssid, style: const TextStyle(
                  fontSize: 12, color: AppTheme.textHint)),
              ],
            ),
          ),
          Text(time, style: const TextStyle(
            fontSize: 11, color: AppTheme.textHint)),
        ],
      ),
    );
  }
}
