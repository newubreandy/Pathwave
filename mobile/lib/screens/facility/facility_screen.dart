import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../utils/app_theme.dart';

/// 시설 상세 화면
class FacilityScreen extends StatelessWidget {
  final String facilityId;
  const FacilityScreen({super.key, required this.facilityId});

  // Mock 시설 데이터
  Map<String, dynamic> get _facility {
    final facilities = {
      '1': {
        'name': '스타벅스 강남점',
        'address': '서울 강남구 강남대로 390, 1층',
        'phone': '02-1234-5678',
        'hours': '07:00 ~ 22:00',
        'description': '강남역 근처 프리미엄 카페입니다. 넓은 실내와 무료 WiFi를 제공합니다.',
        'wifi': {'ssid': 'Starbucks_WiFi_5G', 'status': '사용 가능'},
        'hasStamp': true,
        'hasCoupon': true,
        'stampCount': '7/10',
        'couponCount': 1,
        'icon': Icons.coffee_rounded,
      },
      '2': {
        'name': '투썸플레이스 역삼점',
        'address': '서울 강남구 역삼로 180, 2층',
        'phone': '02-2345-6789',
        'hours': '08:00 ~ 23:00',
        'description': '역삼역 도보 3분 거리에 위치한 케이크 전문 카페입니다.',
        'wifi': {'ssid': 'A_Twosome_Place', 'status': '사용 가능'},
        'hasStamp': false,
        'hasCoupon': true,
        'stampCount': '0',
        'couponCount': 2,
        'icon': Icons.local_cafe_rounded,
      },
    };
    return facilities[facilityId] ?? {
      'name': '시설',
      'address': '주소 정보 없음',
      'phone': '-',
      'hours': '-',
      'description': '',
      'wifi': {'ssid': '-', 'status': '-'},
      'hasStamp': false,
      'hasCoupon': false,
      'stampCount': '0',
      'couponCount': 0,
      'icon': Icons.store_rounded,
    };
  }

