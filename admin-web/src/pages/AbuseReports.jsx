import React, { useEffect, useState, useCallback } from 'react';
import { RefreshCw, Flag, Eye, Gavel } from 'lucide-react';
import Modal from '../components/Modal.jsx';
import { supportApi } from '../services/support.js';
import './Beacons.css';   // table-card 등 공통 스타일 재사용

// 출시 심사 HIGH#1 — 신고(abuse-reports) 접수 · 검토 · 조치 화면.
// 백엔드: routes/abuse_report.py (GET/PATCH /api/admin/abuse-reports).
// 손님(mobile) ↔ 매장(provider-web) 채팅에서 올라온 신고를 운영자가 처리한다.

const STATUS_OPTIONS = ['open', 'in_review', 'action_taken', 'dismissed', 'all'];
const STATUS_LABEL = {
  open:         '접수됨',
  in_review:    '검토 중',
  action_taken: '조치 완료',
  dismissed:    '기각',
};
const REASON_LABEL = {
  spam:          '스팸·광고',
  abuse:         '욕설·혐오',
  illegal:       '불법 정보·사기',
  inappropriate: '부적절한 콘텐츠',
  other:         '기타',
};
const KIND_LABEL = { facility: '매장', user: '사용자' };

function badgeClass(status) {
  if (status === 'action_taken') return 'active';
  if (status === 'dismissed')    return 'inactive';
  return 'neutral';   // open / in_review
}
function reasonText(code) { return REASON_LABEL[code] || code || '—'; }
function kindRef(kind, id) {
  return `${KIND_LABEL[kind] || kind} #${id}`;
}

