import React, { useEffect, useState, useCallback } from 'react';
import { RefreshCw, Plus, Search, MapPin, Trash2, Pencil } from 'lucide-react';
import Modal from '../components/Modal.jsx';
import { adminApi } from '../services/admin.js';
import './Beacons.css';

const STATUS_OPTIONS = ['all', 'inventory', 'active', 'inactive', 'lost'];
const STATUS_LABEL = {
  inventory: '입고 (할당 대기)',
  active:    '활성 (할당됨)',
  inactive:  '비활성',
  lost:      '분실',
};
const STATUS_COLOR = {
  inventory: '#1f6feb',
  active:    '#2ea043',
  inactive:  '#8b949e',
  lost:      '#da3633',
};

export default function Beacons() {
  const [filter, setFilter] = useState({ status: 'all', q: '' });
  const [beacons, setBeacons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [importOpen, setImportOpen] = useState(false);
  const [assignTarget, setAssignTarget] = useState(null);   // beacon row
  const [editTarget, setEditTarget]     = useState(null);   // beacon row

  const reload = useCallback(() => {
    setLoading(true);
    setError('');
    const params = {};
    if (filter.status !== 'all') params.status = filter.status;
    if (filter.q.trim()) params.q = filter.q.trim();
    adminApi.listBeacons(params)
      .then((data) => setBeacons(data.beacons || []))
      .catch((err) => setError(err.message || '비콘 목록을 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, [filter.status, filter.q]);

  useEffect(() => { reload(); }, [reload]);

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">비콘 인벤토리</h1>
            <p className="sub-title">
              비콘 입고 (CSV / SN 배열) · 목록 · 매장 할당 / 해제 / 상태 변경.
            </p>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
              <span>새로고침</span>
            </button>
            <button className="btn btn-primary" onClick={() => setImportOpen(true)}>
              <Plus size={16} />
              <span>입고</span>
            </button>
          </div>
        </div>

        <div className="filter-bar">
          <div className="filter-group">
            <span className="filter-label">상태</span>
            <select
              value={filter.status}
              onChange={(e) => setFilter((f) => ({ ...f, status: e.target.value }))}
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s === 'all' ? '전체' : STATUS_LABEL[s] || s}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-group filter-search">
            <Search size={16} />
            <input
              type="text"
              placeholder="시리얼 번호 검색"
              value={filter.q}
              onChange={(e) => setFilter((f) => ({ ...f, q: e.target.value }))}
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      <div className="card table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>시리얼</th>
              <th>UUID</th>
              <th>상태</th>
              <th>할당 매장</th>
              <th>배터리</th>
              <th>FW</th>
              <th>입고일</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={9} className="row-empty">로딩 중...</td></tr>
            )}
            {!loading && beacons.length === 0 && (
              <tr><td colSpan={9} className="row-empty">
                비콘이 없습니다. 우측 상단 "입고" 버튼으로 등록하세요.
              </td></tr>
            )}
            {!loading && beacons.map((b) => (
              <tr key={b.id}>
                <td className="cell-mono">{b.id}</td>
                <td className="cell-mono">{b.serial_no}</td>
                <td className="cell-mono cell-uuid" title={b.uuid}>{b.uuid}</td>
                <td>
                  <span
                    className="status-pill"
                    style={{
                      background: (STATUS_COLOR[b.status] || '#8b949e') + '22',
                      color: STATUS_COLOR[b.status] || '#8b949e',
                    }}
                  >
                    {STATUS_LABEL[b.status] || b.status}
                  </span>
                </td>
                <td>
                  {b.facility_id
                    ? <span>{b.facility_name || `매장 #${b.facility_id}`}</span>
                    : <span className="text-hint">—</span>}
                </td>
                <td className="cell-mono">{b.battery_pct != null ? `${b.battery_pct}%` : '—'}</td>
                <td className="cell-mono">{b.firmware_ver || '—'}</td>
                <td className="cell-mono">{b.created_at?.slice(0, 10) || '—'}</td>
                <td className="cell-actions">
                  <button
                    className="icon-btn"
                    title="할당/해제"
                    onClick={() => setAssignTarget(b)}
                  >
                    <MapPin size={15} />
                  </button>
                  <button
                    className="icon-btn"
                    title="수정"
                    onClick={() => setEditTarget(b)}
                  >
                    <Pencil size={15} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ImportModal
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onImported={() => { setImportOpen(false); reload(); }}
      />
      <AssignModal
        beacon={assignTarget}
        onClose={() => setAssignTarget(null)}
        onChanged={() => { setAssignTarget(null); reload(); }}
      />
      <EditModal
        beacon={editTarget}
        onClose={() => setEditTarget(null)}
        onSaved={() => { setEditTarget(null); reload(); }}
      />
    </div>
  );
}


// ── 입고 모달 ────────────────────────────────────────────────────────────────
function ImportModal({ open, onClose, onImported }) {
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  // 파싱 규칙:
  //   각 줄: SN,UUID[,FW]  또는  SN UUID [FW]
  function parse(raw) {
    return raw.split(/\r?\n/).map((line) => line.trim()).filter(Boolean).map((line) => {
      const parts = line.split(/[,\s]+/).filter(Boolean);
      const [sn, uuid, fw] = parts;
      return { serial_no: sn || '', uuid: (uuid || '').toUpperCase(), firmware_ver: fw || undefined };
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const items = parse(text);
    if (items.length === 0) { setError('입고할 비콘 행을 한 줄 이상 입력해 주세요.'); return; }
    setBusy(true);
    setError('');
    setResult(null);
    try {
      const data = await adminApi.importBeacons({ beacons: items });
      setResult(data);
      if ((data.errors || []).length === 0) {
        setTimeout(() => { onImported?.(); }, 600);
      }
    } catch (err) {
      setError(err.message || '입고에 실패했습니다.');
    } finally {
      setBusy(false);
    }
  }

  function handleClose() {
    if (busy) return;
    setText('');
    setResult(null);
    setError('');
    onClose?.();
  }

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="비콘 입고"
      size="lg"
      footer={
        <>
          <button className="btn btn-ghost" onClick={handleClose} disabled={busy}>취소</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={busy || !text.trim()}>
            {busy ? '등록 중...' : '등록'}
          </button>
        </>
      }
    >
      <p className="text-muted" style={{ marginTop: 0, fontSize: '0.875rem' }}>
        한 줄에 비콘 1개. 형식 — <code>SN,UUID[,FW]</code> 또는 공백 구분.
        UUID는 대소문자 구분 없이 입력 가능 (자동 대문자 변환).
      </p>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={`예시)
B108-0001 12345678-1234-1234-1234-123456789ABC
B108-0002,11111111-2222-3333-4444-555555555555,1.0.3
B108-0003 22222222-3333-4444-5555-666666666666 1.0.3`}
        rows={10}
        className="import-textarea"
        disabled={busy}
      />
      {error && (
        <div className="error-box" style={{ marginTop: '0.75rem' }}>{error}</div>
      )}
      {result && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <div style={{ marginBottom: '0.5rem' }}>
            ✓ 성공: <strong>{result.imported_count || 0}</strong> · 실패: <strong>{result.errors?.length || 0}</strong>
          </div>
          {result.errors?.length > 0 && (
            <div className="text-muted" style={{ fontSize: '0.8125rem' }}>
              {result.errors.slice(0, 5).map((e, i) => (
                <div key={i}>#{e.index + 1} ({e.serial_no || 'no-sn'}): {e.error}</div>
              ))}
              {result.errors.length > 5 && <div>... 외 {result.errors.length - 5}건</div>}
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}


// ── 할당/해제 모달 ───────────────────────────────────────────────────────────
function AssignModal({ beacon, onClose, onChanged }) {
  const [facilityId, setFacilityId] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (beacon) {
      setFacilityId(beacon.facility_id ? String(beacon.facility_id) : '');
      setError('');
    }
  }, [beacon]);

  async function handleAssign() {
    const fid = parseInt(facilityId, 10);
    if (!fid) { setError('매장 ID를 입력해 주세요.'); return; }
    setBusy(true); setError('');
    try {
      await adminApi.assignBeacon(beacon.id, fid);
      onChanged?.();
    } catch (err) {
      setError(err.message || '할당에 실패했습니다.');
    } finally { setBusy(false); }
  }

  async function handleUnassign() {
    setBusy(true); setError('');
    try {
      await adminApi.unassignBeacon(beacon.id);
      onChanged?.();
    } catch (err) {
      setError(err.message || '해제에 실패했습니다.');
    } finally { setBusy(false); }
  }

  return (
    <Modal
      open={!!beacon}
      onClose={onClose}
      title={beacon ? `비콘 #${beacon.id} 할당 / 해제` : ''}
      size="sm"
    >
      {beacon && (
        <>
          <div className="kv">
            <div><span className="kv-key">시리얼</span> <span className="cell-mono">{beacon.serial_no}</span></div>
            <div><span className="kv-key">현재 상태</span> {STATUS_LABEL[beacon.status] || beacon.status}</div>
            <div><span className="kv-key">현재 매장</span> {beacon.facility_id
              ? `${beacon.facility_name || ''} (#${beacon.facility_id})`
              : '없음'}</div>
          </div>

          <label className="form-label" style={{ marginTop: '1rem' }}>
            <span>할당할 매장 ID</span>
            <input
              type="number"
              value={facilityId}
              onChange={(e) => setFacilityId(e.target.value)}
              placeholder="예: 1"
              disabled={busy}
            />
          </label>

          {error && <div className="error-box">{error}</div>}

          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
            <button className="btn btn-primary flex-1" onClick={handleAssign} disabled={busy}>
              할당
            </button>
            {beacon.facility_id && (
              <button className="btn btn-danger" onClick={handleUnassign} disabled={busy}>
                해제
              </button>
            )}
          </div>
        </>
      )}
    </Modal>
  );
}


// ── 수정 모달 (firmware/battery/status/uuid) ───────────────────────────────────
function EditModal({ beacon, onClose, onSaved }) {
  const [form, setForm] = useState({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (beacon) {
      setForm({
        firmware_ver: beacon.firmware_ver || '',
        battery_pct:  beacon.battery_pct ?? '',
        status:       beacon.status,
        uuid:         beacon.uuid || '',
      });
      setError('');
    }
  }, [beacon]);

  async function handleSave() {
    const payload = {};
    if (form.firmware_ver !== beacon.firmware_ver) payload.firmware_ver = form.firmware_ver;
    if (form.battery_pct !== '' && Number(form.battery_pct) !== beacon.battery_pct)
      payload.battery_pct = Number(form.battery_pct);
    if (form.status !== beacon.status) payload.status = form.status;
    if (form.uuid !== beacon.uuid) payload.uuid = form.uuid;

    if (Object.keys(payload).length === 0) {
      setError('변경된 필드가 없습니다.');
      return;
    }
    setBusy(true); setError('');
    try {
      await adminApi.updateBeacon(beacon.id, payload);
      onSaved?.();
    } catch (err) {
      setError(err.message || '저장에 실패했습니다.');
    } finally { setBusy(false); }
  }

  return (
    <Modal
      open={!!beacon}
      onClose={onClose}
      title={beacon ? `비콘 #${beacon.id} 수정` : ''}
      size="md"
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>취소</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={busy}>
            {busy ? '저장 중...' : '저장'}
          </button>
        </>
      }
    >
      {beacon && (
        <>
          <label className="form-label">
            <span>UUID</span>
            <input
              type="text"
              value={form.uuid || ''}
              onChange={(e) => setForm((f) => ({ ...f, uuid: e.target.value.toUpperCase() }))}
              disabled={busy}
            />
          </label>
          <label className="form-label">
            <span>펌웨어 버전</span>
            <input
              type="text"
              value={form.firmware_ver || ''}
              onChange={(e) => setForm((f) => ({ ...f, firmware_ver: e.target.value }))}
              disabled={busy}
            />
          </label>
          <label className="form-label">
            <span>배터리 (0~100)</span>
            <input
              type="number"
              min={0}
              max={100}
              value={form.battery_pct ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, battery_pct: e.target.value }))}
              disabled={busy}
            />
          </label>
          <label className="form-label">
            <span>상태</span>
            <select
              value={form.status || ''}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
              disabled={busy}
            >
              {Object.keys(STATUS_LABEL).map((s) => (
                <option key={s} value={s}>{STATUS_LABEL[s]}</option>
              ))}
            </select>
          </label>

          {error && <div className="error-box">{error}</div>}
        </>
      )}
    </Modal>
  );
}
