import 'package:flutter/material.dart';

import '../../utils/error_message.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../services/coupon_service.dart';
import '../../services/i18n_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/pw.dart';

const _statusTabs = ['active', 'used', 'expired'];
const _statusLabel = {
  'active': '사용 가능', 'used': '사용 완료', 'expired': '만료',
};

/// 새로 발급된 쿠폰 판별: is_new 플래그 또는 created_at 기준 최근 5분 이내.
bool _isNewlyIssued(Map<String, dynamic> data) {
  if (data['is_new'] == true) return true;
  final createdAt = data['created_at']?.toString();
  if (createdAt == null) return false;
  final ts = DateTime.tryParse(createdAt);
  if (ts == null) return false;
  return DateTime.now().difference(ts) < const Duration(minutes: 5);
}

/// SharedPreferences 키: 쿠폰별 환영 카드 노출 여부.
String _welcomeSeenKey(dynamic couponId) => 'pw.coupon_issue.welcome_seen_$couponId';

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
      appBar: PwAppBar(
        title: Text(_t.t('coupon_issue.title', defaultValue: '내 쿠폰')),
        // 색상/인디케이터는 NeuTheme.tabBarTheme 글로벌 정책 따름 (흰 톤 통일).
        bottom: TabBar(
          controller: _tabCtrl,
          tabs: _statusTabs.map((s) => Tab(text: _statusLabel[s])).toList(),
        ),
      ),
      body: SafeArea(child: TabBarView(
        controller: _tabCtrl,
        children: _statusTabs.map((s) => _CouponList(
          status: s,
          future: _futures[s]!,
          onRetry: () => _reload(s),
        )).toList(),
      )),
    );
  }
}


class _CouponList extends StatefulWidget {
  final String status;
  final Future<List<Map<String, dynamic>>> future;
  final Future<void> Function() onRetry;
  const _CouponList({required this.status, required this.future, required this.onRetry});

  @override
  State<_CouponList> createState() => _CouponListState();
}

class _CouponListState extends State<_CouponList> {
  /// coupon id → 이 세션에서 환영 카드를 숨겼는지 여부.
  final Set<dynamic> _dismissed = {};

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: widget.onRetry,
      child: FutureBuilder<List<Map<String, dynamic>>>(
        future: widget.future,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return PwErrorState(message: friendlyError(snap.error), onRetry: widget.onRetry);
          }
          final list = snap.data ?? [];
          if (list.isEmpty) {
            return ListView(
              children: [
                const SizedBox(height: 100),
                PwEmptyState(
                  icon: Icons.confirmation_number_outlined,
                  title: '${_statusLabel[widget.status]} 쿠폰이 없습니다',
                ),
              ],
            );
          }
          return _CouponListBody(
            list: list,
            status: widget.status,
            dismissed: _dismissed,
            onDismiss: (id) => setState(() => _dismissed.add(id)),
          );
        },
      ),
    );
  }
}


class _CouponListBody extends StatefulWidget {
  final List<Map<String, dynamic>> list;
  final String status;
  final Set<dynamic> dismissed;
  final void Function(dynamic id) onDismiss;
  const _CouponListBody({
    required this.list,
    required this.status,
    required this.dismissed,
    required this.onDismiss,
  });

  @override
  State<_CouponListBody> createState() => _CouponListBodyState();
}

class _CouponListBodyState extends State<_CouponListBody> {
  /// coupon id → SharedPreferences 에서 already-seen 여부 (async 로드).
  final Map<dynamic, bool> _prefsSeen = {};
  bool _prefsLoaded = false;

  @override
  void initState() {
    super.initState();
    _loadPrefs();
  }

  Future<void> _loadPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    final result = <dynamic, bool>{};
    for (final item in widget.list) {
      final id = item['id'];
      if (id != null && _isNewlyIssued(item)) {
        result[id] = prefs.getBool(_welcomeSeenKey(id)) ?? false;
      }
    }
    if (mounted) setState(() { _prefsSeen.addAll(result); _prefsLoaded = true; });
  }

  Future<void> _markSeen(dynamic id) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_welcomeSeenKey(id), true);
    widget.onDismiss(id);
  }

  @override
  Widget build(BuildContext context) {
    // 새로 발급된 쿠폰 중 아직 환영 카드를 본 적 없는 것들
    final newCoupons = widget.list.where((item) {
      final id = item['id'];
      if (id == null) return false;
      if (widget.dismissed.contains(id)) return false;
      if (!_isNewlyIssued(item)) return false;
      // prefs 로드 전: 숨기지 않음(기본 노출)
      if (_prefsLoaded && (_prefsSeen[id] ?? false)) return false;
      return true;
    }).toList();

    return ListView(
      padding: EdgeInsets.fromLTRB(16, 16, 16,
          16 + MediaQuery.of(context).viewPadding.bottom),
      children: [
        // 환영 카드 — 새로 발급된 쿠폰 수만큼 표시
        for (final item in newCoupons)
          _WelcomeCard(
            data: item,
            onDismiss: () => _markSeen(item['id']),
          ),
        if (newCoupons.isNotEmpty) const SizedBox(height: 4),
        // 전체 쿠폰 목록
        ...List.generate(widget.list.length, (i) {
          final item = widget.list[i];
          return Padding(
            padding: EdgeInsets.only(top: i == 0 ? 0 : 12),
            child: _CouponCard(data: item, status: widget.status),
          );
        }),
      ],
    );
  }
}


