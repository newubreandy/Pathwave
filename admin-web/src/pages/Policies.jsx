import React, { useEffect, useState, useCallback } from 'react';
import {
  RefreshCw, Plus, FileText, History, Send, Trash2, Pencil, Eye,
} from 'lucide-react';
import Modal from '../components/Modal.jsx';
import { useDialog } from '../components/DialogProvider.jsx';
import PolicyEditor from '../components/PolicyEditor.jsx';
import { adminApi } from '../services/admin.js';
import './Beacons.css';

const KIND_OPTIONS = [
  { value: 'terms',       label: '서비스 이용약관' },
  { value: 'privacy',     label: '개인정보 수집·이용' },
  { value: 'location',    label: '위치 정보 이용' },
  { value: 'age14',       label: '만 14세 이상' },
  { value: 'camera',      label: '카메라 접근' },
  { value: 'storage',     label: '저장공간 접근' },
  { value: 'push',        label: '푸시 알림' },
  { value: 'marketing',   label: '마케팅 수신' },
  { value: 'third_party', label: '제3자 정보 제공' },
];
const KIND_LABEL = Object.fromEntries(KIND_OPTIONS.map((o) => [o.value, o.label]));

export default function Policies() {
  const { confirm, alert } = useDialog();
  const [active, setActive] = useState([]);
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editTarget, setEditTarget] = useState(null);   // null | {} | row
  const [historyKind, setHistoryKind] = useState(null);
  // P12 — ko/en 두 언어만. 어드민이 토글로 전환해 영어 본문도 보고/수정 가능.
  const [lang, setLang] = useState('ko');

  const reload = useCallback(() => {
    setLoading(true); setError('');
    adminApi.listPolicies(lang)
      .then((data) => {
        setActive(data.active || []);
        setPending(data.pending || []);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [lang]);

  useEffect(() => { reload(); }, [reload]);

  async function handleDelete(p) {
    const ok = await confirm({
      title: '약관 버전 삭제',
      message: `"${KIND_LABEL[p.kind]} v${p.version}" 미시행 버전을 삭제하시겠습니까?`,
      danger: true, confirmText: '삭제',
    });
    if (!ok) return;
    try {
      await adminApi.deletePolicy(p.id);
      reload();
    } catch (e) {
      alert(e.message || '삭제 실패');
    }
  }

  async function handleNotify(p) {
    const ok = await confirm({
      title: '변경 안내 메일 발송',
      message: `"${KIND_LABEL[p.kind]} v${p.version}" 변경 안내 메일을 모든 사용자/사장에게 발송하시겠습니까?\n\n발송 후 재발송은 불가합니다.`,
      confirmText: '발송',
    });
    if (!ok) return;
    try {
      const res = await adminApi.notifyPolicy(p.id, 'all');
      alert(`발송 완료: ${res.sent}건 (실패 ${res.failed}건)`);
      reload();
    } catch (e) {
      alert(e.message || '발송 실패');
    }
  }

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">약관 / 정책 관리</h1>
            <p className="sub-title">
              버전 관리 · 적용 예약 · 변경 메일 공지 · 이전 버전 보기.
            </p>
          </div>
          <div className="header-actions" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {/* P12 — ko/en 토글. 어드민이 영어 본문도 직접 검토·수정 가능. */}
            <div style={{ display: 'flex', gap: 0, border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
              {['ko', 'en'].map((l) => (
                <button
                  key={l}
                  onClick={() => setLang(l)}
                  style={{
                    padding: '6px 14px',
                    background: lang === l ? 'var(--accent)' : 'var(--bg-3)',
                    color:      lang === l ? '#000' : 'var(--text-muted)',
                    border: 'none',
                    fontWeight: lang === l ? 600 : 400,
                    fontSize: 'var(--fs-sm)',
                    cursor: 'pointer',
                  }}
                >
                  {l === 'ko' ? '한국어' : 'English'}
                </button>
              ))}
            </div>
            <button className="btn btn-ghost" onClick={reload} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
              <span>새로고침</span>
            </button>
            <button className="btn btn-primary" onClick={() => setEditTarget({})}>
              <Plus size={16} /> 새 버전
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      {/* 현재 시행 중 */}
      <h3 style={{ margin: '0 0 0.75rem 0' }}>현재 시행 중</h3>
      <div className="card table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>항목</th>
              <th>버전</th>
              <th>적용일</th>
              <th>출처</th>
              <th>최근 메일 공지</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={6} className="row-empty">로딩 중...</td></tr>}
            {!loading && active.map((p) => (
              <tr key={p.kind}>
                <td>{KIND_LABEL[p.kind] || p.kind}</td>
                <td className="cell-mono">{p.version}</td>
                <td className="cell-mono">
                  {p.effective_at ? p.effective_at.slice(0, 16) : <span className="text-hint">—</span>}
                </td>
                <td>
                  {p.source === 'static_file' && (
                    <span className="status-badge neutral">파일 (PR #45)</span>
                  )}
                  {p.source === 'placeholder' && (
                    <span className="status-badge neutral">placeholder</span>
                  )}
                  {!p.source && (
                    <span className="status-badge active">DB</span>
                  )}
                </td>
                <td>
                  {p.email_notified
                    ? <span style={{ color: 'var(--accent)' }}>발송됨</span>
                    : <span className="text-hint">—</span>}
                </td>
                <td className="cell-actions">
                  <button className="icon-btn" title="이전 버전 보기"
                          onClick={() => setHistoryKind(p.kind)}>
                    <History size={15} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 예약된 버전 */}
      {pending.length > 0 && (
        <>
          <h3 style={{ margin: '1.5rem 0 0.75rem 0' }}>적용 예약 ({pending.length})</h3>
          <div className="card table-card">
            <table className="data-table">
              <thead>
                <tr>
                  <th>항목</th>
                  <th>버전</th>
                  <th>적용 예정</th>
                  <th>변경 내역</th>
                  <th>메일</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {pending.map((p) => (
                  <tr key={p.id}>
                    <td>{KIND_LABEL[p.kind] || p.kind}</td>
                    <td className="cell-mono">{p.version}</td>
                    <td className="cell-mono">{p.effective_at?.slice(0, 16)}</td>
                    <td style={{ maxWidth: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {p.change_log || <span className="text-hint">—</span>}
                    </td>
                    <td>
                      {p.email_notified
                        ? <span style={{ color: 'var(--accent)' }}>발송됨</span>
                        : <span className="text-hint">미발송</span>}
                    </td>
                    <td className="cell-actions">
                      {!p.email_notified && (
                        <button className="icon-btn" title="변경 메일 공지" onClick={() => handleNotify(p)}>
                          <Send size={15} />
                        </button>
                      )}
                      <button className="icon-btn" title="수정" onClick={() => setEditTarget(p)}>
                        <Pencil size={15} />
                      </button>
                      <button className="icon-btn danger" title="삭제"
                              onClick={() => handleDelete(p)}>
                        <Trash2 size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {editTarget !== null && (
        <PolicyEditor
          target={editTarget}
          onClose={() => setEditTarget(null)}
          onSaved={() => { setEditTarget(null); reload(); }}
        />
      )}

      <VersionHistoryModal
        kind={historyKind}
        onClose={() => setHistoryKind(null)}
      />
    </div>
  );
}


function VersionHistoryModal({ kind, onClose }) {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [bodyTarget, setBodyTarget] = useState(null);

  useEffect(() => {
    if (!kind) return;
    setLoading(true);
    adminApi.listPolicyVersions(kind)
      .then((d) => setVersions(d.versions || []))
      .finally(() => setLoading(false));
  }, [kind]);

  return (
    <Modal
      open={!!kind}
      onClose={onClose}
      size="lg"
      title={kind ? `${KIND_LABEL[kind] || kind} — 모든 버전` : ''}
    >
      {loading && <div>로딩 중...</div>}
      {!loading && versions.length === 0 && (
        <div className="text-muted" style={{ textAlign: 'center', padding: '2rem' }}>
          DB에 등록된 버전이 없습니다. (현재는 static 파일이 사용 중)
        </div>
      )}
      {!loading && versions.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>버전</th>
              <th>적용일</th>
              <th>변경 내역</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {versions.map((v) => (
              <tr key={v.id}>
                <td className="cell-mono">{v.version}</td>
                <td className="cell-mono">{v.effective_at?.slice(0, 16)}</td>
                <td>{v.change_log || <span className="text-hint">—</span>}</td>
                <td className="cell-actions">
                  <button className="icon-btn" title="본문 보기"
                          onClick={() => setBodyTarget(v)}>
                    <Eye size={15} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {bodyTarget && (
        <BodyPreviewModal
          kind={kind}
          version={bodyTarget}
          onClose={() => setBodyTarget(null)}
        />
      )}
    </Modal>
  );
}


function BodyPreviewModal({ kind, version, onClose }) {
  const [body, setBody] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    adminApi.getPolicyVersion(kind, version.id)
      .then((d) => setBody(d.body || ''))
      .finally(() => setLoading(false));
  }, [kind, version.id]);

  return (
    <Modal
      open={true}
      onClose={onClose}
      size="lg"
      title={`${KIND_LABEL[kind] || kind} v${version.version}`}
    >
      {loading
        ? <div>로딩 중...</div>
        : <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', lineHeight: 1.6 }}>{body}</pre>}
    </Modal>
  );
}


export { KIND_OPTIONS, KIND_LABEL };
