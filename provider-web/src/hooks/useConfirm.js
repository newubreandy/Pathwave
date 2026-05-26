/**
 * useConfirm — Promise 기반 ConfirmModal 헬퍼 (P3-b).
 *
 * 기존 window.alert/confirm 의 동기 호출 패턴을 그대로 유지하되,
 * ConfirmModal 의 디자인 시스템 / 접근성 / 다크 톤 적용.
 *
 * 사용
 * ----
 *   const { confirm, alert, modal } = useConfirm();
 *
 *   const ok = await confirm({
 *     title: '삭제하시겠습니까?',
 *     desc:  '이 동작은 되돌릴 수 없습니다.',
 *     confirmText: '삭제', cancelText: '취소',
 *   });
 *   if (ok) await doDelete();
 *
 *   await alert({ title: '완료', desc: '저장되었습니다.' });
 *
 *   return (
 *     <>
 *       ...
 *       {modal}
 *     </>
 *   );
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

  /** 확인/취소 모달. Promise<boolean> (확인=true, 취소=false). */
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

  /** 단일 버튼 알림 모달. Promise<void>. */
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
