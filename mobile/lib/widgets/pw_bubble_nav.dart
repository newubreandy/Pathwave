import 'dart:ui';

import 'package:flutter/material.dart';

import '../utils/app_theme.dart';

/// PwBubbleNav — 선택 탭이 원형 버블로 돌출되는 하단 네비 (2026-06-12).
///
/// 디자인 (사용자 레퍼런스: Micro-Interaction bottom bar)
/// - 바: 기존 글래스 톤 유지 (backdrop blur + 검정 18% 틴트, 풀폭)
/// - 선택 탭: 보라 그라디언트 원형 버블이 바 위로 돌출 + 바에 오목 노치
/// - 탭 전환: 버블/노치가 옆으로 슬라이드 (easeOutBack 마이크로 인터랙션)
/// - 라벨: 선택 탭만 버블 아래 표시 (기존 onlyShowSelected 정책 유지)
class PwBubbleNavItem {
  final IconData icon;
  final IconData selectedIcon;
  final String label;

  /// 아이콘 우상단 뱃지 (미읽음 수 등). null/0 = 미표시.
  final int? badgeCount;

  const PwBubbleNavItem({
    required this.icon,
    required this.selectedIcon,
    required this.label,
    this.badgeCount,
  });
}

class PwBubbleNav extends StatelessWidget {
  final List<PwBubbleNavItem> items;
  final int selectedIndex;
  final ValueChanged<int> onSelected;

  const PwBubbleNav({
    super.key,
    required this.items,
    required this.selectedIndex,
    required this.onSelected,
  });

  static const double _barHeight = 64;
  static const double _bubbleSize = 54;
  static const double _bubbleLift = 22;   // 바 위로 돌출량

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewPadding.bottom;
    final totalHeight = _barHeight + _bubbleLift + bottomInset;

    // implicit 애니메이션 — 선택 index 를 double 로 트윈하면
    // 노치(클리퍼)와 버블이 같은 t 로 부드럽게 슬라이드.
    return TweenAnimationBuilder<double>(
      tween: Tween(end: selectedIndex.toDouble()),
      duration: const Duration(milliseconds: 350),
      curve: Curves.easeOutBack,
      builder: (context, t, _) {
        return SizedBox(
          height: totalHeight,
          child: LayoutBuilder(builder: (context, box) {
            final slotW = box.maxWidth / items.length;
            final centerX = slotW * (t + 0.5);
            return Stack(
              clipBehavior: Clip.none,
              children: [
                // ── 글래스 바 (노치 파임) ──
                Positioned(
                  left: 0,
                  right: 0,
                  top: _bubbleLift,
                  bottom: 0,
                  child: ClipPath(
                    clipper: _NotchClipper(centerX: centerX),
                    child: BackdropFilter(
                      filter: ImageFilter.blur(sigmaX: 24, sigmaY: 24),
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          color: Colors.black.withValues(alpha: 0.18),
                        ),
                      ),
                    ),
                  ),
                ),
                // ── 돌출 버블 (보라 글래스) ──
                Positioned(
                  left: centerX - _bubbleSize / 2,
                  top: 0,
                  child: Container(
                    width: _bubbleSize,
                    height: _bubbleSize,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [
                          AppTheme.primaryLight.withValues(alpha: 0.95),
                          AppTheme.primary,
                        ],
                      ),
                      border: Border.all(
                          color: Colors.white.withValues(alpha: 0.55),
                          width: 1.5),
                      boxShadow: [
                        BoxShadow(
                          color: AppTheme.primary.withValues(alpha: 0.45),
                          blurRadius: 16,
                          offset: const Offset(0, 6),
                        ),
                      ],
                    ),
                    child: Icon(
                      // 버블 안 아이콘은 슬라이드 도착점(선택 탭) 기준.
                      items[selectedIndex].selectedIcon,
                      color: Colors.white,
                      size: 26,
                    ),
                  ),
                ),
                // ── 탭 터치 영역 + 미선택 아이콘 + 선택 라벨 ──
                Positioned(
                  left: 0,
                  right: 0,
                  top: _bubbleLift,
                  bottom: bottomInset,
                  child: Row(
                    children: [
                      for (int i = 0; i < items.length; i++)
                        Expanded(
                          child: InkWell(
                            onTap: () => onSelected(i),
                            customBorder: const StadiumBorder(),
                            child: i == selectedIndex
                                // 선택 탭: 아이콘은 버블이 담당 — 라벨만 하단에.
                                ? Align(
                                    alignment: Alignment.bottomCenter,
                                    child: Padding(
                                      padding:
                                          const EdgeInsets.only(bottom: 8),
                                      child: Text(
                                        items[i].label,
                                        style: const TextStyle(
                                          color: Colors.white,
                                          fontSize: 11,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ),
                                  )
                                : Center(
                                    child: _Badge(
                                      count: items[i].badgeCount,
                                      child: Icon(
                                        items[i].icon,
                                        color: Colors.white
                                            .withValues(alpha: 0.85),
                                        size: 24,
                                      ),
                                    ),
                                  ),
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            );
          }),
        );
      },
    );
  }
}

/// 바 상단에 버블 주위로 오목한 노치를 파는 클리퍼.
class _NotchClipper extends CustomClipper<Path> {
  final double centerX;
  _NotchClipper({required this.centerX});

  @override
  Path getClip(Size size) {
    const r = PwBubbleNav._bubbleSize / 2 + 7;   // 버블보다 살짝 큰 반경
    final p = Path()..moveTo(0, 0);
    // 좌측 → 노치 시작
    p.lineTo(centerX - r - 14, 0);
    // 오목 곡선 (양 어깨 cubic + 중앙 arc)
    p.cubicTo(centerX - r, 0, centerX - r + 4, r * 0.82,
        centerX, r * 0.82);
    p.cubicTo(centerX + r - 4, r * 0.82, centerX + r, 0,
        centerX + r + 14, 0);
    // 우측 끝 → 아래 → 닫기
    p.lineTo(size.width, 0);
    p.lineTo(size.width, size.height);
    p.lineTo(0, size.height);
    p.close();
    return p;
  }

  @override
  bool shouldReclip(_NotchClipper old) => old.centerX != centerX;
}

class _Badge extends StatelessWidget {
  final int? count;
  final Widget child;
  const _Badge({required this.count, required this.child});

  @override
  Widget build(BuildContext context) {
    if (count == null || count! <= 0) return child;
    return Stack(
      clipBehavior: Clip.none,
      children: [
        child,
        Positioned(
          right: -7,
          top: -5,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
            decoration: BoxDecoration(
              color: AppTheme.primary,
              borderRadius: BorderRadius.circular(999),
              border: Border.all(color: Colors.white, width: 1),
            ),
            constraints: const BoxConstraints(minWidth: 16),
            child: Text(
              count! > 99 ? '99+' : '$count',
              textAlign: TextAlign.center,
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 9,
                  fontWeight: FontWeight.w700),
            ),
          ),
        ),
      ],
    );
  }
}
