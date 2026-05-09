import React from 'react';
import './MetricStrip.css';

/**
 * MetricStrip — 페이지 상단 요약.
 *
 * items: [{ label: '진행', value: 4, tone: 'accent' }, ...]
 *   tone: default | accent | warning | success | danger
 *
 * 3~4개까지만. 너무 많은 배지는 정보 hierarchy 망가짐.
 *
 * 예:
 *   진행 4건  ·  운영 4건  ·  점검 1건
 */
export default function MetricStrip({ items = [], className = '' }) {
  if (items.length === 0) return null;
  return (
    <div className={`pw-metricstrip ${className}`} role="list">
      {items.map((m, idx) => (
        <React.Fragment key={m.label}>
          {idx > 0 && <span className="pw-metricstrip-sep" aria-hidden="true">·</span>}
          <div
            className={`pw-metric pw-metric--${m.tone || 'default'}`}
            role="listitem"
          >
            <span className="pw-metric-label">{m.label}</span>
            <span className="pw-metric-value">{m.value}</span>
            {m.unit !== undefined && <span className="pw-metric-unit">{m.unit}</span>}
          </div>
        </React.Fragment>
      ))}
    </div>
  );
}
