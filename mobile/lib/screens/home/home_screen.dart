import 'dart:ui' show ImageFilter;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../services/ble_service.dart';
import '../../services/i18n_service.dart';
import '../../services/feature_service.dart';
import '../../services/notification_service.dart';
import '../notifications/notifications_screen.dart';
import '../../services/permission_service.dart';
import '../../services/theme_service.dart';
import '../../utils/app_theme.dart';
import '../../utils/i18n_context.dart';
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
  int _unreadNotifCount = 0;   // 알림 탭 뱃지 카운트 (2026-06-08)

  @override
  void initState() {
    super.initState();
    // 앱 진입 시 BLE 자동 스캔 시작 (백그라운드에서 비콘 감지)
    // PR #58 — 권한 사전 안내 다이얼로그를 먼저 표시
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted) return;
      final auth = context.read<AuthService>();
      final ble = context.read<BleService>();
      if (auth.user == null || ble.isScanning) return;

      final granted = await PermissionService.instance.ensureBluetoothScan(
        context,
      );
      if (!granted || !mounted) return;
      await ble.startScan(userId: auth.user?['id']?.toString());

      // 정보통신망법 §50 — 푸시 알림 수신 동의 (마케팅 분리). BLE 흐름 완료 후 1회.
      if (!mounted) return;
      await NotificationPermissionDialog.showIfNeeded(context);
    });
    _refreshUnreadCount();
  }

  /// 미읽음 알림 개수 갱신 — 진입 시 + 탭 전환 시.
  /// preview 모드도 dev 토큰으로 정상 인증되므로 별도 가드 불필요 (2026-06-09).
  Future<void> _refreshUnreadCount() async {
    if (!mounted) return;
    final auth = context.read<AuthService>();
    if (auth.user == null) return;
    final n = await NotificationService.instance.unreadCount();
    if (!mounted) return;
    setState(() => _unreadNotifCount = n);
  }

  @override
  Widget build(BuildContext context) {
    final tabs = [
      const _HomeTab(),
      const SearchScreen(),
      const _MyPageTab(),
      const NotificationsScreen(),
    ];

    return Scaffold(
      // 시즌 배경은 MaterialApp.builder 에서 글로벌로 깔리므로 Scaffold 자체는 투명.
      // extendBody=false — 콘텐츠가 하단 네비를 침범하지 않게(버튼 잘림 방지).
      // 네비는 블러라 뒤의 시즌 배경은 그대로 비친다.
      extendBody: false,
      body: SafeArea(child: tabs[_tab]),
      // 하단 풀폭 글래스 바 — 화면 하단에 고정(타원형/floating 아님). 시즌 배경을 흐리게 비춤.
      // 색/아이콘크기/라벨(흰 라인↔채움·선택만 라벨)은 NeuTheme.navigationBarTheme 글로벌.
      bottomNavigationBar: ClipRect(
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 24, sigmaY: 24),
          child: DecoratedBox(
            decoration: BoxDecoration(
              // 블러 위주 — 배경 이미지가 그대로 비치게. 아주 옅은 틴트로 흰 아이콘 가독성만 확보.
              // 구분선 없음(네비 바 자체가 콘텐츠와의 구분 역할).
              color: Colors.black.withValues(alpha: 0.18),
            ),
            child: SafeArea(
              top: false,
              child: NavigationBar(
                selectedIndex: _tab,
                onDestinationSelected: (i) {
                  setState(() => _tab = i);
                  // 알림 탭(index 3) 진입 시 미읽음 카운트 갱신.
                  if (i == 3) _refreshUnreadCount();
                },
                // 선택된 탭만 라벨 표시 (미선택은 아이콘만).
                labelBehavior:
                    NavigationDestinationLabelBehavior.onlyShowSelected,
                backgroundColor: Colors.transparent,
                destinations: [
                  NavigationDestination(
                    icon: const Icon(Icons.home_outlined),
                    selectedIcon: const Icon(Icons.home),
                    label: I18nService.instance.t(
                      'nav.home',
                      defaultValue: '홈',
                    ),
                  ),
                  NavigationDestination(
                    icon: const Icon(Icons.search),
                    selectedIcon: const Icon(Icons.search),
                    label: I18nService.instance.t(
                      'nav.search',
                      defaultValue: '검색',
                    ),
                  ),
                  NavigationDestination(
                    icon: const Icon(Icons.person_outline),
                    selectedIcon: const Icon(Icons.person),
                    label: I18nService.instance.t('nav.my', defaultValue: '마이'),
                  ),
                  NavigationDestination(
                    // 미읽음 알림 수 뱃지 (2026-06-08). 0 또는 로드 실패 시 미노출.
                    icon: _NotifBadge(
                      count: _unreadNotifCount,
                      child: const Icon(Icons.notifications_outlined),
                    ),
                    selectedIcon: _NotifBadge(
                      count: _unreadNotifCount,
                      child: const Icon(Icons.notifications),
                    ),
                    label: I18nService.instance.t(
                      'nav.notifications',
                      defaultValue: '알림',
                    ),
                  ),
                ],
              ),
            ),
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
        return RefreshIndicator(
          // pull-to-refresh — 시즌 배경 즉시 갱신 (캐시 무시).
          onRefresh: () => context.read<ThemeService>().refresh(),
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              // 히어로 타이틀 (작은 PATHWAVE pill 제거 — 사용자 결정)
              Text(
                'PathWave',
                style: Theme.of(context).textTheme.displaySmall?.copyWith(
                  color: Colors.white,
                  shadows: const [
                    Shadow(
                      color: Colors.black54,
                      blurRadius: 8,
                      offset: Offset(0, 2),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 4),
              Text(
                context.t(
                  'mobile.home.beacon_auto_connect',
                  defaultValue: '비콘이 감지되면 자동으로 WiFi에 연결됩니다.',
                ),
                style: const TextStyle(color: Colors.white70),
              ),
              const SizedBox(height: 20),

              // BLE 스캔 상태 — 글래스 카드
              GlassCard(
                child: Row(
                  children: [
                    Icon(
                      ble.isScanning
                          ? Icons.bluetooth_searching
                          : Icons.bluetooth_disabled,
                      color: ble.isScanning
                          ? AppTheme.success
                          : AppTheme.textHint,
                      size: 28,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            ble.isScanning
                                ? context.t('mobile.home.ble_scanning', defaultValue: '비콘 감지 중')
                                : context.t('mobile.home.ble_idle', defaultValue: '비콘 감지 대기'),
                            style: const TextStyle(
                              fontWeight: FontWeight.w600,
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            ble.isScanning
                                ? context.t('mobile.home.ble_scanning_desc', defaultValue: '주변에 비콘이 있는지 확인합니다.')
                                : context.t('mobile.home.ble_idle_desc', defaultValue: '권한을 허용하면 자동으로 시작합니다.'),
                            style: const TextStyle(
                              color: Colors.white70,
                              fontSize: 13,
                            ),
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
                          final uid = context
                              .read<AuthService>()
                              .user?['id']
                              ?.toString();
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
                  wifi: ble.pendingWifi!['wifi'],
                  onTap: () {
                    final f = ble.pendingWifi!['facility'] ?? {};
                    final w = ble.pendingWifi!['wifi'] ?? {};
                    // push 사용 — wifi-connect 에서 시스템 백 제스처로 홈 복귀.
                    context.push(
                      '/wifi-connect?'
                      'name=${Uri.encodeComponent(f['name']?.toString() ?? '')}'
                      '&ssid=${Uri.encodeComponent(w['ssid']?.toString() ?? '')}',
                    );
                  },
                  onDismiss: ble.clearPendingWifi,
                ),
              ] else
                GlassCard(
                  child: Row(
                    children: [
                      const Icon(Icons.wifi_off, color: Colors.white70),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          context.t(
                            'mobile.home.no_beacon',
                            defaultValue: '아직 감지된 비콘이 없습니다.',
                          ),
                          style: const TextStyle(color: Colors.white70),
                        ),
                      ),
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
    return GlassCard(
      // primary 색을 살짝 강조해서 "WiFi 발견" 임을 시각적으로 명확히
      borderHighlight: AppTheme.primary.withValues(alpha: 0.55),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.wifi, color: Colors.white),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  '${facility?['name'] ?? context.t('mobile.home.default_facility', defaultValue: '매장')} ${context.t('mobile.home.wifi_found', defaultValue: 'WiFi 발견')}',
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 16,
                    color: Colors.white,
                  ),
                ),
              ),
              PwIconButton(
                icon: Icons.close,
                tooltip: I18nService.instance.t('mobile.common.close', defaultValue: '닫기'),
                size: 18,
                color: Colors.white70,
                onPressed: onDismiss,
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'SSID: ${wifi?['ssid'] ?? '—'}',
            style: const TextStyle(color: Colors.white70),
          ),
          const SizedBox(height: 12),
          PwButton(
            onPressed: onTap,
            child: Text(
              context.t('mobile.home.auto_connect', defaultValue: '자동 연결하기'),
            ),
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

    // 자녀 초대 — Feature Flag 'parent_invite' 가 켜져 있을 때만 노출
    // (SOW v1.3: 유흥·숙박 등 2차 서비스 제공 시 활성. 1차 OFF.)
    final showParentInvite = FeatureService.instance.isEnabled('parent_invite');
    final menuItems = <_MenuSpec>[
      _MenuSpec(Icons.qr_code_2, context.t('mobile.mypage.menu.member_qr', defaultValue: '내 회원 QR'), '/mypage/member-qr'),
      _MenuSpec(Icons.local_activity_outlined, context.t('mobile.mypage.menu.stamps', defaultValue: '내 스탬프'), '/mypage/stamps'),
      _MenuSpec(Icons.confirmation_number_outlined, context.t('mobile.mypage.menu.coupons', defaultValue: '내 쿠폰'), '/mypage/coupons'),
      _MenuSpec(Icons.favorite_outline, context.t('mobile.mypage.menu.favorites', defaultValue: '즐겨찾기'), '/mypage/favorites'),
      if (showParentInvite)
        _MenuSpec(Icons.family_restroom, context.t('mobile.mypage.menu.child_invite', defaultValue: '자녀 초대'), '/mypage/parent-invite'),
      _MenuSpec(Icons.person_add_alt, context.t('mobile.mypage.menu.friend_invite', defaultValue: '친구 초대'), '/mypage/friend-invite'),
      _MenuSpec(Icons.chat_bubble_outline, context.t('mobile.mypage.menu.store_chat', defaultValue: '매장 채팅'), '/chat'),
      _MenuSpec(Icons.headset_mic_outlined, context.t('mobile.mypage.menu.support', defaultValue: '고객센터'), '/support'),
      _MenuSpec(Icons.settings_outlined, context.t('mobile.mypage.menu.settings', defaultValue: '설정'), '/settings'),
    ];

    // NavigationBar 와 로그아웃 버튼 사이 안전 마진(40). ConstrainedBox/
    // IntrinsicHeight 제거 — Spacer 가 없으므로 화면 강제 늘릴 필요 없음.
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
                  Text(
                    context.t('mobile.mypage.title', defaultValue: '마이페이지'),
                    style: Theme.of(context).textTheme.displaySmall?.copyWith(
                      color: Colors.white,
                      shadows: const [
                        Shadow(
                          color: Colors.black54,
                          blurRadius: 8,
                          offset: Offset(0, 2),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  // 프로필 헤더 — 글래스 카드
                  GlassCard(
                    child: Row(
                      children: [
                        const CircleAvatar(
                          radius: 20,
                          backgroundColor: AppTheme.primary,
                          child: Icon(Icons.person, color: Colors.white, size: 20),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                email,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                  color: Colors.white,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                context.t(
                                  'mobile.mypage.member',
                                  defaultValue: '일반 회원',
                                ),
                                style: const TextStyle(color: Colors.white70),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  // 메뉴 9개 — 1개의 통합 글래스 카드 + 내부 divider 분리
                  // (iOS 설정앱 / Material 3 grouped list 패턴)
                  GlassCard(
                    padding: EdgeInsets.zero,
                    child: Column(
                      children: [
                        for (int i = 0; i < menuItems.length; i++) ...[
                          _MenuRow(
                            icon: menuItems[i].icon,
                            title: menuItems[i].title,
                            onTap: () => context.push(menuItems[i].route),
                            isFirst: i == 0,
                            isLast: i == menuItems.length - 1,
                          ),
                          if (i != menuItems.length - 1) const _MenuDivider(),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
          // 공통 가이드 — 모든 액션 버튼은 secondary 톤(흰 글래스)으로 통일.
          // 위험 단서는 시각 색이 아닌 [PwDialog confirm] 으로 처리 (PR 가이드).
          PwButton(
            variant: PwButtonVariant.secondary,
            icon: Icons.logout,
            onPressed: () async {
              await context.read<AuthService>().logout();
              if (context.mounted) context.go('/auth/login');
            },
            child: Text(
              context.t('mobile.mypage.logout', defaultValue: '로그아웃'),
            ),
          ),
        ],
      ),
    );
  }
}

class _MenuSpec {
  final IconData icon;
  final String title;
  final String route;
  const _MenuSpec(this.icon, this.title, this.route);
}

class _MenuRow extends StatelessWidget {
  final IconData icon;
  final String title;
  final VoidCallback onTap;
  final bool isFirst;
  final bool isLast;
  const _MenuRow({
    required this.icon,
    required this.title,
    required this.onTap,
    required this.isFirst,
    required this.isLast,
  });

  @override
  Widget build(BuildContext context) {
    // 첫/마지막 행은 GlassCard 의 라운드를 따라가도록 InkWell 의 ripple 도 동일 round 적용.
    final radius = BorderRadius.vertical(
      top: isFirst ? const Radius.circular(AppTheme.rLg) : Radius.zero,
      bottom: isLast ? const Radius.circular(AppTheme.rLg) : Radius.zero,
    );
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: radius,
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: [
              Icon(icon, size: 22, color: Colors.white70),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              const Icon(Icons.chevron_right, size: 20, color: Colors.white54),
            ],
          ),
        ),
      ),
    );
  }
}

class _MenuDivider extends StatelessWidget {
  const _MenuDivider();
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(left: 50), // 아이콘 너비만큼 들여쓰기
    child: Container(height: 1, color: Colors.white.withValues(alpha: 0.10)),
  );
}

/// 알림 탭 미읽음 뱃지 (2026-06-08).
/// count > 0 일 때만 빨간 점/숫자 노출. 99+ 는 ``99+``.
class _NotifBadge extends StatelessWidget {
  final int count;
  final Widget child;
  const _NotifBadge({required this.count, required this.child});

  @override
  Widget build(BuildContext context) {
    if (count <= 0) return child;
    final label = count > 99 ? '99+' : count.toString();
    return Stack(
      clipBehavior: Clip.none,
      children: [
        child,
        Positioned(
          right: -6, top: -4,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
            constraints: const BoxConstraints(minWidth: 18, minHeight: 18),
            decoration: BoxDecoration(
              color: AppTheme.primary,             // 보라 (브랜드 가이드 통일 2026-06-09)
              borderRadius: BorderRadius.circular(9),
              border: Border.all(color: Colors.white.withValues(alpha: 0.25), width: 0.5),
            ),
            alignment: Alignment.center,
            child: Text(label, style: const TextStyle(
              color: Colors.white, fontSize: 10, fontWeight: FontWeight.w700,
            )),
          ),
        ),
      ],
    );
  }
}
