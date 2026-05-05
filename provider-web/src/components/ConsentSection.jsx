/**
 * 회원가입 동의 섹션 — PR #45.
 *
 * Props:
 *   - subType: 'user' | 'facility'
 *   - value: { [kind]: boolean }
 *   - onChange: (next) => void
 *
 * 백엔드 `/api/policies?sub_type=` 으로 항목 메타 fetch, 보기 클릭 시 본문 모달.
 */
import React, { useEffect, useState } from 'react';
import './ConsentSection.css';

export default function ConsentSection({ subType = 'facility', value = {}, onChange }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalKind, setModalKind] = useState(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    fetch(`/api/policies?sub_type=${subType}`)
      .then((r) => r.json())
      .then((data) => { if (alive) setItems(data.items || []); })
      .catch(() => { if (alive) setItems([]); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [subType]);

  function toggle(kind, v) {
    onChange?.({ ...value, [kind]: v });
  }

  function toggleAll(v) {
    const next = {};
    items.forEach((it) => { next[it.kind] = v; });
    onChange?.(next);
  }

  const allChecked = items.length > 0 && items.every((it) => value[it.kind]);

  if (loading) return <div className="consent-loading">동의 항목을 불러오는 중...</div>;

  return (
    <div className="consent-section">
      <h3>약관 및 동의</h3>
      <p className="consent-hint">필수 항목에 모두 동의해야 가입할 수 있습니다.</p>

      <label className="consent-all" onClick={(e) => { e.preventDefault(); toggleAll(!allChecked); }}>
        <input type="checkbox" checked={allChecked} readOnly />
        <span>전체 동의 (선택 항목 포함)</span>
      </label>

      <div className="consent-list">
        {items.map((it) => (
          <div key={it.kind} className="consent-row">
            <label>
              <input
                type="checkbox"
                checked={!!value[it.kind]}
                onChange={(e) => toggle(it.kind, e.target.checked)}
              />
              <span className={`consent-required ${it.required ? 'required' : 'optional'}`}>
                {it.required ? '필수' : '선택'}
              </span>
              <span className="consent-label">{it.label}</span>
            </label>
            <button
              type="button"
              className="consent-view-btn"
              onClick={() => setModalKind(it.kind)}
            >
              보기
            </button>
          </div>
        ))}
      </div>

      {modalKind && (
        <PolicyModal kind={modalKind} onClose={() => setModalKind(null)} />
      )}
    </div>
  );
}


function PolicyModal({ kind, onClose }) {
  const [body, setBody] = useState('');
  const [label, setLabel] = useState('');
  const [needsContent, setNeedsContent] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    fetch(`/api/policies/${kind}?lang=ko`)
      .then((r) => r.json())
      .then((data) => {
        if (!alive) return;
        setBody(data.body || '');
        setLabel(data.label || kind);
        setNeedsContent(!!data.needs_content);
      })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [kind]);

  return (
    <div className="policy-modal-backdrop" onClick={onClose}>
      <div className="policy-modal" onClick={(e) => e.stopPropagation()}>
        <div className="policy-modal-header">
          <h4>{label}</h4>
          <button onClick={onClose}>×</button>
        </div>
        <div className="policy-modal-body">
          {loading ? (
            <div>로딩 중...</div>
          ) : (
            <>
              {needsContent && (
                <div className="policy-warning">
                  ⚠️ 정책 본문이 아직 등록되지 않았습니다 (placeholder).
                </div>
              )}
              <pre className="policy-body">{body}</pre>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
