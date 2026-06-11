import 'dart:ui' show ImageFilter;

import 'package:flutter/material.dart';

import '../../utils/error_message.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:go_router/go_router.dart';
import 'package:latlong2/latlong.dart' as latlng;
import 'package:url_launcher/url_launcher.dart';

import '../../services/favorite_service.dart';
import '../../services/store_service.dart';
import '../../services/i18n_service.dart';
import '../../utils/app_theme.dart';
import '../../utils/i18n_context.dart';
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
  late Future<Map<String, dynamic>> _menu;
  String _menuLang = 'ko';

  bool _isFavorite = false;
  bool _favLoading = false;

  int get _id => int.tryParse(widget.facilityId) ?? 0;

  @override
  void initState() {
    super.initState();
    _reload();
    _loadFavoriteState();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // 디바이스 lang 으로 메뉴 fetch 갱신 (ko 외에는 백엔드가 자동 번역 fallback)
    final newLang = Localizations.localeOf(context).languageCode;
    if (newLang != _menuLang) {
      _menuLang = newLang;
      _menu = StoreService().menu(_id, lang: _menuLang);
    }
  }

  void _reload() {
    _detail = StoreService().get(_id);
    _images = StoreService().images(_id);
    _menu   = StoreService().menu(_id, lang: _menuLang);
  }

  Future<void> _refresh() async {
    setState(() { _reload(); });
    await Future.wait([_detail, _images, _menu]);
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
      // 2026-06-09 — SafeArea 제거: SliverAppBar 가 top 자동 처리, bottom 은 마지막 SliverPadding 으로.
      // SafeArea wrapping 시 SliverAppBar/CustomScrollView 의 viewport 가 padding 흡수 → 잘림 버그.
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
                      message: friendlyError(snap.error),
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
                SliverToBoxAdapter(child: _buildHeroImage(f)),
                // 2026-06-09 — provider StoreInfo 와 노출 순서 통일.
                // (1) 헤더 주소 (2) 연락처 (3) 영업시간+휴무 (4) 설명 (5) 메뉴
                // (6) 혜택 (7) 추가 갤러리 (8) 지도
                SliverToBoxAdapter(child: _buildHeader(f)),
                SliverToBoxAdapter(child: _buildContact(f)),
                SliverToBoxAdapter(child: _buildHours(f)),
                SliverToBoxAdapter(child: _buildDescription(f)),
                SliverToBoxAdapter(child: _buildMenu()),
                SliverToBoxAdapter(child: _buildBenefits(f)),
                SliverToBoxAdapter(child: _buildImages()),
                SliverToBoxAdapter(child: _buildMap(f)),
                SliverToBoxAdapter(child: _buildActions(f)),
                // 2026-06-09 — iPhone home indicator 영역 보정 (SafeArea 가 CustomScrollView 내부에 영향 안 미치는 케이스).
                SliverToBoxAdapter(
                  // viewPadding = SafeArea 가 흡수해도 원본 OS padding 유지.
                  child: SizedBox(height: 24 + MediaQuery.of(context).viewPadding.bottom),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  /// loading/error 상태용 단순 AppBar — 백 버튼 + 제목만.
  /// PwAppBar 와 동일한 글래스 헤더 — blur(14) + 흰 12% + 하단 흰 22% 보더.
  /// (SliverAppBar 는 PwAppBar 를 직접 못 쓰므로 flexibleSpace 로 동일 시각 재현)
  Widget _glassBarSpace() {
    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.12),
            border: Border(
              bottom: BorderSide(
                color: Colors.white.withValues(alpha: 0.22),
                width: 1,
              ),
            ),
          ),
        ),
      ),
    );
  }

  SliverAppBar _buildPlainAppBar() {
    return SliverAppBar(
      pinned: true,
      backgroundColor: Colors.transparent,
      flexibleSpace: _glassBarSpace(),
      leading: PwIconButton(
        icon: Icons.arrow_back,
        tooltip: context.t('mobile.common.back', defaultValue: '뒤로'),
        onPressed: () => context.pop(),
      ),
      title: Text(context.t('mobile.facility.title', defaultValue: '매장 정보')),
    );
  }

  SliverAppBar _buildAppBar(Map<String, dynamic> f) {
    final name = f['name']?.toString() ?? I18nService.instance.t('mobile.common.fallback_store', defaultValue: '매장');
    return SliverAppBar(
      pinned: true,
      // 2026-06-11 — PwAppBar 와 완전 동일 가이드: blur 글래스 + 테마 title 스타일.
      // (이전: 블러 없는 반투명 + 커스텀 17px 타이틀 → 다른 화면과 미세 불일치)
      backgroundColor: Colors.transparent,
      flexibleSpace: _glassBarSpace(),
      title: Text(name),
      leading: PwIconButton(
        icon: Icons.arrow_back,
        color: AppTheme.textPrimary,
        tooltip: context.t('mobile.common.back', defaultValue: '뒤로'),
        onPressed: () => context.pop(),
      ),
      actions: [
        PwIconButton(
          icon: _isFavorite ? Icons.favorite : Icons.favorite_border,
          color: _isFavorite ? AppTheme.primary : AppTheme.textPrimary,
          tooltip: _isFavorite
              ? context.t('mobile.facility.unfavorite', defaultValue: '즐겨찾기 해제')
              : context.t('mobile.facility.add_favorite', defaultValue: '즐겨찾기 추가'),
          onPressed: _favLoading ? null : _toggleFavorite,
        ),
        PwIconButton(
          icon: Icons.flag_outlined,
          tooltip: context.t('mobile.facility.report', defaultValue: '신고하기'),
          onPressed: () => context.push(
            '/support?tab=report&target=facility&id=$_id',
          ),
        ),
      ],
    );
  }

  /// 매장 메인 이미지 — AppBar 와 겹치지 않게 별도 영역.
  Widget _buildHeroImage(Map<String, dynamic> f) {
    final imageUrl = f['image_url']?.toString();
    return SizedBox(
      height: 220,
      width: double.infinity,
      child: imageUrl != null && imageUrl.isNotEmpty
          ? CachedNetworkImage(
              imageUrl: imageUrl,
              fit: BoxFit.cover,
              alignment: Alignment.topCenter,
              errorWidget: (_, _, _) =>
                  Container(color: Colors.white.withValues(alpha: 0.08)),
            )
          : Container(
              color: Colors.white.withValues(alpha: 0.08),
              child: const Icon(Icons.store, size: 64, color: AppTheme.textHint),
            ),
    );
  }

  /// 천단위 콤마 + "원" 표기. 비숫자/null 은 원본 문자열 그대로.
  String _formatPrice(dynamic v) {
    if (v == null) return '';
    final s = v.toString();
    final n = int.tryParse(s.replaceAll(RegExp(r'[^0-9-]'), ''));
    if (n == null) return s;
    final str = n.toString();
    final buf = StringBuffer();
    for (int i = 0; i < str.length; i++) {
      if (i > 0 && (str.length - i) % 3 == 0) buf.write(',');
      buf.write(str[i]);
    }
    return '${buf.toString()}원';
  }

  Widget _buildHeader(Map<String, dynamic> f) {
    // 2026-06-09 — 매장명은 상단 AppBar 에 표시. 설명은 _buildDescription 으로 분리.
    final address = f['address']?.toString() ?? '';
    if (address.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (address.isNotEmpty) ...[
            Row(
              children: [
                const Icon(Icons.place, size: 16, color: AppTheme.textHint),
                const SizedBox(width: 4),
                Expanded(child: Text(address,
                  style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13))),
              ],
            ),
          ],
        ],
      ),
    );
  }

  /// 매장 설명 — 별도 섹션 (영업시간 뒤·메뉴 앞).
  Widget _buildDescription(Map<String, dynamic> f) {
    final desc = f['description']?.toString() ?? '';
    if (desc.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
      child: Text(
        desc,
        style: const TextStyle(color: AppTheme.textSecondary, height: 1.45),
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
                // 2026-06-09 — backend 응답 키 정합: image_url 또는 url.
                final url = (list[i]['image_url'] ?? list[i]['url'])?.toString() ?? '';
                return ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: SizedBox(
                    width: 150, height: 110,
                    child: url.isEmpty
                      ? Container(color: Colors.white.withValues(alpha: 0.08))
                      : CachedNetworkImage(
                          imageUrl: url,
                          fit: BoxFit.cover,
                          placeholder: (_, _) => Container(color: Colors.white.withValues(alpha: 0.08)),
                          errorWidget: (_, _, _) => Container(color: Colors.white.withValues(alpha: 0.08)),
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

  Widget _buildMenu() {
    return FutureBuilder<Map<String, dynamic>>(
      future: _menu,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 24),
            child: Center(child: SizedBox(width: 24, height: 24,
              child: CircularProgressIndicator(strokeWidth: 2))),
          );
        }
        if (snap.hasError) return const SizedBox.shrink();
        final data = snap.data ?? const {};
        final items = (data['items'] as List?)?.cast<Map<String, dynamic>>() ?? const [];
        if (items.isEmpty) return const SizedBox.shrink();
        final source = (data['source'] as String?) ?? 'cache';
        final isTranslated = source == 'translated';
        final isFallback = source == 'fallback_blocked';

        return Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  const Icon(Icons.menu_book_outlined,
                    size: 18, color: AppTheme.textSecondary),
                  const SizedBox(width: 6),
                  Text(context.t('mobile.facility.menu', defaultValue: '메뉴'),
                    style: Theme.of(context).textTheme.titleMedium),
                  if (isTranslated) ...[
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppTheme.primary.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(context.t('mobile.facility.auto_translate',
                          defaultValue: '자동 번역'), style: const TextStyle(
                        fontSize: 10, color: AppTheme.primary,
                        fontWeight: FontWeight.w600,
                      )),
                    ),
                  ],
                ],
              ),
              if (isFallback)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    context.t('mobile.facility.translate_suspended', defaultValue: '※ 자동 번역 일시 중단 — 원본 표시'),
                    style: const TextStyle(fontSize: 11,
                      color: AppTheme.textHint, fontStyle: FontStyle.italic),
                  ),
                ),
              const SizedBox(height: 8),
              Container(
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.10),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.white.withValues(alpha: 0.18)),
                ),
                child: Column(
                  children: [
                    for (int i = 0; i < items.length; i++) ...[
                      if (i > 0) Divider(height: 1,
                        color: Colors.white.withValues(alpha: 0.18),
                        indent: 12, endIndent: 12),
                      Padding(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 10),
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    (items[i]['name'] ?? '').toString(),
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w600),
                                  ),
                                  if ((items[i]['description'] ?? '').toString().isNotEmpty)
                                    Padding(
                                      padding: const EdgeInsets.only(top: 2),
                                      child: Text(
                                        items[i]['description'].toString(),
                                        style: const TextStyle(
                                          fontSize: 12,
                                          color: AppTheme.textSecondary),
                                      ),
                                    ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 8),
                            // 가격은 항상 KRW (백엔드 정규화) — 환산/단위 변경 X
                            // 2026-06-09 — 천단위 콤마 + "원" 단위 표기
                            Text(
                              _formatPrice(items[i]['price']),
                              style: const TextStyle(
                                fontWeight: FontWeight.w600,
                                color: Colors.white,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildHours(Map<String, dynamic> f) {
    final hours = f['business_hours'];
    final holidays = (f['holidays'] as List?)?.cast<dynamic>() ?? const [];
    if (hours == null && holidays.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.10),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white.withValues(alpha: 0.18)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (hours != null) ...[
              Row(children: [
                const Icon(Icons.access_time, size: 16, color: AppTheme.textSecondary),
                const SizedBox(width: 6),
                Text(context.t('mobile.facility.business_hours', defaultValue: '영업시간'),
                  style: const TextStyle(fontWeight: FontWeight.w600)),
              ]),
              const SizedBox(height: 8),
              Text(
                hours is Map ? hours.entries.map((e) => '${e.key}: ${e.value}').join('\n') : hours.toString(),
                style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
              ),
            ],
            if (holidays.isNotEmpty) ...[
              if (hours != null) const SizedBox(height: 12),
              Row(children: [
                const Icon(Icons.event_busy, size: 16, color: AppTheme.textSecondary),
                const SizedBox(width: 6),
                Text(context.t('mobile.facility.regular_holiday', defaultValue: '정기휴무'),
                    style: const TextStyle(fontWeight: FontWeight.w600)),
              ]),
              const SizedBox(height: 8),
              Text(
                holidays.join(' · '),
                style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
              ),
            ],
          ],
        ),
      ),
    );
  }

  /// 진행중 혜택 — welcome 쿠폰·스탬프·할인 카드 리스트.
  Widget _buildBenefits(Map<String, dynamic> f) {
    final benefits = (f['benefits'] as List?)?.cast<dynamic>() ?? const [];
    if (benefits.isEmpty) return const SizedBox.shrink();
    IconData iconFor(String kind) {
      switch (kind) {
        case 'stamp':   return Icons.approval;
        case 'coupon':  return Icons.confirmation_number;
        case 'welcome': return Icons.celebration;
        default:        return Icons.card_giftcard;
      }
    }
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.10),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white.withValues(alpha: 0.18)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              const Icon(Icons.card_giftcard, size: 16, color: AppTheme.textSecondary),
              const SizedBox(width: 6),
              Text(context.t('mobile.facility.active_benefits', defaultValue: '진행중인 혜택'),
                  style: const TextStyle(fontWeight: FontWeight.w600)),
            ]),
            const SizedBox(height: 10),
            for (final b in benefits) ...[
              if (b != benefits.first)
                Divider(
                    height: 18,
                    color: Colors.white.withValues(alpha: 0.18)),
              Row(children: [
                Container(
                  width: 32, height: 32,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [
                        AppTheme.primary.withValues(alpha: 0.85),
                        AppTheme.primary.withValues(alpha: 0.45),
                      ],
                    ),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                        color: Colors.white.withValues(alpha: 0.28)),
                  ),
                  child: Icon(
                      iconFor((b is Map ? b['kind']?.toString() : null) ?? ''),
                      size: 18, color: Colors.white),
                ),
                const SizedBox(width: 10),
                Expanded(child: Text(
                  (b is Map ? b['title']?.toString() : b.toString()) ?? '',
                  style: const TextStyle(
                      color: Colors.white, fontSize: 13.5),
                )),
              ]),
            ],
          ],
        ),
      ),
    );
  }

  /// OSM 매장 위치 지도 (2026-06-09). lat/lng 없으면 미표시.
  /// flutter_map + OpenStreetMap tile — Google Maps 비용 회피.
  Widget _buildMap(Map<String, dynamic> f) {
    final lat = (f['lat'] ?? f['latitude']) as num?;
    final lng = (f['lng'] ?? f['longitude']) as num?;
    if (lat == null || lng == null) return const SizedBox.shrink();
    final pos = latlng.LatLng(lat.toDouble(), lng.toDouble());
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: SizedBox(
          height: 180,
          child: FlutterMap(
            options: MapOptions(initialCenter: pos, initialZoom: 16),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.triggersoft.pathwave',
              ),
              MarkerLayer(markers: [
                Marker(
                  point: pos,
                  width: 36, height: 36,
                  child: const Icon(Icons.location_on,
                      color: AppTheme.primary, size: 36),
                ),
              ]),
            ],
          ),
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
            color: Colors.white.withValues(alpha: 0.10),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.white.withValues(alpha: 0.18)),
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
              child: Text(context.t('mobile.facility.chat_with_store', defaultValue: '매장과 채팅')),
            ),
          ),
        ],
      ),
    );
  }
}
