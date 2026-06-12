/**
 * A-022 — 회원 (사용자) 관리.
 *
 * GET /api/admin/users 로 사용자 목록 조회. 검색 + status 필터 + 강제 탈퇴.
 * 신고 누적 / 채팅방 수 / 가입 채널(provider) / 만 14 미만 분류(age_group)
 * 한 페이지로 모니터링.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { RefreshCw, Search, Trash2, AlertTriangle } from 'lucide-react';
import { adminApi } from '../services/admin.js';
import Modal from '../components/Modal.jsx';
import './Beacons.css';

const STATUS_OPTIONS = [
  { value: 'active',  label: '활성' },
  { value: 'deleted', label: '탈퇴' },
  { value: 'all',     label: '전체' },
];

const PROVIDER_OPTIONS = [
  { value: '',       label: '전체 채널' },
  { value: 'email',  label: '이메일' },
  { value: 'google', label: '구글' },
  { value: 'apple',  label: '애플' },
  { value: 'kakao',  label: '카카오' },
  { value: 'naver',  label: '네이버' },
];

const PAGE_SIZE = 50;

export default function Users() {
  const [users, setUsers]     = useState([]);
  const [total, setTotal]     = useState(0);
  const [offset, setOffset]   = useState(0);
  const [filter, setFilter]   = useState({ q: '', status: 'active', provider: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [detailTarget, setDetailTarget] = useState(null);

  const reload = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const params = { limit: PAGE_SIZE, offset, status: filter.status };
      if (filter.q.trim())     params.q = filter.q.trim();
      if (filter.provider)     params.provider = filter.provider;
      const data = await adminApi.adminListUsers(params);
      setUsers(data.users || []);
      setTotal(data.total || 0);
    } catch (e) {
      setError(e?.message || '불러오기 실패');
    } finally {
      setLoading(false);
    }
  }, [filter, offset]);

  useEffect(() => { reload(); }, [reload]);

  function onFilterChange(k, v) {
    setOffset(0);
    setFilter((f) => ({ ...f, [k]: v }));
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex',
            alignItems: 'center', justifyContent: 'space-between',
            marginBottom: '1rem' }}>
        <div>
          <h1 className="page-title">회원 관리</h1>
          <p className="page-subtitle">
            가입 사용자 검색·필터 + 신고 누적 / 채팅방 / 강제 탈퇴.
          </p>
        </div>
        <button className="btn btn-ghost" onClick={reload}
                disabled={loading} aria-label="새로고침">
          <RefreshCw size={16} className={loading ? 'spin' : ''} aria-hidden="true" />
        </button>
      </div>

      {/* 필터 바 */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem',
                    flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: '1 1 220px' }}>
          <Search size={14} aria-hidden="true"
                  style={{ position: 'absolute', left: 10, top: 11,
                           color: 'var(--text-muted)' }} />
          <input
            value={filter.q}
            onChange={(e) => onFilterChange('q', e.target.value)}
            placeholder="이메일 검색"
            style={{ paddingLeft: '2rem', width: '100%' }} />
        </div>
        <select value={filter.status}
                onChange={(e) => onFilterChange('status', e.target.value)}>
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <select value={filter.provider}
                onChange={(e) => onFilterChange('provider', e.target.value)}>
          {PROVIDER_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <div style={{ color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>
          총 <strong style={{ color: 'var(--text)' }}>{total.toLocaleString()}</strong>명
        </div>
      </div>

      {error && <div className="error-box" style={{ marginBottom: '1rem' }}>{error}</div>}

      {/* 표 */}
      <div style={{ overflowX: 'auto', border: '1px solid var(--border)',
                    borderRadius: 10 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse',
                        fontSize: 'var(--fs-sm)' }}>
          <thead>
            <tr style={{ background: 'var(--bg-3)' }}>
              <Th>ID</Th>
              <Th>이메일</Th>
              <Th>채널</Th>
              <Th>언어</Th>
              <Th>연령</Th>
              <Th>가입일</Th>
              <Th>채팅</Th>
              <Th>신고</Th>
              <Th>상태</Th>
              <Th>작업</Th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}
                  className="row-clickable"
                  style={{ borderTop: '1px solid var(--border)' }}
                  onClick={() => setDetailTarget(u)}>
                <Td>{u.id}</Td>
                <Td><code>{u.email}</code></Td>
                <Td>{u.provider}</Td>
                <Td>{u.language}</Td>
                <Td>
                  {u.age_group === 'adult' ? '성인'
                   : u.age_group === 'minor' ? '미성년' : '—'}
                </Td>
                <Td>{u.created_at?.slice(0, 10)}</Td>
                <Td style={{ textAlign: 'right' }}>{u.chat_rooms_count}</Td>
                <Td style={{ textAlign: 'right',
                              color: u.reported_count > 0 ? 'var(--danger)' : undefined }}>
                  {u.reported_count}
                </Td>
                <Td>
                  {u.deleted_at
                    ? <Badge color="var(--text-muted)">탈퇴</Badge>
                    : <Badge color="var(--accent)">활성</Badge>}
                </Td>
                <Td>
                  {!u.deleted_at && (
                    <button className="btn btn-ghost"
                            onClick={(e) => { e.stopPropagation(); setDeleteTarget(u); }}
                            aria-label="강제 탈퇴"
                            style={{ padding: '4px 8px', color: 'var(--danger)' }}>
                      <Trash2 size={14} aria-hidden="true" />
                    </button>
                  )}
                </Td>
              </tr>
            ))}
            {!loading && users.length === 0 && (
              <tr><Td colSpan={10}
                    style={{ textAlign: 'center', padding: '2rem',
                             color: 'var(--text-muted)' }}>
                검색 조건에 맞는 사용자가 없습니다.
              </Td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* 페이지네이션 */}
      {total > PAGE_SIZE && (
        <div style={{ marginTop: '1rem', display: 'flex',
                      justifyContent: 'center', gap: '0.5rem' }}>
          <button className="btn btn-ghost"
                  onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                  disabled={offset === 0 || loading}>이전</button>
          <span style={{ alignSelf: 'center', color: 'var(--text-muted)' }}>
            {Math.floor(offset / PAGE_SIZE) + 1} / {Math.ceil(total / PAGE_SIZE)}
          </span>
          <button className="btn btn-ghost"
                  onClick={() => setOffset(offset + PAGE_SIZE)}
                  disabled={offset + PAGE_SIZE >= total || loading}>다음</button>
        </div>
      )}

      {/* 회원 상세 모달 */}
      {detailTarget && (
        <UserDetailModal
          user={detailTarget}
          onClose={() => setDetailTarget(null)}
          onDelete={(u) => { setDetailTarget(null); setDeleteTarget(u); }}
        />
      )}

      {/* 강제 탈퇴 확인 모달 */}
      {deleteTarget && (
        <DeleteUserModal
          user={deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onDeleted={() => { setDeleteTarget(null); reload(); }}
        />
      )}
    </div>
  );
}

