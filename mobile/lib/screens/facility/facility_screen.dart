import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../services/favorite_service.dart';
import '../../services/store_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/pw.dart';

/// 매장 상세 — 이미지 / 영업시간 / 위치 / 채팅 진입.
class FacilityScreen extends StatefulWidget {
  final String facilityId;
  const FacilityScreen({super.key, required this.facilityId});

  @override
  State<FacilityScreen> createState() => _FacilityScreenState();
}

class _FacilityScreenState extends State<FacilityScreen> {
  late Future<Map<String, dynamic>> _detail;
  late Future<List<Map<String, dynamic>>> _images;

  bool _isFavorite = false;
  bool _favLoading = false;

  int get _id => int.tryParse(widget.facilityId) ?? 0;

  @override
  void initState() {
    super.initState();
    _reload();
    _loadFavoriteState();
  }

  void _reload() {
    _detail = StoreService().get(_id);
    _images = StoreService().images(_id);
  }

  Future<void> _refresh() async {
    setState(() { _reload(); });
    await Future.wait([_detail, _images]);
  }

  Future<void> _loadFavoriteState() async {
    try {
      final list = await FavoriteService().list();
      if (!mounted) return;
      setState(() {
        _isFavorite = list.any((f) => f['id'] == _id);
      });
    } catch (_) {
      // 즐겨찾기 상태 로드 실패는 무시
    }
  }

