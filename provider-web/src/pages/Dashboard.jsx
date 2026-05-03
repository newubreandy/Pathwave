import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Store, Wifi, Users, Tag, TrendingUp, BarChart3, PieChart as PieChartIcon, Activity } from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import './Dashboard.css';

/* ═══════════════════════════════════════════════════
   Mock Data — 대시보드
   실제 운영시 API로 교체
   ═══════════════════════════════════════════════════ */

// 와이파이 접속 추이 (최근 7일)
const WIFI_TREND_DATA = [
  { date: '4/26', 접속자: 98 },
  { date: '4/27', 접속자: 125 },
  { date: '4/28', 접속자: 142 },
  { date: '4/29', 접속자: 118 },
  { date: '4/30', 접속자: 156 },
  { date: '5/1', 접속자: 189 },
  { date: '5/2', 접속자: 214 },
];

// 서비스별 매출 (최근 4개월)
const REVENUE_DATA = [
  { month: '1월', wifi: 1024, event: 12, push: 6 },
  { month: '2월', wifi: 1024, event: 18, push: 12 },
  { month: '3월', wifi: 1030, event: 12, push: 18 },
  { month: '4월', wifi: 1024, event: 24, push: 12 },
];

// 쿠폰 사용률
const COUPON_DATA = [
  { name: '사용', value: 89, color: '#16A34A' },
  { name: '미사용', value: 45, color: '#D1D5DB' },
  { name: '만료', value: 22, color: '#F59E0B' },
];

// 차트 색상 (디자인 토큰 연동)
const CHART_COLORS = {
  primary: '#16A34A',
  primaryLight: '#DCFCE7',
  secondary: '#3B82F6',
  warning: '#F59E0B',
  gray: '#9CA3AF',
};

/* ═══════════════════════════════════════════════════
   커스텀 툴팁
   ═══════════════════════════════════════════════════ */
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'white',
      border: '1px solid var(--pw-border-light)',
      borderRadius: 'var(--pw-radius-md)',
      padding: '8px 12px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
      fontSize: 'var(--pw-caption-size)',
    }}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
      {payload.map((entry, i) => (
        <div key={i} style={{ color: entry.color, display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: entry.color, display: 'inline-block' }} />
          {entry.name}: {typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}
        </div>
      ))}
    </div>
  );
};

/* ═══════════════════════════════════════════════════
   StatCard Component
   ═══════════════════════════════════════════════════ */
const StatCard = ({ icon: Icon, label, value, color, trend, to }) => {
  const navigate = useNavigate();

  return (
    <div
      className="dashboard-stat-card"
      style={{ '--card-accent': color }}
      onClick={() => to && navigate(to)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && to && navigate(to)}
    >
      <div className="dashboard-stat-top">
        <div className="dashboard-stat-icon" style={{ background: `${color}14` }}>
          <Icon size={20} color={color} />
        </div>
        {trend != null && (
          <span className={`dashboard-stat-trend ${trend > 0 ? 'up' : 'down'}`}>
            <TrendingUp size={14} style={{ transform: trend > 0 ? 'none' : 'rotate(180deg)' }} />
            {Math.abs(trend)}%
          </span>
        )}
      </div>
      <div className="dashboard-stat-label">{label}</div>
      <div className="dashboard-stat-value">{value}</div>
    </div>
  );
};

/* ═══════════════════════════════════════════════════
   Dashboard Main
   ═══════════════════════════════════════════════════ */
