/**
 * 사용자 앱 시즌 배경 테마 관리 (슈퍼어드민).
 *
 * - 계절별(spring/summer/autumn/winter) + 이벤트(event) 배경을 등록·활성화·삭제.
 * - 큰 이미지(권장 2160×3840, 9:16) 업로드 → BoxFit.cover 방식으로 사용자 앱 전면 표시.
 * - 활성화된 1건만 사용자 앱에 노출 (같은 season 에서 active 배타).
 * - 디바이스 비율 4종 라이브 프리뷰 (16:9 / 19.5:9 / 20:9 / 21:9) — 잘림 사전 확인.
 * - 무재배포 운영: 모바일 앱은 1시간 캐시 + pull-to-refresh 로 새 배경 즉시 반영.
 */
import React, { useEffect, useState, useCallback, useMemo } from 'react';
import {
  RefreshCw, Plus, Pencil, Trash2, CheckCircle, Image as ImageIcon, Eye,
} from 'lucide-react';
import Modal from '../components/Modal.jsx';
import { adminApi } from '../services/admin.js';
import { useConfirm } from '../hooks/useConfirm.jsx';
import './Beacons.css';

// ── 계절 메타 ────────────────────────────────────────────────────────────────
const SEASONS = [
  { code: 'spring', label: '봄 (3-5월)',    emoji: '🌸', months: '3·4·5' },
  { code: 'summer', label: '여름 (6-8월)',  emoji: '☀️', months: '6·7·8' },
  { code: 'autumn', label: '가을 (9-11월)', emoji: '🍁', months: '9·10·11' },
  { code: 'winter', label: '겨울 (12-2월)', emoji: '❄️', months: '12·1·2' },
  { code: 'event',  label: '이벤트 (기간 한정)', emoji: '🎉', months: '직접 지정' },
];
const SEASON_LABEL = Object.fromEntries(SEASONS.map((s) => [s.code, s.label]));
const SEASON_EMOJI = Object.fromEntries(SEASONS.map((s) => [s.code, s.emoji]));

// 디바이스 비율 — 미리보기에서 잘림 확인용
const PREVIEW_RATIOS = [
  { label: 'iPhone 8 (16:9)',     ratio: '9 / 16' },
  { label: 'iPhone 15 (19.5:9)',  ratio: '9 / 19.5' },
  { label: 'Galaxy S24 (20:9)',   ratio: '9 / 20' },
  { label: '21:9 (롱폼)',          ratio: '9 / 21' },
];

// 글래스 카드 미리보기 스타일 — 텍스처가 있으면 "유리 안에 패턴이 비치는" 모습을 재현.
// 모바일 GlassCard 와 동일: 텍스처 위 상단 하이라이트 림(광택) + backdrop blur 최소화.
function glassPreviewStyle(textureUrl, textOnDark) {
  const base = { color: textOnDark ? '#fff' : '#111' };
  if (!textureUrl) return base;
  return {
    ...base,
    backgroundImage:
      'linear-gradient(to bottom, rgba(255,255,255,0.28), rgba(255,255,255,0) 25%, ' +
      'rgba(255,255,255,0) 85%, rgba(255,255,255,0.10)), url(' + textureUrl + ')',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backdropFilter: 'none',
    WebkitBackdropFilter: 'none',
  };
}

// 업로드 한도 (백엔드와 일치)
// 권장 사이즈 1440×3200 (QHD+) — 모든 현존 디바이스(iPhone 15 Pro Max 1290×2796,
// Galaxy S24 Ultra 1440×3120)에 1:1 또는 약간 다운스케일 = 항상 선명.
// 그 이상은 사람 눈에 차이 없고 파일만 커지므로 5MB 캡으로 충분.
const MAX_UPLOAD_MB = 5;
const ALLOWED_EXT = ['png', 'jpg', 'jpeg', 'webp'];

