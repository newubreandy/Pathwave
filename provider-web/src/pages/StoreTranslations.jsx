/**
 * P-025 — 매장 다국어 관리.
 *
 * 백엔드 facility_translations 캐시를 사장이 직접 등록·수정·자동번역.
 * 외국인 사용자(USER)의 매장 상세 화면이 lang 별로 이 캐시를 사용.
 *
 * 동작
 * ----
 * - 마운트 시 본인 매장 ID 가져오고 (StoreService.list() 첫 번째)
 *   listTranslations(fid) 로 캐시 + 매장 base 정보 fetch
 * - 언어 탭 (ko=base / en / ja / zh / zh-TW / fr / th)
 * - 각 탭에서 name/address/description 편집 → 저장 (PUT)
 * - "자동 번역" 버튼 → autoTranslate(fid) → DeepL 호출, force 옵션
 * - 삭제 → 다음 조회 시 자동 번역 폴백
 */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Languages, Save, RefreshCw, Wand2, Trash2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import StoreService from '../services/store/StoreService';

// 지원 언어 (백엔드 _ALLOWED_LANGUAGES 와 동기 — ko 는 base 라 탭에서 제외)
const TARGET_LANGS = [
  { code: 'en',    label: 'English',  flag: '🇺🇸' },
  { code: 'ja',    label: '日本語',    flag: '🇯🇵' },
  { code: 'zh',    label: '简体中文',  flag: '🇨🇳' },
  { code: 'zh-TW', label: '繁體中文',  flag: '🇹🇼' },
  { code: 'fr',    label: 'Français',  flag: '🇫🇷' },
  { code: 'th',    label: 'ไทย',       flag: '🇹🇭' },
];

const EMPTY = { name: '', address: '', description: '' };

