/**
 * 매장 관리 (슈퍼어드민용 — 2026-06-09).
 *
 * - 모든 매장 리스트 + 행 클릭 = 상세 모달.
 * - mobile/provider 와 동일 노출 정보: 이미지/주소/설명/메뉴X(별도)/영업시간+휴무/혜택/연락처/좌표.
 * - 백엔드: GET /api/search/facilities (리스트) · GET /api/search/facilities/<id> (상세). 인증 X 공개.
 */
import React, { useEffect, useState } from 'react';

export default function Facilities() {
  const [list, setList] = useState([]);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [q, setQ] = useState('');

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/search/facilities${q ? `?q=${encodeURIComponent(q)}` : ''}`).then(r => r.json());
      setList(res.results || []);
    } catch (e) {
      setError(e.message || '로드 실패');
    } finally {
      setLoading(false);
    }
  }

  async function loadDetail(id) {
    try {
      const res = await fetch(`/api/search/facilities/${id}`).then(r => r.json());
      setDetail(res.facility || null);
    } catch (e) {
      setError(e.message || '상세 로드 실패');
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div>
          <h1>매장 관리</h1>
          <p className="page-subtitle">
            사용자 앱·시설관리자와 동일 노출 정보 (정기휴무 + 진행중 혜택 포함). 행 클릭 = 상세.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            placeholder="매장명/주소 검색"
            value={q}
            onChange={e => setQ(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') load(); }}
            style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.2)', background: 'rgba(255,255,255,0.05)', color: 'white' }}
          />
          <button className="btn" onClick={load} disabled={loading}>
            {loading ? '로딩…' : '새로고침'}
          </button>
        </div>
      </div>

      {error && <div className="alert-danger">{error}</div>}

      <div style={{ display: 'grid', gap: 8, marginTop: 16 }}>
        {list.map(f => (
          <div
            key={f.id}
            onClick={() => loadDetail(f.id)}
            style={{
              padding: '14px 16px',
              background: 'rgba(255,255,255,0.04)',
              borderRadius: 10,
              cursor: 'pointer',
              border: '1px solid rgba(255,255,255,0.10)',
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.08)'}
            onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.04)'}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              {f.image_url && (
                <img src={f.image_url} alt=""
                  style={{ width: 56, height: 56, objectFit: 'cover', borderRadius: 8, flexShrink: 0 }} />
              )}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600 }}>{f.name}</div>
                <div style={{ fontSize: 12, opacity: 0.7, marginTop: 2 }}>
                  <code>#{f.id}</code>
                  {f.address && <> · {f.address}</>}
                  {f.phone && <> · {f.phone}</>}
                </div>
              </div>
              {f.adult_only && (
                <span style={{
                  padding: '2px 8px', background: '#7C3AED', color: '#fff',
                  borderRadius: 4, fontSize: 10, fontWeight: 700,
                }}>성인전용</span>
              )}
            </div>
          </div>
        ))}
        {list.length === 0 && !loading && (
          <div style={{ padding: 40, textAlign: 'center', opacity: 0.6 }}>등록된 매장이 없습니다.</div>
        )}
      </div>

      {detail && <FacilityDetailModal facility={detail} onClose={() => setDetail(null)} />}
    </div>
  );
}

function FacilityDetailModal({ facility, onClose }) {
  const f = facility;
  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
        zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20, backdropFilter: 'blur(4px)',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: 'rgba(30,30,46,0.96)', backdropFilter: 'blur(14px)',
          padding: 24, borderRadius: 16, maxWidth: 720, width: '100%',
          maxHeight: '90vh', overflow: 'auto', border: '1px solid rgba(255,255,255,0.2)',
          color: 'white',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
          <div>
            <h2 style={{ margin: 0 }}>{f.name}</h2>
            <div style={{ opacity: 0.7, fontSize: 13, marginTop: 4 }}>
              #{f.id} · {f.address || '주소 없음'}
            </div>
          </div>
          <button onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'white', fontSize: 22, cursor: 'pointer', padding: 4 }}
            aria-label="닫기">×</button>
        </div>

        {f.image_url && (
          <img src={f.image_url} alt={f.name}
            style={{
              width: '100%', height: 220, objectFit: 'cover',
              objectPosition: 'top', borderRadius: 12, marginBottom: 16,
            }} />
        )}

        <Section title="설명">{f.description || <span style={{ opacity: 0.5 }}>없음</span>}</Section>

        <Section title="영업시간">{f.business_hours || <span style={{ opacity: 0.5 }}>미설정</span>}</Section>

        <Section title="정기휴무">
          {(f.holidays || []).length > 0
            ? (f.holidays || []).join(' · ')
            : <span style={{ opacity: 0.5 }}>설정 없음</span>}
        </Section>

        <Section title="진행중 혜택">
          {(f.benefits || []).length > 0 ? (
            <div style={{ display: 'grid', gap: 6, marginTop: 4 }}>
              {(f.benefits || []).map((b, i) => (
                <div key={i} style={{
                  padding: '10px 12px',
                  background: 'rgba(124,58,237,0.15)',
                  border: '1px solid rgba(124,58,237,0.35)',
                  borderRadius: 8,
                  fontSize: 13,
                }}>
                  <strong style={{ color: '#A78BFA', marginRight: 6 }}>
                    {KIND_LABEL[b.kind] || '혜택'}
                  </strong>
                  {b.title}
                </div>
              ))}
            </div>
          ) : <span style={{ opacity: 0.5 }}>등록된 혜택 없음</span>}
        </Section>

        <Section title="연락처">{f.phone || <span style={{ opacity: 0.5 }}>미설정</span>}</Section>

        <Section title="좌표">
          {f.latitude && f.longitude
            ? <code>{f.latitude}, {f.longitude}</code>
            : <span style={{ opacity: 0.5 }}>미설정</span>}
        </Section>

        <div style={{ marginTop: 20, textAlign: 'right' }}>
          <button className="btn" onClick={onClose}>닫기</button>
        </div>
      </div>
    </div>
  );
}

const KIND_LABEL = {
  welcome: '환영',
  coupon: '쿠폰',
  stamp: '스탬프',
};

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 6, fontWeight: 600, letterSpacing: '0.02em' }}>{title}</div>
      <div style={{ fontSize: 14 }}>{children}</div>
    </div>
  );
}
