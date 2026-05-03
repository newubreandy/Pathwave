import React, { useState, useRef } from 'react';
import { Plus, MapPin, Edit2, Trash2, X, Camera } from 'lucide-react';
import './Facilities.css';

const Facilities = () => {
  const [facilities, setFacilities] = useState([
    { 
      id: 1, 
      name: '호텔H (데모)', 
      address: '서울특별시 중구 소공로 249', 
      phone: '02-2233-3131',
      description: '호텔H는 최고급 호스피탈리티를 목표로 오랜 세월 동안 전통과 혁신을 유지하며 고객들께 감동을 제공해 왔습니다.',
      benefits: '[혜택] 호텔H 숙박 스탬프 이벤트 진행',
      images: ['https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&q=80&w=400'],
      status: '영업중' 
    },
  ]);

  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [currentId, setCurrentId] = useState(null);
  const [newFacility, setNewFacility] = useState({ name: '', address: '', phone: '', description: '', benefits: '' });
  const [previewUrls, setPreviewUrls] = useState([]);
  const fileInputRef = useRef(null);

  const handleImageChange = (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    
    const remainingSlots = 5 - previewUrls.length;
    const filesToProcess = files.slice(0, remainingSlots);
    const newUrls = [];
    let loadedCount = 0;

    filesToProcess.forEach(file => {
      const reader = new FileReader();
      reader.onloadend = () => {
        newUrls.push(reader.result);
        loadedCount++;
        if (loadedCount === filesToProcess.length) {
          setPreviewUrls(prev => [...prev, ...newUrls]);
        }
      };
      reader.readAsDataURL(file);
    });
    
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeImage = (indexToRemove) => {
    setPreviewUrls(prev => prev.filter((_, idx) => idx !== indexToRemove));
  };

  const openAddModal = () => {
    setIsEditing(false);
    setNewFacility({ name: '', address: '', phone: '', description: '', benefits: '' });
    setPreviewUrls([]);
    setShowModal(true);
  };

  const openEditModal = (facility) => {
    setIsEditing(true);
    setCurrentId(facility.id);
    setNewFacility({ 
      name: facility.name || '', 
      address: facility.address || '', 
      phone: facility.phone || '',
      description: facility.description || '',
      benefits: facility.benefits || ''
    });
    setPreviewUrls(facility.images || []);
    setShowModal(true);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isEditing) {
      setFacilities(facilities.map(f => f.id === currentId ? { ...f, ...newFacility, images: previewUrls } : f));
    } else {
      setFacilities([...facilities, { ...newFacility, id: Date.now(), images: previewUrls, status: '영업중' }]);
    }
    setShowModal(false);
  };

  return (
    <div className="facilities-container">
      <div className="page-header-section" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ flex: '1 1 200px' }}>
          <h1 className="page-title">{t('facility.title', '시설 등록 관리')}</h1>
          <p className="sub-title">운영 중인 시설 정보를 등록하고 관리하세요.</p>
        </div>
        <button className="btn-modern btn-modern-primary" style={{ flexShrink: 0 }} onClick={handleAddFacility}>
          <Plus size={18} style={{ marginRight: '0.25rem' }} />
          {t('facility.btn_add_facility', '시설 추가')}
        </button>
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content card">
            <div className="modal-header">
              <h2>{isEditing ? '매장 수정' : '새 매장 등록'}</h2>
              <button className="close-btn-x" onClick={() => setShowModal(false)}><X size={20} /></button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="image-upload-section">
                <div className="image-preview-grid">
                  {previewUrls.map((url, idx) => (
                    <div key={idx} className="preview-thumb" style={{ backgroundImage: `url(${url})` }}>
                      <button type="button" className="remove-thumb-btn" onClick={(e) => { e.stopPropagation(); removeImage(idx); }}><X size={14} /></button>
                    </div>
                  ))}
                  {previewUrls.length < 5 && (
                    <div className="add-thumb-btn" onClick={() => fileInputRef.current.click()}>
                      <Camera size={24} />
                      <span>{previewUrls.length}/5</span>
                    </div>
                  )}
                </div>
                <input type="file" multiple ref={fileInputRef} onChange={handleImageChange} style={{ display: 'none' }} accept="image/*" />
              </div>
              <div className="form-group">
                <label className="form-label">매장명</label>
                <div className="form-content">
                  <input type="text" className="input-field" value={newFacility.name} onChange={e => setNewFacility({...newFacility, name: e.target.value})} required />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">매장 주소</label>
                <div className="form-content">
                  <input type="text" className="input-field" value={newFacility.address} onChange={e => setNewFacility({...newFacility, address: e.target.value})} required />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">전화번호</label>
                <div className="form-content">
                  <input type="text" className="input-field" value={newFacility.phone} onChange={e => setNewFacility({...newFacility, phone: e.target.value})} placeholder="예: 02-1234-5678" />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">매장 설명</label>
                <div className="form-content">
                  <textarea className="input-field" rows="4" value={newFacility.description} onChange={e => setNewFacility({...newFacility, description: e.target.value})} />
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-ghost" onClick={() => setShowModal(false)}>취소</button>
                <button type="submit" className="btn-primary">{isEditing ? '수정 완료' : '등록하기'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="facility-grid">
        {facilities.map(f => (
          <div key={f.id} className="facility-card card">
            {f.images && f.images.length > 0 && (
              <div className="facility-image" style={{ backgroundImage: `url(${f.images[0]})` }}>
                {f.images.length > 1 && <div className="image-count">1/{f.images.length}</div>}
              </div>
            )}
            <div className="facility-content">
              <div className="facility-info">
                <div className="facility-main"><h3 className="facility-name">{f.name}</h3><span className="status-badge">{f.status}</span></div>
                <p className="facility-address"><MapPin size={14} /> {f.address}</p>
                {f.phone && <p className="facility-meta">📞 {f.phone}</p>}
                {f.benefits && <p className="facility-meta highlight">🎁 {f.benefits}</p>}
              </div>
              <div className="facility-actions">
                <button className="icon-btn" onClick={() => openEditModal(f)}><Edit2 size={16} /></button>
                <button className="icon-btn delete" onClick={() => setFacilities(facilities.filter(x => x.id !== f.id))}><Trash2 size={16} /></button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Facilities;
