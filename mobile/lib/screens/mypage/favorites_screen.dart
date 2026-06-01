import 'package:flutter/material.dart';

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
              padding: const EdgeInsets.all(16),
              itemCount: list.length,
              separatorBuilder: (_, _) => const SizedBox(height: 12),
              itemBuilder: (context, i) => _FavoriteCard(
                data: list[i],
                onRemove: () => _remove(list[i]['id'] as int),
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
          // 즐겨찾기 해제 버튼 (하트)
          PwIconButton(
            icon: Icons.favorite,
            color: AppTheme.primary,
            tooltip: '즐겨찾기 해제',
            onPressed: onRemove,
          ),
        ],
      ),
    );
  }
}
