import 'package:flutter/material.dart';

import '../../services/coupon_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/empty_state.dart';

const _statusTabs = ['active', 'used', 'expired'];
const _statusLabel = {
  'active': '사용 가능', 'used': '사용 완료', 'expired': '만료',
};

class CouponsScreen extends StatefulWidget {
  const CouponsScreen({super.key});
  @override
  State<CouponsScreen> createState() => _CouponsScreenState();
}

class _CouponsScreenState extends State<CouponsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabCtrl;
  final Map<String, Future<List<Map<String, dynamic>>>> _futures = {};

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: _statusTabs.length, vsync: this);
    for (final s in _statusTabs) {
      _futures[s] = CouponService().myCoupons(status: s);
    }
  }

  @override
  void dispose() { _tabCtrl.dispose(); super.dispose(); }

  Future<void> _reload(String status) async {
    setState(() { _futures[status] = CouponService().myCoupons(status: status); });
    await _futures[status];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('내 쿠폰'),
        bottom: TabBar(
          controller: _tabCtrl,
          tabs: _statusTabs.map((s) => Tab(text: _statusLabel[s])).toList(),
          labelColor: AppTheme.primary,
          unselectedLabelColor: AppTheme.textSecondary,
          indicatorColor: AppTheme.primary,
        ),
      ),
      body: TabBarView(
        controller: _tabCtrl,
        children: _statusTabs.map((s) => _CouponList(
          status: s,
          future: _futures[s]!,
          onRetry: () => _reload(s),
        )).toList(),
      ),
    );
  }
}


class _CouponList extends StatelessWidget {
  final String status;
  final Future<List<Map<String, dynamic>>> future;
  final Future<void> Function() onRetry;
  const _CouponList({required this.status, required this.future, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: onRetry,
      child: FutureBuilder<List<Map<String, dynamic>>>(
        future: future,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return ErrorState(message: snap.error.toString(), onRetry: onRetry);
          }
          final list = snap.data ?? [];
          if (list.isEmpty) {
            return ListView(
              children: [
                const SizedBox(height: 100),
                EmptyState(
                  icon: Icons.confirmation_number_outlined,
                  title: '${_statusLabel[status]} 쿠폰이 없습니다',
                ),
              ],
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: list.length,
            separatorBuilder: (_, _) => const SizedBox(height: 12),
            itemBuilder: (context, i) => _CouponCard(data: list[i], status: status),
          );
        },
      ),
    );
  }
}


class _CouponCard extends StatelessWidget {
  final Map<String, dynamic> data;
  final String status;
  const _CouponCard({required this.data, required this.status});

  @override
  Widget build(BuildContext context) {
    final title = data['title']?.toString() ?? '쿠폰';
    final facilityName = data['facility_name']?.toString() ?? '매장';
    final discount = data['discount_amount'] ?? data['discount_pct'];
    final discountSuffix = data['discount_amount'] != null ? '원 할인' : '% 할인';
    final expiresAt = data['expires_at']?.toString();

    final isUsable = status == 'active';
    final color = isUsable ? AppTheme.primary : AppTheme.textHint;

    return Container(
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isUsable ? AppTheme.primary.withValues(alpha: 0.5) : AppTheme.border),
      ),
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Container(
            width: 56, height: 56,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.18),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(Icons.confirmation_number, color: color, size: 28),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
                const SizedBox(height: 4),
                Text(facilityName,
                  style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
                const SizedBox(height: 4),
                Row(
                  children: [
                    if (discount != null)
                      Text('$discount$discountSuffix',
                        style: TextStyle(color: color, fontWeight: FontWeight.w600, fontSize: 13)),
                    if (expiresAt != null) ...[
                      if (discount != null) const Text(' · ', style: TextStyle(color: AppTheme.textHint)),
                      Text('~${expiresAt.split('T').first}',
                        style: const TextStyle(color: AppTheme.textHint, fontSize: 12)),
                    ],
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
