import 'package:flutter/material.dart';

import '../../utils/error_message.dart';

import '../../services/block_service.dart';
import '../../services/i18n_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/pw.dart';

/// 차단 목록 — 손님이 차단한 매장을 보고 해지(unblock).
///
/// 설정 > 차단 목록 에서 진입. Apple App Store Guideline 1.2 (UGC 모더레이션):
/// 차단한 상대를 다시 해제할 수 있는 경로를 사용자에게 제공해야 한다.
class BlockedFacilitiesScreen extends StatefulWidget {
  const BlockedFacilitiesScreen({super.key});

  @override
  State<BlockedFacilitiesScreen> createState() =>
      _BlockedFacilitiesScreenState();
}

class _BlockedFacilitiesScreenState extends State<BlockedFacilitiesScreen> {
  final _t = I18nService.instance;
  late Future<List<Map<String, dynamic>>> _future;
  final _busy = <int>{};

  @override
  void initState() {
    super.initState();
    _future = BlockService().listBlocks();
  }

  void _reload() {
    setState(() => _future = BlockService().listBlocks());
  }

  Future<void> _unblock(int facilityId) async {
    setState(() => _busy.add(facilityId));
    try {
      await BlockService().unblockFacility(facilityId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_t.t('settings.unblock_done',
            defaultValue: '차단을 해제했습니다.'))),
      );
      _reload();
    } catch (e) {
      if (!mounted) return;
      setState(() => _busy.remove(facilityId));
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(
            '${_t.t('settings.unblock_failed', defaultValue: '해제 실패')}: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PwAppBar(
        title: Text(_t.t('settings.blocked_list_title', defaultValue: '차단 목록')),
      ),
      body: SafeArea(child: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return PwErrorState(
              message: friendlyError(snap.error),
              onRetry: _reload,
            );
          }
          final list = snap.data ?? const [];
          if (list.isEmpty) {
            return PwEmptyState(
              icon: Icons.block,
              title: _t.t('settings.blocked_empty_title',
                  defaultValue: '차단한 매장이 없습니다'),
              subtitle: _t.t('settings.blocked_empty_subtitle',
                  defaultValue: '채팅 화면 우측 상단 메뉴에서 매장을 차단할 수 있습니다.'),
            );
          }
          return ListView.separated(
            padding: EdgeInsets.fromLTRB(16, 16, 16,
                16 + MediaQuery.of(context).viewPadding.bottom),
            itemCount: list.length,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (context, i) {
              final item = list[i];
              final fid = (item['facility_id'] as num?)?.toInt() ?? 0;
              final name = item['facility_name']?.toString() ??
                  _t.t('settings.blocked_unknown', defaultValue: '매장');
              final busy = _busy.contains(fid);
              return Container(
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.10),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.border),
                ),
                child: ListTile(
                  leading: const Icon(Icons.store_outlined,
                      color: AppTheme.textSecondary),
                  title: Text(name, style: const TextStyle(fontSize: 14)),
                  trailing: PwButton(
                    variant: PwButtonVariant.outlined,
                    fullWidth: false,
                    loading: busy,
                    onPressed: busy ? null : () => _unblock(fid),
                    child: Text(_t.t('settings.unblock_btn',
                        defaultValue: '차단 해제')),
                  ),
                ),
              );
            },
          );
        },
      )),
    );
  }
}
