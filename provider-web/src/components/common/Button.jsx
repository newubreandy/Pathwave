import React from 'react';
import './Button.css';

/**
 * Common Button Component
 * @param {string} variant - 'primary' | 'outline' | 'danger' | 'text' (default: 'primary')
 * @param {string} size - 'small' | 'medium' | 'large' (default: 'medium')
 * @param {boolean} fullWidth - 버튼 너비를 100%로 채울지 여부 (default: false)
 * @param {boolean} disabled - 비활성화 여부
 * @param {boolean} isLoading - 로딩 상태 여부
 * @param {ReactNode} icon - 버튼 텍스트 앞 또는 뒤에 들어갈 아이콘 컴포넌트
 * @param {function} onClick - 클릭 이벤트 핸들러
 * @param {ReactNode} children - 버튼 내용 (텍스트)
 */
const Button = ({
  variant = 'primary',
  size = 'medium',
  fullWidth = false,
  disabled = false,
  isLoading = false,
  icon = null,
  onClick,
  children,
  className = '',
  type = 'button',
  ...props
}) => {
  const baseClass = 'common-btn';
  const variantClass = `btn-${variant}`;
  const sizeClass = `btn-${size}`;
  const widthClass = fullWidth ? 'btn-full-width' : '';
  const loadingClass = isLoading ? 'btn-loading' : '';

  const classes = [baseClass, variantClass, sizeClass, widthClass, loadingClass, className]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      type={type}
      className={classes}
      onClick={onClick}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="btn-spinner"></span>
      ) : (
        <>
          {icon && <span className="btn-icon">{icon}</span>}
          {children}
        </>
      )}
    </button>
  );
};

export default Button;
