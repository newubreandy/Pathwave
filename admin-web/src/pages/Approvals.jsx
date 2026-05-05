import React from 'react';
import { UserCheck } from 'lucide-react';
import ComingSoon from '../components/ComingSoon.jsx';

export default function Approvals() {
  return (
    <div className="modern-page">
      <div className="page-header-section">
        <h1 className="page-title">사장 가입 승인</h1>
        <p className="sub-title">
          사장 회원가입 신청 → 사업자등록번호 검증 → 승인 / 거부.
        </p>
      </div>
      <ComingSoon
        Icon={UserCheck}
        prNote="PR #37 예정"
        endpoints={[
          'GET   /api/admin/facility-accounts?status=pending',
          'GET   /api/admin/facility-accounts/<id>',
          'POST  /api/admin/facility-accounts/<id>/verify',
          'POST  /api/admin/facility-accounts/<id>/suspend',
          'POST  /api/admin/facility-accounts/<id>/reactivate',
        ]}
      />
    </div>
  );
}
