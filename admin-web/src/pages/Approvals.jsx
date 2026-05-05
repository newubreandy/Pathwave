import React, { useEffect, useState, useCallback } from 'react';
import { RefreshCw, Search, CheckCircle2, XCircle, RotateCcw, Eye } from 'lucide-react';
import Modal from '../components/Modal.jsx';
import { adminApi } from '../services/admin.js';
import './Beacons.css';   // table-card 등 공통 스타일 재사용

const STATUS_OPTIONS = ['pending', 'verified', 'suspended', 'all'];
const STATUS_LABEL = {
  pending:    '승인 대기',
  verified:   '승인됨',
  suspended:  '정지됨',
};
const STATUS_COLOR = {
  pending:   '#d29922',
  verified:  '#2ea043',
  suspended: '#da3633',
};

export default function Approvals() {
  const [filter, setFilter] = useState({ status: 'pending', q: '' });
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [detailTarget, setDetailTarget] = useState(null);
  const [suspendTarget, setSuspendTarget] = useState(null);

  const reload = useCallback(() => {
    setLoading(true);
    setError('');
    const params = {};
    if (filter.status !== 'all') params.status = filter.status;
    if (filter.q.trim()) params.q = filter.q.trim();
    adminApi.listFacilityAccounts(params)
      .then((data) => setAccounts(data.accounts || []))
      .catch((err) => setError(err.message || '목록을 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, [filter.status, filter.q]);

  useEffect(() => { reload(); }, [reload]);

  async function handleVerify(account) {
    if (!confirm(`"${account.company_name || account.email}" 계정을 승인하시겠습니까?`)) return;
    try {
      await adminApi.verifyFacilityAccount(account.id);
      reload();
    } catch (err) {
      alert(err.message || '승인에 실패했습니다.');
    }
  }

  async function handleReactivate(account) {
    if (!confirm(`"${account.company_name || account.email}" 정지를 해제하시겠습니까?`)) return;
    try {
      await adminApi.reactivateFacilityAccount(account.id);
      reload();
    } catch (err) {
      alert(err.message || '정지 해제에 실패했습니다.');
    }
  }

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">사장 가입 승인</h1>
            <p className="sub-title">
              사업자번호 검증 후 가입 승인 / 정지 / 정지 해제.
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
              placeholder="이메일 / 회사명 / 사업자번호 검색"
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
              <th>회사명</th>
              <th>사업자번호</th>
              <th>이메일</th>
              <th>담당자</th>
              <th>상태</th>
              <th>가입일</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={8} className="row-empty">로딩 중...</td></tr>
            )}
            {!loading && accounts.length === 0 && (
              <tr><td colSpan={8} className="row-empty">
                {filter.status === 'pending' ? '대기 중인 가입 신청이 없습니다.' : '결과가 없습니다.'}
              </td></tr>
            )}
            {!loading && accounts.map((a) => (
              <tr key={a.id}>
                <td className="cell-mono">{a.id}</td>
                <td>{a.company_name || '—'}</td>
                <td className="cell-mono">{a.business_no || '—'}</td>
                <td>{a.email}</td>
                <td>{a.manager_name || '—'}</td>
                <td>
                  <span
                    className="status-pill"
                    style={{
                      background: (STATUS_COLOR[a.status] || '#8b949e') + '22',
                      color: STATUS_COLOR[a.status] || '#8b949e',
                    }}
                  >
                    {STATUS_LABEL[a.status] || a.status}
                  </span>
                </td>
                <td className="cell-mono">{a.created_at?.slice(0, 10) || '—'}</td>
                <td className="cell-actions">
                  <button
                    className="icon-btn"
                    title="상세"
                    onClick={() => setDetailTarget(a)}
                  >
                    <Eye size={15} />
                  </button>
                  {a.status === 'pending' && (
                    <button
                      className="icon-btn"
                      title="승인"
                      onClick={() => handleVerify(a)}
                      style={{ color: '#2ea043' }}
                    >
                      <CheckCircle2 size={15} />
                    </button>
                  )}
                  {a.status !== 'suspended' && (
                    <button
                      className="icon-btn"
                      title="정지"
                      onClick={() => setSuspendTarget(a)}
                      style={{ color: '#da3633' }}
                    >
                      <XCircle size={15} />
                    </button>
                  )}
                  {a.status === 'suspended' && (
                    <button
                      className="icon-btn"
                      title="정지 해제"
                      onClick={() => handleReactivate(a)}
                      style={{ color: '#1f6feb' }}
                    >
                      <RotateCcw size={15} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <DetailModal
        account={detailTarget}
        onClose={() => setDetailTarget(null)}
      />
      <SuspendModal
        account={suspendTarget}
        onClose={() => setSuspendTarget(null)}
        onChanged={() => { setSuspendTarget(null); reload(); }}
      />
    </div>
  );
}


// ── 상세 모달 ────────────────────────────────────────────────────────────────
function DetailModal({ account, onClose }) {
  const [full, setFull] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!account) return;
    setLoading(true);
    setFull(null);
    adminApi.getFacilityAccount(account.id)
      .then((data) => setFull(data.account))
      .catch(() => setFull(account))   // fallback: 목록 row 사용
      .finally(() => setLoading(false));
  }, [account]);

  return (
    <Modal
      open={!!account}
      onClose={onClose}
      title={account ? `사장 계정 #${account.id}` : ''}
      size="lg"
    >
      {loading && <div className="text-muted">로딩 중...</div>}
      {!loading && full && (
        <div className="kv" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem 1.5rem' }}>
          <div><span className="kv-key">회사명</span> {full.company_name || '—'}</div>
          <div><span className="kv-key">사업자번호</span> <span className="cell-mono">{full.business_no || '—'}</span></div>
          <div><span className="kv-key">이메일</span> {full.email}</div>
          <div><span className="kv-key">전화</span> {full.phone || '—'}</div>
          <div><span className="kv-key">담당자</span> {full.manager_name || '—'}</div>
          <div><span className="kv-key">담당자 전화</span> {full.manager_phone || '—'}</div>
          <div><span className="kv-key">담당자 이메일</span> {full.manager_email || '—'}</div>
          <div><span className="kv-key">상태</span> {STATUS_LABEL[full.status] || full.status}</div>
          <div><span className="kv-key">가입일</span> {full.created_at || '—'}</div>
          <div><span className="kv-key">승인일</span> {full.approved_at || '—'}</div>
          {full.suspended_at && (
            <>
              <div><span className="kv-key">정지일</span> {full.suspended_at}</div>
              <div><span className="kv-key">정지 사유</span> {full.suspended_reason || '—'}</div>
            </>
          )}
          {full.business_doc_url && (
            <div style={{ gridColumn: '1 / -1' }}>
              <span className="kv-key">사업자등록증</span>{' '}
              <a href={full.business_doc_url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent)' }}>
                문서 보기
              </a>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}


// ── 정지 모달 (사유 입력) ───────────────────────────────────────────────────
function SuspendModal({ account, onClose, onChanged }) {
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (account) { setReason(''); setError(''); }
  }, [account]);

  async function handleSuspend() {
    setBusy(true); setError('');
    try {
      await adminApi.suspendFacilityAccount(account.id, { reason: reason.trim() || undefined });
      onChanged?.();
    } catch (err) {
      setError(err.message || '정지에 실패했습니다.');
    } finally { setBusy(false); }
  }

  return (
    <Modal
      open={!!account}
      onClose={onClose}
      title={account ? `계정 정지 — ${account.company_name || account.email}` : ''}
      size="md"
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>취소</button>
          <button className="btn btn-danger" onClick={handleSuspend} disabled={busy}>
            {busy ? '처리 중...' : '정지'}
          </button>
        </>
      }
    >
      <p className="text-muted" style={{ marginTop: 0, fontSize: '0.875rem' }}>
        해당 계정은 즉시 로그인 거부됩니다. 사유는 향후 정지 해제 / 감사 로그 용도.
      </p>
      <label className="form-label">
        <span>정지 사유 (선택)</span>
        <textarea
          rows={4}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="예: 사업자 등록증 위조 의심"
          disabled={busy}
        />
      </label>
      {error && <div className="error-box">{error}</div>}
    </Modal>
  );
}
