import React, { useEffect, useState, useCallback } from 'react';
import { RefreshCw, MessageSquare, AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { adminApi } from '../services/admin.js';
import Modal from '../components/Modal.jsx';
import './Beacons.css';

// D 번들2 — /api/admin/chat/rooms 백엔드 신설 후 실제 채팅방 목록 연동.
// (이전엔 /api/chat/reports 가정 placeholder 였음)
async function fetchReportedRooms() {
  const data = await adminApi.adminChatRooms(100);
  return data.rooms || [];
}

export default function ChatMonitor() {
  const { t } = useTranslation();
  const [rooms, setRooms]           = useState(null);  // null = API 미구현
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState('');
  const [detailTarget, setDetailTarget] = useState(null);

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
            <button className="btn btn-ghost" onClick={reload} disabled={loading} aria-label="새로고침">
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
              <tr key={room.id || room.room_id}
                  className="row-clickable"
                  onClick={() => setDetailTarget(room)}>
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

      <RoomDetailModal room={detailTarget} onClose={() => setDetailTarget(null)} />
    </div>
  );
}

function RoomDetailModal({ room, onClose }) {
  if (!room) return null;
  const rows = [
    ['채팅방 ID',   room.id || room.room_id || '—'],
    ['채팅방 이름', room.room_name || '—'],
    ['신고 사유',   room.reason || '—'],
    ['신고자 ID',   room.reporter_id || '—'],
    ['신고 일시',   room.reported_at || '—'],
    ['참여자 수',   room.participant_count ?? '—'],
    ['메시지 수',   room.message_count ?? '—'],
  ];
  return (
    <Modal
      open={true}
      onClose={onClose}
      size="md"
      title={`채팅방 상세 — ${room.room_name || room.id || room.room_id}`}
      footer={<button className="btn btn-primary" onClick={onClose}>닫기</button>}
    >
      <dl style={{ display: 'grid', gridTemplateColumns: 'max-content 1fr',
                   gap: '0.5rem 1.5rem', margin: 0 }}>
        {rows.map(([label, value]) => (
          <React.Fragment key={label}>
            <dt style={{ color: 'var(--text-muted)', fontWeight: 500,
                         fontSize: 'var(--fs-sm)', margin: 0 }}>{label}</dt>
            <dd style={{ margin: 0, fontSize: 'var(--fs-sm)',
                         wordBreak: 'break-all' }}>{value}</dd>
          </React.Fragment>
        ))}
      </dl>
    </Modal>
  );
}
