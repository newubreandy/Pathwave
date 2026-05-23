import React, { useEffect, useId, useRef } from 'react';
import './ConfirmModal.css';

/**
 * 확인/취소 공용 모달.
 *
 * 접근성 (C-1d):
 *  - role="dialog" + aria-modal="true"
 *  - aria-labelledby = title id / aria-describedby = desc id
 *  - Escape 키로 취소 (onCancel 호출)
 *  - 열릴 때 기본 액션 버튼으로 포커스 이동
 *  - 닫힐 때 이전 포커스 복원
 *  - 외부 클릭은 일부러 닫지 않음 (오작동 방지 — project_ui_legal_compliance)
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
  const titleId = useId();
  const descId = useId();
  const dialogRef = useRef(null);
  const previouslyFocused = useRef(null);

  // Escape 닫기
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e) => {
      if (e.key === 'Escape') {
        if (singleButton) onConfirm?.();
        else onCancel?.();
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [isOpen, onCancel, onConfirm, singleButton]);

  // 포커스 이동/복원
  useEffect(() => {
    if (!isOpen) return;
    previouslyFocused.current = document.activeElement;
    const node = dialogRef.current;
    if (node) {
      const focusable = node.querySelector(
        'button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      (focusable || node).focus?.();
    }
    return () => {
      previouslyFocused.current?.focus?.();
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="common-modal-overlay" role="presentation">
      <div
        ref={dialogRef}
        className="common-custom-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? titleId : undefined}
        aria-describedby={desc ? descId : undefined}
        tabIndex={-1}
      >
        <div className="common-modal-content">
          {title && (
            <h3 id={titleId} className="common-modal-title">{title}</h3>
          )}
          {desc && (
            <p id={descId} className="common-modal-desc">{desc}</p>
          )}
        </div>
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
      </div>
    </div>
  );
};

export default ConfirmModal;
