import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Building2, UserCheck, Radio, RadioReceiver, CreditCard, Users, Wifi,
  TrendingUp, Battery, Megaphone,
} from 'lucide-react';
import { adminApi } from '../services/admin.js';
import KpiCard, { Sparkline } from '../components/KpiCard.jsx';

const DEMO_SPARK = (seed) => Array.from({ length: 18 },
  (_, i) => 30 + Math.sin((i + seed) * 0.6) * 14 + Math.random() * 6);

const STAT_CARDS = [
  { key: 'total_facility_accounts',   label: '전체 사장 계정', icon: Building2 },
  { key: 'pending_facility_accounts', label: '승인 대기',     icon: UserCheck },
  { key: 'total_facilities',          label: '활성 매장',     icon: Wifi },
  { key: 'total_users',               label: '앱 사용자',     icon: Users },
  { key: 'total_beacons',             label: '비콘 입고',     icon: Radio },
  { key: 'active_beacons',            label: '비콘 활성',     icon: RadioReceiver },
  { key: 'mtd_paid_total_krw',        label: '이번 달 결제',  icon: CreditCard,
    unit: 'KRW', formatter: (v) => (v ?? 0).toLocaleString() },
  { key: 'mtd_payment_count',         label: '결제 건수',     icon: TrendingUp },
];

const TIME_RANGES = ['1W', '1M', '6M', '1Y', 'All Time'];

export default function Dashboard() {
  const [cards, setCards] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [range, setRange] = useState('1M');

  useEffect(() => {
    let alive = true;
    setLoading(true);
    adminApi.statsOverview()
      .then((data) => { if (alive) setCards(data.cards || {}); })
      .catch((err) => {
        if (alive && !err.previewMode) setError(err.message || '통계를 불러오지 못했습니다.');
      })
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, []);

  function v(key, formatter) {
    if (loading) return '—';
    const val = cards?.[key];
    if (val === undefined || val === null) return '—';
    return formatter ? formatter(val) : val.toLocaleString();
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-breadcrumb">
            <span>Home</span><span className="sep">/</span>
            <span className="current">Dashboard</span>
          </div>
          <h1 className="page-title">전체 현황</h1>
        </div>
        <div className="pill-group">
          {TIME_RANGES.map(r => (
            <button key={r}
              className={'pill' + (range === r ? ' active' : '')}
              onClick={() => setRange(r)}>{r}</button>
          ))}
        </div>
      </div>

      {error && (
        <div className="card" style={{
          borderColor: 'var(--danger)', color: 'var(--badge-inactive-fg)',
          marginBottom: 24,
        }}>
          {error}
        </div>
      )}

      {/* 1행: 메인 차트 + KPI 2개 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)',
        gap: 24, marginBottom: 24,
      }}>
        <div className="card" style={{ minHeight: 320, display: 'flex', flexDirection: 'column' }}>
          <div className="card-title">이번 달 결제 합계</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 14, marginBottom: 24 }}>
            <span className="card-value" style={{ fontSize: 'var(--fs-4xl)' }}>
              ₩ {v('mtd_paid_total_krw', (n) => n.toLocaleString())}
            </span>
            <span className="card-delta">↑ 14.3%</span>
          </div>
          <div style={{ flex: 1, display: 'flex', minHeight: 180 }}>
            <Sparkline points={DEMO_SPARK(0)} height={200} />
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <KpiCard title="앱 사용자" value={v('total_users')}
            delta="+12%" deltaPositive icon={Users}
            spark={DEMO_SPARK(2)} />
          <KpiCard title="활성 비콘" value={v('active_beacons')}
            delta="+3%" deltaPositive icon={RadioReceiver}
            spark={DEMO_SPARK(4)} />
        </div>
      </div>

      <div className="kpi-grid">
        {STAT_CARDS.map(({ key, label, icon, unit, formatter }) => (
          <KpiCard
            key={key}
            title={label}
            value={v(key, formatter)}
            unit={unit}
            icon={icon}
          />
        ))}
      </div>

      <div style={{
        display: 'grid', gap: 24,
        gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)',
        marginTop: 24,
      }}>
        <div className="card" style={{ padding: 32 }}>
          <div className="card-title" style={{ marginBottom: 24 }}>최근 시스템 활동</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <ActivityRow icon={UserCheck}
              title="신규 사장 가입 승인 대기" subtitle="3건" time="방금" />
            <ActivityRow icon={Radio}
              title="비콘 50개 신규 입고" subtitle="VPS-2 / Frankfurt" time="2h ago" />
            <ActivityRow icon={Battery}
              title="배터리 20% 미만 비콘" subtitle="7개 — 점검 필요" time="Yesterday" />
            <ActivityRow icon={Megaphone}
              title="시스템 공지 발행됨" subtitle="이용약관 v2.1" time="2d ago" />
          </div>
        </div>

        <div className="card" style={{ padding: 32 }}>
          <div className="card-title" style={{ marginBottom: 24 }}>빠른 작업</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <QuickAction icon={UserCheck} label="가입 승인" to="/dashboard/approvals" />
            <QuickAction icon={Radio} label="비콘 등록" to="/dashboard/beacons" />
            <QuickAction icon={Megaphone} label="공지 발행" to="/dashboard/announcements" />
            <QuickAction icon={CreditCard} label="결제 환불" to="/dashboard/payments" />
          </div>
        </div>
      </div>
    </div>
  );
}

function ActivityRow({ icon: Icon, title, subtitle, time }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
      <div style={{
        width: 52, height: 52, borderRadius: 14,
        background: 'var(--bg-4)',
        border: '1px solid var(--border)',
        display: 'grid', placeItems: 'center', flexShrink: 0,
      }}>
        <Icon size={24} color="var(--text-muted)" strokeWidth={1.75} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 'var(--fs-lg)', color: 'var(--text)', fontWeight: 500 }}>{title}</div>
        <div style={{ fontSize: 'var(--fs-md)', color: 'var(--text-muted)', marginTop: 4 }}>{subtitle}</div>
      </div>
      <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-hint)' }}>{time}</div>
    </div>
  );
}

function QuickAction({ icon: Icon, label, to }) {
  return (
    <Link to={to} style={{
      display: 'flex', alignItems: 'center', gap: 16,
      padding: '24px 22px',
      background: 'var(--bg-4)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-md)',
      transition: 'background 0.15s, border-color 0.15s',
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.background = 'var(--bg-hover)';
      e.currentTarget.style.borderColor = 'var(--border-strong)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.background = 'var(--bg-4)';
      e.currentTarget.style.borderColor = 'var(--border)';
    }}>
      <Icon size={22} color="var(--text-muted)" strokeWidth={1.75} />
      <span style={{ fontSize: 'var(--fs-lg)', fontWeight: 500 }}>{label}</span>
    </Link>
  );
}
