import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Camera, Save, X, Plus, Gift, ChevronRight } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import LocationService from '../services/map/LocationService';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
import './StoreInfo.css';
import { useNavigate } from 'react-router-dom';
import DaumPostcodeEmbed from 'react-daum-postcode';
import CategoryService from '../services/store/CategoryService';

// 커스텀 녹색 마커 (위치 핀 형태 SVG)
const customGreenMarker = L.divIcon({
  html: `<div style="display:flex; justify-content:center; align-items:flex-end; width:32px; height:32px;">
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="var(--primary)" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.3));">
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
      <circle cx="12" cy="10" r="3" fill="white"></circle>
    </svg>
  </div>`,
  className: 'custom-modern-marker',
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32]
});

// 좌표 변경 시 지도를 해당 위치로 부드럽게 이동시키는 컴포넌트
const RecenterAutomatically = ({lat, lng}) => {
  const map = useMap();
  useEffect(() => {
    map.flyTo([lat, lng], 15, { duration: 1.5 });
  }, [lat, lng, map]);
  return null;
};
const StoreInfo = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [store, setStore] = useState({
    name: '패스트파이브 강남점',
    address: '서울특별시 강남구 테헤란로 123',
    detailAddress: '',
    phone: '02-1234-5678',
    description: '크리에이티브 전문가와 고성장 스타트업을 위한 미니멀한 공유 오피스입니다.',
    images: [
      'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&q=80&w=1200',
      'https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&q=80&w=400',
    ],
    hours: { start: '09:00', end: '22:00' },
    holidays: { days: ['토요일', '일요일'], publicHolidays: true },
    categories: ['공유오피스'],
    lat: LocationService.getDefaultCoordinates().lat,
    lng: LocationService.getDefaultCoordinates().lng
  });

  const [categoriesDB, setCategoriesDB] = useState(CategoryService.getCategories());
  const WEEKDAYS = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'];
  const TIME_OPTIONS = Array.from({ length: 49 }, (_, i) => {
    const hours = Math.floor(i / 2).toString().padStart(2, '0');
    const minutes = i % 2 === 0 ? '00' : '30';
    return `${hours}:${minutes}`;
  });

  const [categorySearch, setCategorySearch] = useState('');
  const [showCategoryDropdown, setShowCategoryDropdown] = useState(false);
  const categoryInputRef = useRef(null);

  const [editData, setEditData] = useState({ ...store });
  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const fileInputRef = useRef(null);
  const [isAddressSearchOpen, setIsAddressSearchOpen] = useState(false);

  const handleAddressComplete = (data) => {
    let fullAddress = data.roadAddress || data.jibunAddress;
    let extraAddress = '';

    // 법정동명이 있을 경우 추가 (법정리는 제외)
    if (data.bname !== '' && /[동|로|가]$/g.test(data.bname)) {
      extraAddress += data.bname;
    }
    // 건물명이 있고, 공동주택일 경우 추가
    if (data.buildingName !== '') {
      extraAddress += (extraAddress !== '' ? ', ' + data.buildingName : data.buildingName);
    }
    // 표시할 참고항목이 있을 경우, 괄호까지 추가한 최종 문자열을 만든다.
    if (extraAddress !== '') {
      fullAddress += ` (${extraAddress})`;
    }

    setEditData({ ...editData, address: fullAddress });
    setIsAddressSearchOpen(false);
  };

  // DB 연동으로 자동 노출되는 혜택 (Mock Data)
  const dbBenefits = [
    "[혜택] 호텔H 숙박 스탬프 이벤트 진행",
    "[이벤트] 첫 방문 고객 10% 할인 쿠폰"
  ];

  const handleImageChange = (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    
    const newUrls = [];
    let loadedCount = 0;

    files.forEach(file => {
      const reader = new FileReader();
      reader.onloadend = () => {
        newUrls.push(reader.result);
        loadedCount++;
        if (loadedCount === files.length) {
          setEditData(prev => ({ ...prev, images: [...prev.images, ...newUrls].slice(0, 5) }));
        }
      };
      reader.readAsDataURL(file);
    });
    
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeImage = (index) => {
    setEditData(prev => {
      const newImages = prev.images.filter((_, i) => i !== index);
      let newActiveIndex = activeImageIndex;
      if (activeImageIndex === index) {
        newActiveIndex = 0;
      } else if (activeImageIndex > index) {
        newActiveIndex = activeImageIndex - 1;
      }
      setActiveImageIndex(newActiveIndex);
      return { ...prev, images: newImages };
    });
  };

  const handleEditStart = () => {
    setEditData({ ...store });
    setActiveImageIndex(0);
    setCategorySearch('');
    setIsEditing(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const addCategory = (cat) => {
    if (!editData.categories.includes(cat)) {
      setEditData({ ...editData, categories: [...editData.categories, cat] });
    }
    setCategorySearch('');
    setShowCategoryDropdown(false);
  };

  const removeCategory = (cat) => {
    setEditData({ ...editData, categories: editData.categories.filter(c => c !== cat) });
  };

  const toggleHoliday = (day) => {
    setEditData(prev => {
      const days = prev.holidays.days.includes(day) 
        ? prev.holidays.days.filter(d => d !== day)
        : [...prev.holidays.days, day];
      return { ...prev, holidays: { ...prev.holidays, days } };
    });
  };

  const handleSave = async () => {
    let newLat = editData.lat;
    let newLng = editData.lng;
    
    // 주소가 변경되었을 경우에만 Geocoding (LocationService 사용)
    if (editData.address !== store.address) {
      try {
        const coords = await LocationService.geocodeAddress(editData.address);
        if (coords) {
          newLat = coords.lat;
          newLng = coords.lng;
        }
      } catch (error) {
        console.error("Geocoding failed", error);
      }
    }
    
    const finalData = { ...editData, lat: newLat, lng: newLng };
    setStore(finalData);
    setEditData(finalData);
    setIsEditing(false);
    setActiveImageIndex(0);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const displayHours = `${store.hours.start} ~ ${store.hours.end}`;
  const displayHolidays = store.holidays.days.length > 0 
    ? `${store.holidays.days.join(', ')} 휴무${store.holidays.publicHolidays ? ' (공휴일 휴무)' : ''}`
    : (store.holidays.publicHolidays ? '공휴일 휴무' : '연중무휴');

  return (
    <div className="modern-store-page">
      <header className="page-header-section">
        <h1 className="page-title">{isEditing ? t('store.title_edit') : store.name}</h1>
        <p className="sub-title">{t('store.subtitle')}</p>
      </header>

      <section className="modern-gallery">
        <div className="gallery-main" style={{ backgroundImage: `url(${isEditing ? editData.images[activeImageIndex] || editData.images[0] : store.images[activeImageIndex] || store.images[0]})` }}>
          {isEditing && (
            <>
              {editData.images.length > 0 && (
                <button className="img-delete-btn" onClick={() => removeImage(activeImageIndex)}><X size={16} /></button>
              )}
              <div className="image-overlay" onClick={() => fileInputRef.current.click()}>
                <Camera size={32} />
                <span>{t('store.add_photo')}</span>
              </div>
            </>
          )}
        </div>
        <div className="gallery-thumbs-wrapper">
          <div className="gallery-thumbs">
          {(isEditing ? editData.images : store.images).map((img, i) => {
            if (i === activeImageIndex) return null;
            return (
              <div 
                key={i} 
                className="thumb" 
                style={{ backgroundImage: `url(${img})`, cursor: 'pointer' }}
                onClick={() => setActiveImageIndex(i)}
              >
                {isEditing && <button className="img-delete-btn" onClick={(e) => { e.stopPropagation(); removeImage(i); }}><X size={12} /></button>}
              </div>
            );
          })}
          {isEditing && editData.images.length < 5 && (
            <div className="thumb add-thumb" onClick={() => fileInputRef.current.click()}><Plus size={24} /></div>
          )}
          </div>
        </div>
        <input type="file" multiple ref={fileInputRef} onChange={handleImageChange} style={{ display: 'none' }} accept="image/*" />
      </section>

      <section className="modern-details">
        {/* 매장명 영역 (수정 모드일 때만 표시) */}
        {isEditing && (
          <div className="detail-item">
            <label>{t('store.label_name', '매장명')}</label>
            <input 
              className="input-modern" 
              value={editData.name} 
              onChange={e => setEditData({...editData, name: e.target.value})} 
              placeholder="매장명을 입력하세요" 
            />
          </div>
        )}

        {/* 매장 구분 (카테고리) 영역 */}
        <div className="detail-item">
          <label>{t('store.label_category')}</label>
          {isEditing ? (
            <div className="multi-select-container">
              {/* 상단 검색 영역 */}
              <div className="category-input-wrapper">
                <input 
                  ref={categoryInputRef}
                  className="category-search-input"
                  value={categorySearch}
                  onChange={e => {
                    setCategorySearch(e.target.value);
                    setShowCategoryDropdown(true);
                  }}
                  onFocus={() => setShowCategoryDropdown(true)}
                  onBlur={() => setTimeout(() => setShowCategoryDropdown(false), 200)}
                  placeholder={editData.categories.length === 0 ? t('store.placeholder_category_empty') : t('store.placeholder_category_search')}
                />
                {showCategoryDropdown && (
                  <div className="category-dropdown">
                    {(() => {
                      const keyword = categorySearch.trim();
                      const filtered = categoriesDB.filter(c => !editData.categories.includes(c) && c.toLowerCase().includes(keyword.toLowerCase()));
                      
                      return (
                        <>
                          {filtered.length > 0 ? (
                            filtered.map(cat => (
                              <div key={cat} className="category-option" onClick={() => addCategory(cat)}>
                                {cat}
                              </div>
                            ))
                          ) : (
                            <div className="category-option empty">{t('store.empty_category_result')}</div>
                          )}
                        </>
                      );
                    })()}
                  </div>
                )}
              </div>
              
              {/* 하단 선택된 카테고리(태그) 영역 */}
              {editData.categories.length > 0 && (
                <div className="selected-chips" style={{ marginTop: '1rem' }}>
                  {editData.categories.map(cat => (
                    <span key={cat} className="category-chip edit-mode">
                      {cat}
                      <button type="button" onClick={() => removeCategory(cat)}><X size={14} /></button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="selected-chips read-only">
              {store.categories.map(cat => (
                <span key={cat} className="category-chip read-mode">{cat}</span>
              ))}
            </div>
          )}
        </div>

        <div className="detail-row">
          <div className="detail-item" style={{ flex: '1 1 100%' }}>
            <label>{t('store.label_location')}</label>
            {isEditing ? (
              <div className="address-edit-container">
                <div className="address-search-group">
                  <input 
                    className="input-modern address-input-main" 
                    value={editData.address} 
                    onChange={e => setEditData({...editData, address: e.target.value})}
                    onKeyDown={e => { if(e.key === 'Enter') setIsAddressSearchOpen(true); }}
                    placeholder="지번, 도로명, 건물명으로 검색" 
                  />
                  <button type="button" className="btn-search-address" onClick={() => setIsAddressSearchOpen(true)}>주소 검색</button>
                </div>
                <input className="input-modern detail-address-input" value={editData.detailAddress} onChange={e => setEditData({...editData, detailAddress: e.target.value})} placeholder="상세 주소를 입력해주세요 (동/호수 등)" />
              </div>
            ) : (
              <div className="display-text">{store.address} {store.detailAddress}</div>
            )}
            
            {/* OpenStreetMap 지도 표시 영역 */}
            <div className="store-map-container" style={{ marginTop: '1.5rem', height: '300px', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--border)', position: 'relative', zIndex: 0 }}>
              <MapContainer 
                center={[store.lat, store.lng]} 
                zoom={15} 
                style={{ height: '100%', width: '100%' }} 
                scrollWheelZoom={false} 
                dragging={false} 
                touchZoom={false} 
                tap={false}
                doubleClickZoom={false}
                zoomControl={false}
                boxZoom={false}
                keyboard={false}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <Marker position={[store.lat, store.lng]} icon={customGreenMarker}>
                  <Popup>{store.name}</Popup>
                </Marker>
                <RecenterAutomatically lat={store.lat} lng={store.lng} />
              </MapContainer>
            </div>
          </div>
          <div className="detail-item">
            <label>{t('store.label_phone')}</label>
            {isEditing ? (
              <input className="input-modern" value={editData.phone} onChange={e => setEditData({...editData, phone: e.target.value})} placeholder="예: 02-1234-5678" />
            ) : (
              <div className="display-text">{store.phone}</div>
            )}
          </div>
        </div>

        <div className="detail-row">
          <div className="detail-item">
            <label>{t('store.label_hours')}</label>
            {isEditing ? (
              <div className="time-select-group">
                <select 
                  className="input-modern time-select" 
                  value={editData.hours.start} 
                  onChange={e => setEditData({...editData, hours: {...editData.hours, start: e.target.value}})}
                >
                  {TIME_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
                <span className="time-separator">~</span>
                <select 
                  className="input-modern time-select" 
                  value={editData.hours.end} 
                  onChange={e => setEditData({...editData, hours: {...editData.hours, end: e.target.value}})}
                >
                  {TIME_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            ) : (
              <div className="display-text">{displayHours}</div>
            )}
          </div>
          <div className="detail-item">
            <label>{t('store.label_holidays')}</label>
            {isEditing ? (
              <div className="holiday-selector">
                <div className="selected-chips">
                  {WEEKDAYS.map(day => (
                    <button 
                      key={day}
                      type="button"
                      className={`category-chip ${editData.holidays.days.includes(day) ? 'edit-mode' : 'read-mode'}`}
                      onClick={() => toggleHoliday(day)}
                    >
                      {day.replace('요일', '')}
                    </button>
                  ))}
                </div>
                <label className="checkbox-label" style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer', fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-main)' }}>
                  <input 
                    type="checkbox" 
                    className="custom-checkbox"
                    checked={editData.holidays.publicHolidays} 
                    onChange={e => setEditData({...editData, holidays: {...editData.holidays, publicHolidays: e.target.checked}})} 
                  />
                  공휴일 휴무
                </label>
              </div>
            ) : (
              <div className="display-text">{displayHolidays}</div>
            )}
          </div>
        </div>

        <div className="detail-item">
          <label>{t('store.label_description')}</label>
          {isEditing ? (
            <textarea className="input-modern" rows="4" value={editData.description} onChange={e => setEditData({...editData, description: e.target.value})} />
          ) : (
            <div className="display-text description">{store.description}</div>
          )}
        </div>

        {/* DB 연동으로 노출되는 혜택 영역 */}
        {!isEditing && (
          <div className="detail-item">
            <label>{t('store.label_benefits')}</label>
            <div className="benefits-list">
              {dbBenefits.length > 0 ? (
                dbBenefits.map((benefit, idx) => (
                  <div key={idx} className="benefit-card clickable" onClick={() => navigate(benefit.includes('스탬프') ? '/dashboard/stamps' : '/dashboard/coupons')}>
                    <span className="benefit-icon"><Gift size={18} strokeWidth={1.5} /></span>
                    <span className="benefit-text">{benefit}</span>
                    <ChevronRight size={16} className="benefit-arrow" color="#94A3B8" />
                  </div>
                ))
              ) : (
                <div className="empty-benefits">{t('store.empty_benefits')}</div>
              )}
            </div>
          </div>
        )}
      </section>

      <BottomActionBar>
        {!isEditing ? (
          <Button variant="primary" fullWidth onClick={handleEditStart}>{t('store.btn_edit')}</Button>
        ) : (
          <>
            <Button variant="outline" fullWidth onClick={() => { setIsEditing(false); window.scrollTo({ top: 0, behavior: 'smooth' }); }}>{t('store.btn_cancel')}</Button>
            <Button variant="primary" fullWidth onClick={handleSave}>{t('store.btn_save')}</Button>
          </>
        )}
      </BottomActionBar>

      {/* Address Search Modal */}
      {isAddressSearchOpen && (
        <div className="address-modal-overlay" onClick={() => setIsAddressSearchOpen(false)}>
          <div className="address-modal-content" onClick={e => e.stopPropagation()}>
            <div className="address-modal-header">
              <h3>주소 검색</h3>
              <button type="button" className="close-btn" onClick={() => setIsAddressSearchOpen(false)}><X size={24} /></button>
            </div>
            <DaumPostcodeEmbed 
              defaultQuery={editData.address.includes('서울특별시') ? '' : editData.address} 
              onComplete={handleAddressComplete} 
              style={{ height: '450px' }} 
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default StoreInfo;
