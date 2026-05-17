import React, { useEffect, useState, useCallback } from 'react';
import { BarChart2, RefreshCw, Clock, Inbox, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { supportApi } from '../services/support.js';
import './Beacons.css';

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1.25rem 1.5rem' }}>
      <div style={{
        width: 44, height: 44, borderRadius: 12,
        background: color ? `${color}22` : 'var(--accent-soft, rgba(34,197,94,0.12))',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        <Icon size={22} style={{ color: color || 'var(--accent)' }} />
      </div>
      <div>
        <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)', marginBottom: 2 }}>{label}</div>
        <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text)', lineHeight: 1 }}>{value}</div>
      </div>
    </div>
  );
}

export default function SupportStats() {
  const { t } = useTranslation();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const reload = useCallback(() => {
    setLoading(true); setError('');
    supportApi.loadStats()
      .then((data) => setStats(data.stats || data))
      .catch((err) => setError(err.message || '통계를 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { reload(); }, [reload]);

  const byKind = stats?.by_kind || {};
  const avgMin = stats?.avg_response_minutes;

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">
              <BarChart2 size={22} style={{ verticalAlign: 'middle', marginRight: 8, color: 'var(--accent)' }} />
              응대 통계
            </h1>
            <p className="sub-title">문의 현황 · 평균 응답 시간 · 종류별 분포</p>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
              <span>새로고침</span>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          {t('common.loading')}
        </div>
      )}

      {!loading && stats && (
        <>
          {/* KPI 카드 행 */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <StatCard
              icon={Inbox}
              label="전체 문의"
              value={stats.total ?? '—'}
              color="#94a3b8"
            />
            <StatCard
              icon={AlertCircle}
              label="미답변 (open)"
              value={stats.open ?? '—'}
              color="#f97316"
            />
            <StatCard
              icon={CheckCircle}
              label="답변 완료"
              value={stats.replied ?? '—'}
              color="#22c55e"
            />
            <StatCard
              icon={XCircle}
              label="종료"
              value={stats.closed ?? '—'}
              color="#94a3b8"
            />
            <StatCard
              icon={Clock}
              label="평균 응답 시간"
              value={avgMin != null ? `${Math.round(avgMin)}분` : '—'}
              color="#3b82f6"
            />
          </div>

          {/* 종류별 분포 */}
          {Object.keys(byKind).length > 0 && (
            <div className="card">
              <div style={{ fontWeight: 600, fontSize: 'var(--fs-sm)', color: 'var(--text)', marginBottom: '1rem' }}>
                종류별 분포
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {Object.entries(byKind).map(([k, v]) => {
                  const total = stats.total || 1;
                  const pct = Math.round((v / total) * 100);
                  return (
                    <div key={k}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 'var(--fs-sm)' }}>
                        <span style={{ color: 'var(--text)', fontWeight: 500 }}>
                          {k === 'user' ? '사용자 문의' : k === 'provider' ? '사장님 문의' : k}
                        </span>
                        <span style={{ color: 'var(--text-muted)' }}>{v}건 ({pct}%)</span>
                      </div>
                      <div style={{
                        height: 8, borderRadius: 4,
                        background: 'var(--bg-3)',
                        border: '1px solid var(--border)',
                        overflow: 'hidden',
                      }}>
                        <div style={{
                          height: '100%',
                          width: `${pct}%`,
                          background: 'var(--accent)',
                          borderRadius: 4,
                          transition: 'width 0.4s ease',
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}

      {!loading && !stats && !error && (
        <div className="card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          통계 API 연동 후 수치가 표시됩니다.
        </div>
      )}
    </div>
  );
}
