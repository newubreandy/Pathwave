import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * PR #65 — 미리보기 모드 (실서버 검증용 임시 UI).
 *
 * 활성 조건: `VITE_PREVIEW_MODE=true` 로 빌드/실행했을 때만 렌더.
 * 프로덕션 빌드 (env 미설정) 는 import.meta.env 가 false 가 되어
 * 빈 컴포넌트를 반환 — Vite 가 트리쉐이킹으로 코드 자체를 제거.
 *
 * 출시 전 이 파일 자체와 App.jsx 의 임포트만 삭제하면 됨.
 */
const PREVIEW = import.meta.env.VITE_PREVIEW_MODE === 'true';

const PAGES = [
  ['/dashboard',          '오버뷰'],
  ['/dashboard/store',    '매장 정보'],
  ['/dashboard/wifi',     'WiFi'],
  ['/dashboard/staff',    '직원 관리'],
  ['/dashboard/notifications', '알림'],
  ['/dashboard/stamps',   '스탬프'],
  ['/dashboard/coupons',  '쿠폰'],
  ['/dashboard/payments', '결제'],
  ['/dashboard/chat',     '채팅'],
  ['/dashboard/report',   '리포트'],
  ['/dashboard/settings', '설정'],
];

export default function DevPreviewBar() {
  if (!PREVIEW) return null;
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const enterPreview = () => {
    // 가짜 토큰 — 백엔드 호출은 실패하지만 RequireAuth 통과해 화면 렌더 가능
    localStorage.setItem('pathwave_token', 'preview-mode-fake-token');
    localStorage.setItem('pathwave_user', JSON.stringify({
      id: 0, email: 'preview@dev.local', name: '미리보기 모드',
      role: 'facility',
    }));
    navigate('/dashboard', { replace: true });
  };

  const clearPreview = () => {
    localStorage.removeItem('pathwave_token');
    localStorage.removeItem('pathwave_user');
    localStorage.removeItem('pathwave_refresh_token');
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
