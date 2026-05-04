import React from 'react';
import './BottomActionBar.css';

/**
 * Common Bottom Action Bar Component
 * 화면 최하단에 항상 고정되는 액션 바입니다.
 * 
 * @param {ReactNode} children - 안에 들어갈 버튼 등 컨텐츠
 */
const BottomActionBar = ({ children }) => {
  return (
    <div className="bottom-action-bar-wrapper">
      <div className="bottom-action-bar">
        <div className="bottom-action-bar-inner">
          {children}
        </div>
      </div>
    </div>
  );
};

export default BottomActionBar;
