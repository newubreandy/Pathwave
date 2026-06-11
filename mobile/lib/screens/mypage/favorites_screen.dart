import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show Clipboard, ClipboardData;

import '../../utils/error_message.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:go_router/go_router.dart';

import '../../services/favorite_service.dart';
import '../../services/i18n_service.dart';
import '../../utils/app_theme.dart';
import '../../utils/i18n_context.dart';
import '../../widgets/pw.dart';

/// 즐겨찾기 매장 목록 화면 — `/mypage/favorites`.
class FavoritesScreen extends StatefulWidget {
  const FavoritesScreen({super.key});

  @override
  State<FavoritesScreen> createState() => _FavoritesScreenState();
}

class _FavoritesScreenState extends State<FavoritesScreen> {
  late Future<List<Map<String, dynamic>>> _future;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _future = FavoriteService().list();
  }

  Future<void> _reload() async {
    setState(() { _load(); });
    await _future;
  }

  Future<void> _remove(int facilityId) async {
    await FavoriteService().remove(facilityId);
    await _reload();
  }

  /// 즐겨찾기 해제 확인 다이얼로그 (실수 방지). 2026-06-09.
  Future<void> _confirmRemove(Map<String, dynamic> data) async {
    final id = data['id'] as int?;
    if (id == null) return;
    final name = data['name']?.toString() ?? I18nService.instance.t('mobile.common.fallback_store', defaultValue: '매장');
    final ok = await showPwDialog<bool>(
      context: context,
      title: Text(context.t('favorite.remove_title', defaultValue: '즐겨찾기 해제')),
      content: Text('"$name"${context.t('favorite.remove_confirm_suffix', defaultValue: '을(를) 즐겨찾기에서 제거할까요?')}'),
      actions: [
        PwButton(
          variant: PwButtonVariant.text,
          fullWidth: false,
          onPressed: () => Navigator.of(context).pop(false),
          child: Text(context.t('mobile.common.cancel', defaultValue: '취소')),
        ),
        PwButton(
          variant: PwButtonVariant.danger,
          fullWidth: false,
          onPressed: () => Navigator.of(context).pop(true),
          child: Text(context.t('favorite.remove_btn', defaultValue: '해제')),
        ),
      ],
    );
    if (ok == true) {
      await _remove(id);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PwAppBar(title: Text(context.t('favorite.title', defaultValue: '즐겨찾기'))),
      body: SafeArea(child: RefreshIndicator(
        onRefresh: _reload,
        child: FutureBuilder<List<Map<String, dynamic>>>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snap.hasError) {
              return ListView(children: [
                const SizedBox(height: 100),
                PwErrorState(message: friendlyError(snap.error), onRetry: _reload),
              ]);
            }
            final list = snap.data ?? [];
            if (list.isEmpty) {
              return ListView(children: [
                const SizedBox(height: 100),
                PwEmptyState(
                  icon: Icons.favorite_border,
                  title: context.t('favorite.empty_title', defaultValue: '즐겨찾기한 매장이 없습니다'),
                  subtitle: context.t('favorite.empty_subtitle', defaultValue: '매장 상세나 검색에서 하트를 눌러보세요.'),
                ),
              ]);
            }
            return ListView.separated(
              padding: EdgeInsets.fromLTRB(16, 16, 16,
                  16 + MediaQuery.of(context).viewPadding.bottom),
              itemCount: list.length,
              separatorBuilder: (_, _) => const SizedBox(height: 12),
              itemBuilder: (context, i) => _FavoriteCard(
                data: list[i],
                onRemove: () => _confirmRemove(list[i]),
              ),
            );
          },
        ),
      )),
    );
  }
}


class _FavoriteCard extends StatelessWidget {
  final Map<String, dynamic> data;
  final VoidCallback onRemove;
  const _FavoriteCard({required this.data, required this.onRemove});

  @override
  Widget build(BuildContext context) {
    final id = data['id'] as int?;
    final name = data['name']?.toString() ?? I18nService.instance.t('mobile.common.fallback_store', defaultValue: '매장');
    final address = data['address']?.toString() ?? '';
    final description = data['description']?.toString() ?? '';
    final imageUrl = data['image_url']?.toString();

    return PwCard(
      padding: const EdgeInsets.all(12),
      onTap: id != null ? () => context.push('/facility/$id') : null,
      child: Row(
        children: [
          // 썸네일
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: SizedBox(
              width: 64, height: 64,
              child: imageUrl != null && imageUrl.isNotEmpty
                ? CachedNetworkImage(
                    imageUrl: imageUrl,
                    fit: BoxFit.cover,
                    placeholder: (_, _) => Container(color: Colors.white.withValues(alpha: 0.08)),
                    errorWidget: (_, _, _) => Container(
                      color: Colors.white.withValues(alpha: 0.08),
                      child: const Icon(Icons.store, color: AppTheme.textHint),
                    ),
                  )
                : Container(
                    color: Colors.white.withValues(alpha: 0.08),
                    child: const Icon(Icons.store, color: AppTheme.textHint),
                  ),
            ),
          ),
          const SizedBox(width: 12),
          // 텍스트
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, style: const TextStyle(fontWeight: FontWeight.w600)),
                if (address.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(address,
                    style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
                    maxLines: 1, overflow: TextOverflow.ellipsis),
                ],
                if (description.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(description,
                    style: const TextStyle(color: AppTheme.textHint, fontSize: 12),
                    maxLines: 1, overflow: TextOverflow.ellipsis),
                ],
              ],
            ),
          ),
          // 우측 액션 — 공유 + 즐겨찾기 해제 (카드 본체는 매장 이동)
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              PwIconButton(
                icon: Icons.share_outlined,
                color: Colors.white,
                tooltip: context.t('favorite.share_tooltip', defaultValue: '공유하기'),
                onPressed: () => _share(context, id, name),
              ),
              const SizedBox(height: 4),
              PwIconButton(
                icon: Icons.favorite,
                color: AppTheme.primary,
                tooltip: context.t('favorite.remove_tooltip', defaultValue: '즐겨찾기 해제'),
                onPressed: onRemove,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _share(BuildContext context, int? id, String name) async {
    if (id == null) return;
    // 2026-06-09 — Clipboard 복사 + SnackBar (share_plus 대안 — v1 가벼운 구현).
    final url = 'https://pathwave.io/facility/$id';
    await Clipboard.setData(ClipboardData(text: '$name — $url'));
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('"$name" ${context.t('favorite.link_copied', defaultValue: '링크를 복사했습니다.')}')),
    );
  }
}
