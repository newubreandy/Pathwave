import React, { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { RefreshCw } from 'lucide-react';
import { adminApi } from '../services/admin.js';
import KpiCard from '../components/KpiCard.jsx';

export default function SupportStats() {
  const { t } = useTranslation();
  const [days, setDays] = useState(30);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const reload = useCallback(() => {
    setLoading(true); setError('');
    adminApi.supportStats(days)
      .then((d) => setData(d))
      .catch((e) => setError(e.message || '통계를 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, [days]);

  useEffect(() => { reload(); }, [reload]);

  const total = (data?.counts || []).reduce((s, r) => s + r.n, 0);
  const openNow = (data?.open_now || []).reduce((s, r) => s + r.n, 0);
  const replied = (data?.counts || []).filter((c) => c.status === 'replied')
    .reduce((s, r) => s + r.n, 0);
  const avgUser = (data?.avg_response || []).find((r) => r.kind === 'user');
  const avgProv = (data?.avg_response || []).find((r) => r.kind === 'provider');

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">{t('admin_support.stats_title', '고객센터 통계')}</h1>
            <p className="sub-title">접수량, 응답시간, 처리량을 한 눈에 확인합니다.</p>
          </div>
          <div className="header-actions">
            <select value={days} onChange={(e) => setDays(Number(e.target.value))} className="form-input">
              <option value={7}>최근 7일</option>
              <option value={30}>최근 30일</option>
              <option value={90}>최근 90일</option>
            </select>
            <button className="btn btn-ghost" onClick={reload} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
              <span>새로고침</span>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12,
        marginBottom: 16,
      }}>
        <KpiCard label={t('admin_support.stats_total_tickets', '총 접수')} value={total} />
        <KpiCard label={t('admin_support.stats_open_now', '대기 중')} value={openNow} />
        <KpiCard label={t('admin_support.stats_replied', '응답 완료')} value={replied} />
        <KpiCard
          label={`${t('admin_support.stats_avg_response', '평균 응답시간 (시간)')} (사용자)`}
          value={avgUser?.avg_hours != null ? avgUser.avg_hours.toFixed(1) : '—'}
        />
        <KpiCard
          label={`${t('admin_support.stats_avg_response', '평균 응답시간 (시간)')} (사장님)`}
          value={avgProv?.avg_hours != null ? avgProv.avg_hours.toFixed(1) : '—'}
        />
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>일별 접수량</h3>
        <table className="data-table">
          <thead>
            <tr><th>날짜</th><th>접수 건수</th></tr>
          </thead>
          <tbody>
            {(data?.daily || []).length === 0 && (
              <tr><td colSpan={2} className="row-empty">데이터가 없습니다.</td></tr>
            )}
            {(data?.daily || []).map((d) => (
              <tr key={d.day}>
                <td className="cell-mono">{d.day}</td>
                <td className="cell-mono">{d.created}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
