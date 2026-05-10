import './BottomActionBar.css';

/**
 * BottomActionBar — 페이지 하단 CTA 영역.
 *
 *   inline (default): 콘텐츠 흐름 안에 배치 (form 페이지 등 — 기존 동작 보존).
 *   sticky=true     : 모바일에서 화면 하단에 고정.
 *                     - safe-area-inset-bottom 자동 대응 (iOS notch/home indicator)
 *                     - PC 에서는 inline 처럼 동작 (sticky bottom 0 로 자연 정렬)
 *
 * 키보드 가림 대응: visualViewport API 활용 — 키보드 올라오면 ‘bottom’ 이
 * 키보드 위로 자동 따라 올라감. position: fixed 가 아니라 sticky 라
 * 기본 안전.
 *
 * @param {ReactNode} children
 * @param {boolean}   sticky    — true 면 모바일에서 fixed-bottom 동작
 */
const BottomActionBar = ({ children, sticky = false }) => {
  return (
    <div className={`bottom-action-bar-wrapper ${sticky ? 'is-sticky' : ''}`}>
      <div className="bottom-action-bar">
        <div className="bottom-action-bar-inner">
          {children}
        </div>
      </div>
    </div>
  );
};

export default BottomActionBar;