export default function StoreTranslations() {
  const { t } = useTranslation();
  const [facility, setFacility]   = useState(null);
  const [translations, setTrans]  = useState({});
  const [activeLang, setActive]   = useState('en');
  const [form, setForm]           = useState(EMPTY);
  const [loading, setLoading]     = useState(true);
  const [busy, setBusy]           = useState(false);
  const [error, setError]         = useState('');
  const [success, setSuccess]     = useState('');

  const fid = facility?.id;

  const reload = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const facilities = await StoreService.list();
      const list = facilities?.facilities || facilities?.items || [];
      const my = list[0];
      if (!my) throw new Error('매장을 먼저 등록해 주세요.');
      setFacility(my);
      const tres = await StoreService.listTranslations(my.id);
      const byLang = {};
      for (const tr of tres.translations || []) {
        byLang[tr.language] = tr;
      }
      setTrans(byLang);
    } catch (e) {
      setError(e?.message || '불러오기 실패');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { reload(); }, [reload]);

  // 활성 탭 변경 시 form 동기화
  useEffect(() => {
    const cur = translations[activeLang] || EMPTY;
    setForm({
      name:        cur.name        || '',
      address:     cur.address     || '',
      description: cur.description || '',
    });
    setSuccess(''); setError('');
  }, [activeLang, translations]);

  const baseInfo = useMemo(() => ({
    name:        facility?.name        || '',
    address:     facility?.address     || '',
    description: facility?.description || '',
  }), [facility]);

  async function save() {
    setBusy(true); setError(''); setSuccess('');
    try {
      const payload = {
        name:        form.name.trim()        || null,
        address:     form.address.trim()     || null,
        description: form.description.trim() || null,
      };
      if (!payload.name && !payload.address && !payload.description) {
        throw new Error('하나 이상 입력해 주세요.');
      }
      const res = await StoreService.upsertTranslation(fid, activeLang, payload);
      setTrans((t) => ({ ...t, [activeLang]: res.translation }));
      setSuccess('저장되었습니다.');
    } catch (e) {
      setError(e?.message || '저장 실패');
    } finally {
      setBusy(false);
    }
  }

  async function del() {
    if (!window.confirm(`${activeLang} 번역을 삭제하시겠습니까?\n(다음 조회 시 자동 번역 폴백)`)) return;
    setBusy(true); setError(''); setSuccess('');
    try {
      await StoreService.deleteTranslation(fid, activeLang);
      setTrans((t) => {
        const nt = { ...t }; delete nt[activeLang]; return nt;
      });
      setForm(EMPTY);
      setSuccess('삭제되었습니다.');
    } catch (e) {
      setError(e?.message || '삭제 실패');
    } finally {
      setBusy(false);
    }
  }

  async function auto({ force = false } = {}) {
    setBusy(true); setError(''); setSuccess('');
    try {
      const res = await StoreService.autoTranslate(fid, {
        target_languages: TARGET_LANGS.map((l) => l.code),
        force,
      });
      // 결과 반영을 위해 다시 fetch
      await reload();
      setSuccess(`자동 번역 완료 (${res?.translated_count ?? '—'}건${force ? ', 강제 덮어쓰기' : ''})`);
    } catch (e) {
      setError(e?.message || '자동 번역 실패');
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center',
                         color: 'var(--pw-text-muted)' }}>불러오는 중...</div>;
  }
  if (error && !facility) {
    return <div className="status-error" style={{ margin: '2rem' }}>{error}</div>;
  }

  return (
    <div style={{ padding: '1.5rem', maxWidth: 880, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem',
                    marginBottom: '0.5rem' }}>
        <Languages size={20} aria-hidden="true" />
        <h1 style={{ margin: 0 }}>매장 다국어 관리</h1>
      </div>
      <p style={{ color: 'var(--pw-text-muted)', marginTop: 0,
                  marginBottom: '1.5rem' }}>
        외국인 사용자가 보는 매장명/주소/설명을 언어별로 등록하거나 자동 번역합니다.
      </p>

      {/* 한국어 base 정보 카드 (편집은 매장 정보 페이지에서) */}
      <div style={{ padding: '0.875rem 1rem', background: 'var(--pw-bg-3)',
                    border: '1px solid var(--pw-border)', borderRadius: 10,
                    marginBottom: '1rem', fontSize: 'var(--pw-fs-sm)' }}>
        <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>
          🇰🇷 한국어 원본 (자동 번역 source)
        </div>
        <div style={{ color: 'var(--pw-text-muted)' }}>
          <strong>{baseInfo.name || '(이름 없음)'}</strong>
          {baseInfo.address  && <> · {baseInfo.address}</>}
        </div>
        {baseInfo.description && (
          <div style={{ marginTop: '0.25rem', color: 'var(--pw-text-muted)' }}>
            {baseInfo.description}
          </div>
        )}
        <div style={{ marginTop: '0.5rem', fontSize: 'var(--pw-fs-xs)',
                      color: 'var(--pw-text-hint)' }}>
          원본 수정은 "매장 정보" 페이지에서.
        </div>
      </div>

      {/* 액션 바 */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem',
                    flexWrap: 'wrap' }}>
        <button className="pw-btn" onClick={() => auto({ force: false })}
                disabled={busy}
                style={{ display: 'inline-flex', alignItems: 'center',
                         gap: '0.4rem' }}>
          <Wand2 size={14} aria-hidden="true" />
          비어있는 언어만 자동 번역
        </button>
        <button className="pw-btn pw-btn--ghost" onClick={() => auto({ force: true })}
                disabled={busy}
                style={{ display: 'inline-flex', alignItems: 'center',
                         gap: '0.4rem' }}>
          <Wand2 size={14} aria-hidden="true" />
          전체 강제 재번역
        </button>
        <button className="pw-btn pw-btn--ghost" onClick={reload}
                disabled={busy}
                style={{ display: 'inline-flex', alignItems: 'center',
                         gap: '0.4rem' }}
                aria-label="새로고침">
          <RefreshCw size={14} aria-hidden="true" />
        </button>
      </div>

      {/* 언어 탭 */}
      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid var(--pw-border)',
                    flexWrap: 'wrap', marginBottom: '1rem' }}>
        {TARGET_LANGS.map((l) => {
          const has = !!translations[l.code];
          return (
            <button key={l.code}
                    onClick={() => setActive(l.code)}
                    style={{ padding: '8px 14px', background: 'transparent',
                             border: 'none',
                             borderBottom: activeLang === l.code
                                ? '2px solid var(--pw-accent)'
                                : '2px solid transparent',
                             color: activeLang === l.code
                                ? 'var(--pw-text)' : 'var(--pw-text-muted)',
                             fontWeight: activeLang === l.code ? 600 : 400,
                             cursor: 'pointer', fontSize: 'var(--pw-fs-sm)' }}>
              {l.flag} {l.label}
              <span style={{ marginLeft: 6, fontSize: 10,
                             color: has ? 'var(--pw-accent)' : 'var(--pw-text-hint)' }}>
                {has ? '●' : '○'}
              </span>
            </button>
          );
        })}
      </div>

      {/* 폼 */}
      <div className="form-stack">
        <label className="pw-label">
          <span>매장명 ({activeLang})</span>
          <input value={form.name}
                 onChange={(e) => setForm({ ...form, name: e.target.value })}
                 placeholder={baseInfo.name}
                 disabled={busy} />
        </label>
        <label className="pw-label">
          <span>주소 ({activeLang})</span>
          <input value={form.address}
                 onChange={(e) => setForm({ ...form, address: e.target.value })}
                 placeholder={baseInfo.address}
                 disabled={busy} />
        </label>
        <label className="pw-label">
          <span>설명 ({activeLang})</span>
          <textarea rows={4} value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    placeholder={baseInfo.description}
                    disabled={busy} />
        </label>
      </div>

      {error   && <div className="status-error"   style={{ marginTop: '0.75rem' }}>{error}</div>}
      {success && <div className="status-success" style={{ marginTop: '0.75rem' }}>{success}</div>}

      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
        <button className="pw-btn" onClick={save} disabled={busy}
                style={{ display: 'inline-flex', alignItems: 'center',
                         gap: '0.4rem' }}>
          <Save size={14} aria-hidden="true" />
          저장
        </button>
        {translations[activeLang] && (
          <button className="pw-btn pw-btn--ghost" onClick={del} disabled={busy}
                  style={{ display: 'inline-flex', alignItems: 'center',
                           gap: '0.4rem', color: 'var(--pw-danger)' }}>
            <Trash2 size={14} aria-hidden="true" />
            이 언어 삭제
          </button>
        )}
      </div>
    </div>
  );
}
