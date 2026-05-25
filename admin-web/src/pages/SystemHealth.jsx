/**
 * A-023 — 시스템 환경 점검 (외부 키 상태 + 모드).
 *
 * GET /api/admin/system/health 응답을 카드 그리드로 표시.
 * - live    : 실 키 설정됨 (녹색)
 * - stub    : 개발 모드 (노란색)
 * - missing : 미설정 운영 전 등록 필요 (빨간색)
 *
 * 운영 전 5단계 중 단계 2 (외부 서비스 신청) 후 본 페이지에서 확인 → 모든
 * 서비스가 'live' 가 될 때까지 PR / 환경변수 보강.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { RefreshCw, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { adminApi } from '../services/admin.js';

const MODE_META = {
  live:    { color: '#22C55E', icon: CheckCircle2, label: '✅ 운영' },
  stub:    { color: '#F59E0B', icon: AlertTriangle, label: '⚠️ 개발(stub)' },
  missing: { color: '#EF4444', icon: XCircle,      label: '❌ 미설정' },
};

export default function SystemHealth() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const reload = useCallback(async () => {
    setLoading(true); setError('');
    try {
      setData(await adminApi.systemHealth());
    } catch (e) {
      setError(e?.message || '불러오기 실패');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { reload(); }, [reload]);

  const services = data?.services || [];
  const summary  = data?.summary  || { live: 0, stub: 0, missing: 0 };

  return (
    <div>
      <div className="page-header" style={{ display: 'flex',
            alignItems: 'center', justifyContent: 'space-between',
            marginBottom: '1rem' }}>
        <div>
          <h1 className="page-title">시스템 환경 점검</h1>
          <p className="page-subtitle">
            외부 서비스(Firebase / DeepL / SendGrid / 토스 / Sentry / Maps) 키 설정 + 모드 상태.
          </p>
        </div>
        <button className="btn btn-ghost" onClick={reload} disabled={loading}
                aria-label="새로고침">
          <RefreshCw size={16} className={loading ? 'spin' : ''} aria-hidden="true" />
        </button>
      </div>

      {error && <div className="error-box" style={{ marginBottom: '1rem' }}>{error}</div>}

      {/* 요약 칩 */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem',
                    flexWrap: 'wrap' }}>
        <Chip mode="live"    count={summary.live} />
        <Chip mode="stub"    count={summary.stub} />
        <Chip mode="missing" count={summary.missing} />
      </div>

      {/* 서비스 카드 그리드 */}
      <div style={{ display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '0.875rem' }}>
        {services.map((s) => (
          <ServiceCard key={s.key} service={s} />
        ))}
      </div>

      <div style={{ marginTop: '1.5rem', padding: '1rem',
            background: 'var(--bg-3)', border: '1px solid var(--border)',
            borderRadius: 8, fontSize: 'var(--fs-sm)',
            color: 'var(--text-secondary)' }}>
        💡 <strong>다음 단계</strong>: 모든 서비스가 <span style={{ color: '#22C55E' }}>✅ 운영</span>이 될 때까지 환경변수에 실 키 설정 + 백엔드 재시작. 운영 전 ❌ 항목은 신청/등록 필수.
      </div>
    </div>
  );
}

function Chip({ mode, count }) {
  const m = MODE_META[mode];
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem',
                  padding: '0.4rem 0.8rem', borderRadius: 999,
                  border: `1px solid ${m.color}`,
                  color: m.color, fontSize: 'var(--fs-sm)',
                  fontWeight: 600 }}>
      {m.label} <span style={{ opacity: 0.7 }}>· {count}</span>
    </div>
  );
}

function ServiceCard({ service }) {
  const m = MODE_META[service.mode] || MODE_META.missing;
  const Icon = m.icon;
  return (
    <div style={{ padding: '1rem', background: 'var(--bg-3)',
                  border: '1px solid var(--border)', borderRadius: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem',
                    marginBottom: '0.5rem' }}>
        <Icon size={18} color={m.color} aria-hidden="true" />
        <h3 style={{ margin: 0, fontSize: 'var(--fs-md)' }}>{service.label}</h3>
      </div>
      <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-muted)' }}>
        <code style={{ fontSize: 'var(--fs-xs)' }}>{service.key}</code>
      </div>
      <div style={{ marginTop: '0.5rem', color: m.color,
                    fontWeight: 600, fontSize: 'var(--fs-sm)' }}>
        {m.label}
      </div>
      <div style={{ marginTop: '0.25rem', fontSize: 'var(--fs-xs)',
                    color: 'var(--text-muted)' }}>
        {service.detail}
      </div>
    </div>
  );
}
