import 'package:flutter/material.dart';

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
              padding: const EdgeInsets.all(16),
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
    final t = I18nService.instance;
    final facilityName = data['facility_name']?.toString() ?? '매장';
    final count = (data['count'] as num?)?.toInt() ?? 0;
    final required = (data['required_count'] as num?)?.toInt() ?? 10;
    final progress = required > 0 ? (count / required).clamp(0.0, 1.0) : 0.0;
    final expiresAt = data['expires_at']?.toString();

    // 시설별 스탬프 정책 (백엔드 응답에 포함된 경우)
    final policy = data['policy'] as Map?;
    final hasPolicy = policy != null;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 스탬프 적립 안내 카드 (정책 데이터가 있을 때만)
        if (hasPolicy) ...[
          PwCard(
            padding: const EdgeInsets.all(14),
            color: AppTheme.surfaceLight,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.info_outline, size: 16, color: AppTheme.primary),
                    const SizedBox(width: 6),
                    Text(
                      t.t('stamp.terms_title', defaultValue: '스탬프 적립 안내'),
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 13,
                        color: AppTheme.primary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                _TermsBullet(t.t(
                  'stamp.terms_accrual',
                  defaultValue: '비콘 감지 시 자동 적립되며, 매장 내 체류 중 1회 적립됩니다.',
                )),
                _TermsBullet(t.t(
                  'stamp.terms_cooldown',
                  defaultValue: '동일 매장 재방문 적립은 일정 시간 이후부터 가능합니다.',
                )),
                _TermsBullet(t.t(
                  'stamp.terms_expiry',
                  defaultValue: '스탬프는 마지막 적립일로부터 일정 기간 후 만료됩니다.',
                )),
                _TermsBullet(t.t(
                  'stamp.terms_reward',
                  defaultValue: '목표 개수 달성 시 보상 쿠폰이 자동 발급됩니다.',
                )),
                _TermsBullet(t.t(
                  'stamp.terms_dispute',
                  defaultValue: '적립 관련 분쟁은 해당 매장 사업자가 책임을 부담하며, PathWave 는 중개 플랫폼으로 책임을 지지 않습니다.',
                )),
              ],
            ),
          ),
          const SizedBox(height: 12),
        ],
        // 스탬프 현황 카드
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppTheme.surface,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppTheme.border),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.local_activity, color: AppTheme.primary),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(facilityName,
                      style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.primary.withValues(alpha: 0.18),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text('$count / $required',
                      style: const TextStyle(color: AppTheme.primary, fontWeight: FontWeight.w600)),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: progress,
                  minHeight: 8,
                  backgroundColor: AppTheme.border,
                  color: AppTheme.primary,
                ),
              ),
              if (expiresAt != null) ...[
                const SizedBox(height: 8),
                Row(
                  children: [
                    const Icon(Icons.access_time, size: 13, color: AppTheme.textHint),
                    const SizedBox(width: 4),
                    Text(
                      '${t.t('stamp.expires_at_label', defaultValue: '만료일')}: ${expiresAt.split('T').first}',
                      style: const TextStyle(color: AppTheme.textHint, fontSize: 12),
                    ),
                  ],
                ),
              ],
              if (count >= required) ...[
                const SizedBox(height: 8),
                const Text('🎉 보상 쿠폰이 발급되었어요',
                  style: TextStyle(color: AppTheme.success, fontSize: 13)),
              ],
            ],
          ),
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