export default function Themes() {
  const { confirm, alert: alertModal, modal: confirmModalEl } = useConfirm();

  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editTarget, setEditTarget] = useState(null);     // null=닫힘 / {}=신규 / row=수정
  const [previewTarget, setPreviewTarget] = useState(null);

  const reload = useCallback(() => {
    setLoading(true); setError('');
    adminApi.listThemes()
      .then((data) => setList(data.themes || []))
      .catch((err) => setError(err.message || '불러오기 실패'))
      .finally(() => setLoading(false));
  }, []);
  useEffect(() => { reload(); }, [reload]);

  // season → row[] 그룹핑
  const grouped = useMemo(() => {
    const map = Object.fromEntries(SEASONS.map((s) => [s.code, []]));
    list.forEach((row) => {
      if (map[row.season]) map[row.season].push(row);
    });
    return map;
  }, [list]);

  async function handleDelete(item) {
    const ok = await confirm({
      title: '테마 삭제',
      desc: `"${item.name}" 을(를) 삭제합니다.\n이미지 파일도 함께 제거됩니다.`,
      confirmText: '삭제',
    });
    if (!ok) return;
    try {
      await adminApi.deleteTheme(item.id);
      reload();
    } catch (err) {
      await alertModal({ title: '삭제 실패', desc: err.message || '삭제 실패' });
    }
  }

  async function handleActivate(item) {
    if (item.active) return;
    try {
      await adminApi.activateTheme(item.id);
      reload();
    } catch (err) {
      await alertModal({ title: '활성화 실패', desc: err.message || '활성화 실패' });
    }
  }

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">사용자 앱 시즌 배경</h1>
            <p className="sub-title">
              계절별(자동 전환) + 이벤트 배경. 1440×3200 (QHD+) 권장 이미지를 등록하면
              사용자 앱이 BoxFit.cover 로 가득 채워 표시합니다. 활성 테마 변경 후
              앱 재배포 없이 다음 실행/새로고침부터 반영됩니다.
            </p>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
              <span>새로고침</span>
            </button>
            <button className="btn btn-primary" onClick={() => setEditTarget({})}>
              <Plus size={16} />
              <span>새 테마 등록</span>
            </button>
          </div>
        </div>
      </div>

      {error && <div className="form-error" role="alert">{error}</div>}

      {loading ? (
        <div className="empty-state">불러오는 중…</div>
      ) : (
        <div className="theme-season-grid">
          {SEASONS.map((s) => (
            <SeasonGroup
              key={s.code}
              meta={s}
              rows={grouped[s.code]}
              onEdit={setEditTarget}
              onPreview={setPreviewTarget}
              onActivate={handleActivate}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {editTarget !== null && (
        <ThemeEditor
          target={editTarget}
          onClose={() => setEditTarget(null)}
          onSaved={() => { setEditTarget(null); reload(); }}
          onError={(msg) => alertModal({ title: '오류', desc: msg })}
        />
      )}

      {previewTarget && (
        <ThemePreview
          theme={previewTarget}
          onClose={() => setPreviewTarget(null)}
        />
      )}

      {confirmModalEl}

      <style>{themeStyles}</style>
    </div>
  );
}

// ── 계절 그룹 카드 ───────────────────────────────────────────────────────────
function SeasonGroup({ meta, rows, onEdit, onPreview, onActivate, onDelete }) {
  const active = rows.find((r) => r.active);
  return (
    <section className="theme-season-card">
      <header className="theme-season-head">
        <div className="theme-season-title">
          <span className="theme-season-emoji">{meta.emoji}</span>
          <div>
            <h2>{meta.label}</h2>
            <p className="sub-title">{meta.months} · 등록 {rows.length}건</p>
          </div>
        </div>
        {active ? (
          <span className="theme-badge theme-badge--active">
            <CheckCircle size={14} /> 활성 中
          </span>
        ) : (
          <span className="theme-badge theme-badge--idle">미설정 — 앱 기본 그라데이션</span>
        )}
      </header>

      {rows.length === 0 ? (
        <div className="theme-empty">
          <ImageIcon size={28} strokeWidth={1.4} />
          <p>등록된 배경이 없습니다.</p>
        </div>
      ) : (
        <ul className="theme-list">
          {rows.map((row) => (
            <li key={row.id} className={'theme-row' + (row.active ? ' theme-row--active' : '')}>
              <div className="theme-thumb"
                   style={{
                     backgroundImage: `url(${row.image_url})`,
                     '--overlay': `rgba(15,15,26,${row.overlay_alpha ?? 0.45})`,
                   }} />
              <div className="theme-meta">
                <div className="theme-name">{row.name}</div>
                <div className="theme-sub">
                  Overlay {Math.round((row.overlay_alpha ?? 0.45) * 100)}% ·
                  텍스트 {row.text_on_dark ? '흰색' : '검정'}
                  {row.accent_color && (
                    <> · accent <span className="theme-color-dot" style={{ background: row.accent_color }} /></>
                  )}
                  {row.texture_url && <> · 🫧 텍스처</>}
                </div>
              </div>
              <div className="theme-actions">
                <button className="btn btn-ghost btn-sm" onClick={() => onPreview(row)}>
                  <Eye size={14} /> 미리보기
                </button>
                {!row.active && (
                  <button className="btn btn-primary btn-sm" onClick={() => onActivate(row)}>
                    <CheckCircle size={14} /> 활성화
                  </button>
                )}
                <button className="btn btn-ghost btn-sm" onClick={() => onEdit(row)}>
                  <Pencil size={14} /> 수정
                </button>
                <button className="btn btn-ghost btn-sm theme-btn-danger" onClick={() => onDelete(row)}>
                  <Trash2 size={14} /> 삭제
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

// ── 신규/수정 모달 ───────────────────────────────────────────────────────────
function ThemeEditor({ target, onClose, onSaved, onError }) {
  const isEdit = !!target.id;
  const [season, setSeason]                 = useState(target.season || 'spring');
  const [name, setName]                     = useState(target.name || '');
  const [overlayAlpha, setOverlayAlpha]     = useState(
    target.overlay_alpha != null ? target.overlay_alpha : 0.45
  );
  const [textOnDark, setTextOnDark]         = useState(target.text_on_dark !== false);
  const [accentColor, setAccentColor]       = useState(target.accent_color || '');
  const [eventStartsAt, setEventStartsAt]   = useState(target.event_starts_at || '');
  const [eventEndsAt, setEventEndsAt]       = useState(target.event_ends_at || '');
  const [activate, setActivate]             = useState(false);
  const [file, setFile]                     = useState(null);
  const [filePreview, setFilePreview]       = useState(target.image_url || '');
  const [fileMeta, setFileMeta]             = useState('');
  // 글래스 텍스처 (선택) — 유리 카드 안에 비치는 패턴
  const [textureFile, setTextureFile]       = useState(null);
  const [texturePreview, setTexturePreview] = useState(target.texture_url || '');
  const [textureMeta, setTextureMeta]       = useState('');
  const [removeTexture, setRemoveTexture]   = useState(false);
  const [saving, setSaving]                 = useState(false);
  const [localError, setLocalError]         = useState('');

  function pickFile(f) {
    setLocalError('');
    if (!f) { setFile(null); setFilePreview(target.image_url || ''); setFileMeta(''); return; }
    const ext = (f.name.split('.').pop() || '').toLowerCase();
    if (!ALLOWED_EXT.includes(ext)) {
      setLocalError(`허용되지 않는 확장자: .${ext} (허용: ${ALLOWED_EXT.join(', ')})`);
      return;
    }
    if (f.size > MAX_UPLOAD_MB * 1024 * 1024) {
      setLocalError(`파일이 너무 큽니다: ${(f.size / 1024 / 1024).toFixed(1)}MB (최대 ${MAX_UPLOAD_MB}MB)`);
      return;
    }
    setFile(f);
    const url = URL.createObjectURL(f);
    setFilePreview(url);
    setFileMeta(`${(f.size / 1024).toFixed(0)} KB · ${f.type || ext.toUpperCase()}`);
  }

  function pickTexture(f) {
    setLocalError('');
    if (!f) {
      setTextureFile(null);
      setTexturePreview(target.texture_url || '');
      setTextureMeta('');
      return;
    }
    const ext = (f.name.split('.').pop() || '').toLowerCase();
    if (!ALLOWED_EXT.includes(ext)) {
      setLocalError(`텍스처: 허용되지 않는 확장자 .${ext} (허용: ${ALLOWED_EXT.join(', ')})`);
      return;
    }
    if (f.size > MAX_UPLOAD_MB * 1024 * 1024) {
      setLocalError(`텍스처 파일이 너무 큽니다: ${(f.size / 1024 / 1024).toFixed(1)}MB (최대 ${MAX_UPLOAD_MB}MB)`);
      return;
    }
    setTextureFile(f);
    setRemoveTexture(false);
    setTexturePreview(URL.createObjectURL(f));
    setTextureMeta(`${(f.size / 1024).toFixed(0)} KB · ${f.type || ext.toUpperCase()}`);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLocalError('');
    if (!name.trim()) return setLocalError('이름을 입력하세요.');
    if (!isEdit && !file) return setLocalError('이미지 파일을 선택하세요.');

    setSaving(true);
    try {
      const fd = new FormData();
      fd.append('season', season);
      fd.append('name', name.trim());
      fd.append('overlay_alpha', String(overlayAlpha));
      fd.append('text_on_dark', textOnDark ? '1' : '0');
      if (accentColor) fd.append('accent_color', accentColor);
      if (season === 'event') {
        if (eventStartsAt) fd.append('event_starts_at', eventStartsAt);
        if (eventEndsAt)   fd.append('event_ends_at', eventEndsAt);
      }
      if (file) fd.append('image', file);
      if (textureFile) fd.append('texture', textureFile);
      else if (isEdit && removeTexture) fd.append('remove_texture', '1');
      if (!isEdit && activate) fd.append('activate', '1');

      if (isEdit) {
        await adminApi.updateTheme(target.id, fd);
      } else {
        await adminApi.createTheme(fd);
      }
      onSaved();
    } catch (err) {
      const msg = err.message || '저장 실패';
      setLocalError(msg);
      onError?.(msg);
    } finally {
      setSaving(false);
    }
  }

  // 제거 체크 시 미리보기는 텍스처 없는 기본 유리로
  const effTexture = removeTexture ? '' : texturePreview;

  return (
    <Modal open={true} onClose={onClose} title={isEdit ? '테마 수정' : '새 테마 등록'} size="lg">
      <form onSubmit={handleSubmit} className="theme-form">
        <div className="theme-form-grid">
          <div className="theme-form-col">
            <label className="form-label">
              계절 / 이벤트
              <select className="form-input"
                      value={season}
                      onChange={(e) => setSeason(e.target.value)}>
                {SEASONS.map((s) => (
                  <option key={s.code} value={s.code}>{s.label}</option>
                ))}
              </select>
            </label>

            <label className="form-label">
              이름 (운영자 식별용)
              <input className="form-input" type="text"
                     value={name}
                     onChange={(e) => setName(e.target.value)}
                     placeholder="예: 2026 봄 - 벚꽃 글래스" />
            </label>

            <label className="form-label">
              배경 이미지 ({ALLOWED_EXT.join('/')}, 최대 {MAX_UPLOAD_MB}MB)
              <input className="form-input" type="file"
                     accept={ALLOWED_EXT.map((e) => '.' + e).join(',')}
                     onChange={(e) => pickFile(e.target.files?.[0] || null)} />
              <span className="form-hint">
                📐 권장 사이즈: <strong>1440 × 3200 (QHD+, 9:20)</strong> — 모든 현존 디바이스에
                선명합니다. WebP 사용 시 같은 화질에 파일 30~50% ↓.
              </span>
              {fileMeta && <span className="form-hint">선택됨: {fileMeta}</span>}
            </label>

            <label className="form-label">
              가독성 보정 어두운 오버레이 ({Math.round(overlayAlpha * 100)}%)
              <input type="range" min={0} max={1} step={0.05}
                     value={overlayAlpha}
                     onChange={(e) => setOverlayAlpha(parseFloat(e.target.value))} />
              <span className="form-hint">
                높을수록 어두워져 텍스트 가독성 ↑. 밝은 배경엔 50% 이상 권장.
              </span>
            </label>

            <label className="form-checkbox-row">
              <input type="checkbox" checked={textOnDark}
                     onChange={(e) => setTextOnDark(e.target.checked)} />
              <span>배경이 어두워 텍스트는 <strong>흰색</strong>으로 표시 (체크 해제 = 검은 텍스트)</span>
            </label>

            <label className="form-label">
              포인트 색상 (선택)
              <div className="theme-color-input">
                <input type="color" value={accentColor || '#7C3AED'}
                       onChange={(e) => setAccentColor(e.target.value)} />
                <input className="form-input" type="text"
                       value={accentColor}
                       onChange={(e) => setAccentColor(e.target.value)}
                       placeholder="#7C3AED (비우면 기본값)" />
              </div>
            </label>

            <label className="form-label">
              글래스 텍스처 (선택, {ALLOWED_EXT.join('/')}, 최대 {MAX_UPLOAD_MB}MB)
              <input className="form-input" type="file"
                     accept={ALLOWED_EXT.map((e) => '.' + e).join(',')}
                     onChange={(e) => pickTexture(e.target.files?.[0] || null)} />
              <span className="form-hint">
                🫧 유리 카드(GlassCard) <strong>안에 비치는 패턴</strong>입니다. 비우면 기본 반투명 유리.
                작은 타일·패브릭·은은한 그라데이션을 권장 (전면 배경 이미지 X). 교체하면 앱 재배포 없이
                전 글래스 카드 무드가 바뀝니다.
              </span>
              {textureMeta && <span className="form-hint">선택됨: {textureMeta}</span>}
            </label>

            {isEdit && (target.texture_url || texturePreview) && !textureFile && (
              <label className="form-checkbox-row">
                <input type="checkbox" checked={removeTexture}
                       onChange={(e) => setRemoveTexture(e.target.checked)} />
                <span>현재 텍스처 <strong>제거</strong> (기본 반투명 유리로 복귀)</span>
              </label>
            )}

            {season === 'event' && (
              <div className="theme-event-window">
                <label className="form-label">
                  이벤트 시작 (ISO)
                  <input className="form-input" type="datetime-local"
                         value={eventStartsAt.slice(0, 16)}
                         onChange={(e) => setEventStartsAt(e.target.value)} />
                </label>
                <label className="form-label">
                  이벤트 종료 (ISO)
                  <input className="form-input" type="datetime-local"
                         value={eventEndsAt.slice(0, 16)}
                         onChange={(e) => setEventEndsAt(e.target.value)} />
                </label>
              </div>
            )}

            {!isEdit && (
              <label className="form-checkbox-row">
                <input type="checkbox" checked={activate}
                       onChange={(e) => setActivate(e.target.checked)} />
                <span>등록 직후 바로 활성화 (해당 계절의 기존 활성 테마 자동 교체)</span>
              </label>
            )}
          </div>

          <div className="theme-form-col theme-preview-col">
            <h4 className="form-section-title">디바이스 비율별 미리보기</h4>
            <p className="form-hint">큰 이미지를 가로/세로 중 한 쪽 기준으로 풀로 채움 (BoxFit.cover)</p>
            <div className="theme-preview-grid">
              {PREVIEW_RATIOS.map((p) => (
                <div key={p.label} className="theme-preview-tile">
                  <div className="theme-preview-frame"
                       style={{
                         aspectRatio: p.ratio,
                         backgroundImage: filePreview ? `url(${filePreview})` : 'linear-gradient(135deg,#6D28D9,#06B6D4)',
                       }}>
                    <div className="theme-preview-dim"
                         style={{ background: `rgba(15,15,26,${overlayAlpha})` }} />
                    <div className="theme-preview-card"
                         style={glassPreviewStyle(effTexture, textOnDark)}>
                      <div className="theme-preview-pill"
                           style={{ background: accentColor || 'rgba(255,255,255,0.18)' }}>
                        NEW FEATURE
                      </div>
                      <div className="theme-preview-h">PathWave</div>
                      <div className="theme-preview-b">
                        가독성 시뮬레이션 텍스트입니다. 실제 앱에서 이 정도로 보입니다.
                      </div>
                    </div>
                  </div>
                  <div className="theme-preview-label">{p.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {localError && <div className="form-error" role="alert">{localError}</div>}

        <div className="modal-footer">
          <button type="button" className="btn btn-ghost" onClick={onClose} disabled={saving}>
            취소
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? '저장 중…' : (isEdit ? '저장' : '등록')}
          </button>
        </div>
      </form>
    </Modal>
  );
}

// ── 큰 미리보기 (실제 앱 사이즈) ──────────────────────────────────────────────
function ThemePreview({ theme, onClose }) {
  return (
    <Modal open={true} onClose={onClose} title={`미리보기 — ${SEASON_EMOJI[theme.season]} ${theme.name}`} size="lg">
      <div className="theme-preview-large">
        {PREVIEW_RATIOS.map((p) => (
          <div key={p.label} className="theme-preview-tile theme-preview-tile--lg">
            <div className="theme-preview-frame"
                 style={{
                   aspectRatio: p.ratio,
                   backgroundImage: `url(${theme.image_url})`,
                 }}>
              <div className="theme-preview-dim"
                   style={{ background: `rgba(15,15,26,${theme.overlay_alpha ?? 0.45})` }} />
              <div className="theme-preview-card"
                   style={glassPreviewStyle(theme.texture_url, theme.text_on_dark)}>
                <div className="theme-preview-pill"
                     style={{ background: theme.accent_color || 'rgba(255,255,255,0.18)' }}>
                  NEW FEATURE
                </div>
                <div className="theme-preview-h">PathWave</div>
                <div className="theme-preview-b">실제 사용자 앱에서 보이는 모습입니다.</div>
              </div>
            </div>
            <div className="theme-preview-label">{p.label}</div>
          </div>
        ))}
      </div>
    </Modal>
  );
}

// ── 스타일 (페이지 한정 — 토큰은 index.css 의 var(--accent) 등 재사용) ──────
const themeStyles = `
.theme-season-grid {
  display: grid; gap: 20px; grid-template-columns: 1fr;
}
.theme-season-card {
  background: var(--bg-2); border: 1px solid var(--border); border-radius: 14px;
  padding: 20px; display: flex; flex-direction: column; gap: 14px;
}
.theme-season-head {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
}
.theme-season-title { display: flex; align-items: center; gap: 14px; }
.theme-season-title h2 { font-size: 18px; margin: 0; color: var(--text); }
.theme-season-emoji { font-size: 28px; line-height: 1; }
.theme-badge {
  display: inline-flex; align-items: center; gap: 6px; font-size: 12px;
  padding: 6px 10px; border-radius: 999px; font-weight: 600;
}
.theme-badge--active { background: rgba(34,197,94,0.16); color: #4ade80; }
.theme-badge--idle   { background: var(--bg-3); color: var(--text-hint); }
.theme-empty {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 28px; color: var(--text-hint); background: var(--bg-3);
  border-radius: 10px; border: 1px dashed var(--border);
}
.theme-empty p { margin: 0; font-size: 13px; }
.theme-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.theme-row {
  display: grid; grid-template-columns: 100px 1fr auto; gap: 14px;
  align-items: center; padding: 12px; border-radius: 12px;
  background: var(--bg-3); border: 1px solid var(--border);
}
.theme-row--active { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(124,58,237,0.18) inset; }
.theme-thumb {
  width: 100px; aspect-ratio: 9 / 16; border-radius: 8px;
  background-size: cover; background-position: center;
  position: relative; overflow: hidden;
}
.theme-thumb::after {
  content: ''; position: absolute; inset: 0;
  background: var(--overlay, rgba(15,15,26,0.45));
}
.theme-name { font-weight: 600; color: var(--text); margin-bottom: 4px; }
.theme-sub  { font-size: 12px; color: var(--text-hint); display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.theme-color-dot {
  display: inline-block; width: 12px; height: 12px; border-radius: 3px;
  border: 1px solid var(--border);
}
.theme-actions { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
.theme-btn-danger:hover { color: #ef4444; border-color: #ef4444; }

.theme-form { display: flex; flex-direction: column; gap: 16px; }
.theme-form-grid {
  display: grid; gap: 24px;
  grid-template-columns: minmax(280px, 1fr) minmax(320px, 1.4fr);
}
@media (max-width: 980px) { .theme-form-grid { grid-template-columns: 1fr; } }
.theme-form-col { display: flex; flex-direction: column; gap: 14px; }
.form-section-title { margin: 0; font-size: 14px; color: var(--text); }
.theme-color-input { display: flex; gap: 8px; align-items: center; }
.theme-color-input input[type="color"] {
  width: 44px; height: 38px; padding: 2px; border-radius: 8px;
  border: 1px solid var(--border); background: var(--bg-3);
}
.form-checkbox-row { display: flex; gap: 8px; align-items: flex-start; font-size: 13px; color: var(--text-2); }
.theme-event-window { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 600px) { .theme-event-window { grid-template-columns: 1fr; } }

.theme-preview-grid {
  display: grid; gap: 12px; grid-template-columns: repeat(2, 1fr);
}
.theme-preview-tile { display: flex; flex-direction: column; gap: 6px; }
.theme-preview-frame {
  position: relative; width: 100%; border-radius: 12px; overflow: hidden;
  background-size: cover; background-position: center;
  border: 1px solid var(--border);
}
.theme-preview-dim { position: absolute; inset: 0; }
.theme-preview-card {
  position: absolute; inset: auto 10% 14% 10%;
  background: rgba(255,255,255,0.12);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(255,255,255,0.18);
  border-radius: 14px; padding: 10px 12px;
  display: flex; flex-direction: column; gap: 4px;
}
.theme-preview-pill {
  align-self: flex-start; font-size: 9px; padding: 3px 8px; border-radius: 999px;
  letter-spacing: 0.06em; font-weight: 600; text-transform: uppercase;
}
.theme-preview-h { font-size: 14px; font-weight: 700; }
.theme-preview-b { font-size: 9px; opacity: 0.9; line-height: 1.35; }
.theme-preview-label { font-size: 11px; color: var(--text-hint); text-align: center; }

.theme-preview-large {
  display: grid; gap: 16px; grid-template-columns: repeat(2, 1fr);
}
.theme-preview-tile--lg .theme-preview-h { font-size: 22px; }
.theme-preview-tile--lg .theme-preview-b { font-size: 12px; }
.theme-preview-tile--lg .theme-preview-pill { font-size: 11px; }

.modal-footer {
  display: flex; gap: 8px; justify-content: flex-end;
  padding-top: 12px; border-top: 1px solid var(--border);
}
`;
