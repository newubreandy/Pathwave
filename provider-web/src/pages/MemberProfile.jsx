import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, X } from 'lucide-react';
import ConfirmModal from '../components/common/ConfirmModal';
import './MemberProfile.css';

/* ── 더미 회원 데이터 ── */
const INITIAL_DATA = {
  company: {
    name: '호텔H',
    type: '법인사업자',
    registrationNumber: '759-07-12345',
    registrationFile: '사업자등록증.jpg',
    ceoName: '홍길동',
    cellularPhone: '010-1234-5678',
    officePhone: '02-1234-5678',
    address: '서울특별시 중구 동호로 249 (우편번호 : 04605)',
  },
  agent: {
    name: '신나라',
    phone: '010-1234-5678',
  },
  account: {
    id: 'hotel_H',
    password: 'Abcd468@',
    email: 'webmaster@hotelh.com',
  },
};

/* ── 편집 모달 ── */
const EditModal = ({ title, fields, onClose, onSave }) => {
  const [values, setValues] = useState(
    fields.reduce((acc, f) => ({ ...acc, [f.key]: f.value }), {})
  );

  const handleChange = (key, val) => {
    setValues(prev => ({ ...prev, [key]: val }));
  };

  return (
    <div className="settings-modal-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-modal-header">
          <h3 className="settings-modal-title">{title}</h3>
          <button className="settings-modal-close" onClick={onClose}><X size={20} /></button>
        </div>
        {fields.map(f => (
          <div key={f.key} className="settings-modal-field">
            <label className="settings-modal-label">{f.label}</label>
            <input
              className="settings-modal-input"
              type={f.type || 'text'}
              value={values[f.key]}
              onChange={e => handleChange(f.key, e.target.value)}
              disabled={f.disabled}
            />
          </div>
        ))}
        <div className="settings-modal-actions">
          <button className="settings-modal-btn cancel" onClick={onClose}>취소</button>
          <button className="settings-modal-btn confirm" onClick={() => onSave(values)}>저장</button>
        </div>
      </div>
    </div>
  );
};

/* ── Main Component ── */
const MemberProfile = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(INITIAL_DATA);
  const [editModal, setEditModal] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleSave = (section, values) => {
    setData(prev => ({
      ...prev,
      [section]: { ...prev[section], ...values },
    }));
    setEditModal(null);
  };

  const handleSubmit = () => {
    setShowConfirm(true);
  };

  const getEditFields = (section) => {
    switch (section) {
      case 'company':
        return [
          { key: 'ceoName', label: 'Ceo Name', value: data.company.ceoName },
          { key: 'cellularPhone', label: 'Cellular Phone', value: data.company.cellularPhone, type: 'tel' },
          { key: 'officePhone', label: 'Office', value: data.company.officePhone, type: 'tel' },
          { key: 'address', label: 'Address', value: data.company.address },
        ];
      case 'agent':
        return [
          { key: 'name', label: 'Agent', value: data.agent.name },
          { key: 'phone', label: 'Cellular Phone', value: data.agent.phone, type: 'tel' },
        ];
      case 'account':
        return [
          { key: 'id', label: 'ID', value: data.account.id, disabled: true },
          { key: 'password', label: 'PW', value: data.account.password, type: 'password' },
          { key: 'email', label: 'e-mail', value: data.account.email, type: 'email' },
        ];
      default:
        return [];
    }
  };

  const sectionTitles = {
    company: '회사정보 변경',
    agent: '담당자정보 변경',
    account: '계정정보 변경',
  };

  return (
    <div className="common-form-page">
      {/* 공통 폼 헤더 (모바일: sticky, PC: inline) */}
      <header className="common-form-header">
        <button className="back-btn d-md-none" onClick={() => navigate(-1)}>
          <ChevronLeft size={24} />
        </button>
        <h1>회원정보</h1>
      </header>

      <p className="sub-title mp-sub-title">업체 및 담당자 정보를 확인하고 수정합니다.</p>

      <div className="mp-content">
        {/* ── 회사정보 섹션 ── */}
        <section className="mp-section">
          <div className="mp-section-header">
            <h2 className="mp-section-title">회사정보</h2>
            <button className="mp-edit-btn" onClick={() => setEditModal('company')}>변경</button>
          </div>
          <div className="mp-table">
            <div className="mp-row">
              <span className="mp-label">Name</span>
              <span className="mp-value">{data.company.name}</span>
            </div>
            <div className="mp-row">
              <span className="mp-label">Type</span>
              <span className="mp-value">{data.company.type}</span>
            </div>
            <div className="mp-row">
              <span className="mp-label">Registration Number</span>
              <span className="mp-value">
                {data.company.registrationNumber}
                <br />
                <span className="mp-file-name">{data.company.registrationFile}</span>
              </span>
            </div>
          </div>
          <div className="mp-table mp-table-gap">
            <div className="mp-row">
              <span className="mp-label">Ceo Name</span>
              <span className="mp-value">{data.company.ceoName}</span>
            </div>
            <div className="mp-row">
              <span className="mp-label">Cellular Phone</span>
              <span className="mp-value">{data.company.cellularPhone}</span>
            </div>
            <div className="mp-row">
              <span className="mp-label">Office</span>
              <span className="mp-value">{data.company.officePhone}</span>
            </div>
            <div className="mp-row">
              <span className="mp-label">Address</span>
              <span className="mp-value">{data.company.address}</span>
            </div>
          </div>
        </section>

        {/* ── 담당자정보 섹션 ── */}
        <section className="mp-section">
          <div className="mp-section-header">
            <h2 className="mp-section-title">담당자정보</h2>
            <button className="mp-edit-btn" onClick={() => setEditModal('agent')}>변경</button>
          </div>
          <div className="mp-table">
            <div className="mp-row">
              <span className="mp-label">Agent</span>
              <span className="mp-value">{data.agent.name}</span>
            </div>
            <div className="mp-row">
              <span className="mp-label">Cellular Phone</span>
              <span className="mp-value">{data.agent.phone}</span>
            </div>
          </div>
        </section>

        {/* ── 계정정보 섹션 ── */}
        <section className="mp-section">
          <div className="mp-section-header">
            <h2 className="mp-section-title">계정정보</h2>
            <button className="mp-edit-btn" onClick={() => setEditModal('account')}>변경</button>
          </div>
          <div className="mp-table">
            <div className="mp-row">
              <span className="mp-label">ID</span>
              <span className="mp-value">{data.account.id}</span>
            </div>
            <div className="mp-row">
              <span className="mp-label">PW</span>
              <span className="mp-value">{data.account.password}</span>
            </div>
            <div className="mp-row">
              <span className="mp-label">e-mail</span>
              <span className="mp-value">{data.account.email}</span>
            </div>
          </div>
        </section>

        {/* ── 수정 버튼 ── */}
        <button className="mp-submit-btn" onClick={handleSubmit}>
          수정
        </button>
      </div>

      {/* ── 편집 모달 (Settings.css의 공통 모달 재사용) ── */}
      {editModal && (
        <EditModal
          title={sectionTitles[editModal]}
          fields={getEditFields(editModal)}
          onClose={() => setEditModal(null)}
          onSave={(values) => handleSave(editModal, values)}
        />
      )}

      {/* ── 확인 모달 ── */}
      {showConfirm && (
        <ConfirmModal
          title="저장 완료"
          message="회원정보가 성공적으로 저장되었습니다."
          confirmText="확인"
          onConfirm={() => setShowConfirm(false)}
          onCancel={() => setShowConfirm(false)}
        />
      )}
    </div>
  );
};

export default MemberProfile;
