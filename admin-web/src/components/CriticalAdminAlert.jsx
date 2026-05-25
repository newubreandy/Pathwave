/**
 * D-4-pre — 슈퍼어드민 글로벌 알림 모달.
 *
 * DashboardLayout 에서 마운트 → 매 1분 /api/admin/critical-alerts polling.
 * 활성 알림 (snooze 안 된 popup level) 이 있으면 모달로 표시.
 *
 * 디자인
 * ------
 * - warn (cost-80) : 노랑 보더 + 일반 모달
 * - critical (cost-100) : 빨강 보더 + 사이렌 아이콘 + 강한 강조
 * - 모두 닫기 가능 (snooze) — 80%=24h / 100%=2h 자동 재표시
 * - 닫기 = X 버튼 또는 "나중에 다시 알림 받기" 버튼
 * - 본문 + 액션 가이드 링크 (전환 PoC docs)
 */
import React, { useEffect, useState } from 'react';
import { AlertTriangle, Siren, X } from 'lucide-react';
import { adminApi } from '../services/admin.js';

const POLL_INTERVAL_MS = 60_000;   // 1분

export default function CriticalAdminAlert() {
  const [alerts, setAlerts] = useState([]);
  const [busy, setBusy] = useState(false);

  // polling
  useEffect(() => {
    let alive = true;
    async function fetchOnce() {
      try {
        const res = await adminApi.criticalAlerts();
        if (alive) setAlerts(res?.alerts || []);
      } catch (_) {
        // 조용히 실패 (네트워크 에러 등 — 다음 polling 에서 재시도)
      }
    }
    fetchOnce();
    const id = setInterval(fetchOnce, POLL_INTERVAL_MS);
    return () => { alive = false; clearInterval(id); };
  }, []);

  if (!alerts.length) return null;

  // 우선순위: critical 먼저 표시
  const sorted = [...alerts].sort((a, b) => {
    const pri = { critical: 0, warn: 1, info: 2 };
    return (pri[a.level] || 9) - (pri[b.level] || 9);
  });
  const current = sorted[0];

  async function dismiss() {
    if (busy) return;
    setBusy(true);
    try {
      await adminApi.dismissAlert(current.id, current.snooze_hours || 2);
      // 로컬 제거 → 다음 polling 또는 즉시 다음 알림 표시
      setAlerts((cur) => cur.filter((a) => a.id !== current.id));
    } catch (_) {
      // 실패 시 그대로 두기 (사용자가 재시도 가능)
    } finally {
      setBusy(false);
    }
  }

  const isCritical = current.level === 'critical';

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="cad-title"
         style={{
           position: 'fixed', inset: 0, zIndex: 2000,
           background: 'rgba(0,0,0,0.6)',
           display: 'flex', alignItems: 'center', justifyContent: 'center',
           padding: '1rem',
         }}>
      <div style={{
        background: 'var(--bg-2)',
        border: `2px solid ${isCritical ? '#EF4444' : '#F59E0B'}`,
        borderRadius: 12,
        boxShadow: isCritical
          ? '0 0 40px rgba(239,68,68,0.4)'
          : '0 24px 48px rgba(0,0,0,0.4)',
        maxWidth: 520, width: '100%',
        padding: '1.5rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
          {isCritical
            ? <Siren size={28} color="#EF4444" aria-hidden="true"
                     style={{ flexShrink: 0 }} />
            : <AlertTriangle size={28} color="#F59E0B" aria-hidden="true"
                             style={{ flexShrink: 0 }} />}
          <div style={{ flex: 1, minWidth: 0 }}>
            <h2 id="cad-title" style={{ margin: 0, fontSize: 'var(--fs-lg)',
                  color: isCritical ? '#EF4444' : '#F59E0B' }}>
              {current.title}
            </h2>
            <p style={{ marginTop: '0.5rem', marginBottom: 0,
                        color: 'var(--text-secondary)',
                        fontSize: 'var(--fs-sm)', lineHeight: 1.6 }}>
              {current.body}
            </p>
          </div>
          <button onClick={dismiss} disabled={busy}
                  aria-label="알림 닫기 (자동 재표시)"
                  style={{ background: 'none', border: 'none',
                           color: 'var(--text-muted)', cursor: 'pointer',
                           padding: 4 }}>
            <X size={20} aria-hidden="true" />
          </button>
        </div>

        <div style={{ marginTop: '1.25rem', display: 'flex',
                      justifyContent: 'flex-end', gap: '0.5rem' }}>
          <a href="/dashboard/cost-monitor"
             className="btn btn-ghost"
             style={{ textDecoration: 'none' }}>
            비용 모니터로 이동
          </a>
          <button className="btn btn-primary" onClick={dismiss} disabled={busy}>
            {busy ? '처리 중...' : `확인 (${current.snooze_hours || 2}시간 후 재알림)`}
          </button>
        </div>

        {/* 추가 알림이 있으면 알려주기 */}
        {sorted.length > 1 && (
          <div style={{ marginTop: '0.5rem', textAlign: 'center',
                        color: 'var(--text-muted)',
                        fontSize: 'var(--fs-xs)' }}>
            (다른 알림 {sorted.length - 1}개 더 있음 — 확인 후 표시)
          </div>
        )}
      </div>
    </div>
  );
}
