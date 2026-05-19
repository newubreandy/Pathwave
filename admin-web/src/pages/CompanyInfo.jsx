import React, { useEffect, useState, useCallback } from 'react';
import { Building2, RefreshCw, Save } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { companyInfoApi } from '../services/companyInfo.js';
import './Beacons.css';

/**
 * Phase M — 법인 정보 (footer 자동 동기).
 *
 * 슈퍼어드민이 한 번 입력 → 3 콘솔 footer 모두 그 값 사용.
 * 이메일은 일단 default 유지 (DNS/MX 연결 후 별도 적용) — UI 노출 안 함.
 */
const FIELDS = [
  { key: 'company_name',    label: '상호 (법인명)',           placeholder: '예: 주식회사 트리거소프트' },
  { key: 'ceo',             label: '대표자 성명',              placeholder: '예: 홍길동' },
  { key: 'biz_number',      label: '사업자등록번호',           placeholder: '예: 123-45-67890' },
  { key: 'commerce_number', label: '통신판매업 신고번호',      placeholder: '예: 제2026-서울강남-0001호' },
  { key: 'address',         label: '사업장 주소',              placeholder: '예: 서울특별시 강남구 ...' },
  { key: 'phone',           label: '대표 전화',                placeholder: '예: 02-1234-5678' },
  { key: 'hosting',         label: '호스팅 제공자',            placeholder: '예: AWS Korea / Vercel' },
];

export default function CompanyInfo() {
  const { t } = useTranslation();
  const [form, setForm]       = useState({});
  const [initial, setInitial] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving]   = useState(false);
  const [error, setError]     = useState('');
  const [updatedAt, setUpdatedAt] = useState(null);
  const [savedTick, setSavedTick] = useState(false);

  const reload = useCallback(() => {
    setLoading(true); setError('');
    companyInfoApi.get()
      .then((data) => {
        const ci = data.company_info || {};
        const next = {};
        for (const f of FIELDS) next[f.key] = ci[f.key] ?? '';
        setForm(next);
        setInitial(next);
        setUpdatedAt(ci.updated_at || null);
      })
      .catch((err) => setError(err.message || '법인 정보를 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { reload(); }, [reload]);

  const dirty = FIELDS.some((f) => (form[f.key] ?? '') !== (initial[f.key] ?? ''));

  async function handleSave() {
    setSaving(true); setError('');
    try {
      const payload = {};
      for (const f of FIELDS) payload[f.key] = form[f.key] ?? '';
      const data = await companyInfoApi.put(payload);
      const ci = data.company_info || {};
      const next = {};
      for (const f of FIELDS) next[f.key] = ci[f.key] ?? '';
      setForm(next);
      setInitial(next);
      setUpdatedAt(ci.updated_at || null);
      setSavedTick(true);
      setTimeout(() => setSavedTick(false), 2200);
    } catch (err) {
      setError(err.message || '저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">
              <Building2 size={22} style={{ verticalAlign: 'middle', marginRight: 8, color: 'var(--accent)' }} />
              법인 정보
            </h1>
            <p className="sub-title">
              여기서 입력한 정보가 mobile / 사장님 / 어드민 3 콘솔의 footer 에 동일하게 노출됩니다.
              {' '}이메일은 DNS/MX 연결 후 별도 적용 — 지금은 default <code>support@pathwave.co.kr</code> 유지.
            </p>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading || saving} title="새로고침">
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
            </button>
            <button
              className="btn btn-primary"
              onClick={handleSave}
              disabled={!dirty || saving || loading}
              title={!dirty ? '변경사항 없음' : '저장'}
            >
              <Save size={16} />
              <span>{saving ? '저장 중…' : '저장'}</span>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)', marginBottom: '1rem' }}>
          {error}
        </div>
      )}
      {savedTick && (
        <div className="card" style={{ borderColor: 'var(--accent)', color: 'var(--accent)', marginBottom: '1rem' }}>
          저장되었습니다. 3 콘솔 footer 가 다음 새로고침부터 반영합니다.
        </div>
      )}

      <div className="card" style={{ padding: '1.25rem' }}>
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            {t('common.loading', '불러오는 중...')}
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1rem',
          }}>
            {FIELDS.map((f) => (
              <label key={f.key} className="form-label">
                <span>{f.label}</span>
                <input
                  type="text"
                  value={form[f.key] ?? ''}
                  placeholder={f.placeholder}
                  disabled={saving}
                  onChange={(e) => setForm((prev) => ({ ...prev, [f.key]: e.target.value }))}
                />
              </label>
            ))}
          </div>
        )}

        {updatedAt && (
          <div className="text-hint" style={{ marginTop: '1rem', fontSize: 'var(--fs-xs)' }}>
            마지막 수정: {updatedAt}
          </div>
        )}
      </div>
    </div>
  );
}