const Dashboard = () => {
  const couponTotal = COUPON_DATA.reduce((sum, d) => sum + d.value, 0);
  const couponUsedPct = Math.round((COUPON_DATA[0].value / couponTotal) * 100);

  return (
    <div style={{ animation: 'fadeIn var(--pw-duration-slow) var(--pw-ease-out)' }}>
      <div className="page-header-section">
        <h1 className="page-title">오버뷰</h1>
        <p className="sub-title">모든 매장의 운영 현황을 확인하세요.</p>
      </div>

      {/* ── 통계 카드 ── */}
      <div className="dashboard-stats">
        <StatCard
          icon={Store} label="운영 중인 매장" value="3개"
          color="#111827" trend={null}
          to="/dashboard/store"
        />
        <StatCard
          icon={Wifi} label="활성 비콘" value="12개"
          color={CHART_COLORS.primary} trend={8}
          to="/dashboard/wifi"
        />
        <StatCard
          icon={Users} label="이번 달 접속자" value="842명"
          color={CHART_COLORS.secondary} trend={12}
          to="/dashboard/report"
        />
        <StatCard
          icon={Tag} label="발급된 쿠폰" value="156건"
          color={CHART_COLORS.warning} trend={-3}
          to="/dashboard/coupons"
        />
      </div>

      {/* ── 차트 영역 ── */}
      <div className="dashboard-charts">

        {/* 와이파이 접속 추이 — Area Chart */}
        <div className="dashboard-chart-card full-width">
          <div className="dashboard-chart-header">
            <Activity size={18} color="var(--pw-text-secondary)" />
            <span className="dashboard-chart-title">와이파이 접속 추이</span>
            <span className="dashboard-chart-subtitle">최근 7일</span>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={WIFI_TREND_DATA} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gradientGreen" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={CHART_COLORS.primary} stopOpacity={0.3} />
                  <stop offset="100%" stopColor={CHART_COLORS.primary} stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
              <XAxis
                dataKey="date" axisLine={false} tickLine={false}
                tick={{ fontSize: 11, fill: '#9CA3AF' }}
              />
              <YAxis
                axisLine={false} tickLine={false}
                tick={{ fontSize: 11, fill: '#9CA3AF' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone" dataKey="접속자"
                stroke={CHART_COLORS.primary} strokeWidth={2.5}
                fill="url(#gradientGreen)"
                dot={{ r: 3, fill: CHART_COLORS.primary, strokeWidth: 0 }}
                activeDot={{ r: 5, fill: CHART_COLORS.primary, strokeWidth: 2, stroke: 'white' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* 서비스별 매출 — Bar Chart */}
        <div className="dashboard-chart-card">
          <div className="dashboard-chart-header">
            <BarChart3 size={18} color="var(--pw-text-secondary)" />
            <span className="dashboard-chart-title">서비스별 매출</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={REVENUE_DATA} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
              <XAxis
                dataKey="month" axisLine={false} tickLine={false}
                tick={{ fontSize: 11, fill: '#9CA3AF' }}
              />
              <YAxis
                axisLine={false} tickLine={false}
                tick={{ fontSize: 11, fill: '#9CA3AF' }}
                tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}K` : v}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="wifi" name="Wifi" fill={CHART_COLORS.primary} radius={[4,4,0,0]} barSize={14} />
              <Bar dataKey="event" name="이벤트" fill={CHART_COLORS.secondary} radius={[4,4,0,0]} barSize={14} />
              <Bar dataKey="push" name="알림" fill={CHART_COLORS.warning} radius={[4,4,0,0]} barSize={14} />
            </BarChart>
          </ResponsiveContainer>
          <div className="dashboard-chart-legend">
            <span className="dashboard-legend-item">
              <span className="dashboard-legend-dot" style={{ background: CHART_COLORS.primary }} /> Wifi
            </span>
            <span className="dashboard-legend-item">
              <span className="dashboard-legend-dot" style={{ background: CHART_COLORS.secondary }} /> 이벤트
            </span>
            <span className="dashboard-legend-item">
              <span className="dashboard-legend-dot" style={{ background: CHART_COLORS.warning }} /> 알림
            </span>
          </div>
        </div>

        {/* 쿠폰 사용률 — Donut Chart */}
        <div className="dashboard-chart-card">
          <div className="dashboard-chart-header">
            <PieChartIcon size={18} color="var(--pw-text-secondary)" />
            <span className="dashboard-chart-title">쿠폰 사용률</span>
          </div>
          <div style={{ position: 'relative' }}>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={COUPON_DATA}
                  cx="50%" cy="50%"
                  innerRadius={60} outerRadius={85}
                  paddingAngle={3}
                  dataKey="value"
                  stroke="none"
                >
                  {COUPON_DATA.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            {/* 도넛 중앙 라벨 */}
            <div style={{
              position: 'absolute', top: '50%', left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center', pointerEvents: 'none'
            }}>
              <div className="dashboard-donut-center-value">{couponUsedPct}%</div>
              <div className="dashboard-donut-center-label">사용률</div>
            </div>
          </div>
          <div className="dashboard-chart-legend">
            {COUPON_DATA.map((d, i) => (
              <span key={i} className="dashboard-legend-item">
                <span className="dashboard-legend-dot" style={{ background: d.color }} /> {d.name} ({d.value})
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
