import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import './PasswordInput.css';

const PasswordInput = ({ value, onChange, placeholder, autoComplete, disabled, className = '' }) => {
  const [visible, setVisible] = useState(false);

  return (
    <div className="pw-password-wrap">
      <input
        type={visible ? 'text' : 'password'}
        className={`settings-modal-input ${className}`}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        autoComplete={autoComplete}
        disabled={disabled}
      />
      <button
        type="button"
        className="pw-password-toggle"
        onClick={() => setVisible(v => !v)}
        tabIndex={-1}
        aria-label={visible ? '비밀번호 숨기기' : '비밀번호 보기'}
      >
        {visible ? <EyeOff size={18} /> : <Eye size={18} />}
      </button>
    </div>
  );
};

export default PasswordInput;
