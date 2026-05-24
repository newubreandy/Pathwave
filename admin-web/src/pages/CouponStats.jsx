import React, { useEffect, useState, useCallback } from 'react';
import { RefreshCw, Ticket, CheckCircle, Clock } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import apiClient from '../services/apiClient.js';
import './Beacons.css';

async function fetchCouponStats() {
  try {
    // 백엔드 /api/admin/coupons 가 생기면 여기서 집계
    const data = await apiClient.get('/api/admin/coupons');
    const coupons = data.coupons || data || [];
    const issued  = coupons.length;
    const used    = coupons.filter((c) => c.used_at || c.status === 'used').length;
    const expired = coupons.filter((c) => c.status === 'expired').length;
    return { issued, used, expired };
  } catch (_) {
    // API 미구현 시 placeholder 반환
    return null;
  }
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
