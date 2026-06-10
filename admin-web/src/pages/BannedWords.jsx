/**
 * 금지어 관리 (2026-06-09).
 * - 욕설 / 성적 / 도박 / 불법 / 광고 / 일반 카테고리 분리
 * - severity: block (차단) / warn (경고)
 * - PathWave (매장명·리뷰·채팅) + woorichat (프로필·채팅) 공통 사용
 */
import React, { useEffect, useState } from 'react';
import { adminApi as admin } from '../services/admin.js';

// 한국 표준 분류 (정보통신망법 제44조의7 / KISO / 카카오·네이버 운영정책 / 틴더 커뮤니티 가이드 기준)
const KIND_LABEL = {
  profanity:     '욕설/폭력',
  sexual:        '음란/성적',
  hate:          '혐오/차별',
  defamation:    '명예훼손/모욕',
  gambling:      '도박/사행성',
  illegal:       '마약/불법',
  self_harm:     '자해/자살',
  ads:           '광고/스팸',
  impersonation: '사칭/피싱',
  privacy_leak:  '개인정보 유출',
  general:       '일반',
};

const SEVERITY_LABEL = {
  block: '차단',
  warn:  '경고',
};

export default function BannedWords() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [q, setQ] = useState('');
  const [kindFilter, setKindFilter] = useState('');
  const [newWord, setNewWord] = useState('');
  const [newKind, setNewKind] = useState('general');
  const [newSeverity, setNewSeverity] = useState('block');
  const [newNote, setNewNote] = useState('');

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const qs = [];
      if (q) qs.push(`q=${encodeURIComponent(q)}`);
      if (kindFilter) qs.push(`kind=${kindFilter}`);
      const res = await admin.listBannedWords(q, kindFilter);
      setItems(res.items || []);
    } catch (e) {
      setError(e.message || '로드 실패');
    } finally {
      setLoading(false);
    }
  }

  async function addWord() {
    if (!newWord.trim()) {
      setError('금지어를 입력하세요.');
      return;
    }
    try {
      await admin.createBannedWord({ word: newWord.trim(), kind: newKind, severity: newSeverity, note: newNote.trim() || null });
      setNewWord(''); setNewNote('');
      await load();
    } catch (e) {
      setError(e.message || '등록 실패');
    }
  }

  async function delWord(id) {
    if (!confirm('이 금지어를 삭제할까요?')) return;
    try {
      await admin.deleteBannedWord(id);
      await load();
    } catch (e) {
      setError(e.message || '삭제 실패');
    }
  }

  useEffect(() => { load(); }, []);

  // kind 별 그룹
  const grouped = {};
  for (const it of items) {
    grouped[it.kind] = grouped[it.kind] || [];
    grouped[it.kind].push(it);
  }

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div>
          <h1>금지어 관리</h1>
          <p className="page-subtitle">
            매장명·리뷰·채팅·프로필 등에 사용 시 차단/경고되는 단어.
            PathWave + woorichat 공통 적용.
          </p>
        </div>
        <button className="btn" onClick={load} disabled={loading}>
          {loading ? '로딩…' : '새로고침'}
        </button>
      </div>

      {error && <div className="alert-danger">{error}</div>}

      {/* 신규 등록 */}
      <section style={{
        marginTop: 16, padding: 16,
        background: 'rgba(255,255,255,0.04)',
        borderRadius: 10, border: '1px solid rgba(255,255,255,0.10)',
      }}>
        <h3 style={{ margin: '0 0 12px', fontSize: 14 }}>신규 등록</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 2fr auto', gap: 8 }}>
          <input
            placeholder="금지어"
            value={newWord}
            onChange={e => setNewWord(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') addWord(); }}
            style={inputStyle}
          />
          <select value={newKind} onChange={e => setNewKind(e.target.value)} style={inputStyle}>
            {Object.entries(KIND_LABEL).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          <select value={newSeverity} onChange={e => setNewSeverity(e.target.value)} style={inputStyle}>
            {Object.entries(SEVERITY_LABEL).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          <input
            placeholder="비고 (선택)"
            value={newNote}
            onChange={e => setNewNote(e.target.value)}
            style={inputStyle}
          />
          <button className="btn-primary" onClick={addWord}>추가</button>
        </div>
      </section>

      {/* 검색 + 필터 */}
      <section style={{ marginTop: 16, display: 'flex', gap: 8 }}>
        <input
          placeholder="단어 검색"
          value={q}
          onChange={e => setQ(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') load(); }}
          style={{ ...inputStyle, flex: 1 }}
        />
        <select value={kindFilter} onChange={e => setKindFilter(e.target.value)} style={inputStyle}>
          <option value="">전체 카테고리</option>
          {Object.entries(KIND_LABEL).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <button className="btn" onClick={load}>검색</button>
      </section>

      {/* 그룹별 목록 */}
      <div style={{ marginTop: 24 }}>
        {Object.keys(KIND_LABEL).map(kind => {
          const list = grouped[kind];
          if (!list || list.length === 0) return null;
          return (
            <section key={kind} style={{ marginBottom: 24 }}>
              <h3 style={{ margin: '0 0 10px', fontSize: 14, color: 'rgba(255,255,255,0.85)' }}>
                {KIND_LABEL[kind]} ({list.length})
              </h3>
              <div style={{ display: 'grid', gap: 6 }}>
                {list.map(it => (
                  <div key={it.id} style={{
                    display: 'grid',
                    gridTemplateColumns: '120px 80px 1fr auto',
                    gap: 12, alignItems: 'center',
                    padding: '10px 14px',
                    background: 'rgba(255,255,255,0.04)',
                    borderRadius: 8,
                  }}>
                    <code style={{ color: '#fff', fontWeight: 600 }}>{it.word}</code>
                    <span style={{
                      padding: '2px 8px',
                      background: it.severity === 'block'
                        ? 'rgba(239,68,68,0.25)' : 'rgba(245,158,11,0.25)',
                      color: it.severity === 'block' ? '#FCA5A5' : '#FCD34D',
                      borderRadius: 4, fontSize: 11, fontWeight: 700,
                      textAlign: 'center',
                    }}>{SEVERITY_LABEL[it.severity]}</span>
                    <span style={{ color: 'rgba(255,255,255,0.6)', fontSize: 12 }}>
                      {it.note || '—'}
                    </span>
                    <button
                      onClick={() => delWord(it.id)}
                      style={{
                        background: 'none', border: '1px solid rgba(239,68,68,0.4)',
                        color: '#FCA5A5', padding: '4px 10px',
                        borderRadius: 4, cursor: 'pointer', fontSize: 12,
                      }}
                    >삭제</button>
                  </div>
                ))}
              </div>
            </section>
          );
        })}
        {items.length === 0 && !loading && (
          <div style={{ padding: 40, textAlign: 'center', opacity: 0.6 }}>
            등록된 금지어가 없습니다.
          </div>
        )}
      </div>
    </div>
  );
}

const inputStyle = {
  padding: '8px 12px',
  background: 'rgba(255,255,255,0.05)',
  border: '1px solid rgba(255,255,255,0.20)',
  borderRadius: 6,
  color: 'white',
  fontSize: 13,
};
