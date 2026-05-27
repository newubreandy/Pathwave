/**
 * useConfirm — Promise 기반 ConfirmModal 헬퍼 (P3-b, admin-web).
 *
 * provider-web 의 useConfirm 와 동일 구조 + admin 의 ConfirmModal 사용
 * (--pw-accent 블루 #2563EB 토큰).
 */
import { useState, useCallback } from 'react';
import ConfirmModal from '../components/common/ConfirmModal';

export function useConfirm() {
  const [state, setState] = useState({
    open: false,
    title: '',
    desc: '',
    singleButton: false,
    confirmText: '확인',
    cancelText: '취소',
    resolver: null,
  });

  const close = useCallback((result) => {
    setState((s) => {
      s.resolver?.(result);
      return { ...s, open: false, resolver: null };
    });
  }, []);

  const confirm = useCallback((opts = {}) => {
    return new Promise((resolve) => {
      setState({
        open: true,
        title: opts.title || '확인',
        desc: opts.desc || '',
        singleButton: false,
        confirmText: opts.confirmText || '확인',
        cancelText: opts.cancelText || '취소',
        resolver: resolve,
      });
    });
  }, []);

  const alert = useCallback((opts = {}) => {
    return new Promise((resolve) => {
      setState({
        open: true,
        title: opts.title || '알림',
        desc: opts.desc || '',
        singleButton: true,
        confirmText: opts.confirmText || '확인',
        cancelText: '',
        resolver: () => resolve(),
      });
    });
  }, []);

  const modal = (
    <ConfirmModal
      isOpen={state.open}
      title={state.title}
      desc={state.desc}
      singleButton={state.singleButton}
      confirmText={state.confirmText}
      cancelText={state.cancelText}
      onConfirm={() => close(true)}
      onCancel={() => close(false)}
    />
  );

  return { confirm, alert, modal };
}

export default useConfirm;
