import React from 'react';
import PwModal from './PwModal.jsx';

/**
 * 확인/취소 공용 모달.
 *
 * 접근성:
 *  - ESC 키로 취소 (onCancel 호출) — PwModal 내장 + onClose 연결
 *  - 열릴 때 기본 액션 버튼으로 포커스 이동 — PwModal 내장
 *  - 닫힐 때 이전 포커스 복원 — PwModal 내장
 *  - 외부 클릭은 일부러 닫지 않음 (오작동 방지) → busy=true 로 백드롭 닫힘 차단
 *
 * props (외부 API 무변경):
 *  - isOpen, title, desc, onConfirm, onCancel
 *  - singleButton, confirmText, cancelText
 */
const ConfirmModal = ({
  isOpen,
  title,
  desc,
  onConfirm,
  onCancel,
  singleButton,
  confirmText = '확인',
  cancelText = '취소',
}) => {
  // ESC: singleButton → onConfirm, 아니면 onCancel
  const handleClose = () => {
    if (singleButton) onConfirm?.();
    else onCancel?.();
  };

  return (
    <PwModal
      open={!!isOpen}
      onClose={handleClose}
      title={title}
      size="sm"
      footer={
        <div className="common-modal-actions">
          {!singleButton && (
            <button
              type="button"
              className="common-modal-btn cancel"
              onClick={onCancel}
            >
              {cancelText}
            </button>
          )}
          <button
            type="button"
            className="common-modal-btn"
            onClick={onConfirm}
            style={singleButton ? { borderLeft: 'none' } : {}}
          >
            {confirmText}
          </button>
        </div>
      }
    >
      {desc && (
        <p className="common-modal-desc">{desc}</p>
      )}
    </PwModal>
  );
};

export default ConfirmModal;
