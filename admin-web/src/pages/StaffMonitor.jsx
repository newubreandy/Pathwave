import React, { useEffect, useState, useCallback } from 'react';
import { RefreshCw, Users, AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { adminApi } from '../services/admin.js';
import './Beacons.css';

// D 번들2 — /api/admin/staff/reports 백엔드 신설 후 실제 데이터 연동.
async function fetchStaffReports() {
  const data = await adminApi.adminStaffReports();
  return data.reports || [];
}

export default function StaffMonitor() {
  const { t } = useTranslation();
  const [reports, setReports] = useState(null); // null = API 미구현
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');

  const reload = useCallback(() => {
    setLoading(true); setError('');
    fetchStaffReports()
      .then((data) => setReports(data))
      .catch((err) => setError(err.message || ''))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { reload(); }, [reload]);

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">{t('staff_mgmt.admin_monitor_title')}</h1>
            <p className="sub-title">{t('staff_mgmt.admin_monitor_subtitle')}</p>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading} aria-label="새로고침">
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
              <span>{t('staff_mgmt.refresh')}</span>
            </button>
          </div>
        </div>
      </div>

      {/* 운영 안내 박스 */}
      <div className="card" style={{
        display: 'flex',
        gap: 14,
        alignItems: 'flex-start',
        background: 'var(--bg-3)',
        border: '1px solid var(--border)',
        padding: '1.25rem 1.5rem',
      }}>
        <AlertTriangle size={20} style={{ color: 'var(--accent)', flexShrink: 0, marginTop: 2 }} />
        <p style={{ margin: 0, fontSize: 'var(--fs-sm)', color: 'var(--text-muted)', lineHeight: 1.6 }}>
          {t('staff_mgmt.admin_monitor_hint')}
        </p>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      {/* 신고/의심 활동 큐 */}
      <div className="card table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th><Users size={14} style={{ verticalAlign: 'middle', marginRight: 6 }} />{t('staff_mgmt.col_staff_id')}</th>
              <th>{t('staff_mgmt.col_facility')}</th>
              <th>{t('staff_mgmt.col_reason')}</th>
              <th>{t('staff_mgmt.col_reported_at')}</th>
              <th>{t('staff_mgmt.col_action')}</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={5} className="row-empty">{t('common.loading')}</td></tr>
            )}
            {!loading && reports === null && (
              <tr>
                <td colSpan={5} className="row-empty">
                  <div style={{ marginBottom: 8, fontWeight: 500 }}>
                    {t('staff_mgmt.queue_placeholder')}
                  </div>
                  <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-hint)' }}>
                    {t('staff_mgmt.queue_desc')}
                  </div>
                </td>
              </tr>
            )}
            {!loading && reports !== null && reports.length === 0 && (
              <tr><td colSpan={5} className="row-empty">{t('common.empty')}</td></tr>
            )}
            {!loading && reports !== null && reports.map((r) => (
              <tr key={r.id || r.staff_id}>
                <td className="cell-mono">{r.staff_id || r.id || '—'}</td>
                <td className="cell-mono">{r.facility_id || r.facility_name || '—'}</td>
                <td>{r.reason || '—'}</td>
                <td className="cell-mono" style={{ fontSize: '0.8125rem' }}>
                  {r.reported_at?.slice(0, 16) || '—'}
                </td>
                <td className="cell-actions">
                  <span className="text-hint" style={{ fontSize: 'var(--fs-xs)' }}>—</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
