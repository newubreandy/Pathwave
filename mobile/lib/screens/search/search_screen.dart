import 'dart:async';

import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';

import '../../services/store_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/empty_state.dart';

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

  @override
  void initState() {
    super.initState();
    _resolveLocation();
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  Future<void> _resolveLocation() async {
    try {
      var perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied) {
        perm = await Geolocator.requestPermission();
      }
      if (perm == LocationPermission.denied || perm == LocationPermission.deniedForever) {
        setState(() => _locationDenied = true);
        await _runSearch();
        return;
      }
      final pos = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(accuracy: LocationAccuracy.medium),
      );
      setState(() { _myPos = pos; });
      await _runSearch();
    } catch (_) {
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
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('매장 검색', style: Theme.of(context).textTheme.displaySmall),
          const SizedBox(height: 12),
          TextField(
            controller: _searchCtrl,
            onChanged: _onChanged,
            textInputAction: TextInputAction.search,
            onSubmitted: (_) => _runSearch(),
            decoration: const InputDecoration(
              hintText: '매장명 / 주소 / 키워드 검색',
              prefixIcon: Icon(Icons.search),
            ),
          ),
          if (_locationDenied) ...[
            const SizedBox(height: 8),
            const Text('위치 권한이 없어 거리 정렬을 이용할 수 없습니다.',
              style: TextStyle(color: AppTheme.warning, fontSize: 12)),
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
      return ErrorState(message: _error!, onRetry: _runSearch);
    }
    if (_results.isEmpty) {
      return const EmptyState(
        icon: Icons.search_off,
        title: '결과가 없습니다',
        subtitle: '다른 키워드로 검색해 보세요.',
      );
    }
    return RefreshIndicator(
      onRefresh: _runSearch,
      child: ListView.separated(
        padding: const EdgeInsets.only(bottom: 16),
        itemCount: _results.length,
        separatorBuilder: (_, _) => const SizedBox(height: 10),
        itemBuilder: (context, i) => _ResultCard(data: _results[i]),
      ),
    );
  }
}


class _ResultCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const _ResultCard({required this.data});

  @override
  Widget build(BuildContext context) {
    final id = data['id'] as int?;
    final name = data['name']?.toString() ?? '매장';
    final address = data['address']?.toString() ?? '';
    final imageUrl = data['image_url']?.toString();
    final dist = data['distance_km'];

    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: id != null ? () => context.push('/facility/$id') : null,
      child: Container(
        decoration: BoxDecoration(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppTheme.border),
        ),
        padding: const EdgeInsets.all(12),
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
                  if (dist != null) ...[
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        const Icon(Icons.place, size: 12, color: AppTheme.textHint),
                        const SizedBox(width: 2),
                        Text('${(dist as num).toStringAsFixed(2)} km',
                          style: const TextStyle(color: AppTheme.textHint, fontSize: 11)),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: AppTheme.textHint),
          ],
        ),
      ),
    );
  }
}
