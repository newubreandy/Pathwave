/// 시즌별 흩날리는 (정적) 파티클 — 배경 위에 얹는 순수 시각 효과 (인터랙티브 X).
///
/// 봄: 분홍 꽃잎 / 여름: 물방울 / 가을: 단풍 / 겨울: 눈송이.
///
/// ⭐ 정적(애니메이션 없음): 계절별 고정 시드로 "흩날리는 한 장면"을 고정 렌더한다.
///   (사용자 결정 2026-06-04 — 바탕화면 배경은 움직이지 않는다.)
///   depth(흐림·크기·투명도) 레이어로 앞뒤 깊이감을, 그라데이션으로 입체감을 준다.
///   추후 슈퍼어드민이 사실적 배경 이미지를 등록하면 SeasonalBackground 가 그
///   이미지를 우선 사용하므로(activeTheme), 이 위젯은 fallback 시각 효과로 남는다.
/// IgnorePointer 로 감싸므로 터치/스크롤은 통과.
library;

import 'dart:math';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';

import '../utils/season.dart';

class SeasonalParticles extends StatelessWidget {
  final Season season;
  final int density;

  const SeasonalParticles({
    super.key,
    required this.season,
    this.density = 18,
  });

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: RepaintBoundary(
        child: CustomPaint(
          size: Size.infinite,
          painter: _ParticlePainter(season: season, density: density),
          isComplex: true, // 정적이라 raster 캐시 효과를 크게 받는다.
        ),
      ),
    );
  }
}

/// 계절별 고정 시드 — 재시작·rebuild 시 항상 동일한 배치(깜빡임 방지).
int _seedFor(Season s) {
  switch (s) {
    case Season.spring: return 1101;
    case Season.summer: return 2202;
    case Season.autumn: return 3303;
    case Season.winter: return 4404;
  }
}

class _Particle {
  final double x;        // 0~1 가로 비율
  final double y;        // 0~1 세로 비율
  final double size;     // px
  final double rot;      // radian
  final double blur;     // maskFilter sigma (0=선명, 클수록 뒤쪽)
  final double opacity;  // 0~1
  final Color colorA;    // 그라데이션 진한 쪽
  final Color colorB;    // 그라데이션 밝은 쪽

  const _Particle({
    required this.x,
    required this.y,
    required this.size,
    required this.rot,
    required this.blur,
    required this.opacity,
    required this.colorA,
    required this.colorB,
  });
}

List<_Particle> _buildParticles(Season season, int density) {
  final rand = Random(_seedFor(season));
  final pairs = _paletteFor(season);
  return List.generate(density, (_) {
    final depth = rand.nextDouble();          // 0=뒤(흐림·반투명) ~ 1=앞(선명)
    final near = depth > 0.5;
    final pair = pairs[rand.nextInt(pairs.length)];
    return _Particle(
      x: rand.nextDouble(),
      y: rand.nextDouble(),
      // 원근: 가까울수록 큼. 28~74px 에 개체별 ±15%.
      size: ui.lerpDouble(28, 74, depth)! * (0.85 + rand.nextDouble() * 0.3),
      rot: rand.nextDouble() * pi * 2,
      // 뒤쪽일수록 흐림. 앞쪽(near)은 거의 선명.
      blur: near
          ? rand.nextDouble() * 1.0
          : ui.lerpDouble(7.0, 2.0, depth / 0.5)!,
      opacity: near ? 0.80 + rand.nextDouble() * 0.16 : 0.32 + depth * 0.6,
      colorA: pair[0],
      colorB: pair[1],
    );
  });
}

/// (진한 쪽, 밝은 쪽) 색 쌍 — 꽃잎/요소에 그라데이션으로 입체감.
/// 봄 팔레트는 레퍼런스(핫핑크~마젠타)에 맞춰 채도를 높였다.
List<List<Color>> _paletteFor(Season s) {
  switch (s) {
    case Season.spring:
      return const [
        [Color(0xFFDB2777), Color(0xFFF9A8D4)], // 마젠타 → 연분홍
        [Color(0xFFEC4899), Color(0xFFFBCFE8)],
        [Color(0xFFF472B6), Color(0xFFFCE7F3)],
      ];
    case Season.summer:
      return const [
        [Color(0xFF22D3EE), Color(0xFFCFFAFE)], // 청록 → 연하늘
        [Color(0xFF38BDF8), Color(0xFFE0F2FE)],
        [Color(0xFF67E8F9), Color(0xFFFFFFFF)],
      ];
    case Season.autumn:
      return const [
        [Color(0xFFEA580C), Color(0xFFFDBA74)], // 주황 → 살구
        [Color(0xFFDC2626), Color(0xFFFCA5A5)], // 빨강 → 연빨강
        [Color(0xFFD97706), Color(0xFFFCD34D)], // 황토 → 노랑
      ];
    case Season.winter:
      return const [
        [Color(0xFFFFFFFF), Color(0xFFFFFFFF)], // 흰 눈
        [Color(0xFFE0F2FE), Color(0xFFFFFFFF)],
        [Color(0xFFC7E8FF), Color(0xFFF0F9FF)],
      ];
  }
}

