import React, { useState } from 'react';
import { X, Info } from 'lucide-react';
import AuthService from '../../services/auth/AuthService';
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
  const [formData, setFormData] = useState({
    name: user?.name || '시원컴퍼니',
    bizNumber: '123-45-67890',
    phone: '02-1234-5678',
    email: user?.email || 'admin@pathwave.com',
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
    <div className="settings-modal-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="settings-modal-header">
          <h2 className="settings-modal-title">사업자 정보 변경</h2>
          <button className="settings-modal-close" onClick={onClose} aria-label="닫기">
            <X size={20} />
          </button>
        </div>

        <div className="settings-modal-body">
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

              <div className="settings-modal-field">
                <label className="settings-modal-label">대표자명</label>
                <input
                  type="text"
                  className="settings-modal-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>

              <div className="settings-modal-field">
                <label className="settings-modal-label">사업자번호</label>
                <input
                  type="text"
                  className="settings-modal-input"
                  value={formData.bizNumber}
                  onChange={(e) => setFormData({ ...formData, bizNumber: e.target.value })}
                  placeholder="000-00-00000"
                />
              </div>

              <div className="settings-modal-field">
                <label className="settings-modal-label">연락처</label>
                <input
                  type="tel"
                  className="settings-modal-input"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="02-0000-0000"
                />
              </div>

              <div className="settings-modal-field">
                <label className="settings-modal-label">이메일</label>
                <input
                  type="email"
                  className="settings-modal-input"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>

              <div className="settings-modal-actions">
                <button className="settings-modal-btn cancel" onClick={onClose}>취소</button>
                <button className="settings-modal-btn confirm" onClick={handleSubmit}>변경 요청</button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
