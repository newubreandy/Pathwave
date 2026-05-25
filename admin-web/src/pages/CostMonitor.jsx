/**
 * D-4-pre — 외부 AI API 비용 모니터링 (슈퍼어드민 전용).
 *
 * GET /api/admin/cost-monitor 응답으로 월 누적 USD + 임계점 (%)
 * + provider 별 / operation 별 합계 + 활성 알림.
 *
 * 임계점 동작
 * ---------
 * - 50%  : 사이드바 배지 (DashboardLayout 에서 직접 표시)
 * - 80%  : 글로벌 알림 모달 (CriticalAdminAlert), 24h snooze
 * - 100% : 동일 + 빨강 critical 스타일 + 번역 호출 자동 차단
 *
 * 출시 후 M+3~6 시점에 도달 예상 — 도달 전 자체 모델 (Helsinki/NLLB) 전환.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { RefreshCw, AlertTriangle, TrendingUp, DollarSign } from 'lucide-react';
import { adminApi } from '../services/admin.js';

export default function CostMonitor() {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');

  const now = new Date();
  const [year,  setYear]  = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);

  const reload = useCallback(async () => {
    setLoading(true); setError('');
    try {
      setData(await adminApi.costMonitor(year, month));
    } catch (e) {
      setError(e?.message || '불러오기 실패');
    } finally {
      setLoading(false);
    }
  }, [year, month]);

  useEffect(() => { reload(); }, [reload]);

  const monthly   = data?.monthly   || { total_usd: 0, total_krw: 0, by_provider: {}, by_operation: {}, call_count: 0 };
  const threshold = data?.threshold || { usd: 100, krw: 151020, krw_per_usd: 1510.20 };
  const pct       = data?.percent   || 0;
  const blocked   = data?.translation_blocked;

  const pctColor = pct >= 100 ? '#EF4444'
                 : pct >= 80  ? '#F59E0B'
                 : pct >= 50  ? '#FACC15' : '#22C55E';

  return (
    <div>
      <div className="page-header" style={{ display: 'flex',
            alignItems: 'center', justifyContent: 'space-between',
            marginBottom: '1rem' }}>
        <div>
          <h1 className="page-title">외부 AI 비용 모니터링</h1>
          <p className="page-subtitle">
            DeepL / Anthropic / GCV 등 외부 API 월 누적 비용 + 임계점 (${threshold.usd} = ₩{threshold.krw.toLocaleString()}).
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.4rem' }}>
          <input type="number" value={year}
                 onChange={(e) => setYear(parseInt(e.target.value, 10))}
                 style={{ width: 80 }} aria-label="연도" />
          <select value={month}
                  onChange={(e) => setMonth(parseInt(e.target.value, 10))}
                  aria-label="월">
            {Array.from({length: 12}, (_, i) => i + 1).map((m) => (
              <option key={m} value={m}>{m}월</option>
            ))}
          </select>
          <button className="btn btn-ghost" onClick={reload} disabled={loading}
                  aria-label="새로고침">
            <RefreshCw size={16} className={loading ? 'spin' : ''} aria-hidden="true" />
          </button>
        </div>
      </div>

      {error && <div className="error-box" style={{ marginBottom: '1rem' }}>{error}</div>}

      {/* 메인 KPI */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                    gap: '0.875rem', marginBottom: '1.5rem' }}>
        <KpiCard icon={DollarSign} label="이번 달 누적 비용 (USD)"
                 value={`$${monthly.total_usd.toFixed(2)}`}
                 sub={`₩${monthly.total_krw.toLocaleString()} (₩${threshold.krw_per_usd}/USD)`} />
        <KpiCard icon={TrendingUp} label="임계점 진행률"
                 value={`${pct.toFixed(1)}%`}
                 color={pctColor}
                 sub={`임계 $${threshold.usd}`} />
        <KpiCard icon={TrendingUp} label="API 호출 수"
                 value={monthly.call_count.toLocaleString()} />
      </div>

      {/* 진행률 바 */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between',
                      fontSize: 'var(--fs-sm)', color: 'var(--text-muted)',
                      marginBottom: '0.25rem' }}>
          <span>$0</span>
          <span>$50 (50%)</span>
          <span>$80 (80%)</span>
          <span>${threshold.usd} (100%)</span>
        </div>
        <div style={{ height: 12, background: 'var(--bg-3)',
                      border: '1px solid var(--border)', borderRadius: 6,
                      overflow: 'hidden', position: 'relative' }}>
          <div style={{ width: `${Math.min(pct, 100)}%`, height: '100%',
                        background: pctColor, transition: 'width 300ms' }} />
        </div>
      </div>

      {blocked && (
        <div style={{ padding: '1rem', background: 'rgba(239,68,68,0.10)',
                      border: '1px solid #EF4444', borderRadius: 8,
                      marginBottom: '1.5rem',
                      display: 'flex', gap: '0.6rem', alignItems: 'flex-start' }}>
          <AlertTriangle size={20} color="#EF4444" aria-hidden="true" style={{ flexShrink: 0 }} />
          <div>
            <strong style={{ color: '#EF4444' }}>번역 호출 자동 차단됨</strong>
            <p style={{ margin: '0.25rem 0 0', fontSize: 'var(--fs-sm)',
                        color: 'var(--text-secondary)' }}>
              임계점 초과로 채팅/메뉴 자동 번역 일시 중단. 자체 모델 전환 즉시 작업
              (docs/translation_cost_runaway_plan.md 참조).
            </p>
          </div>
        </div>
      )}

      {/* 활성 알림 */}
      {data?.alerts && data.alerts.length > 0 && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginTop: 0 }}>활성 알림</h3>
          {data.alerts.map((a) => (
            <div key={a.id} style={{ padding: '0.75rem 1rem',
                    background: a.level === 'critical' ? 'rgba(239,68,68,0.08)'
                              : a.level === 'warn'     ? 'rgba(245,158,11,0.08)'
                                                       : 'var(--bg-3)',
                    border: `1px solid ${
                      a.level === 'critical' ? '#EF4444'
                      : a.level === 'warn'   ? '#F59E0B' : 'var(--border)'}`,
                    borderRadius: 8, marginBottom: '0.5rem' }}>
              <strong>{a.title}</strong>
              <div style={{ marginTop: '0.25rem',
                            fontSize: 'var(--fs-sm)',
                            color: 'var(--text-secondary)' }}>
                {a.body}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* provider/operation 분류 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                    gap: '0.875rem' }}>
        <BreakdownCard title="Provider 별" data={monthly.by_provider} />
        <BreakdownCard title="Operation 별" data={monthly.by_operation} />
      </div>
    </div>
  );
}

function KpiCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div style={{ padding: '1rem', background: 'var(--bg-3)',
                  border: '1px solid var(--border)', borderRadius: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem',
                    color: 'var(--text-muted)', fontSize: 'var(--fs-sm)',
                    marginBottom: '0.4rem' }}>
        <Icon size={14} aria-hidden="true" /> {label}
      </div>
      <div style={{ fontSize: '1.6rem', fontWeight: 700,
                    color: color || 'var(--text)' }}>{value}</div>
      {sub && <div style={{ marginTop: '0.25rem',
                            fontSize: 'var(--fs-xs)',
                            color: 'var(--text-muted)' }}>{sub}</div>}
    </div>
  );
}

function BreakdownCard({ title, data }) {
  const entries = Object.entries(data || {});
  return (
    <div style={{ padding: '1rem', background: 'var(--bg-3)',
                  border: '1px solid var(--border)', borderRadius: 10 }}>
      <h3 style={{ margin: '0 0 0.5rem', fontSize: 'var(--fs-md)' }}>{title}</h3>
      {entries.length === 0 && (
        <div style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>
          (아직 호출 없음)
        </div>
      )}
      {entries.map(([k, v]) => (
        <div key={k} style={{ display: 'flex', justifyContent: 'space-between',
                              padding: '0.4rem 0',
                              borderTop: '1px solid var(--border)' }}>
          <span style={{ color: 'var(--text-secondary)' }}>{k}</span>
          <code>${v.toFixed(4)}</code>
        </div>
      ))}
    </div>
  );
}
