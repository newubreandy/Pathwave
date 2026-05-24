import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  RefreshCw, Search, Globe, Plus, CheckCircle2, AlertTriangle,
} from 'lucide-react';
import Modal from '../components/Modal.jsx';
import { i18nApi } from '../services/i18n.js';
import './Beacons.css';

// source 별 뱃지 색상
const SOURCE_COLOR = {
  manual: 'var(--accent)',
  seed:   'var(--text-muted)',
  deepl:  '#38bdf8',
  stub:   'var(--text-hint)',
};
function sourceLabel(src) {
  if (src === 'manual') return '수동';
  if (src === 'seed')   return '시드';
  if (src === 'deepl')  return 'DeepL';
  if (src === 'stub')   return 'stub';
  return src || '—';
}

export default function Translations() {
  const [grid, setGrid]               = useState([]);          // keys[]
  const [langs, setLangs]             = useState([]);          // supported_langs[]
  const [deeplOk, setDeeplOk]         = useState(true);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState('');
  const [q, setQ]                     = useState('');
  const [missingLang, setMissingLang] = useState('');          // '' = 전체
  const [missingKeys, setMissingKeys] = useState(null);        // Set<key> | null
  const [editRow, setEditRow]         = useState(null);        // 행 클릭 → 편집 모달
  const [addOpen, setAddOpen]         = useState(false);

  const reload = useCallback(() => {
    setLoading(true);
    setError('');
    i18nApi.loadGrid()
      .then((data) => {
        setGrid(data.keys || []);
        setLangs(data.supported_langs || []);
        setDeeplOk(data.deepl_configured !== false);
      })
      .catch((err) => setError(err.message || '번역 목록을 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { reload(); }, [reload]);

  // 미번역 필터 적용
  useEffect(() => {
    if (!missingLang) { setMissingKeys(null); return; }
    i18nApi.loadMissing(missingLang)
      .then((data) => {
        const keys = (data.missing || []).map((k) => (typeof k === 'string' ? k : k.key));
        setMissingKeys(new Set(keys));
      })
      .catch(() => setMissingKeys(null));
  }, [missingLang]);

  // 검색 + 미번역 필터링
  const filteredGrid = grid.filter((row) => {
    const matchQ = !q.trim() || row.key.toLowerCase().includes(q.trim().toLowerCase());
    const matchMissing = !missingKeys || missingKeys.has(row.key);
    return matchQ && matchMissing;
  });

  return (
    <div className="modern-page">
      {/* ── 헤더 ── */}
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">i18n 관리</h1>
            <p className="sub-title">
              다국어 번역 키 관리 · DeepL 자동 번역 · 검수 완료 토글.
              지원 언어 {langs.length}개.
            </p>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading} aria-label="새로고침">
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
              <span>새로고침</span>
            </button>
            <button className="btn btn-primary" onClick={() => setAddOpen(true)} aria-label="번역 추가">
              <Plus size={16} />
              <span>키 추가</span>
            </button>
          </div>
        </div>

        {/* DeepL 미설정 배너 */}
        {!deeplOk && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '10px',
            background: 'rgba(234,179,8,0.10)', border: '1px solid rgba(234,179,8,0.35)',
            borderRadius: 'var(--radius)', padding: '12px 16px',
            fontSize: 'var(--fs-sm)', color: '#fbbf24',
          }}>
            <AlertTriangle size={16} style={{ flexShrink: 0 }} />
            <span>
              DeepL API 키가 설정되지 않았습니다.
              자동 번역은 <strong>[lang] 원문</strong> 형태의 stub 으로 채워집니다.
              실 작동을 위해 환경변수 <code>DEEPL_API_KEY</code>를 설정하세요.
            </span>
          </div>
        )}

        {/* 필터 바 */}
        <div className="filter-bar">
          <div className="filter-group filter-search">
            <Search size={16} />
            <input
              type="text"
              placeholder="키 검색"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <div className="filter-group">
            <Globe size={14} style={{ flexShrink: 0, color: 'var(--text-hint)' }} />
            <span className="filter-label">미번역만</span>
            <select
              value={missingLang}
              onChange={(e) => setMissingLang(e.target.value)}
            >
              <option value="">— 전체 —</option>
              {langs.map((l) => (
                <option key={l} value={l}>{l}</option>
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

      {/* ── 번역 그리드 테이블 ── */}
      <div className="card table-card" style={{ overflowX: 'auto' }}>
        <table className="data-table" style={{ minWidth: `${120 + langs.length * 110}px` }}>
          <thead>
            <tr>
              <th style={{ minWidth: 180, position: 'sticky', left: 0, background: 'var(--bg-3)', zIndex: 2 }}>
                키
              </th>
              {langs.map((l) => (
                <th key={l} style={{ minWidth: 110, textAlign: 'center' }}>{l}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={langs.length + 1} className="row-empty">로딩 중...</td>
              </tr>
            )}
            {!loading && filteredGrid.length === 0 && (
              <tr>
                <td colSpan={langs.length + 1} className="row-empty">
                  {q || missingLang ? '검색 결과가 없습니다.' : '번역 키가 없습니다. "키 추가" 버튼으로 등록하세요.'}
                </td>
              </tr>
            )}
            {!loading && filteredGrid.map((row) => (
              <tr
                key={row.key}
                style={{ cursor: 'pointer' }}
                onClick={() => setEditRow(row)}
                title="클릭하여 편집"
              >
                <td
                  className="cell-mono"
                  style={{
                    position: 'sticky', left: 0,
                    background: 'var(--bg-2)', zIndex: 1,
                    maxWidth: 200, overflow: 'hidden',
                    textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}
                >
                  {row.key}
                </td>
                {langs.map((l) => {
                  const cell = row.values?.[l];
                  return (
                    <td key={l} style={{ textAlign: 'center', verticalAlign: 'middle' }}>
                      {cell ? (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                          <span style={{
                            display: 'block', maxWidth: 96,
                            overflow: 'hidden', textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap', fontSize: 'var(--fs-xs)',
                            color: 'var(--text)',
                          }} title={cell.value}>
                            {cell.value}
                          </span>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                            <span style={{
                              fontSize: 10, color: SOURCE_COLOR[cell.source] || 'var(--text-hint)',
                            }}>
                              {sourceLabel(cell.source)}
                            </span>
                            {cell.verified && (
                              <CheckCircle2 size={10} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                            )}
                          </div>
                        </div>
                      ) : (
                        <span style={{ color: 'var(--text-hint)', fontSize: 'var(--fs-xs)' }}>—</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── 편집 모달 ── */}
      <EditRowModal
        row={editRow}
        langs={langs}
        onClose={() => setEditRow(null)}
        onSaved={() => { setEditRow(null); reload(); }}
      />

      {/* ── 키 추가 모달 ── */}
      <AddKeyModal
        open={addOpen}
        langs={langs}
        onClose={() => setAddOpen(false)}
        onAdded={() => { setAddOpen(false); reload(); }}
      />
    </div>
  );
}


// ── 행 편집 모달 ───────────────────────────────────────────────────────────
function EditRowModal({ row, langs, onClose, onSaved }) {
  const [koValue, setKoValue]   = useState('');
  const [cells, setCells]       = useState({});   // { lang: { value, verified } }
  const [busy, setBusy]         = useState(false);
  const [autoMsg, setAutoMsg]   = useState('');
  const [error, setError]       = useState('');
  const [editLang, setEditLang] = useState(null); // 인라인 편집 중인 언어

  // row 바뀔 때마다 초기화
  useEffect(() => {
    if (!row) return;
    setKoValue(row.values?.ko?.value || '');
    const init = {};
    langs.forEach((l) => {
      init[l] = {
        value:    row.values?.[l]?.value    || '',
        verified: row.values?.[l]?.verified || false,
        source:   row.values?.[l]?.source   || '',
      };
    });
    setCells(init);
    setAutoMsg('');
    setError('');
    setEditLang(null);
  }, [row, langs]);

  async function handleAutoTranslate() {
    if (!koValue.trim()) { setError('한국어 원문을 입력해 주세요.'); return; }
    setBusy(true); setError(''); setAutoMsg('');
    try {
      const data = await i18nApi.autoTranslate({ key: row.key, ko: koValue, onlyMissing: false });
      // data.translations: { lang: value } 또는 data.results
      const translations = data.translations || data.results || {};
      setCells((prev) => {
        const next = { ...prev };
        Object.entries(translations).forEach(([l, v]) => {
          if (l === 'ko') return;
          next[l] = { ...next[l], value: typeof v === 'string' ? v : v.value || '', source: 'deepl' };
        });
        return next;
      });
      // ko 도 upsert
      await i18nApi.upsert(row.key, 'ko', koValue, false);
      setAutoMsg(`자동 번역 완료 — ${Object.keys(translations).length}개 언어 갱신됨.`);
    } catch (err) {
      setError(err.message || '자동 번역에 실패했습니다.');
    } finally { setBusy(false); }
  }

  async function handleSaveCell(lang) {
    const cell = cells[lang];
    if (!cell) return;
    setBusy(true); setError('');
    try {
      await i18nApi.upsert(row.key, lang, cell.value, cell.verified);
      setEditLang(null);
      setAutoMsg(`${lang} 저장 완료.`);
    } catch (err) {
      setError(err.message || '저장에 실패했습니다.');
    } finally { setBusy(false); }
  }

  async function handleToggleVerified(lang) {
    const cell = cells[lang];
    if (!cell || !cell.value) return;
    const newVerified = !cell.verified;
    setBusy(true); setError('');
    try {
      await i18nApi.upsert(row.key, lang, cell.value, newVerified);
      setCells((prev) => ({ ...prev, [lang]: { ...prev[lang], verified: newVerified } }));
    } catch (err) {
      setError(err.message || '검수 상태 변경에 실패했습니다.');
    } finally { setBusy(false); }
  }

  if (!row) return null;

  return (
    <Modal
      open={!!row}
      onClose={onClose}
      title={`번역 편집 — ${row.key}`}
      size="xl"
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>닫기</button>
          <button className="btn btn-primary" onClick={onSaved} disabled={busy}>완료</button>
        </>
      }
    >
      {/* 한국어 원문 + 자동 번역 */}
      <div style={{ marginBottom: 16 }}>
        <label className="form-label">
          <span>한국어 원문 (ko)</span>
          <textarea
            rows={3}
            value={koValue}
            onChange={(e) => setKoValue(e.target.value)}
            placeholder="한국어 텍스트를 입력하세요"
            disabled={busy}
          />
        </label>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            className="btn btn-primary"
            onClick={handleAutoTranslate}
            disabled={busy || !koValue.trim()}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
          >
            <Globe size={15} />
            {busy ? '번역 중...' : `자동 번역 ${langs.filter(l => l !== 'ko').length}개 언어`}
          </button>
          {autoMsg && (
            <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--accent)' }}>{autoMsg}</span>
          )}
        </div>
      </div>

      {error && <div className="error-box" style={{ marginBottom: 12 }}>{error}</div>}

      {/* 언어별 셀 편집 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
        gap: 12,
        maxHeight: 480,
        overflowY: 'auto',
        paddingRight: 4,
      }}>
        {langs.filter(l => l !== 'ko').map((l) => {
          const cell = cells[l] || { value: '', verified: false, source: '' };
          const isEditing = editLang === l;
          return (
            <div key={l} style={{
              background: 'var(--bg-4)',
              border: `1px solid ${isEditing ? 'var(--accent)' : 'var(--border)'}`,
              borderRadius: 'var(--radius)',
              padding: '12px 14px',
            }}>
              <div style={{
                display: 'flex', justifyContent: 'space-between',
                alignItems: 'center', marginBottom: 6,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{
                    fontWeight: 600, fontSize: 'var(--fs-sm)',
                    color: 'var(--text)', fontFamily: 'ui-monospace, monospace',
                  }}>{l}</span>
                  {cell.source && (
                    <span style={{
                      fontSize: 10,
                      color: SOURCE_COLOR[cell.source] || 'var(--text-hint)',
                    }}>
                      {sourceLabel(cell.source)}
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  {/* 검수 완료 체크박스 */}
                  <label
                    style={{
                      display: 'flex', alignItems: 'center', gap: 4,
                      fontSize: 'var(--fs-xs)', color: cell.verified ? 'var(--accent)' : 'var(--text-hint)',
                      cursor: cell.value ? 'pointer' : 'default',
                    }}
                    title="검수 완료 토글"
                  >
                    <input
                      type="checkbox"
                      checked={cell.verified}
                      disabled={busy || !cell.value}
                      onChange={() => handleToggleVerified(l)}
                      style={{ width: 13, height: 13, accentColor: 'var(--accent)' }}
                    />
                    검수
                  </label>
                </div>
              </div>

              {isEditing ? (
                <div>
                  <textarea
                    rows={2}
                    value={cell.value}
                    onChange={(e) => setCells((prev) => ({
                      ...prev, [l]: { ...prev[l], value: e.target.value },
                    }))}
                    disabled={busy}
                    style={{
                      width: '100%', fontSize: 'var(--fs-sm)',
                      resize: 'vertical', marginBottom: 6,
                    }}
                    autoFocus
                  />
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => handleSaveCell(l)}
                      disabled={busy}
                    >저장</button>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => setEditLang(null)}
                      disabled={busy}
                    >취소</button>
                  </div>
                </div>
              ) : (
                <div
                  onClick={() => setEditLang(l)}
                  style={{
                    fontSize: 'var(--fs-sm)', color: cell.value ? 'var(--text)' : 'var(--text-hint)',
                    cursor: 'text', minHeight: 40, wordBreak: 'break-word',
                    padding: '4px 0',
                  }}
                  title="클릭하여 편집"
                >
                  {cell.value || <em style={{ fontSize: 'var(--fs-xs)' }}>미번역 — 클릭하여 입력</em>}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Modal>
  );
}


// ── 키 추가 모달 ───────────────────────────────────────────────────────────
function AddKeyModal({ open, langs, onClose, onAdded }) {
  const [key, setKey]     = useState('');
  const [ko, setKo]       = useState('');
  const [busy, setBusy]   = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (open) { setKey(''); setKo(''); setError(''); }
  }, [open]);

  async function handleAdd() {
    if (!key.trim())  { setError('키 이름을 입력해 주세요.'); return; }
    if (!ko.trim())   { setError('한국어 원문을 입력해 주세요.'); return; }
    setBusy(true); setError('');
    try {
      await i18nApi.upsert(key.trim(), 'ko', ko.trim(), false);
      onAdded?.();
    } catch (err) {
      setError(err.message || '키 추가에 실패했습니다.');
    } finally { setBusy(false); }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="새 번역 키 추가"
      size="sm"
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>취소</button>
          <button className="btn btn-primary" onClick={handleAdd} disabled={busy || !key.trim() || !ko.trim()}>
            {busy ? '추가 중...' : '추가'}
          </button>
        </>
      }
    >
      <label className="form-label">
        <span>키 이름</span>
        <input
          type="text"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder="예: common.button.save"
          disabled={busy}
        />
      </label>
      <label className="form-label">
        <span>한국어 원문 (ko)</span>
        <textarea
          rows={3}
          value={ko}
          onChange={(e) => setKo(e.target.value)}
          placeholder="한국어 텍스트"
          disabled={busy}
        />
      </label>
      {error && <div className="error-box">{error}</div>}
    </Modal>
  );
}
