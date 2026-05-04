import React from 'react';
import './ConfirmModal.css';

const ConfirmModal = ({ isOpen, title, desc, onConfirm, onCancel, singleButton, confirmText = '확인', cancelText = '취소' }) => {
  if (!isOpen) return null;
  return (
    <div className="common-modal-overlay">
      <div className="common-custom-modal">
        <div className="common-modal-content">
          {title && <h3 className="common-modal-title">{title}</h3>}
          <p className="common-modal-desc">{desc}</p>
        </div>
        <div className="common-modal-actions">
          {!singleButton && (
            <button className="common-modal-btn cancel" onClick={onCancel}>
              {cancelText}
            </button>
          )}
          <button className="common-modal-btn" onClick={onConfirm} style={singleButton ? { borderLeft: 'none' } : {}}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;
