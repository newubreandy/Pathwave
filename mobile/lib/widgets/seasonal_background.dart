/// 사용자 앱 시즌 배경 — 슈퍼어드민 등록 이미지 또는 계절 그라데이션 fallback.
///
/// 사용:
///   Scaffold(
///     body: SeasonalBackground(child: SafeArea(child: ...))
///   )
///
/// 동작:
/// - ``ThemeService.activeTheme`` 가 있으면 ``BoxFit.cover`` 로 화면 가득.
///   가로/세로 중 한 쪽 기준으로 풀, 다른 쪽은 비율 유지 후 자연스러운 잘림.
///   ``cached_network_image`` 로 1차 디스크 캐시.
/// - 없으면 ``SeasonUtils.fallbackGradient(currentKst)`` 그라데이션.
/// - 가독성 보정 어두운 오버레이는 항상 위에 1장 깔린다 (overlayAlpha).
library;

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/theme_service.dart';
import '../utils/api_config.dart';
import '../utils/season.dart';

class SeasonalBackground extends StatelessWidget {
  final Widget child;

  /// 명시적으로 어두운 오버레이를 끄고 싶을 때 (예: 모달).
  final bool applyOverlay;

  const SeasonalBackground({
    super.key,
    required this.child,
    this.applyOverlay = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = context.watch<ThemeService>();
    return Stack(
      fit: StackFit.expand,
      children: [
        _buildBackground(theme),
        if (applyOverlay) _buildOverlay(theme),
        child,
      ],
    );
  }

  Widget _buildBackground(ThemeService svc) {
    final t = svc.activeTheme;
    if (t == null || t.imageUrl.isEmpty) {
      return DecoratedBox(
        decoration: BoxDecoration(gradient: SeasonUtils.fallbackGradient(svc.season)),
      );
    }
    // 서버 image_url 은 '/static/themes/...' 상대 경로. 절대 URL 로 변환.
    final url = t.imageUrl.startsWith('http')
        ? t.imageUrl
        : '${ApiConfig.baseUrl}${t.imageUrl}';
    return CachedNetworkImage(
      imageUrl: url,
      fit: BoxFit.cover,                // ⭐ 큰 이미지 가득 채움. 잘려도 자연스러움.
      placeholder: (_, _) => DecoratedBox(
        decoration: BoxDecoration(gradient: SeasonUtils.fallbackGradient(svc.season)),
      ),
      errorWidget: (_, _, _) => DecoratedBox(
        decoration: BoxDecoration(gradient: SeasonUtils.fallbackGradient(svc.season)),
      ),
    );
  }

  Widget _buildOverlay(ThemeService svc) {
    final alpha = svc.activeTheme?.overlayAlpha ?? 0.45;
    return Positioned.fill(
      child: IgnorePointer(
        child: ColoredBox(
          color: Color.fromRGBO(15, 15, 26, alpha),
        ),
      ),
    );
  }
}
