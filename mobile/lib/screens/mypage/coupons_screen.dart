import 'package:flutter/material.dart';
import '../../utils/app_theme.dart';

/// 쿠폰 화면 (탭 필터: 사용 가능 / 사용 완료 / 만료)
class CouponsScreen extends StatefulWidget {
  const CouponsScreen({super.key});
  @override
  State<CouponsScreen> createState() => _CouponsScreenState();
}

class _CouponsScreenState extends State<CouponsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  // Mock 데이터
  final _available = [
    {'title': '아메리카노 1잔 무료', 'facility': '스타벅스 강남점',
     'expires': '2025.05.15', 'icon': Icons.coffee_rounded},
    {'title': '케이크 50% 할인', 'facility': '투썸플레이스 역삼점',
     'expires': '2025.06.01', 'icon': Icons.cake_rounded},
    {'title': '사이즈업 무료', 'facility': '공차 강남역점',
     'expires': '2025.05.30', 'icon': Icons.emoji_food_beverage_rounded},
  ];
  final _used = [
    {'title': '음료 1잔 무료', 'facility': '메가커피 선릉점',
     'usedDate': '2025.04.20', 'icon': Icons.coffee_maker_rounded},
  ];
  final _expired = [
    {'title': '10% 할인', 'facility': '이디야커피 삼성점',
     'expires': '2025.03.15', 'icon': Icons.local_drink_rounded},
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('쿠폰'),
        centerTitle: true,
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(48),
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 20),
            decoration: BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.circular(12),
            ),
            child: TabBar(
              controller: _tabController,
              indicator: BoxDecoration(
                color: AppTheme.primary,
                borderRadius: BorderRadius.circular(10),
              ),
              indicatorSize: TabBarIndicatorSize.tab,
              dividerHeight: 0,
              labelColor: Colors.white,
              unselectedLabelColor: AppTheme.textHint,
              labelStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
              unselectedLabelStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w400),
              tabs: [
                Tab(text: '사용 가능 (${_available.length})'),
                Tab(text: '사용 완료 (${_used.length})'),
                Tab(text: '만료 (${_expired.length})'),
              ],
            ),
          ),
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildList(_available, _CouponStatus.available),
          _buildList(_used, _CouponStatus.used),
          _buildList(_expired, _CouponStatus.expired),
        ],
      ),
    );
  }

  Widget _buildList(List<Map<String, dynamic>> coupons, _CouponStatus status) {
    if (coupons.isEmpty) return _buildEmpty(status);

    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: coupons.length,
      itemBuilder: (context, index) {
        final c = coupons[index];
        return _CouponCard(
          title: c['title'] as String,
          facility: c['facility'] as String,
          date: (c['expires'] ?? c['usedDate']) as String,
          icon: c['icon'] as IconData,
          status: status,
        );
      },
    );
  }

  Widget _buildEmpty(_CouponStatus status) {
    final messages = {
      _CouponStatus.available: ['사용 가능한 쿠폰이 없어요', '스탬프를 모아 쿠폰을 받아보세요'],
      _CouponStatus.used: ['사용한 쿠폰이 없어요', '쿠폰을 사용하면 여기에 표시돼요'],
      _CouponStatus.expired: ['만료된 쿠폰이 없어요', '기간이 지난 쿠폰이 여기에 표시돼요'],
    };

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 80, height: 80,
            decoration: BoxDecoration(
              color: const Color(0xFFEC4899).withOpacity(0.1),
              borderRadius: BorderRadius.circular(24),
            ),
            child: const Icon(Icons.card_giftcard_outlined,
              color: Color(0xFFEC4899), size: 40),
          ),
          const SizedBox(height: 20),
          Text(messages[status]![0],
            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600,
              color: AppTheme.textPrimary)),
          const SizedBox(height: 8),
          Text(messages[status]![1],
            style: const TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
        ],
      ),
    );
  }
}

enum _CouponStatus { available, used, expired }

class _CouponCard extends StatelessWidget {
  final String title;
  final String facility;
  final String date;
  final IconData icon;
  final _CouponStatus status;

  const _CouponCard({
    required this.title, required this.facility,
    required this.date, required this.icon, required this.status,
  });

  @override
  Widget build(BuildContext context) {
    final isInactive = status != _CouponStatus.available;

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      child: Stack(
        children: [
          // 쿠폰 본체
          Container(
            decoration: BoxDecoration(
              color: isInactive ? AppTheme.surface : Colors.white,
              borderRadius: BorderRadius.circular(18),
              border: Border.all(
                color: isInactive
                  ? AppTheme.border.withOpacity(0.5)
                  : const Color(0xFFEC4899).withOpacity(0.2)),
              boxShadow: isInactive ? [] : [
                BoxShadow(
                  color: Colors.black.withOpacity(0.04),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: IntrinsicHeight(
              child: Row(
                children: [
                  // 좌측 컬러 바
                  Container(
                    width: 6,
                    decoration: BoxDecoration(
                      color: isInactive
                        ? AppTheme.textHint.withOpacity(0.3)
                        : const Color(0xFFEC4899),
                      borderRadius: const BorderRadius.horizontal(
                        left: Radius.circular(18)),
                    ),
                  ),
                  // 본문
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.all(18),
                      child: Row(
                        children: [
                          Container(
                            width: 48, height: 48,
                            decoration: BoxDecoration(
                              color: isInactive
                                ? AppTheme.textHint.withOpacity(0.08)
                                : const Color(0xFFEC4899).withOpacity(0.1),
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: Icon(icon, size: 24,
                              color: isInactive
                                ? AppTheme.textHint
                                : const Color(0xFFEC4899)),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(title, style: TextStyle(
                                  fontSize: 15, fontWeight: FontWeight.w600,
                                  color: isInactive
                                    ? AppTheme.textHint
                                    : AppTheme.textPrimary,
                                  decoration: isInactive
                                    ? TextDecoration.lineThrough : null,
                                )),
                                const SizedBox(height: 4),
                                Text(facility, style: TextStyle(
                                  fontSize: 13, color: isInactive
                                    ? AppTheme.textHint.withOpacity(0.7)
                                    : AppTheme.textSecondary)),
                                const SizedBox(height: 6),
                                Row(
                                  children: [
                                    Icon(
                                      status == _CouponStatus.used
                                        ? Icons.check_circle_rounded
                                        : Icons.schedule_rounded,
                                      size: 13,
                                      color: isInactive
                                        ? AppTheme.textHint.withOpacity(0.5)
                                        : AppTheme.textHint,
                                    ),
                                    const SizedBox(width: 4),
                                    Text(
                                      status == _CouponStatus.used
                                        ? '사용일: $date'
                                        : '~$date',
                                      style: TextStyle(fontSize: 12,
                                        color: isInactive
                                          ? AppTheme.textHint.withOpacity(0.5)
                                          : AppTheme.textHint),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                          if (status == _CouponStatus.available)
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12, vertical: 8),
                              decoration: BoxDecoration(
                                color: const Color(0xFFEC4899),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: const Text('사용',
                                style: TextStyle(color: Colors.white,
                                  fontSize: 13, fontWeight: FontWeight.w600)),
                            ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // 티켓 찢어진 효과 (좌측 반원 노치)
          Positioned(
            left: -6,
            top: 0, bottom: 0,
            child: Center(
              child: Container(
                width: 12, height: 12,
                decoration: BoxDecoration(
                  color: AppTheme.background,
                  shape: BoxShape.circle,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
