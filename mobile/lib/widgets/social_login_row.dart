import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_svg/flutter_svg.dart';
import 'package:simple_icons/simple_icons.dart';

import '../services/i18n_service.dart';
import '../utils/neu_theme.dart';

/// PR #68 — Google / Apple / Facebook / Kakao / Naver 5종 소셜 로그인 버튼.
/// 로그인 화면 + 회원가입 화면 양쪽에서 동일하게 사용.
class SocialLoginRow extends StatelessWidget {
  final bool busy;
  final VoidCallback? onGoogle;
  final VoidCallback? onApple;
  final VoidCallback? onFacebook;
  final VoidCallback? onKakao;
  final VoidCallback? onNaver;

  const SocialLoginRow({
    super.key,
    this.busy = false,
    this.onGoogle, this.onApple, this.onFacebook, this.onKakao, this.onNaver,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        // 1차: assets/brand_logos/{name}.svg (공식 brand 가이드 SVG 다운로드 시 자동 적용)
        // 2차: simple_icons 단색 fallback (CC0 라이센스, simple-icons.org)
        _socialBtn(
          color: const Color(0xFFFFFFFF),
          icon: const _BrandIcon(
            brand: 'google',
            fallback: SimpleIcons.google,
            fallbackColor: Color(0xFF4285F4),
          ),
          label: 'Google',
          onTap: busy ? null : onGoogle,
        ),
        _socialBtn(
          color: const Color(0xFF000000),
          icon: const _BrandIcon(
            brand: 'apple',
            fallback: SimpleIcons.apple,
            fallbackColor: Colors.white,
          ),
          label: 'Apple',
          onTap: busy ? null : onApple,
          labelColor: NeuTheme.textPrimary,
        ),
        _socialBtn(
          color: const Color(0xFF1877F2),
          icon: const _BrandIcon(
            brand: 'facebook',
            fallback: SimpleIcons.facebook,
            fallbackColor: Colors.white,
          ),
          label: 'Facebook',
          onTap: busy ? null : onFacebook,
        ),
        _socialBtn(
          color: const Color(0xFFFEE500),
          icon: const _BrandIcon(
            brand: 'kakao',
            fallback: SimpleIcons.kakaotalk,
            fallbackColor: Color(0xFF3C1E1E),
          ),
          label: 'Kakao',
          onTap: busy ? null : onKakao,
        ),
        _socialBtn(
          color: const Color(0xFF03C75A),
          icon: const _BrandIcon(
            brand: 'naver',
            fallback: SimpleIcons.naver,
            fallbackColor: Colors.white,
          ),
          label: 'Naver',
          onTap: busy ? null : onNaver,
        ),
      ],
    );
  }

  Widget _socialBtn({
    required Color color,
    required Widget icon,
    required String label,
    VoidCallback? onTap,
    Color? labelColor,
  }) {
    // Apple HIG / Material 3 / WCAG 2.5.5 — 터치 영역 ≥44×44pt, 의미있는 레이블.
    return Column(
      children: [
        Semantics(
          button: true,
          enabled: onTap != null,
          label: '$label ${I18nService.instance.t('mobile.common.login_with_suffix', defaultValue: '로 로그인')}',
          child: Material(
            color: Colors.transparent,
            shape: const CircleBorder(),
            child: InkWell(
              onTap: onTap,
              customBorder: const CircleBorder(),
              child: Container(
                width: 56, height: 56,
                decoration: BoxDecoration(
                  color: color,
                  shape: BoxShape.circle,
                  // 가이드 — 흐린 그림자(alpha 12%, blur 16, offset 4).
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.12),
                      blurRadius: 16,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                // ClipOval — PNG/SVG 의 사각형 모서리(흰 배경 등) 잘라서 정원만 노출.
                child: ClipOval(child: icon),
              ),
            ),
          ),
        ),
        const SizedBox(height: 6),
        Text(label,
          style: TextStyle(
            fontSize: 11,
            color: labelColor ?? NeuTheme.textSecondary,
            fontWeight: FontWeight.w500,
          )),
      ],
    );
  }
}

/// 브랜드 아이콘 헬퍼.
/// 1차: `assets/brand_logos/{brand}.svg` (사용자가 공식 가이드에서 받은 SVG)
/// 2차: `fallback` IconData (simple_icons — CC0 단색)
///
/// SVG 자체에 브랜드 색상이 인코딩되어 있으므로 SVG 로드 시 색 override 하지 않는다.
/// fallback 만 `fallbackColor` 적용.
class _BrandIcon extends StatelessWidget {
  final String brand;
  final IconData fallback;
  final Color fallbackColor;
  final double size;

  const _BrandIcon({
    required this.brand,
    required this.fallback,
    required this.fallbackColor,
    this.size = 24,
  });

  /// 1순위 SVG, 2순위 PNG, 3순위 simple_icons 단색 fallback.
  /// 파일명 규칙: `{brand}.svg|png` 또는 `logo_{brand}.svg|png`.
  Future<String?> _resolveAsset() async {
    for (final prefix in const ['', 'logo_']) {
      for (final ext in const ['svg', 'png']) {
        final path = 'assets/brand_logos/$prefix$brand.$ext';
        try {
          await rootBundle.load(path);
          return path;
        } catch (_) {}
      }
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<String?>(
      future: _resolveAsset(),
      builder: (ctx, snap) {
        final path = snap.data;
        if (path != null) {
          // 원형 컨테이너(56) 가득 — ClipOval 부모 제약을 그대로 받음.
          if (path.endsWith('.svg')) {
            return SvgPicture.asset(path, fit: BoxFit.cover,
                width: double.infinity, height: double.infinity);
          }
          return Image.asset(path, fit: BoxFit.cover,
              width: double.infinity, height: double.infinity);
        }
        // simple_icons 단색 fallback — 가운데 작게.
        return Center(child: Icon(fallback, color: fallbackColor, size: size));
      },
    );
  }
}
