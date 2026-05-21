import React from 'react';
import './ConfirmModal.css';

/**
 * 공용 확인/안내 모달 — 네이티브 alert()/confirm() 대체.
 *
 * 직접 렌더링도 가능하지만, 명령형(async) 흐름에는 `useDialog()` 훅 사용을 권장한다.
 *
 * props
 *  - isOpen        표시 여부
 *  - title         제목 (선택)
 *  - desc          본문 — \n 줄바꿈 지원
 *  - onConfirm     확인 버튼
 *  - onCancel      취소 버튼
 *  - singleButton  true 면 확인 버튼만 (alert 모드)
 *  - danger        true 면 확인 버튼을 위험(빨강)으로 — 삭제 등 파괴적 동작
 *  - confirmText / cancelText  버튼 라벨
 */
const ConfirmModal = ({
  isOpen, title, desc, onConfirm, onCancel,
  singleButton, danger = false,
  confirmText = '확인', cancelText = '취소',
}) => {
  if (!isOpen) return null;
  return (
    <div className="common-modal-overlay">
      <div className="common-custom-modal" role="alertdialog" aria-modal="true">
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
          <button
            className={`common-modal-btn${danger ? ' danger' : ''}`}
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
