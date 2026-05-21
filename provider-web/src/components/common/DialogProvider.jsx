import React, {
  createContext, useContext, useState, useRef, useCallback, useEffect,
} from 'react';
import ConfirmModal from './ConfirmModal';

/**
 * 명령형 확인/안내 다이얼로그 — 네이티브 alert()/confirm() 대체.
 *
 * 사용
 * ----
 *   const { confirm, alert } = useDialog();
 *
 *   if (await confirm('정말 삭제하시겠습니까?')) { ... }
 *   await confirm({ title: '삭제', message: '...', danger: true });
 *   await alert('저장되었습니다.');
 *
 * confirm → Promise<boolean>, alert → Promise<true>.
 * 문자열을 넘기면 message 로 처리한다.
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

  // Escape — confirm 은 취소(false), alert 는 닫기(true).
  useEffect(() => {
    if (!dialog) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') close(dialog.mode === 'alert');
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [dialog, close]);

  return (
    <DialogContext.Provider value={{ confirm, alert }}>
      {children}
      {dialog && (
        <ConfirmModal
          isOpen
          title={dialog.title}
          desc={dialog.message}
          singleButton={dialog.mode === 'alert'}
          danger={!!dialog.danger}
          confirmText={dialog.confirmText || '확인'}
          cancelText={dialog.cancelText || '취소'}
          onConfirm={() => close(true)}
          onCancel={() => close(false)}
        />
      )}
    </DialogContext.Provider>
  );
}

export function useDialog() {
  const ctx = useContext(DialogContext);
  if (!ctx) throw new Error('useDialog 는 DialogProvider 안에서만 사용할 수 있습니다.');
  return ctx;
}
