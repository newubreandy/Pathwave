import 'dart:async';

import 'package:flutter/material.dart';

import '../../utils/error_message.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';

import '../../services/favorite_service.dart';
import '../../services/permission_service.dart';
import '../../services/store_service.dart';
import '../../services/i18n_service.dart';
import '../../utils/app_theme.dart';
import '../../utils/i18n_context.dart';
import '../../widgets/pw.dart';

/// 매장 검색 — 키워드 + 현재 위치 기반 거리 정렬.
class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});
  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _searchCtrl = TextEditingController();
  Timer? _debounce;

  bool _loading = false;
  String? _error;
  List<Map<String, dynamic>> _results = [];
  Position? _myPos;
  bool _locationDenied = false;

  Set<int> _favoriteIds = {};

  @override
  void initState() {
    super.initState();
    _resolveLocation();
    _loadFavorites();
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  Future<void> _loadFavorites() async {
    try {
      final list = await FavoriteService().list();
      if (!mounted) return;
      setState(() {
        _favoriteIds = list.map((f) => f['id'] as int).toSet();
      });
    } catch (_) {
      // 즐겨찾기 로드 실패는 무시 (검색 기능에 영향 없음)
    }
  }

  Future<void> _resolveLocation() async {
    try {
      // PR #58 — OS 다이얼로그 전에 사용 목적 안내
      final granted = await PermissionService.instance.ensureLocation(context);
      if (!granted) {
        if (!mounted) return;
        setState(() => _locationDenied = true);
        await _runSearch();
        return;
      }
      final pos = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(accuracy: LocationAccuracy.medium),
      );
      if (!mounted) return;
      setState(() { _myPos = pos; });
      await _runSearch();
    } catch (_) {
      if (!mounted) return;
      setState(() => _locationDenied = true);
      await _runSearch();
    }
  }

  void _onChanged(String s) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 350), _runSearch);
  }

  Future<void> _runSearch() async {
    setState(() { _loading = true; _error = null; });
    try {
      final list = await StoreService().search(
        q: _searchCtrl.text.trim().isEmpty ? null : _searchCtrl.text.trim(),
        lat: _myPos?.latitude,
        lng: _myPos?.longitude,
        limit: 50,
      );
      if (!mounted) return;
      setState(() { _results = list; _loading = false; });
    } catch (e) {
      if (!mounted) return;
      setState(() { _error = friendlyError(e); _loading = false; });
    }
  }

  Future<void> _toggleFavorite(int facilityId) async {
    final isFav = _favoriteIds.contains(facilityId);
    setState(() {
      if (isFav) {
        _favoriteIds.remove(facilityId);
      } else {
        _favoriteIds.add(facilityId);
      }
    });
    final ok = isFav
      ? await FavoriteService().remove(facilityId)
      : await FavoriteService().add(facilityId);
    if (!ok && mounted) {
      // 실패 시 롤백
      setState(() {
        if (isFav) {
          _favoriteIds.add(facilityId);
        } else {
          _favoriteIds.remove(facilityId);
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            context.t('mobile.search.title', defaultValue: '매장 검색'),
            style: Theme.of(context).textTheme.displaySmall?.copyWith(
              color: Colors.white,
              shadows: const [
                Shadow(color: Colors.black54, blurRadius: 8, offset: Offset(0, 2)),
              ],
            ),
          ),
          const SizedBox(height: 12),
          PwTextField(
            controller: _searchCtrl,
            hint: context.t('mobile.search.hint', defaultValue: '매장명 / 주소 / 키워드 검색'),
            prefixIcon: Icons.search,
            textInputAction: TextInputAction.search,
            onChanged: _onChanged,
            onSubmitted: (_) => _runSearch(),
          ),
          if (_locationDenied) ...[
            const SizedBox(height: 8),
            Text(context.t('mobile.search.location_denied', defaultValue: '위치 권한이 없어 거리 정렬을 이용할 수 없습니다.'),
              style: const TextStyle(color: AppTheme.warning, fontSize: 12)),
          ],
          const SizedBox(height: 12),
          Expanded(
            child: _buildBody(),
          ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return PwErrorState(message: _error!, onRetry: _runSearch);
    }
    if (_results.isEmpty) {
      return PwEmptyState(
        icon: Icons.search_off,
        title: context.t('mobile.search.empty_title', defaultValue: '결과가 없습니다'),
        subtitle: context.t('mobile.search.empty_subtitle', defaultValue: '다른 키워드로 검색해 보세요.'),
      );
    }
    return RefreshIndicator(
      onRefresh: _runSearch,
      child: ListView.separated(
        padding: const EdgeInsets.only(bottom: 16),
        itemCount: _results.length,
        separatorBuilder: (_, _) => const SizedBox(height: 10),
        itemBuilder: (context, i) {
          final id = _results[i]['id'] as int?;
          return _ResultCard(
            data: _results[i],
            isFavorite: id != null && _favoriteIds.contains(id),
            onFavoriteToggle: id != null ? () => _toggleFavorite(id) : null,
          );
        },
      ),
    );
  }
}


class _ResultCard extends StatelessWidget {
  final Map<String, dynamic> data;
  final bool isFavorite;
  final VoidCallback? onFavoriteToggle;
  const _ResultCard({
    required this.data,
    required this.isFavorite,
    this.onFavoriteToggle,
  });

  @override
  Widget build(BuildContext context) {
    final id = data['id'] as int?;
    final name = data['name']?.toString() ?? I18nService.instance.t('mobile.common.fallback_store', defaultValue: '매장');
    final address = data['address']?.toString() ?? '';
    final imageUrl = data['image_url']?.toString();
    final dist = data['distance_km'];

    // 2026-06-09 — InkWell → GestureDetector (Material 없는 글래스카드 안에서도 hit 보장).
    return GlassCard(
      padding: const EdgeInsets.all(12),
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: id != null ? () => context.push('/facility/$id') : null,
        child: Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: SizedBox(
                width: 64, height: 64,
                child: imageUrl != null && imageUrl.isNotEmpty
                  ? CachedNetworkImage(
                      imageUrl: imageUrl,
                      fit: BoxFit.cover,
                      placeholder: (_, _) => Container(color: Colors.white12),
                      errorWidget: (_, _, _) => Container(
                        color: Colors.white12,
                        child: const Icon(Icons.store, color: Colors.white54),
                      ),
                    )
                  : Container(
                      color: Colors.white12,
                      child: const Icon(Icons.store, color: Colors.white54),
                    ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                  if (address.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(address,
                      style: const TextStyle(color: Colors.white70, fontSize: 12),
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                  ],
                  if (dist != null) ...[
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        const Icon(Icons.place, size: 12, color: Colors.white54),
                        const SizedBox(width: 2),
                        Text('${(dist as num).toStringAsFixed(2)} km',
                          style: const TextStyle(color: Colors.white54, fontSize: 11)),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            // 즐겨찾기 토글 하트
            PwIconButton(
              icon: isFavorite ? Icons.favorite : Icons.favorite_border,
              color: isFavorite ? AppTheme.primary : Colors.white54,
              tooltip: isFavorite
                  ? context.t('mobile.facility.unfavorite', defaultValue: '즐겨찾기 해제')
                  : context.t('mobile.facility.add_favorite', defaultValue: '즐겨찾기 추가'),
              onPressed: onFavoriteToggle,
            ),
          ],
        ),
      ),
    );
  }
}
