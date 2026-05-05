import React from 'react';
import { Radio } from 'lucide-react';
import ComingSoon from '../components/ComingSoon.jsx';

export default function Beacons() {
  return (
    <div className="modern-page">
      <div className="page-header-section">
        <h1 className="page-title">비콘 인벤토리</h1>
        <p className="sub-title">
          비콘 입고(CSV 업로드 / SN 배열) · 목록 · 매장 할당 / 해제.
        </p>
      </div>
      <ComingSoon
        Icon={Radio}
        prNote="PR #37 예정"
        endpoints={[
          'GET    /api/admin/beacons',
          'POST   /api/admin/beacons/import',
          'PATCH  /api/admin/beacons/<id>',
          'POST   /api/admin/beacons/<id>/assign',
          'POST   /api/admin/beacons/<id>/unassign',
        ]}
      />
    </div>
  );
}
