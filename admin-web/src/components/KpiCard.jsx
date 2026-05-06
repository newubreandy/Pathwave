import React from 'react';

/**
 * PR #69 v2 — 미니멀 KPI 카드.
 * 컬러는 델타 배지에만 (녹색=상승, 빨강=하락). 아이콘은 무채.
 */
export default function KpiCard({
  title, value, unit, delta, deltaPositive = true, icon: Icon,
  spark,
}) {
  return (
    <div className="card">
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
    </div>
  );
}

/**
 * 미니 SVG 스파크라인 — 녹색 단일 톤.
 */
export function Sparkline({ points, color = 'var(--accent)', height = 40 }) {
  if (!points || points.length < 2) return null;
  const w = 100, h = 100;
  const max = Math.max(...points, 1);
  const min = Math.min(...points, 0);
  const range = max - min || 1;
  const step = w / (points.length - 1);
  const path = points.map((p, i) => {
    const x = i * step;
    const y = h - ((p - min) / range) * h;
    return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
  }).join(' ');
  const fillPath = `${path} L ${w} ${h} L 0 ${h} Z`;
  const id = `g${Math.random().toString(36).slice(2,8)}`;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none"
         style={{ height, flex: 1, minWidth: 80 }}>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stopColor={color} stopOpacity="0.25" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={fillPath} fill={`url(#${id})`} />
      <path d={path} fill="none" stroke={color} strokeWidth="1.6"
            strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
