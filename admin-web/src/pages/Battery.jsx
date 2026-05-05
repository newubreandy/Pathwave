import React, { useEffect, useState, useCallback } from 'react';
import {
  RefreshCw, Battery as BatteryIcon, BatteryWarning, BatteryLow, Activity,
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import Modal from '../components/Modal.jsx';
import { adminApi } from '../services/admin.js';
import './Beacons.css';   // 데이터 테이블 / pill 공통

const THRESHOLD_OPTIONS = [10, 20, 30, 50];

export default function Battery() {
  const [threshold, setThreshold] = useState(20);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [historyTarget, setHistoryTarget] = useState(null);

  const reload = useCallback(() => {
    setLoading(true); setError('');
    adminApi.batteryStatus(threshold)
      .then((res) => setData(res))
      .catch((err) => setError(err.message || '배터리 현황을 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, [threshold]);

  useEffect(() => { reload(); }, [reload]);

  const summary = data?.summary || {};
  const lowList = data?.low_battery_beacons || [];

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">배터리 모니터링</h1>
            <p className="sub-title">
              비콘 배터리 현황 + 임계치 미만 비콘 목록 + 시계열 변화.
            </p>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
              <span>새로고침</span>
            </button>
          </div>
        </div>

        <div className="filter-bar">
          <div className="filter-group">
            <span className="filter-label">저전력 임계치</span>
            <select
              value={threshold}
              onChange={(e) => setThreshold(parseInt(e.target.value, 10))}
            >
              {THRESHOLD_OPTIONS.map((t) => (
                <option key={t} value={t}>{t}% 이하</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      <div className="stat-grid">
        <BatterySummaryCard label="전체 비콘" value={summary.total} icon={BatteryIcon} color="#1f6feb" />
        <BatterySummaryCard label="활성"      value={summary.active} icon={Activity} color="#2ea043" />
        <BatterySummaryCard
          label={`저전력 (≤${threshold}%)`}
          value={summary.low_battery}
          icon={BatteryLow}
          color="#da3633"
        />
        <BatterySummaryCard
          label="배터리 정보 없음"
          value={summary.unknown}
          icon={BatteryWarning}
          color="#d29922"
        />
        <BatterySummaryCard
          label="평균 배터리"
          value={summary.avg_pct != null ? `${summary.avg_pct}%` : '—'}
          icon={BatteryIcon}
          color="#a371f7"
        />
      </div>

      <div className="card table-card" style={{ marginTop: '1.5rem' }}>
        <div style={{ padding: '0.875rem 1rem', borderBottom: '1px solid var(--border)' }}>
          <strong>저전력 비콘 ({lowList.length}대)</strong>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>시리얼</th>
              <th>매장</th>
              <th>상태</th>
              <th>배터리</th>
              <th>마지막 보고</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={7} className="row-empty">로딩 중...</td></tr>}
            {!loading && lowList.length === 0 && (
              <tr><td colSpan={7} className="row-empty">
                현재 임계치 이하 비콘이 없습니다. 👍
              </td></tr>
            )}
            {!loading && lowList.map((b) => (
              <tr key={b.id}>
                <td className="cell-mono">{b.id}</td>
                <td className="cell-mono">{b.serial_no}</td>
                <td>{b.facility_name || (b.facility_id ? `#${b.facility_id}` : '—')}</td>
                <td>{b.status}</td>
                <td>
                  <BatteryBar pct={b.battery_pct} />
                </td>
                <td className="cell-mono">{b.battery_updated_at?.slice(0, 16) || '—'}</td>
                <td className="cell-actions">
                  <button
                    className="btn btn-ghost"
                    style={{ padding: '0.3rem 0.7rem', fontSize: '0.8125rem' }}
                    onClick={() => setHistoryTarget(b)}
                  >
                    시계열
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <HistoryModal
        beacon={historyTarget}
        onClose={() => setHistoryTarget(null)}
      />
    </div>
  );
}


function BatterySummaryCard({ label, value, icon: Icon, color }) {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ background: color + '22', color }}>
        <Icon size={20} strokeWidth={2} />
      </div>
      <div className="stat-content">
        <div className="stat-label">{label}</div>
        <div className="stat-value">{value ?? '—'}</div>
      </div>
    </div>
  );
}


function BatteryBar({ pct }) {
  if (pct == null) return <span className="text-hint">—</span>;
  const color = pct <= 10 ? '#da3633' : pct <= 20 ? '#d29922' : pct <= 50 ? '#1f6feb' : '#2ea043';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: 120 }}>
      <div style={{
        flex: 1,
        height: 8,
        background: 'var(--bg-3)',
        borderRadius: 4,
        overflow: 'hidden',
      }}>
        <div style={{
          width: `${pct}%`,
          height: '100%',
          background: color,
          transition: 'width 0.3s',
        }} />
      </div>
      <span className="cell-mono" style={{ color, minWidth: 40, textAlign: 'right' }}>{pct}%</span>
    </div>
  );
}


function HistoryModal({ beacon, onClose }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!beacon) return;
    setLoading(true); setError(''); setHistory([]);
    adminApi.batteryHistory(beacon.id, 100)
      .then((data) => {
        // 시간순(오래된 → 최신)으로 정렬해서 차트 X축에 맞춤
        const sorted = [...(data.history || [])].reverse();
        setHistory(sorted);
      })
      .catch((err) => setError(err.message || '시계열을 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, [beacon]);

  return (
    <Modal
      open={!!beacon}
      onClose={onClose}
      title={beacon ? `${beacon.serial_no} 배터리 시계열` : ''}
      size="lg"
    >
      {loading && <div className="text-muted">로딩 중...</div>}
      {error && <div className="error-box">{error}</div>}
      {!loading && history.length === 0 && !error && (
        <div className="text-muted" style={{ textAlign: 'center', padding: '2rem 0' }}>
          시계열 데이터가 없습니다.
        </div>
      )}
      {!loading && history.length > 0 && (
        <>
          <div style={{ width: '100%', height: 280 }}>
            <ResponsiveContainer>
              <LineChart data={history.map((h) => ({
                time: h.reported_at?.slice(5, 16) || '',
                pct: h.battery_pct,
                voltage: h.voltage_mv,
              }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="time" stroke="var(--text-muted)" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} stroke="var(--text-muted)" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    background: 'var(--bg-2)',
                    border: '1px solid var(--border)',
                    borderRadius: 8,
                    fontSize: '0.8125rem',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="pct"
                  stroke="#2ea043"
                  strokeWidth={2}
                  dot={{ r: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="text-hint" style={{ fontSize: '0.8125rem', marginTop: '0.5rem' }}>
            최근 {history.length}건 · 가장 오래된 → 최신 순
          </div>
        </>
      )}
    </Modal>
  );
}
