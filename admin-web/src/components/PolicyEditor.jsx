import React, { useState, useEffect } from 'react';
import {
  MDXEditor, headingsPlugin, listsPlugin, quotePlugin,
  thematicBreakPlugin, markdownShortcutPlugin, linkPlugin,
  toolbarPlugin, UndoRedo, BoldItalicUnderlineToggles,
  BlockTypeSelect, ListsToggle, CreateLink, InsertThematicBreak,
} from '@mdxeditor/editor';
import '@mdxeditor/editor/style.css';
import './PolicyEditor.css';

import Modal from './Modal.jsx';
import { adminApi } from '../services/admin.js';
import { KIND_OPTIONS } from '../pages/Policies.jsx';

/**
 * 정책 작성/수정 에디터.
 *  - target = {} → 새 버전 (kind 선택 가능)
 *  - target = row → 미시행 버전 수정 (kind/version 고정)
 */
export default function PolicyEditor({ target, onClose, onSaved }) {
  const isNew = !target?.id;
  const [kind, setKind] = useState(target?.kind || 'terms');
  const [version, setVersion] = useState(target?.version || _todayIso());
  const [title, setTitle] = useState(target?.title || '');
  const [body, setBody] = useState(target?.body || '');
  const [changeLog, setChangeLog] = useState(target?.change_log || '');
  const [effectiveAt, setEffectiveAt] = useState(
    target?.effective_at?.slice(0, 16) || _nextHour()
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [loadedFromDb, setLoadedFromDb] = useState(!!target?.id);

  // 새 버전 생성이면, 같은 kind 의 현재 시행 본문을 미리 로드 (편의)
  useEffect(() => {
    if (!isNew) return;
    if (loadedFromDb) return;
    if (body && body.trim().length > 0) return;
    adminApi.getActivePolicy(kind)
      .then((p) => {
        if (p?.body) setBody(p.body);
        setLoadedFromDb(true);
      })
      .catch(() => {});
  }, [kind, isNew, body, loadedFromDb]);

  async function handleSave() {
    setBusy(true); setError('');
    try {
      const payload = {
        kind, lang: 'ko', version,
        title: title.trim() || null,
        body, change_log: changeLog.trim() || null,
        effective_at: new Date(effectiveAt).toISOString(),
      };
      if (isNew) {
        await adminApi.createPolicy(payload);
      } else {
        await adminApi.updatePolicy(target.id, {
          title: payload.title, body: payload.body,
          change_log: payload.change_log, effective_at: payload.effective_at,
        });
      }
      onSaved?.();
    } catch (e) {
      setError(e.message || '저장 실패');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      open={true}
      onClose={busy ? undefined : onClose}
      size="lg"
      title={isNew ? '새 정책 버전 작성' : `정책 #${target.id} 수정`}
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>취소</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={busy || !body.trim()}>
            {busy ? '저장 중...' : (isNew ? '발행' : '저장')}
          </button>
        </>
      }
    >
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.875rem', marginBottom: '0.875rem' }}>
        <label className="form-label">
          <span>항목</span>
          <select value={kind} onChange={(e) => setKind(e.target.value)} disabled={!isNew || busy}>
            {KIND_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </label>
        <label className="form-label">
          <span>버전 (예: 2026-05-05)</span>
          <input value={version} onChange={(e) => setVersion(e.target.value)}
                 disabled={!isNew || busy} />
        </label>
      </div>

      <label className="form-label">
        <span>제목 (생략 가능)</span>
        <input value={title} onChange={(e) => setTitle(e.target.value)}
               placeholder="기본값: 항목 라벨" disabled={busy} />
      </label>

      <label className="form-label">
        <span>적용 일시</span>
        <input type="datetime-local" value={effectiveAt}
               onChange={(e) => setEffectiveAt(e.target.value)} disabled={busy} />
      </label>

      <label className="form-label">
        <span>변경 내역 (메일 공지에 사용)</span>
        <textarea rows={2} value={changeLog} onChange={(e) => setChangeLog(e.target.value)}
                  placeholder="예: 제3조 항목 명확화, 제5조 추가" disabled={busy} />
      </label>

      <label className="form-label">
        <span>본문 (Markdown)</span>
      </label>
      <div className="policy-editor-wrap">
        <MDXEditor
          markdown={body}
          onChange={setBody}
          plugins={[
            headingsPlugin(),
            listsPlugin(),
            quotePlugin(),
            thematicBreakPlugin(),
            linkPlugin(),
            markdownShortcutPlugin(),
            toolbarPlugin({
              toolbarContents: () => (
                <>
                  <UndoRedo />
                  <BoldItalicUnderlineToggles />
                  <BlockTypeSelect />
                  <ListsToggle />
                  <CreateLink />
                  <InsertThematicBreak />
                </>
              ),
            }),
          ]}
        />
      </div>

      {error && <div className="error-box" style={{ marginTop: '0.75rem' }}>{error}</div>}
    </Modal>
  );
}


function _todayIso() {
  const d = new Date();
  return d.toISOString().slice(0, 10);
}

function _nextHour() {
  const d = new Date();
  d.setMinutes(0, 0, 0);
  d.setHours(d.getHours() + 1);
  return d.toISOString().slice(0, 16);
}
