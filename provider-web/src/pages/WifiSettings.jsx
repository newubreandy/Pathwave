import React, { useState, useRef } from 'react';
import { Camera, Plus, X, ChevronLeft, ChevronRight, Trash2, Edit3, Search, Image as ImageIcon } from 'lucide-react';
import WifiService from '../services/wifi/WifiService';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
import ConfirmModal from '../components/common/ConfirmModal';
import './WifiSettings.css';

const MOCK_PROFILES = [
  { id: 1, name: '로비정문1', ssid: 'kt5G_1234789', password: 'Ezddd1@3356', date: '2022.03.15', image: null },
  { id: 2, name: '수영장',     ssid: 'kt5G_pool01',  password: 'Ezddd1@3356', date: '2022.03.10', image: null },
  { id: 3, name: '1층카페',    ssid: 'kt5G_cafe01',  password: 'Ezddd1@3356', date: '2022.02.28', image: null },
  { id: 4, name: '2층뷔페',    ssid: 'kt5G_buffet',  password: 'Ezddd1@3356', date: '2022.02.20', image: null },
  { id: 5, name: '5001호',     ssid: 'kt5G_5001',    password: 'Ezddd1@3356', date: '2022.01.15', image: null },
];

const WifiSettings = () => {
  const [profiles, setProfiles] = useState(MOCK_PROFILES);
  const [view, setView] = useState('list'); // 'list' | 'search' | 'detail' | 'add'
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [swipedId, setSwipedId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedChips, setSelectedChips] = useState(new Set());
  const [activeFilter, setActiveFilter] = useState(null); // filtered name after search
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const [formData, setFormData] = useState({
    name: '', ssid: '', password: '', image: null
  });
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  const fileInputRef = useRef(null);
  const touchStartX = useRef(0);
  const touchCurrentX = useRef(0);

  // ── List Actions ──
  const openDetail = (profile) => {
    setSelectedProfile(profile);
    setFormData({ name: profile.name, ssid: profile.ssid, password: profile.password, image: profile.image });
    setPreviewUrl(profile.image);
    setIsEditing(false);
    setView('detail');
  };

  const openAdd = () => {
    setFormData({ name: '', ssid: '', password: '', image: null });
    setPreviewUrl(null);
    setIsEditing(true);
    setSelectedProfile(null);
    setView('add');
  };

  const handleDelete = (id) => {
    setProfiles(prev => prev.filter(p => p.id !== id));
    setSwipedId(null);
    setDeleteConfirm(null);
    if (view !== 'list') setView('list');
  };

  const handleSave = () => {
    if (view === 'add') {
      const newProfile = {
        id: Date.now(),
        name: formData.name,
        ssid: formData.ssid,
        password: formData.password,
        date: new Date().toISOString().slice(0, 10).replace(/-/g, '.'),
        image: previewUrl
      };
      setProfiles(prev => [...prev, newProfile]);
    } else if (selectedProfile) {
      setProfiles(prev => prev.map(p =>
        p.id === selectedProfile.id
          ? { ...p, name: formData.name, ssid: formData.ssid, password: formData.password, image: previewUrl }
          : p
      ));
    }
    setView('list');
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const removeImage = () => {
    setPreviewUrl(null);
    setFormData(prev => ({ ...prev, image: null }));
  };

  // ── Touch swipe for list items ──
  const handleTouchStart = (e, id) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = (e, id) => {
    const diff = touchStartX.current - e.changedTouches[0].clientX;
    if (diff > 60) {
      setSwipedId(id);
    } else if (diff < -60) {
      setSwipedId(null);
    }
  };

  // ── Search Actions ──
  const openSearch = () => {
    setSearchQuery('');
    setSelectedChips(new Set());
    setView('search');
  };

  const toggleChip = (name) => {
    setSelectedChips(prev => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const confirmSearch = () => {
    if (selectedChips.size > 0) {
      setActiveFilter([...selectedChips]);
    } else {
      setActiveFilter(null);
    }
    setView('list');
  };

  const clearFilter = () => {
    setActiveFilter(null);
    setSearchQuery('');
    setSelectedChips(new Set());
  };

  // ── Filter ──
  const searchFiltered = profiles.filter(p =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.ssid.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const displayProfiles = activeFilter
    ? profiles.filter(p => activeFilter.includes(p.name))
    : profiles;

  // ═════════════════════════════════════
  // SEARCH VIEW — Figma "와이파이 검색"
  // ═════════════════════════════════════
  if (view === 'search') {
    return (
      <div className="wifi-search-page">
        <h1 className="wifi-search-title">와이파이 검색</h1>

        <div className="wifi-search-field">
          <label className="wifi-field-label">Search</label>
          <div className="wifi-search-input-wrap">
            <Search size={20} className="wifi-search-icon" />
            <input
              type="text"
              className="wifi-field-input"
              placeholder="찾고자 하는 와이파이 이름을 입력하세요"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              autoFocus
            />
          </div>
          <span className="wifi-field-hint">예) 로비, 정문1, 1234호, 카페앞문, 뒷문</span>
        </div>

        {/* Chip Results */}
        {searchQuery && (
          <div className="wifi-chip-grid">
            {searchFiltered.map(p => (
              <button
                key={p.id}
                className={`wifi-chip ${selectedChips.has(p.name) ? 'selected' : ''}`}
                onClick={() => toggleChip(p.name)}
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="wifi-chip-check">
                  <path d="M3.5 8L6.5 11L12.5 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                {p.name}
              </button>
            ))}
          </div>
        )}

        <BottomActionBar>
          <Button variant="primary" fullWidth onClick={confirmSearch}
            style={{ background: 'var(--pw-gray-900)', borderColor: 'var(--pw-gray-900)' }}>
            검색
          </Button>
        </BottomActionBar>
      </div>
    );
  }

  // ═════════════════════════════════════
  // LIST VIEW — Figma "서비스관리"
  // ═════════════════════════════════════
  if (view === 'list') {
    return (
      <div className="wifi-page">
        <div className="page-header-section" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ flex: '1 1 200px' }}>
            <h1 className="page-title">와이파이관리</h1>
            <p className="sub-title">wifi 서비스 이용내역</p>
          </div>
        </div>

        {/* Count + Search */}
        <div className="wifi-list-meta">
          <span className="wifi-count">{displayProfiles.length}개의 서비스이용중 입니다.</span>
          <button className="wifi-search-btn" onClick={openSearch}>
            <Search size={16} />
            검색
          </button>
        </div>

        {/* Active filter indicator */}
        {activeFilter && (
          <div className="wifi-active-filter">
            <div className="wifi-filter-chips">
              {activeFilter.map(name => (
                <span key={name} className="wifi-filter-chip">{name}</span>
              ))}
            </div>
            <button className="wifi-clear-filter" onClick={clearFilter}>
              <X size={14} /> 필터 해제
            </button>
          </div>
        )}

        {/* WiFi List */}
        <div className="wifi-list">
          {displayProfiles.map(p => (
            <div
              key={p.id}
              className={`wifi-list-item ${swipedId === p.id ? 'swiped' : ''}`}
              onTouchStart={(e) => handleTouchStart(e, p.id)}
              onTouchEnd={(e) => handleTouchEnd(e, p.id)}
            >
              <div className="wifi-item-content" onClick={() => openDetail(p)}>
                <div className="wifi-item-row">
                  <span className="wifi-item-label">Name</span>
                  <span className="wifi-item-name">{p.name}</span>
                </div>
                {p.date && (
                  <div className="wifi-item-row">
                    <span className="wifi-item-label">최근 업데이트</span>
                    <span className="wifi-item-sub">{p.date}</span>
                  </div>
                )}
                <ChevronRight size={18} className="wifi-item-arrow" />
              </div>

              {/* Swipe actions */}
              <div className="wifi-swipe-actions">
                <button className="swipe-btn delete" onClick={() => setDeleteConfirm(p.id)}>
                  <Trash2 size={20} />
                </button>
                <button className="swipe-btn edit" onClick={() => { openDetail(p); setIsEditing(true); }}>
                  <Edit3 size={20} />
                </button>
              </div>
            </div>
          ))}
        </div>

        <BottomActionBar>
          <Button variant="primary" fullWidth icon={<Plus size={18} />} onClick={openAdd}
            style={{ background: 'var(--pw-gray-900)', borderColor: 'var(--pw-gray-900)' }}>
            추가
          </Button>
        </BottomActionBar>

        {deleteConfirm && (
          <ConfirmModal
            title="와이파이 삭제"
            description="이 와이파이 정보를 삭제하시겠습니까?"
            onConfirm={() => handleDelete(deleteConfirm)}
            onCancel={() => setDeleteConfirm(null)}
          />
        )}
      </div>
    );
  }

  // ═════════════════════════════════════
  // DETAIL / ADD VIEW — Figma "와이파이 상세" / "와이파이 추가"
  // ═════════════════════════════════════
  const isAddMode = view === 'add';
  const canEdit = isEditing || isAddMode;
  const title = isAddMode ? '와이파이 추가' : '와이파이 상세';

  return (
    <div className="common-form-page">
      {/* Header */}
      <header className="common-form-header">
        <button className="back-btn" onClick={() => setView('list')}>
          <ChevronLeft size={24} />
        </button>
        <h1>{title}</h1>
      </header>

      <div className="wifi-detail-body">
        {/* Name */}
        <div className="wifi-field-group">
          <label className="wifi-field-label">Name</label>
          <input
            type="text"
            className="wifi-field-input"
            placeholder="설정하고자 하는 와이파이 위치를 입력하세요"
            value={formData.name}
            onChange={e => setFormData({ ...formData, name: e.target.value })}
            disabled={!canEdit}
          />
          <div className="wifi-field-meta">
            <span className="wifi-field-hint">예) 로비, 정문1, 1234호, 카페앞문, 뒷문</span>
            {selectedProfile && <span className="wifi-field-date">등록일 {selectedProfile.date}</span>}
          </div>
        </div>

        {/* Photo Area */}
        <div className="wifi-photo-area">
          {previewUrl ? (
            <div className="wifi-photo-preview">
              <img src={previewUrl} alt="공유기 사진" />
              {canEdit && (
                <button className="wifi-photo-remove" onClick={removeImage}>
                  <X size={16} />
                </button>
              )}
            </div>
          ) : (
            <div className="wifi-photo-placeholder">
              {canEdit ? (
                <>
                  <div className="wifi-photo-icon">
                    <Camera size={28} color="var(--pw-primary)" />
                  </div>
                  <p className="wifi-photo-title">공유기 뒷면의 와이파이정보를 촬영하세요!</p>
                  <p className="wifi-photo-desc">※ 직접입력하기 어려우실 경우 공유기 뒷면의 와이파이 정보를 촬영하시면 입력을 도와드립니다!</p>
                </>
              ) : (
                <>
                  <p className="wifi-photo-title" style={{ color: 'var(--pw-text-hint)' }}>와이파이 정보 등록/수정 시 사진을 이용해</p>
                  <p className="wifi-photo-title" style={{ color: 'var(--pw-text-hint)' }}>보다 쉽게 정보를 입력할 수 있습니다.</p>
                </>
              )}
            </div>
          )}

          {canEdit && (
            <button className="wifi-photo-remove-corner" onClick={removeImage} style={{ display: previewUrl ? 'flex' : 'none' }}>
              <X size={14} />
            </button>
          )}
        </div>

        {/* Photo actions */}
        {canEdit && (
          <div className="wifi-photo-actions">
            <button className="wifi-photo-action" onClick={() => fileInputRef.current?.click()}>
              <ImageIcon size={14} /> 앨범에서 선택
            </button>
            <button className="wifi-photo-action" onClick={() => fileInputRef.current?.click()}>
              <Camera size={14} /> 카메라 촬영
            </button>
            <input type="file" ref={fileInputRef} accept="image/*" onChange={handleImageChange} style={{ display: 'none' }} />
          </div>
        )}

        {!canEdit && (
          <div className="wifi-photo-actions">
            <button className="wifi-photo-action" disabled>앨범에서 선택</button>
            <button className="wifi-photo-action" disabled>카메라 촬영</button>
          </div>
        )}

        {/* ID */}
        <div className="wifi-field-group">
          <label className="wifi-field-label">ID</label>
          <input
            type="text"
            className="wifi-field-input"
            placeholder="해당와이파이의 ID를 입력해 주세요"
            value={formData.ssid}
            onChange={e => setFormData({ ...formData, ssid: e.target.value })}
            disabled={!canEdit}
          />
          <span className="wifi-field-hint">예) kt5g_1234789</span>
        </div>

        {/* PW */}
        <div className="wifi-field-group">
          <label className="wifi-field-label">PW</label>
          <input
            type="text"
            className="wifi-field-input"
            placeholder="해당와이파이의 비밀번호를 입력해 주세요"
            value={formData.password}
            onChange={e => setFormData({ ...formData, password: e.target.value })}
            disabled={!canEdit}
          />
          <span className="wifi-field-hint">예) ezddd1@3356</span>
        </div>

        {/* Notes */}
        <div className="wifi-notes">
          <p>※ 와이파이 정보는 자동으로 업데이트 되지 않습니다. 와이파이 공유기의 비밀번호 업데이트 시 해당정보를 같이 업데이트해 주셔야 서비스이용이 가능합니다.</p>
          <p>※ 통신사 공유기에 다른 공유기를 이용할 경우 해당공유기의 정보를 입력해 주셔야 합니다.</p>
        </div>
      </div>

      {/* Bottom Actions */}
      <BottomActionBar>
        {isAddMode ? (
          <>
            <Button variant="outline" fullWidth onClick={() => setView('list')}>취소</Button>
            <Button variant="primary" fullWidth onClick={handleSave}>
              저장
            </Button>
          </>
        ) : canEdit ? (
          <>
            <Button variant="outline" fullWidth onClick={() => setIsEditing(false)}>취소</Button>
            <Button variant="primary" fullWidth onClick={handleSave}>
              수정
            </Button>
          </>
        ) : (
          <>
            <Button variant="outline" fullWidth onClick={() => setDeleteConfirm(selectedProfile?.id)}>삭제</Button>
            <Button variant="primary" fullWidth onClick={() => setIsEditing(true)}>
              수정
            </Button>
          </>
        )}
      </BottomActionBar>

      {deleteConfirm && (
        <ConfirmModal
          title="와이파이 삭제"
          description="이 와이파이 정보를 삭제하시겠습니까?"
          onConfirm={() => handleDelete(deleteConfirm)}
          onCancel={() => setDeleteConfirm(null)}
        />
      )}
    </div>
  );
};

export default WifiSettings;