  @override
  Widget build(BuildContext context) {
    final f = _facility;
    final wifi = f['wifi'] as Map<String, String>;

    return Scaffold(
      backgroundColor: AppTheme.background,
      body: CustomScrollView(
        slivers: [
          // ── 이미지 헤더 ────────────────────────────────────
          SliverAppBar(
            expandedHeight: 220,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      AppTheme.primary.withOpacity(0.8),
                      const Color(0xFF065F46),
                    ],
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                  ),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const SizedBox(height: 40),
                    Container(
                      width: 72, height: 72,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Icon(f['icon'] as IconData,
                        color: Colors.white, size: 36),
                    ),
                    const SizedBox(height: 14),
                    Text(f['name'] as String,
                      style: const TextStyle(color: Colors.white,
                        fontSize: 22, fontWeight: FontWeight.w700)),
                    const SizedBox(height: 4),
                    Text(f['address'] as String,
                      style: TextStyle(color: Colors.white.withOpacity(0.8),
                        fontSize: 13)),
                  ],
                ),
              ),
            ),
          ),

          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── WiFi 정보 카드 ─────────────────────────────
                  _InfoCard(
                    icon: Icons.wifi_rounded,
                    title: 'WiFi',
                    color: AppTheme.primary,
                    children: [
                      _InfoRow('네트워크', wifi['ssid']!),
                      _InfoRow('상태', wifi['status']!),
                    ],
                    action: ElevatedButton.icon(
                      onPressed: () => context.push(
                        '/wifi-connect?name=${f['name']}&ssid=${wifi['ssid']}'),
                      icon: const Icon(Icons.wifi_rounded, size: 16),
                      label: const Text('연결하기'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primary,
                        foregroundColor: Colors.white,
                        minimumSize: const Size(0, 40),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12)),
                        textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),

                  // ── 서비스 카드 ────────────────────────────────
                  Row(
                    children: [
                      if (f['hasStamp'] == true)
                        Expanded(
                          child: _ServiceMiniCard(
                            icon: Icons.star_rounded,
                            label: '스탬프',
                            value: f['stampCount'] as String,
                            color: AppTheme.warning,
                            onTap: () => context.push('/mypage/stamps'),
                          ),
                        ),
                      if (f['hasStamp'] == true && f['hasCoupon'] == true)
                        const SizedBox(width: 12),
                      if (f['hasCoupon'] == true)
                        Expanded(
                          child: _ServiceMiniCard(
                            icon: Icons.card_giftcard_rounded,
                            label: '쿠폰',
                            value: '${f['couponCount']}장',
                            color: const Color(0xFFEC4899),
                            onTap: () => context.push('/mypage/coupons'),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 14),

                  // ── 시설 정보 ──────────────────────────────────
                  _InfoCard(
                    icon: Icons.info_outline_rounded,
                    title: '시설 정보',
                    color: AppTheme.textSecondary,
                    children: [
                      _InfoRow('영업시간', f['hours'] as String),
                      _InfoRow('전화', f['phone'] as String),
                      if ((f['description'] as String).isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 10),
                          child: Text(f['description'] as String,
                            style: const TextStyle(fontSize: 13,
                              color: AppTheme.textSecondary, height: 1.5)),
                        ),
                    ],
                  ),
                  const SizedBox(height: 14),

                  // ── 지도 플레이스홀더 ──────────────────────────
                  Container(
                    width: double.infinity,
                    height: 180,
                    decoration: BoxDecoration(
                      color: AppTheme.surface,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.border.withOpacity(0.5)),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.map_rounded,
                          color: AppTheme.textHint.withOpacity(0.5), size: 40),
                        const SizedBox(height: 8),
                        const Text('지도',
                          style: TextStyle(fontSize: 14, color: AppTheme.textHint)),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // ── 문의 버튼 ──────────────────────────────────
                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: OutlinedButton.icon(
                      onPressed: () => context.push('/chat/$facilityId'),
                      icon: const Icon(Icons.chat_bubble_outline_rounded, size: 18),
                      label: const Text('문의하기'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppTheme.primary,
                        side: const BorderSide(color: AppTheme.primary),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14)),
                        textStyle: const TextStyle(
                          fontSize: 15, fontWeight: FontWeight.w600),
                      ),
                    ),
                  ),
                  const SizedBox(height: 32),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── 정보 카드 ────────────────────────────────────────────────────────────
class _InfoCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final Color color;
  final List<Widget> children;
  final Widget? action;

  const _InfoCard({
    required this.icon, required this.title,
    required this.color, required this.children,
    this.action,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.border.withOpacity(0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 18),
              const SizedBox(width: 8),
              Text(title, style: const TextStyle(
                fontSize: 15, fontWeight: FontWeight.w600, color: AppTheme.textPrimary)),
              if (action != null) ...[const Spacer(), action!],
            ],
          ),
          const SizedBox(height: 14),
          ...children,
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;
  const _InfoRow(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(
            width: 80,
            child: Text(label, style: const TextStyle(
              fontSize: 13, color: AppTheme.textHint)),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(
              fontSize: 14, fontWeight: FontWeight.w500, color: AppTheme.textPrimary)),
          ),
        ],
      ),
    );
  }
}

// ── 서비스 미니 카드 ─────────────────────────────────────────────────────
class _ServiceMiniCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;
  final VoidCallback onTap;

  const _ServiceMiniCard({
    required this.icon, required this.label, required this.value,
    required this.color, required this.onTap,
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
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Row(
          children: [
            Container(
              width: 38, height: 38,
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(11),
              ),
              child: Icon(icon, color: color, size: 18),
            ),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(
                  fontSize: 12, color: AppTheme.textHint)),
                Text(value, style: TextStyle(
                  fontSize: 16, fontWeight: FontWeight.w700, color: color)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
