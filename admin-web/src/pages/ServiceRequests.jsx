import React, { useEffect, useState, useCallback } from 'react';
import { RefreshCw, MapPin, Wifi, CheckCircle2 } from 'lucide-react';
import { adminApi } from '../services/admin.js';

/**
 * ServiceRequests — 서비스 신청 관리 + 비콘 매칭 (P-B, 2026-05-29).
 *
 * 점주가 신청한 설치위치별 유닛에 인벤토리 비콘을 매칭 → 할당·활성·WiFi 연결.
 * 설계: docs/pathwave_beacon_provisioning_design_2026-05-29.md
 */
const STATUS_KO = {
  pending: '신청 접수', matched: '비콘 매칭완료',
  shipped: '발송', installed: '설치완료', canceled: '취소',
};

export default function ServiceRequests() {
  const [requests, setRequests] = useState([]);
  const [inventory, setInventory] = useState([]);   // 할당 대기 비콘
  const [picks, setPicks] = useState({});            // { unitId: beaconId }
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [busyUnit, setBusyUnit] = useState(null);

  const reload = useCallback(() => {
    setLoading(true);
    setError('');
    Promise.all([
      adminApi.listServiceRequests(),
      adminApi.listBeacons({ status: 'inventory' }),
    ])
      .then(([reqData, invData]) => {
        setRequests(reqData.requests || []);
        setInventory(invData.beacons || []);
      })
      .catch((e) => setError(e?.message || '불러오기에 실패했습니다.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { reload(); }, [reload]);

  const handleMatch = async (unit) => {
    const beaconId = picks[unit.id];
    if (!beaconId) { setError('할당할 비콘을 선택해 주세요.'); return; }
    setBusyUnit(unit.id);
    setError('');
    try {
      await adminApi.matchRequestUnit(unit.id, Number(beaconId));
      setPicks((p) => { const n = { ...p }; delete n[unit.id]; return n; });
      reload();
    } catch (e) {
      setError(e?.message || '매칭에 실패했습니다.');
    } finally {
      setBusyUnit(null);
    }
  };

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">서비스 신청 관리</h1>
            <p className="sub-title">
              점주 신청(설치위치·WiFi)에 인벤토리 비콘을 매칭 → 할당·활성·WiFi 연결. 매칭 후 라벨을 출력해 발송하세요.
            </p>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading} aria-label="새로고침">
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

      {requests.length === 0 && !loading && (
        <div className="card"><p className="sub-title" style={{ margin: 0 }}>신청 내역이 없습니다.</p></div>
      )}

      {requests.map((req) => (
        <div className="card" key={req.id} style={{ marginBottom: '1rem' }}>
          <div className="page-header-row" style={{ marginBottom: '0.75rem' }}>
            <div>
              <strong style={{ fontSize: '1.05rem' }}>
                {req.facility_name || `매장 #${req.facility_id ?? '-'}`}
              </strong>
              <span className="sub-title" style={{ marginLeft: 8 }}>
                {req.owner_email || '-'} · 신청 #{req.id} · {req.created_at}
              </span>
            </div>
            <span style={{
              fontSize: '0.82rem', fontWeight: 600, padding: '0.2rem 0.7rem', borderRadius: 6,
              background: req.status === 'matched' ? 'rgba(34,197,94,0.12)' : 'var(--surface-1, rgba(255,255,255,0.05))',
              color: req.status === 'matched' ? '#22C55E' : 'var(--text-secondary)',
              border: '1px solid var(--border, rgba(255,255,255,0.1))',
            }}>{STATUS_KO[req.status] || req.status}</span>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border, rgba(255,255,255,0.1))', textAlign: 'left' }}>
                <th style={{ padding: '0.5rem 0.6rem' }}><MapPin size={13} style={{ verticalAlign: 'middle' }} /> 설치위치</th>
                <th style={{ padding: '0.5rem 0.6rem' }}><Wifi size={13} style={{ verticalAlign: 'middle' }} /> SSID</th>
                <th style={{ padding: '0.5rem 0.6rem' }}>비콘 매칭</th>
              </tr>
            </thead>
            <tbody>
              {req.units.map((u) => (
                <tr key={u.id} style={{ borderBottom: '1px solid var(--surface-line, rgba(255,255,255,0.06))' }}>
                  <td style={{ padding: '0.5rem 0.6rem' }}>{u.location_label || '-'}</td>
                  <td style={{ padding: '0.5rem 0.6rem', fontFamily: 'monospace' }}>{u.ssid || '-'}</td>
                  <td style={{ padding: '0.5rem 0.6rem' }}>
                    {u.beacon_id ? (
                      <span style={{ color: '#22C55E', fontWeight: 600 }}>
                        <CheckCircle2 size={14} style={{ verticalAlign: 'middle' }} /> {u.beacon_serial || `#${u.beacon_id}`}
                      </span>
                    ) : (
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                        <select
                          value={picks[u.id] || ''}
                          onChange={(e) => setPicks((p) => ({ ...p, [u.id]: e.target.value }))}
                          disabled={busyUnit === u.id || inventory.length === 0}
                          style={{ minWidth: 180, padding: '0.3rem 0.5rem' }}
                        >
                          <option value="">{inventory.length ? '비콘 선택…' : '할당 대기 비콘 없음'}</option>
                          {inventory.map((b) => (
                            <option key={b.id} value={b.id}>{b.serial_no}</option>
                          ))}
                        </select>
                        <button
                          className="btn btn-primary"
                          onClick={() => handleMatch(u)}
                          disabled={busyUnit === u.id || !picks[u.id]}
                        >
                          {busyUnit === u.id ? '할당 중…' : '할당'}
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
