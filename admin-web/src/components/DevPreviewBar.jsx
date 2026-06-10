import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * PR #65 — 미리보기 모드 (운영자 콘솔 / 실서버 검증용 임시 UI).
 * 활성: `VITE_PREVIEW_MODE=true` 이며 MODE 가 production 이 아닐 때만.
 *
 * P4 강화(2026-06-08) — MODE='production' 이면 ENV 와 무관하게 강제 비활성.
 */
const PREVIEW = (
  import.meta.env.VITE_PREVIEW_MODE === 'true' &&
  import.meta.env.MODE !== 'production'
);

const PAGES = [
  ['/dashboard',                '대시보드'],
  ['/dashboard/beacons',        '비콘 인벤토리'],
  ['/dashboard/approvals',      '사장 승인'],
  ['/dashboard/battery',        '배터리 모니터'],
  ['/dashboard/announcements',  '공지'],
  ['/dashboard/payments',       '결제·구독'],
  ['/dashboard/policies',       '약관 관리'],
];

export default function DevPreviewBar() {
  if (!PREVIEW) return null;
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const enterPreview = () => {
    localStorage.setItem('pathwave_admin_token', 'preview-mode-fake-token');
    localStorage.setItem('pathwave_admin_user', JSON.stringify({
      id: 0, email: 'preview@dev.local', role: 'super_admin',
      name: '미리보기 모드',
    }));
    navigate('/dashboard', { replace: true });
  };

  const clearPreview = () => {
    localStorage.removeItem('pathwave_admin_token');
    localStorage.removeItem('pathwave_admin_user');
    localStorage.removeItem('pathwave_admin_refresh_token');
    navigate('/login', { replace: true });
  };

  return (
    <div style={styles.bar}>
      <div style={styles.warn}>
        ⚠️ <b>미리보기 모드</b> — PRODUCTION 에서 반드시 제거 (VITE_PREVIEW_MODE=true)
      </div>
      <div style={styles.actions}>
        <button style={styles.btn} onClick={enterPreview}>🔓 토큰 주입</button>
        <button style={styles.btn} onClick={() => setOpen(!open)}>
          📂 페이지 {open ? '▲' : '▼'}
        </button>
        <button style={{...styles.btn, ...styles.btnDanger}} onClick={clearPreview}>
          🗑 토큰 해제
        </button>
      </div>
      {open && (
        <div style={styles.menu}>
          {PAGES.map(([path, label]) => (
            <button key={path} style={styles.menuBtn}
                    onClick={() => { navigate(path); setOpen(false); }}>
              {label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  bar: {
    position: 'fixed', bottom: 0, left: 0, right: 0,
    background: '#fef3c7', borderTop: '2px solid #f59e0b',
    padding: '8px 16px', zIndex: 9999,
    fontSize: 12, color: '#78350f',
    boxShadow: '0 -4px 12px rgba(0,0,0,0.08)',
    fontFamily: 'system-ui',
  },
  warn: { textAlign: 'center', marginBottom: 6 },
  actions: { display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' },
  btn: {
    padding: '4px 10px', fontSize: 11,
    border: '1px solid #d97706', background: '#fff',
    borderRadius: 4, cursor: 'pointer', color: '#78350f',
  },
  btnDanger: { borderColor: '#dc2626', color: '#991b1b' },
  menu: {
    marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 4,
    justifyContent: 'center',
  },
  menuBtn: {
    padding: '3px 8px', fontSize: 11,
    border: '1px solid #fbbf24', background: '#fffbeb',
    borderRadius: 3, cursor: 'pointer', color: '#78350f',
  },
};
