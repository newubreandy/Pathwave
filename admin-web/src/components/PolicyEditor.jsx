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
 *  - target = {} → 새 버전 (kind 선택 + ko/en 동시 입력)  ← C-2-4c
 *  - target = row → 미시행 버전 수정 (한 lang 만, 기존 단일 모드 호환)
 */
export default function PolicyEditor({ target, onClose, onSaved }) {
  const isNew = !target?.id;
  const [kind, setKind] = useState(target?.kind || 'terms_user');
  const [version, setVersion] = useState(target?.version || _todayIso());
  const [effectiveAt, setEffectiveAt] = useState(
    target?.effective_at?.slice(0, 16) || _nextHour()
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  // C-2-4c — 신규 모드: ko/en 양쪽 state. 편집 모드: 단일 (target.lang 의 것).
  const [titleKo, setTitleKo] = useState(target?.lang === 'ko' ? (target?.title || '') : '');
  const [bodyKo,  setBodyKo]  = useState(target?.lang === 'ko' ? (target?.body  || '') : '');
  const [logKo,   setLogKo]   = useState(target?.lang === 'ko' ? (target?.change_log || '') : '');
  const [titleEn, setTitleEn] = useState(target?.lang === 'en' ? (target?.title || '') : '');
  const [bodyEn,  setBodyEn]  = useState(target?.lang === 'en' ? (target?.body  || '') : '');
  const [logEn,   setLogEn]   = useState(target?.lang === 'en' ? (target?.change_log || '') : '');

  // 편집 모드는 target.lang 의 본문만 채움. 신규는 빈 본문에서 시작.
  const [activeTab, setActiveTab] = useState(target?.lang === 'en' ? 'en' : 'ko');

  // 신규 모드 — 같은 kind 의 현재 시행 ko/en 본문을 미리 로드 (편의)
  const [loaded, setLoaded] = useState(!isNew);
  useEffect(() => {
    if (!isNew || loaded) return;
    Promise.all([
      adminApi.getActivePolicy(kind, 'ko').catch(() => null),
      adminApi.getActivePolicy(kind, 'en').catch(() => null),
    ]).then(([ko, en]) => {
      if (ko?.body && !bodyKo) setBodyKo(ko.body);
      if (en?.body && !bodyEn) setBodyEn(en.body);
      setLoaded(true);
    });
  }, [kind, isNew, loaded, bodyKo, bodyEn]);

  async function handleSave() {
    setBusy(true); setError('');
    try {
      if (isNew) {
        // ko + en 두 본문 다 필수
        if (!bodyKo.trim() || !bodyEn.trim()) {
          throw new Error('한국어 본문과 영문 본문 둘 다 입력해 주세요.');
        }
        await adminApi.createPolicyMultilang({
          kind, version,
          effective_at: new Date(effectiveAt).toISOString(),
          ko: {
            title: titleKo.trim() || null,
            body:  bodyKo,
            change_log: logKo.trim() || null,
          },
          en: {
            title: titleEn.trim() || null,
            body:  bodyEn,
            change_log: logEn.trim() || null,
          },
        });
      } else {
        // 편집 모드 — 단일 lang (기존과 동일)
        const isKo = target.lang === 'ko';
        const t = isKo ? titleKo : titleEn;
        const b = isKo ? bodyKo  : bodyEn;
        const l = isKo ? logKo   : logEn;
        if (!b.trim()) throw new Error('본문을 입력해 주세요.');
        await adminApi.updatePolicy(target.id, {
          title: t.trim() || null,
          body: b,
          change_log: l.trim() || null,
          effective_at: new Date(effectiveAt).toISOString(),
        });
      }
      onSaved?.();
    } catch (e) {
      setError(e.message || '저장 실패');
    } finally {
      setBusy(false);
    }
  }

  // 현재 탭의 state binding (편집 모드에서도 같은 컴포넌트로 일관 처리)
  const tabBody     = activeTab === 'ko' ? bodyKo  : bodyEn;
  const setTabBody  = activeTab === 'ko' ? setBodyKo  : setBodyEn;
  const tabTitle    = activeTab === 'ko' ? titleKo : titleEn;
  const setTabTitle = activeTab === 'ko' ? setTitleKo : setTitleEn;
  const tabLog      = activeTab === 'ko' ? logKo   : logEn;
  const setTabLog   = activeTab === 'ko' ? setLogKo   : setLogEn;

  // 편집 모드는 target.lang 만 탭 사용 가능, 신규는 ko/en 둘 다.
  const canSwitchTab = isNew;

  return (
    <Modal
      open={true}
      onClose={busy ? undefined : onClose}
      size="lg"
      title={isNew ? '새 정책 버전 작성 (한국어 + English)' : `정책 #${target.id} 수정`}
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>취소</button>
          <button className="btn btn-primary"
                  onClick={handleSave}
                  disabled={busy || (isNew ? (!bodyKo.trim() || !bodyEn.trim()) : !tabBody.trim())}>
            {busy ? '저장 중...' : (isNew ? '발행 (ko+en)' : '저장')}
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
        <span>적용 일시</span>
        <input type="datetime-local" value={effectiveAt}
               onChange={(e) => setEffectiveAt(e.target.value)} disabled={busy} />
      </label>

      {/* C-2-4c — ko/en 탭 split (신규 모드만 toggle 가능, 편집 모드는 target.lang 고정) */}
      <div style={{ display: 'flex', gap: 4, marginBottom: '0.875rem',
                    borderBottom: '1px solid var(--border)' }}>
        {['ko', 'en'].map((l) => (
          <button
            key={l}
            onClick={() => canSwitchTab && setActiveTab(l)}
            disabled={!canSwitchTab && activeTab !== l}
            style={{
              padding: '8px 18px',
              background: activeTab === l ? 'var(--bg-2)' : 'transparent',
              border: 'none',
              borderBottom: activeTab === l ? '2px solid var(--accent)' : '2px solid transparent',
              color:      activeTab === l ? 'var(--text)' : 'var(--text-muted)',
              fontWeight: activeTab === l ? 600 : 400,
              cursor: (canSwitchTab || activeTab === l) ? 'pointer' : 'not-allowed',
              fontSize: 'var(--fs-sm)',
            }}
          >
            {l === 'ko' ? '한국어 본문' : 'English Body'}
            {isNew && (
              <span style={{
                marginLeft: 6, fontSize: 10,
                color: (l === 'ko' ? bodyKo.trim() : bodyEn.trim()) ? 'var(--accent)' : 'var(--danger)',
              }}>
                {(l === 'ko' ? bodyKo.trim() : bodyEn.trim()) ? '●' : '○'}
              </span>
            )}
          </button>
        ))}
      </div>

      <label className="form-label">
        <span>제목 (생략 가능)</span>
        <input value={tabTitle} onChange={(e) => setTabTitle(e.target.value)}
               placeholder="기본값: 항목 라벨" disabled={busy} />
      </label>

      <label className="form-label">
        <span>변경 내역 (메일 공지에 사용)</span>
        <textarea rows={2} value={tabLog} onChange={(e) => setTabLog(e.target.value)}
                  placeholder="예: 제3조 항목 명확화, 제5조 추가" disabled={busy} />
      </label>

      <label className="form-label">
        <span>본문 (Markdown)</span>
      </label>
      <div className="policy-editor-wrap">
        <MDXEditor
          // C-2-4c — key 를 활성 탭별로 분리해 MDXEditor 재마운트 (state 충돌 방지)
          key={`mdx-${activeTab}`}
          markdown={tabBody}
          onChange={setTabBody}
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

      {isNew && (
        <div style={{ marginTop: '0.75rem', padding: '0.6rem 0.8rem',
                      borderRadius: 6, background: 'var(--bg-3)',
                      border: '1px solid var(--border)',
                      fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>
          💡 새 버전은 <strong>한국어 + 영문 본문 둘 다 필수</strong>입니다.
          같은 버전·적용일로 두 row 가 동시에 등록됩니다.
        </div>
      )}

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
