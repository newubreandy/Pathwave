import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show Clipboard, ClipboardData;

import '../../utils/error_message.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:go_router/go_router.dart';

import '../../services/favorite_service.dart';
import '../../utils/app_theme.dart';
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
    final name = data['name']?.toString() ?? '매장';
    final ok = await showPwDialog<bool>(
      context: context,
      title: const Text('즐겨찾기 해제'),
      content: Text('"$name"을(를) 즐겨찾기에서 제거할까요?'),
      actions: [
        PwButton(
          variant: PwButtonVariant.text,
          fullWidth: false,
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text('취소'),
        ),
        PwButton(
          variant: PwButtonVariant.danger,
          fullWidth: false,
          onPressed: () => Navigator.of(context).pop(true),
          child: const Text('해제'),
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
      appBar: PwAppBar(title: const Text('즐겨찾기')),
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
              return ListView(children: const [
                SizedBox(height: 100),
                PwEmptyState(
                  icon: Icons.favorite_border,
                  title: '즐겨찾기한 매장이 없습니다',
                  subtitle: '매장 상세나 검색에서 하트를 눌러보세요.',
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
    final name = data['name']?.toString() ?? '매장';
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
                    placeholder: (_, _) => Container(color: AppTheme.surfaceLight),
                    errorWidget: (_, _, _) => Container(
                      color: AppTheme.surfaceLight,
                      child: const Icon(Icons.store, color: AppTheme.textHint),
                    ),
                  )
                : Container(
                    color: AppTheme.surfaceLight,
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
                tooltip: '공유하기',
                onPressed: () => _share(context, id, name),
              ),
              const SizedBox(height: 4),
              PwIconButton(
                icon: Icons.favorite,
                color: AppTheme.primary,
                tooltip: '즐겨찾기 해제',
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
      SnackBar(content: Text('"$name" 링크를 복사했습니다.')),
    );
  }
}
