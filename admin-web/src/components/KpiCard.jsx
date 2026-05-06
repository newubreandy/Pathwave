import React from 'react';

/**
 * PR #69 — KPI 카드 (다크 프리미엄).
 * 제목 + 큰 값 + 델타 배지 + (옵션) 미니 스파크라인 + 아이콘.
 */
export default function KpiCard({
  title, value, unit, delta, deltaPositive = true, icon: Icon,
  spark, color = 'info',
}) {
  const colorVar = {
    info:    'var(--info)',
    accent:  'var(--accent)',
    primary: 'var(--primary)',
    warn:    'var(--warn)',
    danger:  'var(--danger)',
  }[color] || 'var(--info)';

  return (
    <div className="card">
      <div style={{
        display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
        marginBottom: 4,
      }}>
        <div className="card-title">{title}</div>
        {Icon && (
          <div style={{
            width: 32, height: 32, borderRadius: 10,
            background: `color-mix(in oklab, ${colorVar} 14%, transparent)`,
            display: 'grid', placeItems: 'center',
            border: '1px solid var(--border)',
          }}>
            <Icon size={16} color={colorVar} />
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 8 }}>
        <span className="card-value">{value}</span>
        {unit && <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>{unit}</span>}
      </div>

      {(delta != null || spark) && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {delta != null && (
            <span className={'card-delta ' + (deltaPositive ? '' : 'negative')}>
              {deltaPositive ? '↑' : '↓'} {delta}
            </span>
          )}
          {spark && <Sparkline points={spark} color={colorVar} />}
        </div>
      )}
    </div>
  );
}

/**
 * 미니 SVG 스파크라인 — 0~100 정규화된 숫자 배열을 받음.
 */
export function Sparkline({ points, color = 'var(--info)', height = 32 }) {
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

  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none"
         style={{ height, flex: 1, minWidth: 60 }}>
      <defs>
        <linearGradient id={`grad-${color.replace(/[^a-z]/gi, '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stopColor={color} stopOpacity="0.4" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={fillPath} fill={`url(#grad-${color.replace(/[^a-z]/gi, '')})`} />
      <path d={path} fill="none" stroke={color} strokeWidth="1.5"
            strokeLinecap="round" strokeLinejoin="round"
            style={{ filter: `drop-shadow(0 0 3px ${color})` }} />
    </svg>
  );
}
