import React from 'react';
import { Battery as BatteryIcon } from 'lucide-react';
import ComingSoon from '../components/ComingSoon.jsx';

export default function Battery() {
  return (
    <div className="modern-page">
      <div className="page-header-section">
        <h1 className="page-title">배터리 모니터링</h1>
        <p className="sub-title">
          비콘별 배터리 잔량 시계열 + 임계치 미만 경고 + 교체 권장.
        </p>
      </div>
      <ComingSoon
        Icon={BatteryIcon}
        prNote="PR #38 예정 (PR #34 백엔드 데이터 활용)"
        endpoints={[
          'GET  /api/admin/beacons/<id>/battery',
          'POST /api/beacons/<id>/battery   (Flutter 앱 보고)',
        ]}
      />
    </div>
  );
}
