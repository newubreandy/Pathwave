import 'package:flutter/material.dart';

import '../utils/app_theme.dart';

/// PathWave 표준 버튼 (Material 3 기반 추상화) — 공통 가이드 통일.
///
/// 화면은 raw [ElevatedButton] / [OutlinedButton] / [TextButton] 대신 항상
/// [PwButton] 을 사용한다. variant 만 바꿔서 톤을 통일하고, loading 상태와
/// leadingIcon 패턴을 한 곳에 모은다.
///
/// ## 공통 디자인 가이드 (글래스 톤)
///
/// 모든 variant 가 공통으로 보장:
///   • **흰 텍스트** (그라데이션 배경 위 가독성)
///   • **min size 50×∞** (fullWidth) / **44×∞** (compact)
///   • **AppTheme.rMd (16px) 라운드**
///   • **흰 로딩 인디케이터**
///
/// variant 별 톤:
///   • [PwButtonVariant.primary]   — 보라(브랜드) fill + 흰 텍스트
///   • [PwButtonVariant.secondary] — 흰 글래스 14% + 흰 보더 22% + 흰 텍스트
///   • [PwButtonVariant.outlined]  — 투명 + 흰 보더 40% + 흰 텍스트
///   • [PwButtonVariant.text]      — 투명 + 흰 텍스트만
///   • [PwButtonVariant.danger]    — 빨강 글래스 22% + 빨강 보더 + 흰 텍스트
///
/// 2차 톤앤매너 교체 시(Neu*) 이 위젯 내부 구현만 바꾸면 화면 코드는 그대로다.
enum PwButtonVariant {
  /// 메인 CTA — 보라 배경 + 흰 텍스트.
  primary,

  /// 보조 — 흰 글래스 채움 + 흰 텍스트.
  secondary,

  /// 외곽선 — 흰 보더 + 흰 텍스트.
  outlined,

  /// 텍스트만 — 흰 텍스트 링크 톤.
  text,

  /// 위험 액션 — 빨강 글래스 + 흰 텍스트.
  danger,
}

class PwButton extends StatelessWidget {
  final VoidCallback? onPressed;
  final Widget child;
  final PwButtonVariant variant;
  final IconData? icon;
  final bool loading;
  final bool fullWidth;
  final EdgeInsetsGeometry? padding;

  const PwButton({
    super.key,
    required this.onPressed,
    required this.child,
    this.variant = PwButtonVariant.primary,
    this.icon,
    this.loading = false,
    this.fullWidth = true,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final disabled = onPressed == null || loading;
    final content = _content(context, scheme);
    final minSize = fullWidth ? const Size(double.infinity, 50) : const Size(0, 44);

    // 공통 가이드 — 모든 variant 의 라운드 + 텍스트 굵기 통일
    final shape = RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(AppTheme.rMd),
    );
    const textStyle = TextStyle(fontWeight: FontWeight.w600, fontSize: 16);

    switch (variant) {
      case PwButtonVariant.primary:
        // 2026-06-09 — 글래스 모피즘 primary: 보라 그라디언트 + 흰 보더 + 보라 glow.
        return _GlassPrimaryButton(
          onPressed: disabled ? null : onPressed,
          minSize: minSize,
          padding: padding,
          textStyle: textStyle,
          primary: scheme.primary,
          disabled: disabled,
          child: content,
        );
      case PwButtonVariant.secondary:
        return FilledButton(
          onPressed: disabled ? null : onPressed,
          style: FilledButton.styleFrom(
            minimumSize: minSize,
            padding: padding,
            backgroundColor: Colors.white.withValues(alpha: 0.14),
            foregroundColor: Colors.white,
            side: BorderSide(color: Colors.white.withValues(alpha: 0.22)),
            textStyle: textStyle,
            shape: shape,
          ),
          child: content,
        );
      case PwButtonVariant.outlined:
        return OutlinedButton(
          onPressed: disabled ? null : onPressed,
          style: OutlinedButton.styleFrom(
            minimumSize: minSize,
            padding: padding,
            foregroundColor: Colors.white,
            side: BorderSide(color: Colors.white.withValues(alpha: 0.40)),
            textStyle: textStyle,
            shape: shape,
          ),
          child: content,
        );
      case PwButtonVariant.text:
        return TextButton(
          onPressed: disabled ? null : onPressed,
          style: TextButton.styleFrom(
            minimumSize: fullWidth ? minSize : null,
            padding: padding,
            foregroundColor: Colors.white,
            textStyle: textStyle,
          ),
          child: content,
        );
      case PwButtonVariant.danger:
        // 흰 글래스 fill + 흐린 빨강 보더 — 위험은 보더로만 암시, 텍스트는 흰색.
        // 사용자 정책: "버튼 안 글씨는 모두 흰색" + "빨간 fill 거부감".
        return FilledButton(
          onPressed: disabled ? null : onPressed,
          style: FilledButton.styleFrom(
            minimumSize: minSize,
            padding: padding,
            backgroundColor: Colors.white.withValues(alpha: 0.14),
            foregroundColor: Colors.white,
            side: BorderSide(color: scheme.error.withValues(alpha: 0.55)),
            textStyle: textStyle,
            shape: shape,
          ),
          child: content,
        );
    }
  }

  Widget _content(BuildContext context, ColorScheme scheme) {
    if (loading) {
      // 모든 variant 흰 로딩 — 글래스 톤 통일 정책.
      return const SizedBox(
        width: 20,
        height: 20,
        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
      );
    }
    if (icon == null) return child;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 18),
        const SizedBox(width: 8),
        child,
      ],
    );
  }
}


/// 글래스 모피즘 Primary 버튼 — 보라 그라디언트 + 흰 보더 + 보라 glow.
/// (2026-06-09) PwButtonVariant.primary 의 시각 표현 교체용.
class _GlassPrimaryButton extends StatelessWidget {
  final VoidCallback? onPressed;
  final Size minSize;
  final EdgeInsetsGeometry? padding;
  final TextStyle textStyle;
  final Color primary;
  final Widget child;
  final bool disabled;

  const _GlassPrimaryButton({
    required this.onPressed,
    required this.minSize,
    required this.padding,
    required this.textStyle,
    required this.primary,
    required this.child,
    required this.disabled,
  });

  @override
  Widget build(BuildContext context) {
    final alpha = disabled ? 0.5 : 1.0;
    return ConstrainedBox(
      constraints: BoxConstraints(
        minWidth: minSize.width,
        minHeight: minSize.height,
      ),
      child: Opacity(
        opacity: alpha,
        child: DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                primary.withValues(alpha: 0.88),
                primary.withValues(alpha: 0.55),
              ],
            ),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: Colors.white.withValues(alpha: 0.28),
              width: 1,
            ),
            boxShadow: [
              BoxShadow(
                color: primary.withValues(alpha: 0.40),
                blurRadius: 18,
                offset: const Offset(0, 6),
              ),
            ],
          ),
          child: Material(
            color: Colors.transparent,
            borderRadius: BorderRadius.circular(14),
            child: InkWell(
              onTap: onPressed,
              borderRadius: BorderRadius.circular(14),
              splashColor: Colors.white.withValues(alpha: 0.18),
              highlightColor: Colors.white.withValues(alpha: 0.08),
              child: Padding(
                padding: padding ?? const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                child: Center(
                  child: DefaultTextStyle.merge(
                    style: textStyle.copyWith(color: Colors.white),
                    child: IconTheme.merge(
                      data: const IconThemeData(color: Colors.white),
                      child: child,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
