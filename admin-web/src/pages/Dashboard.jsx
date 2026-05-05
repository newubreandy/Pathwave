import React, { useEffect, useState } from 'react';
import {
  Building2, UserCheck, Radio, RadioReceiver, CreditCard, Users, Wifi,
} from 'lucide-react';
import { adminApi } from '../services/admin.js';
import './Dashboard.css';

// 백엔드 응답: GET /api/admin/stats/overview → { success, cards: {...} }
const STAT_CARDS = [
  { key: 'total_facility_accounts',   label: '전체 사장 계정',  icon: Building2, color: '#2ea043' },
  { key: 'pending_facility_accounts', label: '승인 대기',       icon: UserCheck, color: '#d29922' },
  { key: 'total_facilities',          label: '활성 매장',       icon: Wifi,      color: '#a371f7' },
  { key: 'total_users',               label: '앱 사용자',       icon: Users,     color: '#1f6feb' },
  { key: 'total_beacons',             label: '비콘 입고',       icon: Radio,     color: '#1f6feb' },
  { key: 'active_beacons',            label: '비콘 활성',       icon: RadioReceiver, color: '#a371f7' },
  { key: 'mtd_paid_total_krw',        label: '이번 달 결제 (KRW)', icon: CreditCard, color: '#2ea043',
    formatter: (v) => (v ?? 0).toLocaleString() },
  { key: 'mtd_payment_count',         label: '이번 달 결제 건수', icon: CreditCard, color: '#1f6feb' },
];

export default function Dashboard() {
  const [cards, setCards] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let alive = true;
    setLoading(true);
    adminApi.statsOverview()
      .then((data) => {
        if (!alive) return;
        setCards(data.cards || {});
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
                      const v = cards?.[key];
                      if (v === undefined || v === null) return '—';
                      return formatter ? formatter(v) : v;
                    })()}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="card next-steps">
        <h3 style={{ marginTop: 0 }}>구현 현황</h3>
        <ul>
          <li><strong>✅ PR #36</strong> — 베이스라인 (Login + Dashboard)</li>
          <li><strong>✅ PR #37</strong> — Beacons 인벤토리 + Approvals 실 구현</li>
          <li>⬜ PR #38 — 배터리 모니터링 + 시스템 공지 + 푸시 통합</li>
          <li>⬜ PR #39 — 결제·구독 관리 + 환불</li>
        </ul>
      </div>
    </div>
  );
}
