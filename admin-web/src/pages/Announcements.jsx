import React from 'react';
import { Megaphone } from 'lucide-react';
import ComingSoon from '../components/ComingSoon.jsx';

export default function Announcements() {
  return (
    <div className="modern-page">
      <div className="page-header-section">
        <h1 className="page-title">시스템 공지</h1>
        <p className="sub-title">
          전체 사용자 / 사장 / 직원 대상 공지 작성, 수정, 삭제 + 푸시 발송.
        </p>
      </div>
      <ComingSoon
        Icon={Megaphone}
        prNote="PR #38 예정 (PR #33 백엔드 + PR #21 푸시 통합)"
        endpoints={[
          'GET    /api/admin/announcements',
          'POST   /api/admin/announcements',
          'PATCH  /api/admin/announcements/<id>',
          'DELETE /api/admin/announcements/<id>',
        ]}
      />
    </div>
  );
}
