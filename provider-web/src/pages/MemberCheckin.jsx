/**
 * MemberCheckin — P22-b (2026-05-26): 회원 QR 체크인 화면 (provider-web).
 *
 * 점주가 손님의 회원 QR 을 스캔 → 백엔드 verify → 손님 정보 표시 →
 * 스탬프 적립 / 쿠폰 사용 버튼.
 *
 * 카메라 권한 / 라이브러리: html5-qrcode (~2.3.x).
 * v1 = 단순 1회 스캔 → 결과 + 액션. 연속 스캔 / 검증 후 자동 적립은 후속.
 */
import { useState, useEffect, useRef } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import { Camera, X, User, Stamp, Gift, Loader2 } from 'lucide-react';

import CheckinService from '../services/checkin/CheckinService';
import StampService from '../services/stamp/StampService';
import AuthService from '../services/auth/AuthService';
import Button from '../components/common/Button';
import { useConfirm } from '../hooks/useConfirm';
import './MemberCheckin.css';

const SCAN_REGION_ID = 'member-qr-scan-region';

export default function MemberCheckin() {
  const { confirm, alert, modal: confirmModal } = useConfirm();
  const scannerRef = useRef(null);
  const [scanning, setScanning] = useState(false);
  const [busy, setBusy] = useState(false);
  const [user, setUser] = useState(null);   // verify 응답
  const [error, setError] = useState(null);

  // ── 스캐너 라이프사이클 ─────────────────────────────────────
  const startScanner = async () => {
    setError(null);
    setUser(null);
    setScanning(true);

    // DOM 준비 대기
    await new Promise((r) => setTimeout(r, 50));
    try {
      const html5 = new Html5Qrcode(SCAN_REGION_ID);
      scannerRef.current = html5;
      await html5.start(
        { facingMode: 'environment' },     // 후면 카메라
        { fps: 10, qrbox: 260 },
        async (decoded) => { await handleScan(decoded); },
        () => {},                          // 디코드 실패는 무시 (계속 시도)
      );
    } catch (err) {
      setError(err?.message || '카메라를 시작할 수 없습니다. 권한을 확인해 주세요.');
      setScanning(false);
    }
  };

  const stopScanner = async () => {
    if (scannerRef.current) {
      try { await scannerRef.current.stop(); } catch { /* noop */ }
      try { await scannerRef.current.clear(); } catch { /* noop */ }
      scannerRef.current = null;
    }
    setScanning(false);
  };

  useEffect(() => {
    // 자동 종료 (페이지 이탈 시)
    return () => { stopScanner(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── 스캔 → verify ───────────────────────────────────────────
  const handleScan = async (token) => {
    if (busy) return;
    setBusy(true);
    await stopScanner();
    try {
      const res = await CheckinService.verify(token);
      if (res?.success) {
        setUser(res);
      } else {
        setError(res?.message || 'QR 검증 실패.');
      }
    } catch (err) {
      setError(err?.message || 'QR 검증 중 오류가 발생했습니다.');
    } finally {
      setBusy(false);
    }
  };

  // ── 스탬프 적립 ────────────────────────────────────────────
  const handleGrantStamp = async () => {
    if (!user?.user_id) return;
    const fid = user?.actor?.facility_id
      || AuthService.getCurrentUser()?.facility_id
      || AuthService.getCurrentUser()?.facilityId;
    if (!fid) {
      await alert({ title: '매장 정보 누락', desc: '점주 계정의 매장 ID 를 찾을 수 없습니다.' });
      return;
    }
    const ok = await confirm({
      title: '스탬프 적립',
      desc:  `회원 ${user.email || user.user_id} 에게 스탬프를 1개 적립하시겠습니까?`,
      confirmText: '적립',
    });
    if (!ok) return;

    setBusy(true);
    try {
      await StampService.grant({ facility_id: fid, user_id: user.user_id });
      await alert({ title: '적립 완료', desc: '스탬프 1개를 적립했습니다.' });
      // 같은 손님에 연속 적립 가능하도록 user 유지
    } catch (err) {
      await alert({
        title: '적립 실패',
        desc:  err?.message || '잠시 후 다시 시도해 주세요.',
      });
    } finally {
      setBusy(false);
    }
  };

  const handleReset = async () => {
    await stopScanner();
    setUser(null);
    setError(null);
  };

  // ── 렌더 ───────────────────────────────────────────────────
  return (
    <div className="member-checkin-page">
      <div className="member-checkin-header">
        <h1 className="page-title">회원 QR 체크인</h1>
        <p className="sub-title">손님의 PathWave 앱에서 회원 QR 을 받아 스캔하세요.</p>
      </div>

      {!scanning && !user && !error && (
        <Button onClick={startScanner} variant="primary" fullWidth>
          <Camera size={18} style={{ marginRight: 8 }} /> 스캔 시작
        </Button>
      )}

      {scanning && (
        <div className="member-checkin-scan-wrap">
          <div id={SCAN_REGION_ID} className="member-checkin-scan-region" />
          <Button onClick={stopScanner} variant="secondary" fullWidth>
            <X size={16} style={{ marginRight: 6 }} /> 취소
          </Button>
        </div>
      )}

      {busy && (
        <div className="member-checkin-busy">
          <Loader2 size={18} className="spin" /> 처리 중...
        </div>
      )}

      {error && (
        <div className="member-checkin-error">
          ⚠ {error}
          <Button onClick={handleReset} variant="secondary" style={{ marginTop: 12 }}>
            다시 시도
          </Button>
        </div>
      )}

      {user && !busy && (
        <div className="member-checkin-result">
          <div className="member-checkin-user-card">
            <User size={20} />
            <div>
              <div className="user-id">회원 ID: {user.user_id}</div>
              <div className="user-email">{user.email}</div>
              {user.is_minor && (
                <div className="user-minor">⚠ 미성년 회원 — 청소년 보호 정책 적용</div>
              )}
            </div>
          </div>

          <div className="member-checkin-actions">
            <Button onClick={handleGrantStamp} variant="primary" fullWidth>
              <Stamp size={16} style={{ marginRight: 6 }} /> 스탬프 1개 적립
            </Button>
            <Button onClick={handleReset} variant="secondary" fullWidth>
              <Gift size={16} style={{ marginRight: 6 }} /> 다른 손님 스캔
            </Button>
          </div>
        </div>
      )}

      {confirmModal}
    </div>
  );
}
