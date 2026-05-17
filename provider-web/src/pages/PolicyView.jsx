import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ChevronLeft } from 'lucide-react';
import apiClient from '../services/apiClient';

/**
 * PolicyView — 공개 약관 본문 뷰어.
 *
 * 경로: /policy/:kind  (terms / privacy / location / marketing / push / camera / storage / third_party / age14)
 * Backend: GET /api/policies/<kind>?lang=ko (인증 불필요)
 *
 * 푸터 링크에서 진입. 비로그인 상태도 본문 노출.
 */
const KIND_LABEL = {
  terms:       '이용약관',
  privacy:     '개인정보처리방침',
  location:    '위치기반서비스 이용약관',
  marketing:   '마케팅 정보 수신 동의',
  push:        '푸시 알림 동의',
  camera:      '카메라 접근 권한',
  storage:     '저장공간 접근 권한',
  third_party: '제3자 정보 제공 동의',
  age14:       '만 14세 이상 동의',
};

export default function PolicyView() {
  const { t } = useTranslation();
  const { kind } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true); setError('');
    apiClient.get(`/api/policies/${kind}?lang=ko`)
      .then((d) => setData(d.policy || d))
      .catch((e) => setError(e.message || t('policy.load_failed', '약관을 불러오지 못했습니다.')))
      .finally(() => setLoading(false));
  }, [kind, t]);

  return (
    <div className="modern-page" style={{ maxWidth: 880, margin: '0 auto', padding: '24px' }}>
      <div style={{ marginBottom: 12 }}>
        <Link to="/dashboard" style={{
          display: 'inline-flex', alignItems: 'center', gap: 4,
          color: 'var(--pw-text-secondary)', textDecoration: 'none', fontSize: 13,
        }}>
          <ChevronLeft size={14} /> 대시보드로
        </Link>
      </div>

      <h1 style={{ marginBottom: 6 }}>{KIND_LABEL[kind] || t('policy.viewer_title', '약관 보기')}</h1>
      {data && (
        <p style={{ color: 'var(--pw-text-hint)', fontSize: 13, marginBottom: 24 }}>
          {t('policy.version_label', '버전')}: {data.version || '-'}
          {data.effective_at && (
            <> · {t('policy.effective_at_label', '시행일')}: {data.effective_at.slice(0, 10)}</>
          )}
        </p>
      )}

      {loading && <div style={{ color: 'var(--pw-text-hint)' }}>불러오는 중...</div>}
      {error && (
        <div className="card" style={{
          padding: 16, color: 'var(--pw-danger, #ef4444)',
          background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)',
        }}>{error}</div>
      )}
      {!loading && !error && data && (
        <pre style={{
          whiteSpace: 'pre-wrap', lineHeight: 1.7,
          color: 'var(--pw-text)', fontSize: 14,
          fontFamily: 'inherit',
          background: 'var(--pw-surface-1)',
          padding: 20, borderRadius: 12, border: '1px solid var(--pw-surface-line)',
        }}>{data.body}</pre>
      )}
    </div>
  );
}
