import 'package:flutter/material.dart';
import '../../utils/app_theme.dart';

/// 스탬프 현황 화면
class StampsScreen extends StatelessWidget {
  const StampsScreen({super.key});

  // Mock 데이터
  static final _stamps = [
    {'facility': '스타벅스 강남점', 'count': 7, 'max': 10, 'lastDate': '2025.04.28',
     'icon': Icons.coffee_rounded, 'reward': '아메리카노 1잔 무료'},
    {'facility': '투썸플레이스 역삼점', 'count': 3, 'max': 10, 'lastDate': '2025.04.25',
     'icon': Icons.local_cafe_rounded, 'reward': '케이크 50% 할인'},
    {'facility': '메가커피 선릉점', 'count': 10, 'max': 10, 'lastDate': '2025.04.20',
     'icon': Icons.coffee_maker_rounded, 'reward': '음료 1잔 무료'},
    {'facility': '공차 강남역점', 'count': 4, 'max': 8, 'lastDate': '2025.04.15',
     'icon': Icons.emoji_food_beverage_rounded, 'reward': '사이즈업 무료'},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('스탬프'),
        centerTitle: true,
      ),
      body: _stamps.isEmpty
        ? _buildEmptyState()
        : ListView.builder(
            padding: const EdgeInsets.all(20),
            itemCount: _stamps.length,
            itemBuilder: (context, index) {
              final stamp = _stamps[index];
              return _StampCard(
                facility: stamp['facility'] as String,
                count: stamp['count'] as int,
                max: stamp['max'] as int,
                lastDate: stamp['lastDate'] as String,
                icon: stamp['icon'] as IconData,
                reward: stamp['reward'] as String,
              );
            },
          ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 80, height: 80,
            decoration: BoxDecoration(
              color: AppTheme.warning.withOpacity(0.1),
              borderRadius: BorderRadius.circular(24),
            ),
            child: const Icon(Icons.star_outline_rounded,
              color: AppTheme.warning, size: 40),
          ),
          const SizedBox(height: 20),
          const Text('아직 적립한 스탬프가 없어요',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600,
              color: AppTheme.textPrimary)),
          const SizedBox(height: 8),
          const Text('WiFi에 접속하면 자동으로 스탬프가 적립돼요',
            style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
        ],
      ),
    );
  }
}

class _StampCard extends StatelessWidget {
  final String facility;
  final int count;
  final int max;
  final String lastDate;
  final IconData icon;
  final String reward;

  const _StampCard({
    required this.facility, required this.count, required this.max,
    required this.lastDate, required this.icon, required this.reward,
  });

  bool get isComplete => count >= max;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: isComplete ? AppTheme.primary.withOpacity(0.3) : AppTheme.border.withOpacity(0.5)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.03),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 시설 정보
                Row(
                  children: [
                    Container(
                      width: 44, height: 44,
                      decoration: BoxDecoration(
                        color: isComplete
                          ? AppTheme.primary.withOpacity(0.1)
                          : AppTheme.warning.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(13),
                      ),
                      child: Icon(icon,
                        color: isComplete ? AppTheme.primary : AppTheme.warning,
                        size: 22),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(facility, style: const TextStyle(
                            fontSize: 15, fontWeight: FontWeight.w600,
                            color: AppTheme.textPrimary)),
                          const SizedBox(height: 3),
                          Text('최근 적립: $lastDate', style: const TextStyle(
                            fontSize: 12, color: AppTheme.textHint)),
                        ],
                      ),
                    ),
                    if (isComplete)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                        decoration: BoxDecoration(
                          color: AppTheme.primary,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Text('완성!',
                          style: TextStyle(color: Colors.white,
                            fontSize: 12, fontWeight: FontWeight.w600)),
                      )
                    else
                      Text('$count/$max',
                        style: const TextStyle(fontSize: 15,
                          fontWeight: FontWeight.w700, color: AppTheme.textPrimary)),
                  ],
                ),
                const SizedBox(height: 16),

                // 프로그레스 바
                ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: LinearProgressIndicator(
                    value: count / max,
                    minHeight: 8,
                    backgroundColor: AppTheme.surface,
                    valueColor: AlwaysStoppedAnimation(
                      isComplete ? AppTheme.primary : AppTheme.warning),
                  ),
                ),
                const SizedBox(height: 14),

                // 스탬프 도트
                Row(
                  children: List.generate(max, (i) {
                    final isFilled = i < count;
                    return Expanded(
                      child: Container(
                        height: 28,
                        margin: EdgeInsets.only(right: i < max - 1 ? 4 : 0),
                        decoration: BoxDecoration(
                          color: isFilled
                            ? (isComplete ? AppTheme.primary : AppTheme.warning).withOpacity(0.15)
                            : AppTheme.surface,
                          borderRadius: BorderRadius.circular(7),
                          border: Border.all(
                            color: isFilled
                              ? (isComplete ? AppTheme.primary : AppTheme.warning).withOpacity(0.3)
                              : AppTheme.border.withOpacity(0.5),
                          ),
                        ),
                        child: isFilled
                          ? Icon(Icons.star_rounded,
                              size: 14,
                              color: isComplete ? AppTheme.primary : AppTheme.warning)
                          : null,
                      ),
                    );
                  }),
                ),
              ],
            ),
          ),

          // 보상 정보
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
            decoration: BoxDecoration(
              color: isComplete
                ? AppTheme.primary.withOpacity(0.05)
                : AppTheme.surface,
              borderRadius: const BorderRadius.vertical(bottom: Radius.circular(18)),
            ),
            child: Row(
              children: [
                Icon(
                  isComplete ? Icons.card_giftcard_rounded : Icons.emoji_events_outlined,
                  size: 16,
                  color: isComplete ? AppTheme.primary : AppTheme.textHint,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    isComplete ? '🎉 $reward' : '보상: $reward',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: isComplete ? FontWeight.w600 : FontWeight.w400,
                      color: isComplete ? AppTheme.primary : AppTheme.textHint,
                    ),
                  ),
                ),
                if (isComplete)
                  const Text('사용하기 →',
                    style: TextStyle(fontSize: 13, color: AppTheme.primary,
                      fontWeight: FontWeight.w600)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
