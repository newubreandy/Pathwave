import React from 'react';
import { Link } from 'react-router-dom';

/**
 * PR #69 v2 — 미니멀 KPI 카드.
 * 컬러는 델타 배지에만 (녹색=상승, 빨강=하락). 아이콘은 무채.
 *
 * 2026-05-27: `to` prop 추가 — 카드 클릭 시 해당 라우트로 이동 + hover lift.
 */
export default function KpiCard({
  title, value, unit, delta, deltaPositive = true, icon: Icon,
  spark, to,
}) {
  const inner = (
    <>
      <div style={{
        display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
        marginBottom: 8,
      }}>
        <div className="card-title" style={{ marginBottom: 0 }}>{title}</div>
        {Icon && (
          <div style={{
            width: 36, height: 36, borderRadius: 12,
            background: 'var(--bg-4)',
            display: 'grid', placeItems: 'center',
            border: '1px solid var(--border)',
          }}>
            <Icon size={18} color="var(--text-muted)" strokeWidth={1.75} />
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 14 }}>
        <span className="card-value">{value}</span>
        {unit && <span style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-md)' }}>{unit}</span>}
      </div>

      {(delta != null || spark) && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {delta != null && (
            <span className={'card-delta ' + (deltaPositive ? '' : 'negative')}>
              {deltaPositive ? '↑' : '↓'} {delta}
            </span>
          )}
          {spark && <Sparkline points={spark} />}
        </div>
      )}
    </>
  );

  if (to) {
    return (
      <Link to={to} className="card card--clickable"
            aria-label={`${title} 상세로 이동`}>
        {inner}
      </Link>
    );
  }
  return <div className="card">{inner}</div>;
}

/**
 * 미니 SVG 스파크라인 — 녹색 단일 톤. Catmull-Rom 스플라인으로 부드러운 곡선.
 */
export function Sparkline({ points, color = 'var(--accent)', height = 40 }) {
  if (!points || points.length < 2) return null;
  const w = 100, h = 100;
  const padY = 4;                       // stroke 가 svg 위/아래로 잘리지 않도록 여유
  const usableH = h - 2 * padY;
  const max = Math.max(...points, 1);
  const min = Math.min(...points, 0);
  const range = max - min || 1;
  const step = w / (points.length - 1);
  const xy = points.map((p, i) => ({
    x: i * step,
    y: padY + (max - p) / range * usableH,
  }));

  // Catmull-Rom → cubic Bezier 변환 (tension 0.5 → /6).
  const segs = [];
  for (let i = 0; i < xy.length - 1; i++) {
    const p0 = xy[i - 1] || xy[i];
    const p1 = xy[i];
    const p2 = xy[i + 1];
    const p3 = xy[i + 2] || p2;
    const c1x = p1.x + (p2.x - p0.x) / 6;
    const c1y = p1.y + (p2.y - p0.y) / 6;
    const c2x = p2.x - (p3.x - p1.x) / 6;
    const c2y = p2.y - (p3.y - p1.y) / 6;
    segs.push(`C ${c1x.toFixed(1)} ${c1y.toFixed(1)}, ${c2x.toFixed(1)} ${c2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`);
  }
  const path = `M ${xy[0].x.toFixed(1)} ${xy[0].y.toFixed(1)} ${segs.join(' ')}`;
  const fillPath = `${path} L ${w} ${h} L 0 ${h} Z`;
  const id = `g${Math.random().toString(36).slice(2,8)}`;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none"
         width="100%"
         style={{ height, display: 'block', flex: 1, minWidth: 80, overflow: 'visible' }}>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stopColor={color} stopOpacity="0.10" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={fillPath} fill={`url(#${id})`} />
      <path d={path} fill="none" stroke={color} strokeWidth="2"
            vectorEffect="non-scaling-stroke"
            strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
