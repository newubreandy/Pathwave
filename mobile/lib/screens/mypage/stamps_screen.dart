import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../utils/error_message.dart';

import '../../services/i18n_service.dart';
import '../../services/stamp_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/pw.dart';

/// 내 스탬프 — 시설별 카드 형태.
class StampsScreen extends StatefulWidget {
  const StampsScreen({super.key});
  @override
  State<StampsScreen> createState() => _StampsScreenState();
}

class _StampsScreenState extends State<StampsScreen> {
  late Future<List<Map<String, dynamic>>> _future;
  final _t = I18nService.instance;

  @override
  void initState() {
    super.initState();
    _future = StampService().myStamps();
  }

  Future<void> _reload() async {
    setState(() { _future = StampService().myStamps(); });
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PwAppBar(
        title: Text(_t.t('stamp.title', defaultValue: '내 스탬프')),
      ),
      body: SafeArea(child: RefreshIndicator(
        onRefresh: _reload,
        child: FutureBuilder<List<Map<String, dynamic>>>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snap.hasError) {
              return PwErrorState(message: friendlyError(snap.error), onRetry: _reload);
            }
            final list = snap.data ?? [];
            if (list.isEmpty) {
              return ListView(
                children: [
                  const SizedBox(height: 100),
                  PwEmptyState(
                    icon: Icons.local_activity_outlined,
                    title: _t.t('stamp.empty', defaultValue: '아직 적립된 스탬프가 없습니다'),
                    subtitle: '매장에 방문하면 비콘으로 자동 적립됩니다.',
                  ),
                ],
              );
            }
            return ListView.separated(
              padding: EdgeInsets.fromLTRB(16, 16, 16,
                  16 + MediaQuery.of(context).viewPadding.bottom),
              itemCount: list.length,
              separatorBuilder: (_, _) => const SizedBox(height: 12),
              itemBuilder: (context, i) => _StampCard(data: list[i]),
            );
          },
        ),
      )),
    );
  }
}


class _StampCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const _StampCard({required this.data});

  @override
  Widget build(BuildContext context) {
    // 2026-06-09 — 쿠폰 카드와 동일 디자인 가이드 + 도장 아이콘.
    // 응답 키 정합: facility_name / total_stamps / reward_threshold / reward_description / reward_available
    final facilityName = data['facility_name']?.toString() ?? '매장';
    final count    = (data['total_stamps']    as num?)?.toInt() ?? 0;
    final required = (data['reward_threshold'] as num?)?.toInt() ?? 10;
    final progress = required > 0 ? (count / required).clamp(0.0, 1.0) : 0.0;
    final rewardDesc      = data['reward_description']?.toString();
    final rewardAvailable = data['reward_available'] == true;

    // 카드 터치 → 정책 + 진행도 + 보상 다이얼로그 (스탬프 상세).
    final facilityId = data['facility_id'];
    return PwCard(
      onTap: () => _showStampDetail(context, data, facilityId),
      child: Row(
        children: [
          // 글래스 모피즘 도장 박스 — 보라 그라디언트 + 흰 보더 + glow.
          Container(
            width: 44, height: 44,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  AppTheme.primary.withValues(alpha: 0.85),
                  AppTheme.primary.withValues(alpha: 0.45),
                ],
              ),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: Colors.white.withValues(alpha: 0.28),
                width: 1,
              ),
              boxShadow: [
                BoxShadow(
                  color: AppTheme.primary.withValues(alpha: 0.45),
                  blurRadius: 16,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: const Icon(Icons.approval, color: Colors.white, size: 22),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(facilityName,
                          style: const TextStyle(fontWeight: FontWeight.w600)),
                    ),
                    Text('$count / $required',
                        style: const TextStyle(
                            color: AppTheme.primary,
                            fontWeight: FontWeight.w700,
                            fontSize: 13)),
                  ],
                ),
                const SizedBox(height: 8),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: progress,
                    minHeight: 6,
                    backgroundColor: AppTheme.border,
                    color: AppTheme.primary,
                  ),
                ),
                if (rewardAvailable) ...[
                  const SizedBox(height: 6),
                  const Text('🎉 보상 쿠폰이 발급되었어요',
                      style: TextStyle(color: AppTheme.success, fontSize: 12)),
                ] else if (rewardDesc != null && rewardDesc.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  Text('보상: $rewardDesc',
                      style: const TextStyle(
                          color: AppTheme.textHint, fontSize: 12)),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _showStampDetail(BuildContext context, Map<String, dynamic> data, dynamic facilityId) async {
    final facilityName = data['facility_name']?.toString() ?? '매장';
    final count    = (data['total_stamps']    as num?)?.toInt() ?? 0;
    final required = (data['reward_threshold'] as num?)?.toInt() ?? 10;
    final progress = required > 0 ? (count / required).clamp(0.0, 1.0) : 0.0;
    final rewardDesc      = data['reward_description']?.toString();
    final rewardAvailable = data['reward_available'] == true;
    final remain = (required - count).clamp(0, required);

    await showPwDialog<void>(
      context: context,
      title: Text(facilityName),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('적립 현황', style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
              Text('$count / $required',
                  style: const TextStyle(color: AppTheme.primary, fontWeight: FontWeight.w700)),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 8,
              backgroundColor: AppTheme.border,
              color: AppTheme.primary,
            ),
          ),
          const SizedBox(height: 16),
          if (rewardDesc != null && rewardDesc.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Text('🎁 보상: $rewardDesc',
                  style: const TextStyle(color: Colors.white)),
            ),
          if (rewardAvailable)
            const Text('🎉 보상 쿠폰이 발급되었어요!',
                style: TextStyle(color: AppTheme.success, fontWeight: FontWeight.w600))
          else if (remain > 0)
            Text('$remain개 더 모으면 보상을 받을 수 있어요.',
                style: const TextStyle(color: AppTheme.textHint, fontSize: 13)),
          const SizedBox(height: 8),
          const Divider(color: AppTheme.border, height: 24),
          const Text('· 비콘 감지 시 자동 적립됩니다.',
              style: TextStyle(color: AppTheme.textHint, fontSize: 12)),
          const SizedBox(height: 4),
          const Text('· 동일 매장 재방문 적립은 일정 시간 후 가능합니다.',
              style: TextStyle(color: AppTheme.textHint, fontSize: 12)),
          const SizedBox(height: 4),
          const Text('· 적립 분쟁은 매장 사업자가 책임을 부담합니다.',
              style: TextStyle(color: AppTheme.textHint, fontSize: 12)),
        ],
      ),
      actions: [
        if (facilityId != null)
          PwButton(
            variant: PwButtonVariant.text,
            fullWidth: false,
            onPressed: () {
              Navigator.of(context).pop();
              context.push('/facility/$facilityId');
            },
            child: const Text('매장 보기'),
          ),
        PwButton(
          fullWidth: false,
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('닫기'),
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
