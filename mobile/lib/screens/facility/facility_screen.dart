import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../services/store_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/empty_state.dart';

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

  int get _id => int.tryParse(widget.facilityId) ?? 0;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  void _reload() {
    _detail = StoreService().get(_id);
    _images = StoreService().images(_id);
  }

  Future<void> _refresh() async {
    setState(() { _reload(); });
    await Future.wait([_detail, _images]);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<Map<String, dynamic>>(
          future: _detail,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snap.hasError) {
              return ListView(children: [
                const SizedBox(height: 100),
                ErrorState(message: snap.error.toString(), onRetry: _refresh),
              ]);
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

  SliverAppBar _buildAppBar(Map<String, dynamic> f) {
    final imageUrl = f['image_url']?.toString();
    return SliverAppBar(
      expandedHeight: 220,
      pinned: true,
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
            child: ElevatedButton.icon(
              onPressed: () => context.push('/chat/$_id'),
              icon: const Icon(Icons.chat_bubble_outline),
              label: const Text('매장과 채팅'),
            ),
          ),
        ],
      ),
    );
  }
}
