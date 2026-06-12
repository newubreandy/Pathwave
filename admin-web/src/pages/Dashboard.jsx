import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Building2, UserCheck, Radio, RadioReceiver, CreditCard, Users, Wifi,
  TrendingUp, Megaphone, Inbox, ClipboardList, Flag, BellRing, RadioTower,
} from 'lucide-react';
import { adminApi } from '../services/admin.js';
import KpiCard, { Sparkline } from '../components/KpiCard.jsx';
import './Dashboard.css';   // 2026-06-12 — 액션 보드 스타일 (이전엔 미참조 dead css)

const DEMO_SPARK = (seed) => Array.from({ length: 18 },
  (_, i) => 30 + Math.sin((i + seed) * 0.6) * 14 + Math.random() * 6);

// 2026-05-27: 카드 클릭 시 해당 상세 화면으로 이동 (to 추가)
// 2026-06-12: 승인 대기 카드는 액션 보드로 승격 (중복 제거) + 죽은 /owners 링크 정리.
const STAT_CARDS = [
  { key: 'total_facility_accounts',   label: '전체 사장 계정', icon: Building2,    to: '/dashboard/approvals' },
  { key: 'total_facilities',          label: '활성 매장',     icon: Wifi,         to: '/dashboard/facilities' },
  { key: 'total_users',               label: '앱 사용자',     icon: Users,        to: '/dashboard/users' },
  { key: 'total_beacons',             label: '비콘 입고',     icon: Radio,        to: '/dashboard/beacons?status=inventory' },
  { key: 'active_beacons',            label: '비콘 활성',     icon: RadioReceiver, to: '/dashboard/beacons?status=active' },
  { key: 'mtd_paid_total_krw',        label: '이번 달 결제',  icon: CreditCard,
    unit: 'KRW', formatter: (v) => (v ?? 0).toLocaleString(),                    to: '/dashboard/payments' },
  { key: 'mtd_payment_count',         label: '결제 건수',     icon: TrendingUp,   to: '/dashboard/payments' },
];

// 2026-06-12 — 처리 필요(액션) 보드. 운영관리자가 대응해야 하는 건수 + 클릭 이동.
// 키는 GET /api/admin/stats/pending 응답(counts)과 1:1.
const ACTION_CARDS = [
  { key: 'owners_pending',           label: '계정 승인 대기',   icon: UserCheck,     to: '/dashboard/approvals' },
  { key: 'support_open',             label: '문의 미답변',     icon: Inbox,         to: '/dashboard/support' },
  { key: 'service_requests_pending', label: '서비스 신청 대기', icon: ClipboardList, to: '/dashboard/service-requests' },
  { key: 'abuse_open',               label: '신고 미처리',     icon: Flag,          to: '/dashboard/abuse-reports' },
  { key: 'notifications_pending',    label: '알림 처리 대기',   icon: BellRing,      to: '/dashboard/notifications' },
  { key: 'beacons_lost',             label: '비콘 분실',       icon: RadioTower,    to: '/dashboard/beacons?status=lost' },
];

const PENDING_POLL_MS = 30_000;   // 액션 현황 자동 갱신 주기

const TIME_RANGES = ['1W', '1M', '6M', '1Y', 'All Time'];

export default function Dashboard() {
  const [cards, setCards] = useState(null);
  const [pending, setPending] = useState(null);   // 처리 필요 counts
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

    // 처리 필요 현황 — 최초 + 주기 폴링 (운영 모니터링 특성상 자동 갱신)
    const loadPending = () => {
      adminApi.statsPending()
        .then((data) => { if (alive) setPending(data.counts || {}); })
        .catch(() => { /* 폴링 실패는 조용히 — 다음 주기 재시도 */ });
    };
    loadPending();
    const timer = setInterval(loadPending, PENDING_POLL_MS);
    return () => { alive = false; clearInterval(timer); };
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

      {/* 처리 필요 — 액션 보드 (2026-06-12). 카운트 > 0 강조 + 클릭 시 해당 관리 화면. */}
      <section style={{ marginBottom: 28 }}>
        <div className="action-board-title">처리 필요</div>
        <div className="action-grid">
          {ACTION_CARDS.map(({ key, label, icon: Icon, to }) => {
            const n = pending?.[key];
            const active = (n ?? 0) > 0;
            return (
              <Link key={key} to={to}
                className={'action-card' + (active ? ' has-pending' : '')}
                aria-label={`${label} ${n ?? 0}건 — 바로가기`}>
                <div className="action-icon"><Icon size={18} strokeWidth={1.75} /></div>
                <div className="action-count">{pending == null ? '—' : (n ?? 0).toLocaleString()}</div>
                <div className="action-label">{label}</div>
                {active && <span className="action-dot" aria-hidden="true" />}
              </Link>
            );
          })}
        </div>
      </section>

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
            spark={DEMO_SPARK(2)}
            to="/dashboard/users" />
          <KpiCard title="활성 비콘" value={v('active_beacons')}
            delta="+3%" deltaPositive icon={RadioReceiver}
            spark={DEMO_SPARK(4)}
            to="/dashboard/beacons?status=active" />
        </div>
      </div>

      <div className="kpi-grid">
        {STAT_CARDS.map(({ key, label, icon, unit, formatter, to }) => (
          <KpiCard
            key={key}
            title={label}
            value={v(key, formatter)}
            unit={unit}
            icon={icon}
            to={to}
          />
        ))}
      </div>

      {/* 2026-06-12 — "최근 시스템 활동" 하드코딩 더미 카드 제거.
          실데이터 액션 보드(처리 필요)가 그 역할을 대체. 빠른 작업은 풀폭 유지. */}
      <div className="card" style={{ padding: 32, marginTop: 24 }}>
        <div className="card-title" style={{ marginBottom: 24 }}>빠른 작업</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          <QuickAction icon={UserCheck} label="가입 승인" to="/dashboard/approvals" />
          <QuickAction icon={Radio} label="비콘 등록" to="/dashboard/beacons" />
          <QuickAction icon={Megaphone} label="공지 발행" to="/dashboard/announcements" />
          <QuickAction icon={CreditCard} label="결제 환불" to="/dashboard/payments" />
        </div>
      </div>
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
