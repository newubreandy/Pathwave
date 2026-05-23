import React, { useEffect, useRef, useId } from 'react';
import { X } from 'lucide-react';
import './Modal.css';

/**
 * 어드민 공용 모달.
 *
 * 접근성 (C-1d):
 *  - role="dialog" + aria-modal="true"
 *  - aria-labelledby = title 의 id (스크린리더가 모달 진입 시 제목 읽음)
 *  - Escape 키로 닫힘
 *  - 열릴 때 모달 안 첫 focusable 로 포커스 이동
 *  - 닫힐 때 이전 포커스 복원
 *  - Tab 순환은 브라우저 기본 동작에 위임 (별도 trap 미구현 — 모달 외부 요소가 inert 가 아니라
 *    완벽한 trap 은 어렵지만, 백드롭 클릭/Escape 로 항상 빠져나올 수 있음)
 */
export default function Modal({ open, onClose, title, children, footer, size = 'md' }) {
  const titleId = useId();
  const dialogRef = useRef(null);
  const previouslyFocused = useRef(null);

  // 키보드 닫기 (Escape)
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === 'Escape') onClose?.(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  // 포커스 이동/복원
  useEffect(() => {
    if (!open) return;
    previouslyFocused.current = document.activeElement;
    // 모달 안 첫 focusable 또는 dialog 자체로 이동
    const node = dialogRef.current;
    if (node) {
      const focusable = node.querySelector(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      (focusable || node).focus?.();
    }
    return () => {
      // 닫힐 때 이전 포커스 복원
      previouslyFocused.current?.focus?.();
    };
  }, [open]);

  if (!open) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        ref={dialogRef}
        className={`modal modal-${size}`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? titleId : undefined}
        tabIndex={-1}
      >
        <div className="modal-header">
          <h3 id={titleId} className="modal-title">{title}</h3>
          <button className="modal-close" onClick={onClose} aria-label="닫기" type="button">
            <X size={18} aria-hidden="true" />
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
}
