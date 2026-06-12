import React, { useEffect, useState, useCallback } from 'react';
import { RefreshCw, MapPin, Wifi, CheckCircle2, Printer, Truck, X } from 'lucide-react';
import { adminApi } from '../services/admin.js';

// HTML 이스케이프 (라벨 텍스트는 점주 입력값 — 인쇄 창에 안전하게 삽입)
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

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
  // 라벨(스티커) 크기 — 기본 40×25mm (비콘 48×37mm 보다 작게). 프린터/라벨지에 맞춰 조정.
  const [labelW, setLabelW] = useState(40);
  const [labelH, setLabelH] = useState(25);

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

  const handleShip = async (req) => {
    setError('');
    try {
      await adminApi.shipServiceRequest(req.id);
      reload();
    } catch (e) {
      setError(e?.message || '발송 처리에 실패했습니다.');
    }
  };

  // 라벨 인쇄 — 매칭된 유닛(비콘)마다 1장. 새 창에 격리된 print CSS 로 정확한 크기 출력.
  // 저렴한 스티커/라벨 프린터를 OS 인쇄창에서 선택 (드라이버 불필요).
  const printLabels = (req) => {
    const labels = (req.units || []).filter((u) => u.beacon_id);
    if (labels.length === 0) { setError('매칭된 비콘이 없어 인쇄할 라벨이 없습니다.'); return; }
    const w = labelW || 40, h = labelH || 25;
    const win = window.open('', '_blank', 'width=420,height=640');
    if (!win) { setError('팝업이 차단되었습니다. 팝업 허용 후 다시 시도해 주세요.'); return; }
    const html = `<!doctype html><html><head><meta charset="utf-8"><title>비콘 라벨</title>
      <style>
        @page { size: ${w}mm ${h}mm; margin: 0; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body { background: #fff; }
        .label { width: ${w}mm; height: ${h}mm; padding: 1.5mm 2mm; overflow: hidden;
                 page-break-after: always; display: flex; flex-direction: column;
                 justify-content: center; font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", sans-serif; }
        .store { font-size: 7pt; color: #444; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .loc   { font-size: 11pt; font-weight: 700; line-height: 1.15; margin: 0.8mm 0; }
        .sn    { font-size: 6pt; color: #888; font-family: ui-monospace, Menlo, monospace; }
        @media screen { body { padding: 16px; background: #eee; }
          .label { background: #fff; border: 1px dashed #bbb; margin-bottom: 8px; } }
      </style></head><body>
      ${labels.map((u) => `<div class="label">
        <div class="store">${esc(req.facility_name || ('매장 #' + (req.facility_id ?? '')))}</div>
        <div class="loc">${esc(u.location_label || '-')}</div>
        <div class="sn">${esc(u.beacon_serial || ('#' + u.beacon_id))}</div>
      </div>`).join('')}
      <script>window.onload = function(){ setTimeout(function(){ window.print(); }, 150); };<\/script>
      </body></html>`;
    win.document.open();
    win.document.write(html);
    win.document.close();
  };

  const [detailReq, setDetailReq] = useState(null);

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
          <div className="header-actions" style={{ alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <Printer size={14} /> 라벨
              <input type="number" min="10" max="100" value={labelW}
                onChange={(e) => setLabelW(Number(e.target.value))}
                style={{ width: 52, padding: '0.25rem 0.4rem' }} aria-label="라벨 폭(mm)" />
              ×
              <input type="number" min="10" max="100" value={labelH}
                onChange={(e) => setLabelH(Number(e.target.value))}
                style={{ width: 52, padding: '0.25rem 0.4rem' }} aria-label="라벨 높이(mm)" />
              mm
            </span>
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

      {detailReq && (
        <ServiceRequestDetailModal
          req={detailReq}
          onClose={() => setDetailReq(null)}
        />
      )}

      {requests.map((req) => (
        <div
          className="card"
          key={req.id}
          style={{ marginBottom: '1rem', cursor: 'pointer' }}
          onClick={() => setDetailReq(req)}
        >
          <div className="page-header-row" style={{ marginBottom: '0.75rem' }}>
            <div>
              <strong style={{ fontSize: '1.05rem' }}>
                {req.facility_name || `매장 #${req.facility_id ?? '-'}`}
              </strong>
              <span className="sub-title" style={{ marginLeft: 8 }}>
                {req.owner_email || '-'} · 신청 #{req.id} · {req.created_at}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              {(req.units || []).some((u) => u.beacon_id) && (
                <button className="btn btn-ghost" onClick={(e) => { e.stopPropagation(); printLabels(req); }} aria-label="라벨 인쇄">
                  <Printer size={15} /> <span>라벨 인쇄</span>
                </button>
              )}
              {req.status === 'matched' && (
                <button className="btn btn-primary" onClick={(e) => { e.stopPropagation(); handleShip(req); }} aria-label="발송 처리">
                  <Truck size={15} /> <span>발송 처리</span>
                </button>
              )}
              <span style={{
                fontSize: '0.82rem', fontWeight: 600, padding: '0.2rem 0.7rem', borderRadius: 6,
                background: req.status === 'matched' ? 'rgba(34,197,94,0.12)' : 'var(--surface-1, rgba(255,255,255,0.05))',
                color: req.status === 'matched' ? '#22C55E' : 'var(--text-secondary)',
                border: '1px solid var(--border, rgba(255,255,255,0.1))',
              }}>{STATUS_KO[req.status] || req.status}</span>
            </div>
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
                  <td style={{ padding: '0.5rem 0.6rem' }} onClick={(e) => e.stopPropagation()}>
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

// ── 서비스 신청 상세 모달 ─────────────────────────────────────────────
function ServiceRequestDetailModal({ req, onClose }) {
  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
        zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20, backdropFilter: 'blur(6px)',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--bg-2, rgba(30,30,46,0.98))',
          border: '1px solid var(--border, rgba(255,255,255,0.15))',
          borderRadius: 16, padding: 24,
          width: '100%', maxWidth: 640,
          maxHeight: '90vh', overflow: 'auto',
          color: 'var(--text, white)',
        }}
      >
        {/* 헤더 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>
              {req.facility_name || `매장 #${req.facility_id ?? '-'}`}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary, rgba(255,255,255,0.55))', marginTop: 4 }}>
              신청 #{req.id} · {req.owner_email || '-'} · {req.created_at}
              <span style={{
                marginLeft: 10, padding: '2px 8px', borderRadius: 5,
                background: req.status === 'matched' ? 'rgba(34,197,94,0.15)' : 'var(--surface-1, rgba(255,255,255,0.06))',
                color: req.status === 'matched' ? '#22C55E' : 'var(--text-secondary)',
                border: '1px solid var(--border, rgba(255,255,255,0.1))',
                fontSize: '0.78rem', fontWeight: 600,
              }}>{STATUS_KO[req.status] || req.status}</span>
            </div>
          </div>
          <button
            className="btn btn-ghost"
            onClick={onClose}
            aria-label="닫기"
            style={{ padding: '4px 8px' }}
          >
            <X size={16} />
          </button>
        </div>

        {/* 유닛 테이블 */}
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border, rgba(255,255,255,0.1))', textAlign: 'left' }}>
              <th style={{ padding: '0.5rem 0.6rem' }}><MapPin size={13} style={{ verticalAlign: 'middle' }} /> 설치위치</th>
              <th style={{ padding: '0.5rem 0.6rem' }}><Wifi size={13} style={{ verticalAlign: 'middle' }} /> SSID</th>
              <th style={{ padding: '0.5rem 0.6rem' }}>비콘</th>
            </tr>
          </thead>
          <tbody>
            {(req.units || []).map((u) => (
              <tr key={u.id} style={{ borderBottom: '1px solid var(--surface-line, rgba(255,255,255,0.06))' }}>
                <td style={{ padding: '0.5rem 0.6rem' }}>{u.location_label || '-'}</td>
                <td style={{ padding: '0.5rem 0.6rem', fontFamily: 'monospace' }}>{u.ssid || '-'}</td>
                <td style={{ padding: '0.5rem 0.6rem' }}>
                  {u.beacon_id ? (
                    <span style={{ color: '#22C55E', fontWeight: 600 }}>
                      <CheckCircle2 size={14} style={{ verticalAlign: 'middle' }} /> {u.beacon_serial || `#${u.beacon_id}`}
                    </span>
                  ) : (
                    <span style={{ color: 'var(--text-secondary, rgba(255,255,255,0.45))' }}>미매칭</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div style={{ marginTop: 20, textAlign: 'right' }}>
          <button className="btn btn-ghost" onClick={onClose}>닫기</button>
        </div>
      </div>
    </div>
  );
}