  Future<void> _toggleFavorite() async {
    if (_favLoading) return;
    setState(() => _favLoading = true);
    final wasFav = _isFavorite;
    setState(() => _isFavorite = !wasFav);
    final ok = wasFav
      ? await FavoriteService().remove(_id)
      : await FavoriteService().add(_id);
    if (!ok && mounted) {
      setState(() => _isFavorite = wasFav); // 실패 시 롤백
    }
    if (mounted) setState(() => _favLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<Map<String, dynamic>>(
          future: _detail,
          builder: (context, snap) {
            // loading/error 상태에도 AppBar + back arrow 보장 (HIG/Material 3 — dead-end 금지).
            if (snap.connectionState == ConnectionState.waiting) {
              return CustomScrollView(
                slivers: [
                  _buildPlainAppBar(),
                  const SliverFillRemaining(
                    hasScrollBody: false,
                    child: Center(child: CircularProgressIndicator()),
                  ),
                ],
              );
            }
            if (snap.hasError) {
              return CustomScrollView(
                slivers: [
                  _buildPlainAppBar(),
                  SliverFillRemaining(
                    hasScrollBody: false,
                    child: PwErrorState(
                      message: snap.error.toString(),
                      onRetry: _refresh,
                    ),
                  ),
                ],
              );
            }
            final f = snap.data ?? {};
            return CustomScrollView(
              slivers: [
                _buildAppBar(f),
                SliverToBoxAdapter(child: _buildHeader(f)),
                SliverToBoxAdapter(child: _buildImages()),
                SliverToBoxAdapter(child: _buildHours(f)),
                SliverToBoxAdapter(child: _buildContact(f)),
                SliverToBoxAdapter(child: _buildActions(f)),
                const SliverToBoxAdapter(child: SizedBox(height: 24)),
              ],
            );
          },
        ),
      ),
    );
  }

  /// loading/error 상태용 단순 AppBar — 백 버튼 + 제목만.
  SliverAppBar _buildPlainAppBar() {
    return SliverAppBar(
      pinned: true,
      leading: PwIconButton(
        icon: Icons.arrow_back,
        tooltip: '뒤로',
        onPressed: () => context.pop(),
      ),
      title: const Text('매장 정보'),
    );
  }

  SliverAppBar _buildAppBar(Map<String, dynamic> f) {
    final imageUrl = f['image_url']?.toString();
    return SliverAppBar(
      expandedHeight: 220,
      pinned: true,
      leading: PwIconButton(
        icon: Icons.arrow_back,
        color: AppTheme.textPrimary,
        tooltip: '뒤로',
        onPressed: () => context.pop(),
      ),
      actions: [
        PwIconButton(
          icon: _isFavorite ? Icons.favorite : Icons.favorite_border,
          color: _isFavorite ? AppTheme.primary : AppTheme.textPrimary,
          tooltip: _isFavorite ? '즐겨찾기 해제' : '즐겨찾기 추가',
          onPressed: _favLoading ? null : _toggleFavorite,
        ),
        PwIconButton(
          icon: Icons.flag_outlined,
          tooltip: '신고하기',
          onPressed: () => context.push(
            '/support?tab=report&target=facility&id=$_id',
          ),
        ),
      ],
      flexibleSpace: FlexibleSpaceBar(
        background: imageUrl != null && imageUrl.isNotEmpty
          ? CachedNetworkImage(
              imageUrl: imageUrl,
              fit: BoxFit.cover,
              errorWidget: (_, _, _) => Container(color: AppTheme.surfaceLight),
            )
          : Container(
              color: AppTheme.surfaceLight,
              child: const Icon(Icons.store, size: 64, color: AppTheme.textHint),
            ),
      ),
    );
  }

  Widget _buildHeader(Map<String, dynamic> f) {
    final name = f['name']?.toString() ?? '매장';
    final desc = f['description']?.toString() ?? '';
    final address = f['address']?.toString() ?? '';
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(name, style: Theme.of(context).textTheme.headlineMedium),
          if (address.isNotEmpty) ...[
            const SizedBox(height: 6),
            Row(
              children: [
                const Icon(Icons.place, size: 16, color: AppTheme.textHint),
                const SizedBox(width: 4),
                Expanded(child: Text(address,
                  style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13))),
              ],
            ),
          ],
          if (desc.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(desc,
              style: const TextStyle(color: AppTheme.textSecondary, height: 1.45)),
          ],
        ],
      ),
    );
  }

  Widget _buildImages() {
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: _images,
      builder: (context, snap) {
        final list = snap.data ?? [];
        if (list.isEmpty) return const SizedBox.shrink();
        return Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
          child: SizedBox(
            height: 110,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: list.length,
              separatorBuilder: (_, _) => const SizedBox(width: 8),
              itemBuilder: (context, i) {
                final url = list[i]['url']?.toString() ?? '';
                return ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: SizedBox(
                    width: 150, height: 110,
                    child: url.isEmpty
                      ? Container(color: AppTheme.surfaceLight)
                      : CachedNetworkImage(
                          imageUrl: url,
                          fit: BoxFit.cover,
                          placeholder: (_, _) => Container(color: AppTheme.surfaceLight),
                          errorWidget: (_, _, _) => Container(color: AppTheme.surfaceLight),
                        ),
                  ),
                );
              },
            ),
          ),
        );
      },
    );
  }

  Widget _buildHours(Map<String, dynamic> f) {
    final hours = f['business_hours'];
    if (hours == null) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppTheme.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(children: [
              Icon(Icons.access_time, size: 16, color: AppTheme.textSecondary),
              SizedBox(width: 6),
              Text('영업시간', style: TextStyle(fontWeight: FontWeight.w600)),
            ]),
            const SizedBox(height: 8),
            Text(
              hours is Map ? hours.entries.map((e) => '${e.key}: ${e.value}').join('\n') : hours.toString(),
              style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContact(Map<String, dynamic> f) {
    final phone = f['phone']?.toString();
    if (phone == null || phone.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => launchUrl(Uri.parse('tel:$phone')),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppTheme.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppTheme.border),
          ),
          child: Row(
            children: [
              const Icon(Icons.call, size: 18, color: AppTheme.primary),
              const SizedBox(width: 8),
              Expanded(child: Text(phone)),
              const Icon(Icons.chevron_right, color: AppTheme.textHint),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildActions(Map<String, dynamic> f) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
      child: Row(
        children: [
          Expanded(
            child: PwButton(
              icon: Icons.chat_bubble_outline,
              onPressed: () => context.push('/chat/$_id'),
              child: const Text('매장과 채팅'),
            ),
          ),
        ],
      ),
    );
  }
}
