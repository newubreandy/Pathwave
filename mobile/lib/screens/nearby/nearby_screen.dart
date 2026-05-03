import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../utils/app_theme.dart';

/// 주변 시설 탐색 화면
class NearbyScreen extends StatefulWidget {
  const NearbyScreen({super.key});
  @override
  State<NearbyScreen> createState() => _NearbyScreenState();
}

class _NearbyScreenState extends State<NearbyScreen> {
  bool _isMapView = false;

  // Mock 시설 데이터
  final _facilities = [
    {'id': '1', 'name': '스타벅스 강남점', 'address': '서울 강남구 강남대로 390',
     'distance': '120m', 'wifi': true, 'stamp': true, 'coupon': true, 'icon': Icons.coffee_rounded},
    {'id': '2', 'name': '투썸플레이스 역삼점', 'address': '서울 강남구 역삼로 180',
     'distance': '350m', 'wifi': true, 'stamp': false, 'coupon': true, 'icon': Icons.local_cafe_rounded},
    {'id': '3', 'name': '메가커피 선릉점', 'address': '서울 강남구 선릉로 420',
     'distance': '500m', 'wifi': true, 'stamp': true, 'coupon': false, 'icon': Icons.coffee_maker_rounded},
    {'id': '4', 'name': '공차 강남역점', 'address': '서울 강남구 강남대로 456',
     'distance': '680m', 'wifi': true, 'stamp': true, 'coupon': true, 'icon': Icons.emoji_food_beverage_rounded},
    {'id': '5', 'name': '이디야커피 삼성점', 'address': '서울 강남구 삼성로 100',
     'distance': '920m', 'wifi': true, 'stamp': false, 'coupon': false, 'icon': Icons.local_drink_rounded},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      body: SafeArea(
        child: Column(
          children: [
            // ── 헤더 ─────────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              child: Column(
                children: [
                  Row(
                    children: [
                      const Expanded(
                        child: Text('주변 시설',
                          style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700,
                            color: AppTheme.textPrimary)),
                      ),
                      // 뷰 전환 토글
                      Container(
                        decoration: BoxDecoration(
                          color: AppTheme.surface,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppTheme.border),
                        ),
                        child: Row(
                          children: [
                            _ViewToggle(
                              icon: Icons.list_rounded,
                              isActive: !_isMapView,
                              onTap: () => setState(() => _isMapView = false),
                            ),
                            _ViewToggle(
                              icon: Icons.map_rounded,
                              isActive: _isMapView,
                              onTap: () => setState(() => _isMapView = true),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // ── 검색 바 ──────────────────────────────────────
                  Container(
                    height: 48,
                    decoration: BoxDecoration(
                      color: AppTheme.surface,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppTheme.border),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 14),
                    child: const Row(
                      children: [
                        Icon(Icons.search_rounded, color: AppTheme.textHint, size: 20),
                        SizedBox(width: 10),
                        Expanded(
                          child: TextField(
                            decoration: InputDecoration(
                              hintText: '시설명 또는 주소로 검색',
                              hintStyle: TextStyle(color: AppTheme.textHint, fontSize: 14),
                              border: InputBorder.none,
                              enabledBorder: InputBorder.none,
                              focusedBorder: InputBorder.none,
                              isDense: true,
                              contentPadding: EdgeInsets.zero,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 8),

                  // ── 필터 칩 ──────────────────────────────────────
                  SizedBox(
                    height: 38,
                    child: ListView(
                      scrollDirection: Axis.horizontal,
                      children: [
                        _FilterChip(label: '전체', isSelected: true),
                        const SizedBox(width: 8),
                        _FilterChip(label: 'WiFi', isSelected: false),
                        const SizedBox(width: 8),
                        _FilterChip(label: '스탬프', isSelected: false),
                        const SizedBox(width: 8),
                        _FilterChip(label: '쿠폰', isSelected: false),
                        const SizedBox(width: 8),
                        _FilterChip(label: '카페', isSelected: false),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),

            // ── 콘텐츠 ──────────────────────────────────────────
            Expanded(
              child: _isMapView ? _buildMapView() : _buildListView(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildListView() {
    return ListView.separated(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      itemCount: _facilities.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final f = _facilities[index];
        return _FacilityCard(
          name: f['name'] as String,
          address: f['address'] as String,
          distance: f['distance'] as String,
          hasWifi: f['wifi'] as bool,
          hasStamp: f['stamp'] as bool,
          hasCoupon: f['coupon'] as bool,
          icon: f['icon'] as IconData,
          onTap: () => context.push('/facility/${f['id']}'),
        );
      },
    );
  }

  Widget _buildMapView() {
    // Google Maps placeholder (API 키 설정 전)
    return Container(
      margin: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.border),
      ),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 72, height: 72,
              decoration: BoxDecoration(
                color: AppTheme.primary.withOpacity(0.1),
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Icon(Icons.map_rounded, color: AppTheme.primary, size: 36),
            ),
            const SizedBox(height: 16),
            const Text('지도 보기',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary)),
            const SizedBox(height: 6),
            const Text('Google Maps API 키 설정 후\n이용 가능합니다',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: AppTheme.textSecondary,
                height: 1.5)),
          ],
        ),
      ),
    );
  }
}

// ── 뷰 전환 토글 ─────────────────────────────────────────────────────────
class _ViewToggle extends StatelessWidget {
  final IconData icon;
  final bool isActive;
  final VoidCallback onTap;
  const _ViewToggle({required this.icon, required this.isActive, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 40, height: 36,
        decoration: BoxDecoration(
          color: isActive ? AppTheme.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(icon, size: 18,
          color: isActive ? Colors.white : AppTheme.textHint),
      ),
    );
  }
}

// ── 필터 칩 ──────────────────────────────────────────────────────────────
class _FilterChip extends StatelessWidget {
  final String label;
  final bool isSelected;
  const _FilterChip({required this.label, required this.isSelected});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: isSelected ? AppTheme.primary : Colors.transparent,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isSelected ? AppTheme.primary : AppTheme.border,
        ),
      ),
      child: Text(label,
        style: TextStyle(
          fontSize: 13,
          fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
          color: isSelected ? Colors.white : AppTheme.textSecondary,
        ),
      ),
    );
  }
}

// ── 시설 카드 ────────────────────────────────────────────────────────────
class _FacilityCard extends StatelessWidget {
  final String name;
  final String address;
  final String distance;
  final bool hasWifi;
  final bool hasStamp;
  final bool hasCoupon;
  final IconData icon;
  final VoidCallback onTap;

  const _FacilityCard({
    required this.name, required this.address, required this.distance,
    required this.hasWifi, required this.hasStamp, required this.hasCoupon,
    required this.icon, required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppTheme.border.withOpacity(0.5)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.03),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 52, height: 52,
              decoration: BoxDecoration(
                color: AppTheme.primary.withOpacity(0.1),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Icon(icon, color: AppTheme.primary, size: 26),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(name, style: const TextStyle(
                    fontSize: 15, fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
                  const SizedBox(height: 3),
                  Text(address, style: const TextStyle(
                    fontSize: 12, color: AppTheme.textHint)),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      if (hasWifi) _ServiceBadge('WiFi', Icons.wifi_rounded, AppTheme.primary),
                      if (hasStamp) _ServiceBadge('스탬프', Icons.star_rounded, AppTheme.warning),
                      if (hasCoupon) _ServiceBadge('쿠폰', Icons.card_giftcard, const Color(0xFFEC4899)),
                    ],
                  ),
                ],
              ),
            ),
            Column(
              children: [
                Text(distance, style: const TextStyle(
                  fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.primary)),
                const SizedBox(height: 4),
                const Icon(Icons.chevron_right_rounded,
                  color: AppTheme.textHint, size: 20),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _ServiceBadge extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  const _ServiceBadge(this.label, this.icon, this.color);

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(right: 6),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 11, color: color),
          const SizedBox(width: 3),
          Text(label, style: TextStyle(fontSize: 10, color: color, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
