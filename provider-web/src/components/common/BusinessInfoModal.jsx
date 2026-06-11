import React, { useState } from 'react';
import { Info } from 'lucide-react';
import AuthService from '../../services/auth/AuthService';
import PwModal, { PwField } from './PwModal.jsx';
import '../../pages/Settings.css';

/**
 * BusinessInfoModal — 사업자(회사) 정보 변경 모달.
 *
 *   회사정보(대표자명/사업자번호/연락처/이메일)는 단순 inline 수정이 아니라
 *   슈퍼어드민 승인 워크플로(요청중 → 검토중 → 승인완료/반려)를 거쳐 적용된다.
 *   따라서 결제 흐름이나 설정 페이지 어디서 호출하든 동일 모달로 진입한다.
 *
 *   props:
 *     - onClose
 *     - context: 'settings' | 'payment'
 *         payment 컨텍스트(결제 단계)에서는 상단 안내 문구가 결제 맥락으로 변환됨.
 */
export default function BusinessInfoModal({ onClose, context = 'settings' }) {
  const user = AuthService.getCurrentUser();
  // P5 (2026-05-26): mock fallback ('시원컴퍼니' / '02-1234-5678' / 'admin@pathwave.com') 제거.
  // 사장이 직접 입력하거나, 백엔드 GET /api/account/business-info 에서 fetch (Phase 2+).
  const [formData, setFormData] = useState({
    name: user?.name || '',
    bizNumber: '',
    phone: '',
    email: user?.email || '',
  });
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    // TODO: POST /api/account/business-info/change-request
    // 슈퍼어드민 승인 큐로 들어감. 즉시 반영되지 않음.
    setSubmitted(true);
    setTimeout(() => onClose(), 1800);
  };

  const noticeText = context === 'payment'
    ? '이메일은 회사 정보의 일부입니다. 결제 단계에서는 직접 변경할 수 없으며, 회사 정보 변경 요청 후 슈퍼어드민 승인이 완료되면 결제가 정상 진행됩니다.'
    : '회사 정보 변경은 슈퍼어드민 승인 후 반영됩니다. 변경 요청 → 검토 → 승인 단계를 거치며, 진행 상태는 알림으로 안내됩니다.';

  return (
    <PwModal
      open
      onClose={onClose}
      title="사업자 정보 변경"
      size="md"
      footer={!submitted && (
        <>
          <button className="settings-modal-btn cancel" onClick={onClose}>취소</button>
          <button className="settings-modal-btn confirm" onClick={handleSubmit}>변경 요청</button>
        </>
      )}
    >
      {submitted ? (
        <div className="biz-modal-success">
          <div className="biz-modal-success-icon">✓</div>
          <p className="biz-modal-success-title">변경 요청이 접수되었습니다</p>
          <p className="biz-modal-success-desc">
            슈퍼어드민 검토 후 반영됩니다. 진행 상태는 설정 &gt; 계정 관리에서 확인하거나 알림으로 안내됩니다.
          </p>
        </div>
      ) : (
        <>
          <div className="biz-modal-notice">
            <Info size={14} aria-hidden="true" />
            <span>{noticeText}</span>
          </div>

          <PwField label="대표자명">
            <input
              type="text"
              className="settings-modal-input"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="대표자명"
            />
          </PwField>

          <PwField label="사업자번호">
            <input
              type="text"
              className="settings-modal-input"
              value={formData.bizNumber}
              onChange={(e) => setFormData({ ...formData, bizNumber: e.target.value })}
              placeholder="000-00-00000"
            />
          </PwField>

          <PwField label="연락처">
            <input
              type="tel"
              className="settings-modal-input"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              placeholder="02-0000-0000"
            />
          </PwField>

          <PwField label="이메일">
            <input
              type="email"
              className="settings-modal-input"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="email@example.com"
            />
          </PwField>
        </>
      )}
    </PwModal>
  );
}
