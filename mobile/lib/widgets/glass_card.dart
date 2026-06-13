/// 글래스모피즘 카드 — 반투명 + backdrop blur + 흰색 1px 보더.
///
/// 사용:
///   GlassCard(
///     padding: EdgeInsets.all(16),
///     child: ...
///   )
///
/// 디자인 토큰 (AppTheme/Material 3 일관):
/// - radius:   AppTheme.rLg (20px)
/// - blur:     sigma 20
/// - bg fill:  white α 0.12 (어두운 배경 위) / black α 0.06 (밝은 배경 위)
/// - border:   white α 0.18, 1px
///
/// ``onDarkBackground`` 가 false 면 fill/border 색을 검정 톤으로 자동 전환.
library;

import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/theme_service.dart';
import '../utils/api_config.dart';
import '../utils/app_theme.dart';

class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final double radius;
  final double sigma;
  final bool   onDarkBackground;

  /// 강조 보더(활성 카드 등) — null 이면 기본 흰색 alpha.
  final Color? borderHighlight;

  /// 카드 자체에 그림자(soft) 표시. 글래스 위에 살짝 떠 보이게.
  final bool elevated;

  /// 서버 지정 글래스 텍스처 적용 여부 (2026-06-13).
  /// true(기본) — 테마에 texture_url 이 있으면 유리 안에 텍스처가 비침
  /// (어드민 교체 = 재배포 없이 전 카드 무드 변경). false = 항상 기본 blur.
  final bool useTexture;

  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(AppTheme.s4),
    this.radius = AppTheme.rLg,
    this.sigma = 20.0,
    this.onDarkBackground = true,
    this.borderHighlight,
    this.elevated = false,
    this.useTexture = true,
  });

  @override
  Widget build(BuildContext context) {
    final fill = onDarkBackground
        ? Colors.white.withValues(alpha: 0.12)
        : Colors.black.withValues(alpha: 0.06);
    final border = borderHighlight ??
        (onDarkBackground
            ? Colors.white.withValues(alpha: 0.18)
            : Colors.black.withValues(alpha: 0.12));

    // 서버 지정 텍스처 — ThemeService(ChangeNotifier) 구독으로
    // 어드민 교체 시 즉시 리빌드.
    final textureUrl = useTexture
        ? context.watch<ThemeService>().activeTheme?.textureUrl
        : null;
    final hasTexture = textureUrl != null && textureUrl.isNotEmpty;
    // 서버 texture_url 은 '/static/themes/...' 상대 경로 → 절대 URL 로 변환
    // (SeasonalBackground 와 동일 규칙). Image.network 는 절대 URL 이 필요하다.
    final textureSrc = hasTexture
        ? (textureUrl.startsWith('http')
            ? textureUrl
            : '${ApiConfig.baseUrl}$textureUrl')
        : null;

    final rect = BorderRadius.circular(radius);
    return Container(
      decoration: elevated
          ? BoxDecoration(
              borderRadius: rect,
              boxShadow: AppTheme.softShadowSm,
            )
          : null,
      child: ClipRRect(
        borderRadius: rect,
        child: BackdropFilter(
          // 텍스처가 깔리면 backdrop 이 가려지므로 blur 최소화 (성능 절약).
          filter: hasTexture
              ? ImageFilter.blur(sigmaX: 0.001, sigmaY: 0.001)
              : ImageFilter.blur(sigmaX: sigma, sigmaY: sigma),
          child: Stack(
            children: [
              // ── 유리 안 텍스처 (레퍼런스: 유리 케이스 속 패브릭) ──
              if (hasTexture)
                Positioned.fill(
                  child: Image.network(
                    textureSrc!,
                    fit: BoxFit.cover,
                    // 로드 실패 시 조용히 기본 글래스로 (빈 위젯).
                    errorBuilder: (_, _, _) => const SizedBox.shrink(),
                  ),
                ),
              // ── 유리 케이스 — fill + 상단 하이라이트 림 (광택) ──
              Positioned.fill(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: hasTexture
                        ? Colors.white.withValues(alpha: 0.06)
                        : fill,
                    borderRadius: rect,
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        Colors.white.withValues(
                            alpha: hasTexture ? 0.28 : 0.10),
                        Colors.white.withValues(alpha: 0.0),
                        Colors.white.withValues(alpha: 0.0),
                        Colors.white.withValues(
                            alpha: hasTexture ? 0.10 : 0.04),
                      ],
                      stops: const [0.0, 0.25, 0.85, 1.0],
                    ),
                  ),
                ),
              ),
              Container(
                padding: padding,
                decoration: BoxDecoration(
                  borderRadius: rect,
                  border: Border.all(color: border, width: 1),
                ),
                child: child,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// 작은 알약형 칩 (예: "NEW FEATURE"). 글래스 위에 자연스럽게 얹힌다.
class GlassPill extends StatelessWidget {
  final String label;
  final Color? color;
  final bool onDarkBackground;

  const GlassPill({
    super.key,
    required this.label,
    this.color,
    this.onDarkBackground = true,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color ??
            (onDarkBackground
                ? Colors.white.withValues(alpha: 0.18)
                : Colors.black.withValues(alpha: 0.10)),
        borderRadius: BorderRadius.circular(AppTheme.rPill),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.6,
          color: onDarkBackground ? Colors.white : Colors.black87,
        ),
      ),
    );
  }
}
