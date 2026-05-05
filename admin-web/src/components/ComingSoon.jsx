import React from 'react';
import './ComingSoon.css';

export default function ComingSoon({ Icon, prNote, endpoints = [] }) {
  return (
    <div className="card coming-soon">
      <div className="cs-icon">
        {Icon ? <Icon size={32} strokeWidth={1.75} /> : null}
      </div>
      <div className="cs-title">UI 구현 예정</div>
      {prNote && <div className="cs-pr">{prNote}</div>}
      {endpoints.length > 0 && (
        <div className="cs-endpoints">
          <div className="cs-endpoints-label">백엔드 API (이미 구현됨)</div>
          <pre>{endpoints.join('\n')}</pre>
        </div>
      )}
    </div>
  );
}