export default function AbuseReports() {
  const [filter, setFilter] = useState({ status: 'open' });
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [detailTarget, setDetailTarget] = useState(null);
  const [actionTarget, setActionTarget] = useState(null);

  const reload = useCallback(() => {
    setLoading(true);
    setError('');
    const params = {};
    if (filter.status !== 'all') params.status = filter.status;
    supportApi.loadReports(params)
      .then((data) => setReports(data.reports || []))
      .catch((err) => setError(err.message || '신고 목록을 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, [filter.status]);

  useEffect(() => { reload(); }, [reload]);

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">신고 관리</h1>
            <p className="sub-title">
              채팅 신고 접수 · 검토 · 조치 (욕설 · 불법 · 스팸 등 UGC 모더레이션).
              신고는 제출 후 취소되지 않으며, 오신고는 "기각" 으로 처리합니다.
            </p>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading} aria-label="새로고침">
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
              <span>새로고침</span>
            </button>
          </div>
        </div>

        <div className="filter-bar">
          <div className="filter-group">
            <span className="filter-label">상태</span>
            <select
              value={filter.status}
              onChange={(e) => setFilter({ status: e.target.value })}
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s === 'all' ? '전체' : STATUS_LABEL[s] || s}
                </option>
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

      <div className="card table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>신고 대상</th>
              <th>신고자</th>
              <th>사유</th>
              <th>상태</th>
              <th>접수일</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={7} className="row-empty">로딩 중...</td></tr>
            )}
            {!loading && reports.length === 0 && (
              <tr><td colSpan={7} className="row-empty">
                {filter.status === 'open' ? '접수된 신고가 없습니다.' : '결과가 없습니다.'}
              </td></tr>
            )}
            {!loading && reports.map((r) => (
              <tr key={r.id} className="row-clickable" onClick={() => setDetailTarget(r)}>
                <td className="cell-mono">{r.id}</td>
                <td>{kindRef(r.target_kind, r.target_id)}</td>
                <td>{kindRef(r.reporter_kind, r.reporter_id)}</td>
                <td>{reasonText(r.reason_code)}</td>
                <td>
                  <span className={`status-badge ${badgeClass(r.status)}`}>
                    {STATUS_LABEL[r.status] || r.status}
                  </span>
                </td>
                <td className="cell-mono">{r.created_at?.slice(0, 10) || '—'}</td>
                <td className="cell-actions">
                  <button
                    className="icon-btn"
                    title="상세"
                    onClick={(e) => { e.stopPropagation(); setDetailTarget(r); }}
                  >
                    <Eye size={15} />
                  </button>
                  <button
                    className="icon-btn accent"
                    title="검토 / 조치"
                    onClick={(e) => { e.stopPropagation(); setActionTarget(r); }}
                  >
                    <Gavel size={15} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <DetailModal report={detailTarget} onClose={() => setDetailTarget(null)} />
      <ActionModal
        report={actionTarget}
        onClose={() => setActionTarget(null)}
        onChanged={() => { setActionTarget(null); reload(); }}
      />
    </div>
  );
}


// ── 상세 모달 ────────────────────────────────────────────────────────────────
function DetailModal({ report, onClose }) {
  return (
    <Modal
      open={!!report}
      onClose={onClose}
      title={report ? `신고 상세 #${report.id}` : ''}
      size="lg"
    >
      {report && (
        <div className="kv" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem 1.5rem' }}>
          <div><span className="kv-key">신고 대상</span> {kindRef(report.target_kind, report.target_id)}</div>
          <div><span className="kv-key">신고자</span> {kindRef(report.reporter_kind, report.reporter_id)}</div>
          <div><span className="kv-key">사유</span> {reasonText(report.reason_code)}</div>
          <div><span className="kv-key">상태</span> {STATUS_LABEL[report.status] || report.status}</div>
          <div style={{ gridColumn: '1 / -1' }}>
            <span className="kv-key">상세 내용</span>
            <p style={{ margin: '8px 0 0', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {report.reason_detail || '— (작성 안 함)'}
            </p>
          </div>
          <div><span className="kv-key">접수일</span> {report.created_at || '—'}</div>
          <div><span className="kv-key">처리일</span> {report.resolved_at || '—'}</div>
          <div><span className="kv-key">처리 운영자</span> {report.resolved_by_admin_id ? `#${report.resolved_by_admin_id}` : '—'}</div>
          <div style={{ gridColumn: '1 / -1' }}>
            <span className="kv-key">처리 메모</span>
            <p style={{ margin: '8px 0 0', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {report.resolution_note || '—'}
            </p>
          </div>
        </div>
      )}
    </Modal>
  );
}


// ── 검토 / 조치 모달 ─────────────────────────────────────────────────────────
function ActionModal({ report, onClose, onChanged }) {
  const [status, setStatus] = useState('in_review');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (report) {
      setStatus(report.status === 'open' ? 'in_review' : report.status);
      setNote(report.resolution_note || '');
      setError('');
    }
  }, [report]);

  async function handleApply() {
    setBusy(true); setError('');
    try {
      await supportApi.patchReport(report.id, {
        status,
        resolution_note: note.trim() || undefined,
      });
      onChanged?.();
    } catch (err) {
      setError(err.message || '처리에 실패했습니다.');
    } finally { setBusy(false); }
  }

  return (
    <Modal
      open={!!report}
      onClose={onClose}
      title={report ? `신고 처리 — #${report.id}` : ''}
      size="md"
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>취소</button>
          <button className="btn btn-primary" onClick={handleApply} disabled={busy}>
            {busy ? '처리 중...' : '상태 변경'}
          </button>
        </>
      }
    >
      {report && (
        <>
          <p className="text-muted" style={{ marginTop: 0, fontSize: '0.875rem' }}>
            {kindRef(report.reporter_kind, report.reporter_id)} 님이 {kindRef(report.target_kind, report.target_id)} 을(를)
            "{reasonText(report.reason_code)}" 사유로 신고했습니다.
          </p>
          <label className="form-label">
            <span>처리 상태</span>
            <select value={status} onChange={(e) => setStatus(e.target.value)} disabled={busy}>
              <option value="open">접수됨</option>
              <option value="in_review">검토 중</option>
              <option value="action_taken">조치 완료</option>
              <option value="dismissed">기각 (오신고 / 위반 아님)</option>
            </select>
          </label>
          <label className="form-label">
            <span>처리 메모 (선택)</span>
            <textarea
              rows={4}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="예: 채팅 이용 제한 조치 / 위반 사항 없어 기각"
              disabled={busy}
            />
          </label>
          {error && <div className="error-box">{error}</div>}
        </>
      )}
    </Modal>
  );
}