/// 발급 직후 환영 안내 카드 (1회 자동 노출).
class _WelcomeCard extends StatelessWidget {
  final Map<String, dynamic> data;
  final VoidCallback onDismiss;
  const _WelcomeCard({required this.data, required this.onDismiss});

  @override
  Widget build(BuildContext context) {
    final t = I18nService.instance;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: PwCard(
        color: AppTheme.primary.withValues(alpha: 0.12),
        border: Border.all(color: AppTheme.primary.withValues(alpha: 0.4)),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.card_giftcard, color: AppTheme.primary, size: 18),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    t.t('coupon_issue.received', defaultValue: '발급된 쿠폰이 도착했습니다'),
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 14,
                      color: AppTheme.primary,
                    ),
                  ),
                ),
                // info 아이콘: 이미 닫은 경우에도 다시 안내 볼 수 있도록 (dismiss 처리는 X 버튼)
                GestureDetector(
                  onTap: onDismiss,
                  child: const Icon(Icons.close, size: 18, color: AppTheme.textHint),
                ),
              ],
            ),
            const SizedBox(height: 10),
            _TermsBullet(t.t(
              'coupon_issue.terms_source',
              defaultValue: '본 쿠폰은 스탬프 적립 보상으로 발급되었습니다.',
            )),
            _TermsBullet(t.t(
              'coupon_issue.terms_facility_only',
              defaultValue: '발급 매장에서만 사용 가능합니다.',
            )),
            _TermsBullet(t.t(
              'coupon_issue.terms_expiry',
              defaultValue: '유효기간 내에만 사용 가능하며, 만료 후 소멸됩니다.',
            )),
            _TermsBullet(t.t(
              'coupon_issue.terms_exclusion',
              defaultValue: '일부 상품·서비스는 쿠폰 적용에서 제외될 수 있습니다.',
            )),
          ],
        ),
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
    // 2026-06-09 — 글래스 모피즘 아이콘 박스 (그라디언트 + 흰 보더 + glow).
    final Color iconColor;
    final List<Color> iconGradient;
    final Color glowColor;
    final double borderAlpha;
    if (status == 'active') {
      iconColor    = Colors.white;
      iconGradient = [
        AppTheme.primary.withValues(alpha: 0.85),
        AppTheme.primary.withValues(alpha: 0.45),
      ];
      glowColor    = AppTheme.primary.withValues(alpha: 0.45);
      borderAlpha  = 0.28;
    } else if (status == 'used') {
      iconColor    = AppTheme.textHint;
      iconGradient = [
        Colors.white.withValues(alpha: 0.18),
        Colors.white.withValues(alpha: 0.08),
      ];
      glowColor    = Colors.transparent;
      borderAlpha  = 0.18;
    } else { // expired
      iconColor    = Colors.black87;
      iconGradient = [
        Colors.black.withValues(alpha: 0.42),
        Colors.black.withValues(alpha: 0.18),
      ];
      glowColor    = Colors.transparent;
      borderAlpha  = 0.18;
    }
    // 본문 텍스트 강조 색은 active 만 보라, 나머지는 회색.
    final color = isUsable ? AppTheme.primary : AppTheme.textHint;

    return PwCard(
      onTap: () => _showDetailDialog(context, data, isUsable),
      child: Row(
        children: [
          Container(
            width: 44, height: 44,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: iconGradient,
              ),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: Colors.white.withValues(alpha: borderAlpha),
                width: 1,
              ),
              boxShadow: glowColor == Colors.transparent
                  ? null
                  : [
                      BoxShadow(
                        color: glowColor,
                        blurRadius: 14,
                        offset: const Offset(0, 4),
                      ),
                    ],
            ),
            child: Icon(Icons.confirmation_number, color: iconColor, size: 22),
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
      barrierColor: const Color(0x99000000),
      barrierDismissible: true,
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
      barrierColor: const Color(0x99000000),
      barrierDismissible: true,
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
              if (id == null) return;
              // P9 (2026-05-26): silent error 수정 — 사용 후 피드백.
              // _CouponCard 는 StatelessWidget — 부모 새로고침 콜백 도입은 후속 PR.
              // 사용자는 SnackBar 후 화면 재진입 시 최신 상태 확인.
              final messenger = ScaffoldMessenger.of(context);
              try {
                await CouponService().useCoupon(id);
                if (!context.mounted) return;
                messenger.showSnackBar(SnackBar(
                  content: Text(t.t('coupon.use_success',
                      defaultValue: '쿠폰을 사용했습니다.')),
                ));
              } catch (e) {
                if (!context.mounted) return;
                messenger.showSnackBar(SnackBar(
                  content: Text('${t.t('coupon.use_failed',
                      defaultValue: '쿠폰 사용 실패')}: $e'),
                ));
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
