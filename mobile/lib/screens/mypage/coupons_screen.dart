import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../services/coupon_service.dart';
import '../../services/i18n_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/pw.dart';

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

  final _t = I18nService.instance;

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
        title: Text(_t.t('coupon.screen_title', defaultValue: '내 쿠폰')),
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

    return PwCard(
      onTap: () => _showDetailDialog(context, data, isUsable),
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
                Text(
                  '${I18nService.instance.t('coupon.facility_label', defaultValue: '사용 가능 매장')}: $facilityName',
                  style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    if (discount != null)
                      Text('$discount$discountSuffix',
                        style: TextStyle(color: color, fontWeight: FontWeight.w600, fontSize: 13)),
                    if (expiresAt != null) ...[
                      if (discount != null) const Text(' · ', style: TextStyle(color: AppTheme.textHint)),
                      Text(
                        '${I18nService.instance.t('coupon.expires_label', defaultValue: '유효기간')}: ~${expiresAt.split('T').first}',
                        style: const TextStyle(color: AppTheme.textHint, fontSize: 12),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
          const Icon(Icons.chevron_right, size: 18, color: AppTheme.textHint),
        ],
      ),
    );
  }

  void _showDetailDialog(BuildContext context, Map<String, dynamic> data, bool isUsable) {
    final t = I18nService.instance;
    final title = data['title']?.toString() ?? '쿠폰';
    final facilityName = data['facility_name']?.toString() ?? '매장';
    final expiresAt = data['expires_at']?.toString();

    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              // 기본 정보
              _DetailRow(
                label: t.t('coupon.facility_label', defaultValue: '사용 가능 매장'),
                value: facilityName,
              ),
              if (expiresAt != null) ...[
                const SizedBox(height: 4),
                _DetailRow(
                  label: t.t('coupon.expires_label', defaultValue: '유효기간'),
                  value: '~${expiresAt.split('T').first}',
                ),
              ],
              const SizedBox(height: 16),

              // 쿠폰 사용 안내 (전자상거래법/소비자보호법 필수 고지)
              PwCard(
                padding: const EdgeInsets.all(14),
                color: AppTheme.background,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      t.t('coupon.terms_title', defaultValue: '쿠폰 사용 안내'),
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 13,
                        color: AppTheme.primary,
                      ),
                    ),
                    const SizedBox(height: 10),
                    _TermsBullet(t.t(
                      'coupon.terms_condition',
                      defaultValue: '본 쿠폰은 발급 매장에서만 사용 가능합니다.',
                    )),
                    _TermsBullet(t.t(
                      'coupon.terms_expiry',
                      defaultValue: '유효기간 내에만 사용 가능하며, 만료 후 소멸됩니다.',
                    )),
                    _TermsBullet(t.t(
                      'coupon.terms_exclusion',
                      defaultValue: '일부 상품·서비스는 쿠폰 적용에서 제외될 수 있습니다.',
                    )),
                    _TermsBullet(t.t(
                      'coupon.terms_transfer',
                      defaultValue: '본 쿠폰은 타인에게 양도하거나 현금으로 교환할 수 없습니다.',
                    )),
                    _TermsBullet(t.t(
                      'coupon.terms_dispute',
                      defaultValue: '쿠폰 관련 분쟁은 발급 매장 사업자가 책임을 부담하며, PathWave 는 중개 플랫폼으로 책임을 지지 않습니다.',
                    )),
                  ],
                ),
              ),
            ],
          ),
        ),
        actions: [
          PwButton(
            variant: PwButtonVariant.text,
            fullWidth: false,
            onPressed: () => ctx.pop(),
            child: const Text('닫기'),
          ),
          if (isUsable)
            PwButton(
              fullWidth: false,
              onPressed: () {
                ctx.pop();
                _showUseConfirm(context, data);
              },
              child: Text(t.t('coupon.use_btn', defaultValue: '쿠폰 사용')),
            ),
        ],
      ),
    );
  }

  void _showUseConfirm(BuildContext context, Map<String, dynamic> data) {
    final t = I18nService.instance;
    final title = data['title']?.toString() ?? '쿠폰';
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Text(t.t('coupon.use_confirm_title', defaultValue: '쿠폰 사용 확인')),
        content: Text(
          t.t(
            'coupon.use_confirm',
            defaultValue: '"$title" 쿠폰을 지금 사용하시겠습니까?\n사용 후에는 취소할 수 없습니다.',
          ).replaceFirst('\$title', title),
          style: const TextStyle(height: 1.5),
        ),
        actions: [
          PwButton(
            variant: PwButtonVariant.text,
            fullWidth: false,
            onPressed: () => ctx.pop(),
            child: const Text('취소'),
          ),
          PwButton(
            fullWidth: false,
            onPressed: () async {
              ctx.pop();
              final id = data['id'] as int?;
              if (id != null) {
                try {
                  await CouponService().useCoupon(id);
                } catch (_) {}
              }
            },
            child: Text(t.t('coupon.use_btn', defaultValue: '사용하기')),
          ),
        ],
      ),
    );
  }
}


class _DetailRow extends StatelessWidget {
  final String label;
  final String value;
  const _DetailRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
        const SizedBox(width: 8),
        Expanded(
          child: Text(value, style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13)),
        ),
      ],
    );
  }
}


class _TermsBullet extends StatelessWidget {
  final String text;
  const _TermsBullet(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('• ', style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 13,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