class _ParticlePainter extends CustomPainter {
  final Season season;
  final int density;
  final List<_Particle> _particles;

  _ParticlePainter({required this.season, required this.density})
      : _particles = _buildParticles(season, density);

  @override
  void paint(Canvas canvas, Size size) {
    // 흐린(뒤) 것부터 그려 깊이감 — 선명한 앞쪽이 위에 겹친다.
    final ordered = [..._particles]..sort((a, b) => b.blur.compareTo(a.blur));
    for (final p in ordered) {
      canvas.save();
      canvas.translate(p.x * size.width, p.y * size.height);
      canvas.rotate(p.rot);
      _drawShape(canvas, p);
      canvas.restore();
    }
  }

  void _drawShape(Canvas canvas, _Particle p) {
    switch (season) {
      case Season.spring:
        _drawPetal(canvas, p);
        break;
      case Season.summer:
        _drawDrop(canvas, p);
        break;
      case Season.autumn:
        _drawMaple(canvas, p);
        break;
      case Season.winter:
        _drawSnow(canvas, p);
        break;
    }
  }

  /// 위→아래 그라데이션 fill (+ blur). 꽃잎·물방울·단풍 공용.
  Paint _gradientFill(_Particle p, double top, double bottom) {
    final paint = Paint()
      ..shader = ui.Gradient.linear(
        Offset(0, top),
        Offset(0, bottom),
        [
          p.colorA.withValues(alpha: p.opacity),
          p.colorB.withValues(alpha: p.opacity),
        ],
      );
    if (p.blur > 0.05) {
      paint.maskFilter = MaskFilter.blur(BlurStyle.normal, p.blur);
    }
    return paint;
  }

  void _drawPetal(Canvas canvas, _Particle p) {
    // 길쭉한 꽃잎 — 양 끝이 좁은 잎사귀형.
    final r = p.size * 0.5;
    final path = ui.Path()
      ..moveTo(0, -r)
      ..cubicTo(r * 0.66, -r * 0.65, r * 0.5, r * 0.75, 0, r)
      ..cubicTo(-r * 0.5, r * 0.75, -r * 0.66, -r * 0.65, 0, -r)
      ..close();
    canvas.drawPath(path, _gradientFill(p, -r, r));
  }

  void _drawDrop(Canvas canvas, _Particle p) {
    // 위가 뾰족, 아래가 둥근 물방울.
    final s = p.size * 0.6;
    final path = ui.Path()
      ..moveTo(0, -s)
      ..cubicTo(s * 0.78, -s * 0.05, s * 0.62, s, 0, s)
      ..cubicTo(-s * 0.62, s, -s * 0.78, -s * 0.05, 0, -s)
      ..close();
    canvas.drawPath(path, _gradientFill(p, -s, s));
    // 앞쪽 물방울에만 작은 하이라이트 → 유리알 느낌.
    if (p.blur < 1.5) {
      final hl = Paint()..color = Colors.white.withValues(alpha: p.opacity * 0.55);
      canvas.drawCircle(Offset(-s * 0.22, -s * 0.12), s * 0.16, hl);
    }
  }

  void _drawMaple(Canvas canvas, _Particle p) {
    // 단풍잎 — 5각 별 간략화.
    final outer = p.size * 0.5;
    final inner = p.size * 0.2;
    final path = ui.Path();
    for (int i = 0; i < 10; i++) {
      final rr = i.isEven ? outer : inner;
      final a = -pi / 2 + i * pi / 5;
      final pt = Offset(rr * cos(a), rr * sin(a));
      i == 0 ? path.moveTo(pt.dx, pt.dy) : path.lineTo(pt.dx, pt.dy);
    }
    path.close();
    canvas.drawPath(path, _gradientFill(p, -outer, outer));
  }

  void _drawSnow(Canvas canvas, _Particle p) {
    // 눈송이 — 6방향 가지 + 중앙 점.
    final r = p.size * 0.42;
    final paint = Paint()
      ..color = p.colorB.withValues(alpha: p.opacity)
      ..style = PaintingStyle.stroke
      ..strokeWidth = max(1.2, p.size * 0.07)
      ..strokeCap = StrokeCap.round;
    if (p.blur > 0.05) {
      paint.maskFilter = MaskFilter.blur(BlurStyle.normal, p.blur);
    }
    for (int i = 0; i < 6; i++) {
      final a = i * pi / 3;
      canvas.drawLine(Offset.zero, Offset(r * cos(a), r * sin(a)), paint);
    }
    canvas.drawCircle(Offset.zero, r * 0.16, paint..style = PaintingStyle.fill);
  }

  @override
  bool shouldRepaint(_ParticlePainter old) =>
      old.season != season || old.density != density;
}
