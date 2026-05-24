/**
 * B-2d — 앱 버전 강제 업데이트 관리 페이지.
 *
 * 백엔드 `PUT /api/admin/app-versions/{platform}` 로 ios/android 별로
 * min_supported / latest / store_url / force_message 를 운영자가 직접 갱신.
 * (mobile 앱은 부팅 시 GET /api/version/check 호출 — current < min_supported
 *  면 강제 업데이트 모달 노출)
 *
 * 디자인 메모
 * ---------
 * - admin-web 다크 테마 + 블루 #2563EB 포인트
 * - ios/android 카드 2열
 * - 저장 시 server 응답으로 카드 갱신
 * - 마지막 갱신 시각 표시
 */
import React, { useCallback, useEffect, useState } from 'react';
import { RefreshCw, Save, Smartphone, AlertCircle } from 'lucide-react';
import { adminApi } from '../services/admin.js';

const PLATFORM_META = {
  ios:     { label: 'iOS',     defaultStore: 'https://apps.apple.com/app/idXXXXXXXXX' },
  android: { label: 'Android', defaultStore: 'https://play.google.com/store/apps/details?id=com.pathwave' },
};

const EMPTY_FORM = {
  min_supported: '',
  latest:        '',
  store_url:     '',
  force_message: '',
};

export default function AppVersions() {
  const [versions, setVersions] = useState({ ios: null, android: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const reload = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const res = await adminApi.listAppVersions();
      const map = { ios: null, android: null };
      for (const v of res.versions || []) {
        map[v.platform] = v;
      }
      setVersions(map);
    } catch (e) {
      setError(e?.message || '버전 목록을 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { reload(); }, [reload]);

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', alignItems: 'center',
                                            justifyContent: 'space-between',
                                            marginBottom: '1rem' }}>
        <div>
          <h1 className="page-title">앱 버전 관리</h1>
          <p className="page-subtitle">
            모바일 앱(iOS/Android) 의 최소 지원 버전·최신 버전·스토어 URL·강제 업데이트 메시지를 운영합니다.
          </p>
        </div>
        <button className="btn btn-ghost" onClick={reload} disabled={loading}
                aria-label="새로고침">
          <RefreshCw size={16} className={loading ? 'spin' : ''} aria-hidden="true" />
        </button>
      </div>

      {error && (
        <div className="error-box" style={{ marginBottom: '1rem' }}>{error}</div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
                    gap: '1rem' }}>
        {['ios', 'android'].map((platform) => (
          <PlatformCard
            key={platform}
            platform={platform}
            current={versions[platform]}
            onSaved={reload}
          />
        ))}
      </div>

      <div style={{ marginTop: '1.5rem', padding: '1rem',
                    background: 'var(--bg-3)', border: '1px solid var(--border)',
                    borderRadius: 8, color: 'var(--text-secondary)',
                    fontSize: 'var(--fs-sm)' }}>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
          <AlertCircle size={18} aria-hidden="true" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <strong>설정 가이드</strong>
            <ul style={{ marginTop: '0.5rem', paddingLeft: '1.25rem', lineHeight: 1.6 }}>
              <li><code>min_supported</code> — 이 버전 미만의 앱은 강제 업데이트 모달로 차단됩니다.</li>
              <li><code>latest</code> — 권장 버전. min_supported &lt; current &lt; latest 면 권장 모달.</li>
              <li><code>store_url</code> — 업데이트 모달의 "스토어로 이동" 링크.</li>
              <li><code>force_message</code> — 강제 업데이트 시 사용자에게 보일 추가 안내(선택).</li>
              <li>semver(0.0.0) 형식. min_supported 는 latest 보다 클 수 없음.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function PlatformCard({ platform, current, onSaved }) {
  const meta = PLATFORM_META[platform];
  const [form, setForm] = useState(EMPTY_FORM);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (current) {
      setForm({
        min_supported: current.min_supported || '',
        latest:        current.latest || '',
        store_url:     current.store_url || '',
        force_message: current.force_message || '',
      });
    } else {
      setForm({ ...EMPTY_FORM, store_url: meta.defaultStore });
    }
  }, [current, meta.defaultStore]);

  function patch(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
    setSuccess('');
    setError('');
  }

  async function save() {
    setBusy(true); setError(''); setSuccess('');
    try {
      if (!form.min_supported.trim() || !form.latest.trim()) {
        throw new Error('min_supported 와 latest 는 필수입니다.');
      }
      await adminApi.upsertAppVersion(platform, {
        min_supported: form.min_supported.trim(),
        latest:        form.latest.trim(),
        store_url:     form.store_url.trim() || null,
        force_message: form.force_message.trim() || null,
      });
      setSuccess('저장되었습니다.');
      onSaved?.();
    } catch (e) {
      setError(e?.message || '저장 실패');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ padding: '1rem', background: 'var(--bg-3)',
                  border: '1px solid var(--border)', borderRadius: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem',
                    marginBottom: '1rem' }}>
        <Smartphone size={20} aria-hidden="true" />
        <h2 style={{ margin: 0 }}>{meta.label}</h2>
        {current?.updated_at && (
          <span style={{ marginLeft: 'auto', fontSize: 'var(--fs-xs)',
                         color: 'var(--text-muted)' }}>
            갱신: {current.updated_at}
          </span>
        )}
      </div>

      <label className="form-label">
        <span>최소 지원 버전 (min_supported) *</span>
        <input value={form.min_supported}
               onChange={(e) => patch('min_supported', e.target.value)}
               placeholder="예: 1.0.0"
               disabled={busy} />
      </label>

      <label className="form-label">
        <span>최신 버전 (latest) *</span>
        <input value={form.latest}
               onChange={(e) => patch('latest', e.target.value)}
               placeholder="예: 1.2.0"
               disabled={busy} />
      </label>

      <label className="form-label">
        <span>스토어 URL</span>
        <input value={form.store_url}
               onChange={(e) => patch('store_url', e.target.value)}
               placeholder={meta.defaultStore}
               disabled={busy} />
      </label>

      <label className="form-label">
        <span>강제 업데이트 안내 (force_message)</span>
        <textarea rows={2} value={form.force_message}
                  onChange={(e) => patch('force_message', e.target.value)}
                  placeholder="예: 보안 강화 + 결제 흐름 안정성 개선"
                  disabled={busy} />
      </label>

      {error   && <div className="error-box"   style={{ marginTop: '0.75rem' }}>{error}</div>}
      {success && <div className="success-box" style={{ marginTop: '0.75rem',
                          padding: '0.5rem 0.75rem', background: 'var(--accent-soft)',
                          border: '1px solid var(--accent)', borderRadius: 6,
                          color: 'var(--accent)' }}>{success}</div>}

      <button className="btn btn-primary"
              onClick={save}
              disabled={busy || !form.min_supported.trim() || !form.latest.trim()}
              style={{ marginTop: '1rem', width: '100%',
                       display: 'flex', alignItems: 'center', justifyContent: 'center',
                       gap: '0.4rem' }}>
        <Save size={16} aria-hidden="true" />
        {busy ? '저장 중...' : (current ? '업데이트' : '신규 등록')}
      </button>
    </div>
  );
}
