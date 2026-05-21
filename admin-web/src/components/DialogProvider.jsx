import React, {
  createContext, useContext, useState, useRef, useCallback,
} from 'react';
import Modal from './Modal';

/**
 * 명령형 확인/안내 다이얼로그 — 네이티브 alert()/confirm() 대체.
 *
 * 사용
 * ----
 *   const { confirm, alert } = useDialog();
 *
 *   if (await confirm('정말 삭제하시겠습니까?')) { ... }
 *   await confirm({ title: '계정 삭제', message: '...', danger: true });
 *   await alert('저장되었습니다.');
 *
 * confirm → Promise<boolean>, alert → Promise<true>.
 * 문자열을 넘기면 message 로 처리한다. 공용 Modal 컴포넌트를 재사용한다.
 */
const DialogContext = createContext(null);

export function DialogProvider({ children }) {
  const [dialog, setDialog] = useState(null);
  const resolverRef = useRef(null);

  const close = useCallback((result) => {
    setDialog(null);
    const resolve = resolverRef.current;
    resolverRef.current = null;
    if (resolve) resolve(result);
  }, []);

  const open = useCallback((mode, opts) => {
    const o = typeof opts === 'string' ? { message: opts } : (opts || {});
    return new Promise((resolve) => {
      resolverRef.current = resolve;
      setDialog({ mode, ...o });
    });
  }, []);

  const confirm = useCallback((opts) => open('confirm', opts), [open]);
  const alert = useCallback((opts) => open('alert', opts), [open]);

  const isAlert = dialog?.mode === 'alert';

  return (
    <DialogContext.Provider value={{ confirm, alert }}>
      {children}
      {dialog && (
        <Modal
          open
          size="sm"
          title={dialog.title || (isAlert ? '알림' : '확인')}
          // backdrop·X·Escape → confirm 은 취소(false), alert 는 닫기(true)
          onClose={() => close(isAlert)}
          footer={(
            <>
              {!isAlert && (
                <button className="btn btn-ghost" onClick={() => close(false)}>
                  {dialog.cancelText || '취소'}
                </button>
              )}
              <button
                className={`btn ${dialog.danger ? 'btn-danger' : 'btn-primary'}`}
                onClick={() => close(true)}
              >
                {dialog.confirmText || '확인'}
              </button>
            </>
          )}
        >
          <p style={{ margin: 0, whiteSpace: 'pre-line', lineHeight: 1.6 }}>
            {dialog.message}
          </p>
        </Modal>
      )}
    </DialogContext.Provider>
  );
}

export function useDialog() {
  const ctx = useContext(DialogContext);
  if (!ctx) throw new Error('useDialog 는 DialogProvider 안에서만 사용할 수 있습니다.');
  return ctx;
}
