import 'package:flutter/material.dart';

import '../../services/stamp_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/empty_state.dart';

/// 내 스탬프 — 시설별 카드 형태.
class StampsScreen extends StatefulWidget {
  const StampsScreen({super.key});
  @override
  State<StampsScreen> createState() => _StampsScreenState();
}

class _StampsScreenState extends State<StampsScreen> {
  late Future<List<Map<String, dynamic>>> _future;

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
      appBar: AppBar(title: const Text('내 스탬프')),
      body: RefreshIndicator(
        onRefresh: _reload,
        child: FutureBuilder<List<Map<String, dynamic>>>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snap.hasError) {
              return ErrorState(message: snap.error.toString(), onRetry: _reload);
            }
            final list = snap.data ?? [];
            if (list.isEmpty) {
              return ListView(
                children: const [
                  SizedBox(height: 100),
                  EmptyState(
                    icon: Icons.local_activity_outlined,
                    title: '아직 적립된 스탬프가 없습니다',
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
      ),
    );
  }
}


class _StampCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const _StampCard({required this.data});

  @override
  Widget build(BuildContext context) {
    final facilityName = data['facility_name']?.toString() ?? '매장';
    final count = (data['count'] as num?)?.toInt() ?? 0;
    final required = (data['required_count'] as num?)?.toInt() ?? 10;
    final progress = required > 0 ? (count / required).clamp(0.0, 1.0) : 0.0;

    return Container(
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
          if (count >= required) ...[
            const SizedBox(height: 8),
            const Text('🎉 보상 쿠폰이 발급되었어요',
              style: TextStyle(color: AppTheme.success, fontSize: 13)),
          ],
        ],
      ),
    );
  }
}