function Th({ children }) {
  return <th style={{ padding: '0.75rem 0.85rem', textAlign: 'left',
                      fontWeight: 600, color: 'var(--text-secondary)' }}>{children}</th>;
}
function Td({ children, ...rest }) {
  return <td style={{ padding: '0.75rem 0.85rem' }} {...rest}>{children}</td>;
}
function Badge({ color, children }) {
  return <span style={{ display: 'inline-block', padding: '2px 8px',
                        borderRadius: 999, fontSize: 'var(--fs-xs)',
                        border: `1px solid ${color}`, color }}>
    {children}
  </span>;
}

function UserDetailModal({ user, onClose, onDelete }) {
  const rows = [
    ['ID',     user.id],
    ['이메일',  <code key="email">{user.email}</code>],
    ['채널',    user.provider || '—'],
    ['언어',    user.language || '—'],
    ['연령',    user.age_group === 'adult' ? '성인' : user.age_group === 'minor' ? '미성년' : '—'],
    ['가입일',  user.created_at?.slice(0, 10) || '—'],
    ['채팅방',  user.chat_rooms_count ?? '—'],
    ['신고 수', user.reported_count ?? '—'],
    ['상태',    user.deleted_at ? '탈퇴' : '활성'],
    ['탈퇴일',  user.deleted_at?.slice(0, 10) || '—'],
  ];
  return (
    <Modal
      open={true}
      onClose={onClose}
      size="md"
      title={`회원 상세 — #${user.id}`}
      footer={
        <>
          {!user.deleted_at && (
            <button
              className="btn btn-ghost"
              style={{ color: 'var(--danger)' }}
              onClick={() => onDelete(user)}
            >
              강제 탈퇴
            </button>
          )}
          <button className="btn btn-primary" onClick={onClose}>닫기</button>
        </>
      }
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

function DeleteUserModal({ user, onClose, onDeleted }) {
  const [reason, setReason] = useState('');
  const [busy, setBusy]     = useState(false);
  const [err, setErr]       = useState('');

  async function submit() {
    setBusy(true); setErr('');
    try {
      await adminApi.adminForceDeleteUser(user.id, reason.trim());
      onDeleted?.();
    } catch (e) {
      setErr(e?.message || '실패');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      open={true}
      onClose={busy ? undefined : onClose}
      size="sm"
      title="강제 탈퇴"
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>취소</button>
          <button className="btn btn-primary"
                  style={{ background: 'var(--danger)', borderColor: 'var(--danger)' }}
                  onClick={submit} disabled={busy}>
            {busy ? '처리 중...' : '강제 탈퇴'}
          </button>
        </>
      }
    >
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start',
                    padding: '0.75rem', background: 'var(--bg-3)',
                    border: '1px solid var(--danger)', borderRadius: 8,
                    marginBottom: '1rem' }}>
        <AlertTriangle size={18} color="var(--danger)" aria-hidden="true"
                       style={{ flexShrink: 0, marginTop: 2 }} />
        <div style={{ fontSize: 'var(--fs-sm)' }}>
          <strong>{user.email}</strong> (ID {user.id}) 를 즉시 탈퇴 처리합니다.
          이메일은 익명화되고 푸시 토큰이 삭제되며 30일 후 영구 삭제됩니다.
          <br />감사 로그에 처리자 + 사유가 남습니다.
        </div>
      </div>
      <label className="form-label">
        <span>사유 (감사용)</span>
        <textarea rows={2} value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="예: 신고 누적 / 위반 / 사용자 요청 대행"
                  disabled={busy} />
      </label>
      {err && <div className="error-box" style={{ marginTop: '0.75rem' }}>{err}</div>}
    </Modal>
  );
}
