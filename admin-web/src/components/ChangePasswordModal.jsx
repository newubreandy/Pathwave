/**
 * A-024 — 운영자 본인 비밀번호 변경 모달.
 *
 * POST /api/admin/change-password.
 * 부트스트랩 초기 비번을 운영 전 강제 변경할 때도 사용.
 */
import React, { useState } from 'react';
import Modal from './Modal.jsx';
import { adminApi } from '../services/admin.js';

export default function ChangePasswordModal({ open, onClose, onChanged }) {
  const [cur, setCur]     = useState('');
  const [nw, setNw]       = useState('');
  const [nw2, setNw2]     = useState('');
  const [busy, setBusy]   = useState(false);
  const [err, setErr]     = useState('');
  const [ok, setOk]       = useState('');

  function reset() {
    setCur(''); setNw(''); setNw2(''); setErr(''); setOk('');
  }

  async function submit(e) {
    e?.preventDefault?.();
    setErr(''); setOk('');
    if (!cur || !nw) { setErr('현재/신규 비밀번호 모두 입력해 주세요.'); return; }
    if (nw !== nw2)  { setErr('새 비밀번호 확인이 일치하지 않습니다.'); return; }
    if (nw === cur)  { setErr('새 비밀번호가 기존과 같습니다.');         return; }
    setBusy(true);
    try {
      await adminApi.changeMyPassword(cur, nw);
      setOk('비밀번호가 변경되었습니다.');
      onChanged?.();
      setTimeout(() => { reset(); onClose?.(); }, 800);
    } catch (e) {
      setErr(e?.message || '변경 실패');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      open={open}
      onClose={busy ? undefined : () => { reset(); onClose?.(); }}
      size="sm"
      title="운영자 비밀번호 변경"
      footer={
        <>
          <button className="btn btn-ghost" type="button"
                  onClick={() => { reset(); onClose?.(); }}
                  disabled={busy}>취소</button>
          <button className="btn btn-primary" type="button"
                  onClick={submit}
                  disabled={busy || !cur || !nw || !nw2}>
            {busy ? '변경 중...' : '변경'}
          </button>
        </>
      }
    >
      <form onSubmit={submit}>
        <label className="form-label">
          <span>현재 비밀번호</span>
          <input type="password" value={cur}
                 onChange={(e) => setCur(e.target.value)}
                 disabled={busy} autoComplete="current-password"
                 autoFocus />
        </label>
        <label className="form-label">
          <span>새 비밀번호 (8자+, 대소문자/숫자/특수)</span>
          <input type="password" value={nw}
                 onChange={(e) => setNw(e.target.value)}
                 disabled={busy} autoComplete="new-password" />
        </label>
        <label className="form-label">
          <span>새 비밀번호 확인</span>
          <input type="password" value={nw2}
                 onChange={(e) => setNw2(e.target.value)}
                 disabled={busy} autoComplete="new-password" />
        </label>

        {err && <div className="error-box" style={{ marginTop: '0.75rem' }}>{err}</div>}
        {ok  && <div style={{ marginTop: '0.75rem',
                              padding: '0.5rem 0.75rem',
                              background: 'var(--accent-soft)',
                              border: '1px solid var(--accent)',
                              borderRadius: 6, color: 'var(--accent)' }}>
                  {ok}
                </div>}
      </form>
    </Modal>
  );
}
