import React, { useEffect, useState, useCallback } from 'react';
import { RefreshCw, Ticket, CheckCircle, Clock } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { adminApi } from '../services/admin.js';
import './Beacons.css';

// D 번들2 — /api/admin/coupons 백엔드 신설 후 실제 집계 사용.
async function fetchCouponStats() {
  const data = await adminApi.adminListCoupons();
  // 백엔드가 이미 summary 를 계산해 줌 (issued/used/active/expired)
  return data.summary || {
    issued:  (data.coupons || []).length,
    used:    0,
    expired: 0,
  };
}

export default function CouponStats() {
  const { t } = useTranslation();
  const [stats, setStats]     = useState(null);   // null = loading/placeholder
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');

  const reload = useCallback(() => {
    setLoading(true); setError('');
    fetchCouponStats()
      .then((data) => setStats(data))
      .catch((err) => setError(err.message || t('coupon.admin_stats_error')))
      .finally(() => setLoading(false));
  }, [t]);

  useEffect(() => { reload(); }, [reload]);

  const CARDS = [
    {
      key:   'issued',
      label: t('coupon.admin_stats_issued'),
      icon:  Ticket,
      cls:   'accent',
      value: stats?.issued,
    },
    {
      key:   'used',
      label: t('coupon.admin_stats_used'),
      icon:  CheckCircle,
      cls:   '',
      value: stats?.used,
    },
    {
      key:   'expired',
      label: t('coupon.admin_stats_expired'),
      icon:  Clock,
      cls:   'danger',
      value: stats?.expired,
    },
  ];

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">{t('coupon.admin_stats_title')}</h1>
            <p className="sub-title">{t('coupon.admin_stats_subtitle')}</p>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading} aria-label="새로고침">
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
              <span>{t('coupon.admin_stats_refresh')}</span>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      <div className="stat-grid">
        {CARDS.map(({ key, label, icon: Icon, cls, value }) => (
          <div className="stat-card" key={key}>
            <div className={`stat-icon${cls ? ' ' + cls : ''}`}>
              <Icon size={22} />
            </div>
            <div className="stat-content">
              <div className="stat-label">{label}</div>
              <div className="stat-value">
                {loading
                  ? '…'
                  : value != null
                    ? value.toLocaleString()
                    : '—'}
              </div>
            </div>
          </div>
        ))}
      </div>

      {!loading && stats === null && (
        <div className="card" style={{
          borderColor: 'var(--border)',
          color: 'var(--text-hint)',
          textAlign: 'center',
          padding: '2.5rem',
          fontSize: 'var(--fs-sm)',
        }}>
          {t('coupon.admin_stats_placeholder')}
        </div>
      )}
    </div>
  );
}
