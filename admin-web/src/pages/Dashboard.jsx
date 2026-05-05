import React, { useEffect, useState } from 'react';
import {
  Building2, UserCheck, Radio, CreditCard, AlertTriangle,
} from 'lucide-react';
import { adminApi } from '../services/admin.js';
import './Dashboard.css';

const STAT_CARDS = [
  { key: 'facility_accounts_total', label: '전체 사장 계정',  icon: Building2,  color: '#2ea043' },
  { key: 'facility_accounts_pending', label: '승인 대기',     icon: UserCheck,  color: '#d29922' },
  { key: 'beacons_total',           label: '비콘 입고',         icon: Radio,      color: '#1f6feb' },
  { key: 'beacons_assigned',        label: '비콘 할당',         icon: Radio,      color: '#a371f7' },
  { key: 'payments_total_amount',   label: '결제 누적 (KRW)',   icon: CreditCard, color: '#2ea043', formatter: (v) => v?.toLocaleString?.() ?? v },
  { key: 'payments_failed_count',   label: '결제 실패',         icon: AlertTriangle, color: '#da3633' },
];

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let alive = true;
    setLoading(true);
    adminApi.statsOverview()
      .then((data) => {
        if (!alive) return;
        setStats(data.stats || data);
      })
      .catch((err) => {
        if (!alive) return;
        setError(err.message || '통계를 불러오지 못했습니다.');
      })
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, []);

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <h1 className="page-title">대시보드</h1>
        <p className="sub-title">PathWave 전체 현황을 한 눈에 확인합니다.</p>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      <div className="stat-grid">
        {STAT_CARDS.map(({ key, label, icon: Icon, color, formatter }) => (
          <div className="stat-card" key={key}>
            <div className="stat-icon" style={{ background: color + '22', color }}>
              <Icon size={20} strokeWidth={2} />
            </div>
            <div className="stat-content">
              <div className="stat-label">{label}</div>
              <div className="stat-value">
                {loading
                  ? <span className="skeleton" />
                  : (() => {
                      const v = stats?.[key];
                      if (v === undefined || v === null) return '—';
                      return formatter ? formatter(v) : v;
                    })()}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="card next-steps">
        <h3 style={{ marginTop: 0 }}>다음 PR 후보</h3>
        <ul>
          <li>비콘 인벤토리 — 입고/목록/할당 (PR #37)</li>
          <li>사장 가입 승인 — pending 목록 + verify (PR #37)</li>
          <li>배터리 모니터링 대시보드 (PR #38)</li>
          <li>시스템 공지 작성/관리 + 푸시 통합 (PR #38)</li>
          <li>결제·구독 관리 + 환불 (PR #39)</li>
        </ul>
      </div>
    </div>
  );
}
