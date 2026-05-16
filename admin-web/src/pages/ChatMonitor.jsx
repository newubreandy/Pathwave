import React, { useEffect, useState, useCallback } from 'react';
import { RefreshCw, MessageSquare, AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import apiClient from '../services/apiClient.js';
import './Beacons.css';

async function fetchReportedRooms() {
  try {
    const data = await apiClient.get('/api/chat/reports');
    return data.rooms || data || [];
  } catch (_) {
    // 엔드포인트 미구현 — placeholder 모드
    return null;
  }
}

export default function ChatMonitor() {
  const { t } = useTranslation();
  const [rooms, setRooms]     = useState(null);  // null = API 미구현
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');

  const reload = useCallback(() => {
    setLoading(true); setError('');
    fetchReportedRooms()
      .then((data) => setRooms(data))
      .catch((err) => setError(err.message || ''))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { reload(); }, [reload]);

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">{t('chat.admin_monitor_title')}</h1>
            <p className="sub-title">{t('chat.admin_monitor_subtitle')}</p>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
              <span>{t('chat.admin_monitor_refresh')}</span>
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
          {t('chat.admin_monitor_hint')}
        </p>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      {/* 신고 큐 */}
      <div className="card table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th><MessageSquare size={14} style={{ verticalAlign: 'middle', marginRight: 6 }} />채팅방</th>
              <th>신고 사유</th>
              <th>신고자</th>
              <th>신고 일시</th>
              <th>처리</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={5} className="row-empty">{t('common.loading')}</td></tr>
            )}
            {!loading && rooms === null && (
              <tr>
                <td colSpan={5} className="row-empty">
                  <div style={{ marginBottom: 8, fontWeight: 500 }}>
                    {t('chat.admin_monitor_queue_placeholder')}
                  </div>
                  <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-hint)' }}>
                    {t('chat.admin_monitor_queue_desc')}
                  </div>
                </td>
              </tr>
            )}
            {!loading && rooms !== null && rooms.length === 0 && (
              <tr><td colSpan={5} className="row-empty">{t('common.empty')}</td></tr>
            )}
            {!loading && rooms !== null && rooms.map((room) => (
              <tr key={room.id || room.room_id}>
                <td style={{ fontWeight: 500 }}>{room.room_name || room.id}</td>
                <td>{room.reason || '—'}</td>
                <td className="cell-mono">{room.reporter_id || '—'}</td>
                <td className="cell-mono" style={{ fontSize: '0.8125rem' }}>
                  {room.reported_at?.slice(0, 16) || '—'}
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
