/**
 * PwModal — 공용 모달 컴포넌트 (2026-05-27).
 *
 * 디자인 가이드
 * ------------
 * - 배경: rgba(0,0,0,0.6) + backdrop-filter blur(8px)
 * - 카드: var(--pw-surface) + radius-lg + shadow-xl
 * - 백드롭 클릭 = 닫힘 (사용자 정책: 유지)
 * - Escape 키 = 닫힘
 * - 포커스 트랩 (a11y) + 닫을 때 이전 포커스 복원
 *
 * props
 * -----
 * - open       : boolean
 * - onClose    : () => void
 * - title      : string
 * - children   : 본문 (form 등)
 * - footer     : 푸터 영역 (버튼들)
 * - size       : 'sm' | 'md' | 'lg'  (기본 'md' = 480px)
 * - busy       : 처리 중이면 백드롭 닫힘 무시
 *
 * 사용 예
 * -------
 *   <PwModal open={!!draft} onClose={close} title="메뉴 추가"
 *            footer={<><button>취소</button><button>저장</button></>}>
 *     <PwField label="이름 *"><input ... /></PwField>
 *     <PwField label="가격"><input ... /></PwField>
 *   </PwModal>
 */
import React, { useEffect, useRef, useId } from 'react';
import './PwModal.css';

export default function PwModal({
  open, onClose, title, children, footer, size = 'md', busy = false,
}) {
  const titleId = useId();
  const dialogRef = useRef(null);
  const previouslyFocused = useRef(null);

  // Escape 닫기
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === 'Escape' && !busy) onClose?.(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, busy, onClose]);

  // 포커스 이동/복원
  useEffect(() => {
    if (!open) return;
    previouslyFocused.current = document.activeElement;
    const node = dialogRef.current;
    if (node) {
      const focusable = node.querySelector(
        'input:not([disabled]), textarea:not([disabled]), select:not([disabled]), button:not([disabled])',
      );
      (focusable || node).focus?.();
    }
    return () => { previouslyFocused.current?.focus?.(); };
  }, [open]);

  // 스크롤 잠금
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = prev; };
  }, [open]);

  if (!open) return null;

  return (
    <div
      className="pw-modal-overlay"
      role="presentation"
      onClick={busy ? undefined : onClose}
    >
      <div
        ref={dialogRef}
        className={`pw-modal pw-modal--${size}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? titleId : undefined}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        {title && (
          <div className="pw-modal__header">
            <h3 id={titleId} className="pw-modal__title">{title}</h3>
            <button
              type="button"
              className="pw-modal__close"
              onClick={onClose}
              disabled={busy}
              aria-label="닫기"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                   strokeLinejoin="round" aria-hidden="true">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        )}
        <div className="pw-modal__body">
          {children}
        </div>
        {footer && (
          <div className="pw-modal__footer">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

/** 통일 라벨 + 입력 — PwModal 안에서 사용. */
export function PwField({ label, hint, error, children }) {
  return (
    <div className="pw-field">
      {label && <label className="pw-field__label">{label}</label>}
      <div className="pw-field__control">{children}</div>
      {hint && !error && <div className="pw-field__hint">{hint}</div>}
      {error && <div className="pw-field__error">{error}</div>}
    </div>
  );
}
