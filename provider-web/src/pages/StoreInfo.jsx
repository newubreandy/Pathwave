import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Camera, Save, X, Plus, Gift, ChevronRight, Utensils } from 'lucide-react';
import CardAvatar from '../components/common/CardAvatar';
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
import StoreService from '../services/store/StoreService';
import AuthService from '../services/auth/AuthService';
import ServiceRequestService from '../services/ServiceRequestService';

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
  const [errorMessage, setErrorMessage] = useState('');

  // 검증 메시지 표시 (모달)
  const showError = (msg) => {
    setIsSuccessMsg(false);
    setErrorMessage(msg);
  };
  // P5 (2026-05-26): mock 매장 정보 ('패스트파이브 강남점' / '02-1234-5678' /
  // unsplash 외부 이미지 등) 제거. 사장이 가입 후 직접 입력 또는 StoreService.get(fid)
  // 로 백엔드 fetch (Phase 2+ 실연동).
  const [store, setStore] = useState({
    name: '',
    address: '',
    detailAddress: '',
    phone: '',
    description: '',
    images: [],
    hours: { start: '09:00', end: '22:00' },
    holidays: { days: [], publicHolidays: false },
    categories: [],
    lat: LocationService.getDefaultCoordinates().lat,
    lng: LocationService.getDefaultCoordinates().lng
  });

  const [categoriesDB, setCategoriesDB] = useState(CategoryService.getCategories());

  // 백엔드 카테고리 fetch (D-polish: API 전환)
  useEffect(() => {
    let alive = true;
    CategoryService.load()
      .then(() => { if (alive) setCategoriesDB(CategoryService.getCategories()); })
      .catch(() => {
        // 폴백: 마지막 캐시 (또는 빈 배열) — 가입 흐름 깨지지 않게
        if (alive) setCategoriesDB(CategoryService.getCategories());
      });
    return () => { alive = false; };
  }, []);

  // ── 비콘 (읽기 전용) ──
  // 정책(2026-05-29): 비콘 할당은 슈퍼어드민 주도. 운영자가 신청 매장에 비콘을
  // 배정 + 설치위치를 지정해 라벨을 붙여 발송한다. 점주는 배정된 비콘을 '확인'만
  // 한다 (시리얼 self-claim 제거). → 본 화면은 내 매장 비콘 목록 read-only.
  const [facilityId, setFacilityId] = useState(null);   // 내 매장 ID (facility/me)
  const [beacons, setBeacons] = useState([]);
  const [requests, setRequests] = useState([]);          // P-D: 내 서비스 신청 상태

  // 비콘 목록 fetch. apiClient 는 본문을 그대로 반환하므로 res.beacons 사용.
  const fetchBeacons = async (fid) => {
    if (!fid) return;
    try {
      const res = await StoreService.listBeacons(fid);
      setBeacons(res?.beacons ?? []);
    } catch {
      // 목록 조회 실패는 조용히 무시 (빈 목록 유지)
    }
  };

  // P-D: 내 서비스 신청 목록 (상태 추적 — 발송/설치완료)
  const fetchRequests = async () => {
    try {
      const res = await ServiceRequestService.list();
      setRequests(res?.requests ?? []);
    } catch { /* noop */ }
  };

  const handleMarkInstalled = async (rid) => {
    try {
      await ServiceRequestService.markInstalled(rid);
      fetchRequests();
      if (facilityId) fetchBeacons(facilityId);
    } catch { /* noop */ }
  };

  // 마운트 시 내 매장 ID 확보 → 비콘 목록 + 신청 상태 로드. (1계정=1매장)
  useEffect(() => {
    let alive = true;
    AuthService.me()
      .then((res) => {
        const fid = res?.facility_account?.facility_id ?? null;
        if (!alive) return;
        setFacilityId(fid);
        if (fid) {
          fetchBeacons(fid);
          // 2026-06-11 — 매장 정보 실연동: 백엔드 값으로 화면 채움 (저장된 휴무/혜택 포함).
          StoreService.get(fid)
            .then((r) => { if (alive && r?.facility) hydrateFromApi(r.facility); })
            .catch(() => { /* 신규 매장 등 — 빈 폼 유지 */ });
        }
        fetchRequests();
      })
      .catch(() => { /* 미가입/오류 시 비콘 섹션 비활성 */ });
    return () => { alive = false; };
  }, []);

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

  // 2026-06-11 — 진행중 혜택: facilities.benefits JSON 컬럼 실연동 (mobile 매장 상세와 동일 소스).
  const [dbBenefits, setDbBenefits] = useState([]);
  // 저장 진행 가드 (연타 방지) + 성공 피드백 모달 분기.
  const [saving, setSaving] = useState(false);
  const [isSuccessMsg, setIsSuccessMsg] = useState(false);

  /// backend facility 응답 → 화면 state 매핑.
  /// holidays JSON ["매주 월요일", "공휴일"] ↔ UI {days:['월요일'], publicHolidays}
  const hydrateFromApi = (f) => {
    const [hs, he] = (f.business_hours || '09:00-22:00').split('-');
    const rawHol = Array.isArray(f.holidays) ? f.holidays : [];
    const days = rawHol
      .filter((s) => typeof s === 'string' && s.startsWith('매주 '))
      .map((s) => s.replace('매주 ', ''));
    const publicHolidays = rawHol.includes('공휴일');
    const next = {
      name: f.name || '',
      address: f.address || '',
      detailAddress: '',
      phone: f.phone || '',
      description: f.description || '',
      images: f.image_url ? [f.image_url] : [],
      hours: { start: (hs || '09:00').trim(), end: (he || '22:00').trim() },
      holidays: { days, publicHolidays },
      categories: [],
      lat: f.latitude ?? LocationService.getDefaultCoordinates().lat,
      lng: f.longitude ?? LocationService.getDefaultCoordinates().lng,
    };
    setStore(next);
    setEditData(next);
    setDbBenefits(Array.isArray(f.benefits) ? f.benefits : []);
  };

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
    if (editData.categories.includes(cat)) {
      setCategorySearch('');
      setShowCategoryDropdown(false);
      return;
    }
    if (editData.categories.length >= 3) {
      showError('업종은 최대 3개까지 선택할 수 있습니다.');
      return;
    }
    setEditData({ ...editData, categories: [...editData.categories, cat] });
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

  // ── 입력 검증 (필수값) ──
  const validateBeforeSave = () => {
    // 0. 매장 사진 (1장 이상)
    if (!editData.images || editData.images.length === 0) {
      return '매장 사진을 1장 이상 등록해주세요.';
    }

    // 1. 매장명 (1자 이상)
    if (!(editData.name || '').trim()) {
      return '매장명을 입력해주세요.';
    }

    // 2. 업종 (1~3개)
    if (!editData.categories || editData.categories.length === 0) {
      return '업종을 1개 이상 선택해주세요.';
    }
    if (editData.categories.length > 3) {
      return '업종은 최대 3개까지 선택할 수 있습니다.';
    }

    // 3. 위치(주소) 필수
    if (!(editData.address || '').trim()) {
      return '매장 주소를 입력해주세요.';
    }

    // 4. 전화번호: 숫자/하이픈만, 최소 8자리 숫자
    const phoneClean = (editData.phone || '').replace(/[^0-9]/g, '');
    if (phoneClean.length < 8) {
      return '전화번호를 정확히 입력해주세요. (숫자와 - 만 입력 가능)';
    }

    // 5. 영업시간: 시작 < 종료
    const { start, end } = editData.hours;
    if (!start || !end) {
      return '영업시간을 설정해주세요.';
    }
    if (start === end) {
      return '영업 시작 시간과 종료 시간이 같을 수 없습니다.';
    }
    if (start >= end) {
      return '영업 시작 시간은 종료 시간보다 빨라야 합니다.';
    }

    // 6. 정기휴무: 주 운영일 ≥ 3일 (= 휴무 ≤ 4일)
    const operatingDays = 7 - editData.holidays.days.length;
    if (operatingDays < 3) {
      return '주 3일 이상 운영하는 매장만 등록할 수 있습니다. 휴무 요일을 4일 이하로 선택해주세요.';
    }

    // 7. 매장 소개: 최소 10자
    const desc = (editData.description || '').trim();
    if (desc.length < 10) {
      return '매장 소개는 최소 10자 이상 입력해주세요.';
    }

    return null;
  };

  const handleSave = async () => {
    const errorMsg = validateBeforeSave();
    if (errorMsg) {
      showError(errorMsg);
      return;
    }
    setErrorMessage('');

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

    // 2026-06-11 — 실저장: 로컬 state 만 갱신하던 버그 수정 (DB 미반영 → 사용자앱 미반영이던 문제).
    if (!facilityId) {
      showError('매장 정보가 아직 등록되지 않았습니다. 가입 승인 후 다시 시도해 주세요.');
      return;
    }
    const payload = {
      name: finalData.name,
      address: [finalData.address, finalData.detailAddress].filter(Boolean).join(' ').trim(),
      phone: finalData.phone,
      description: finalData.description,
      business_hours: `${finalData.hours.start}-${finalData.hours.end}`,
      latitude: newLat,
      longitude: newLng,
      image_url: finalData.images[0] || null,
      // UI {days, publicHolidays} → JSON 배열 (mobile 매장 상세 표기 형식과 동일)
      holidays: [
        ...finalData.holidays.days.map((d) => `매주 ${d}`),
        ...(finalData.holidays.publicHolidays ? ['공휴일'] : []),
      ],
    };
    setSaving(true);
    try {
      await StoreService.update(facilityId, payload);
      setStore(finalData);
      setEditData(finalData);
      setIsEditing(false);
      setActiveImageIndex(0);
      setIsSuccessMsg(true);
      setErrorMessage('매장 정보가 저장되었습니다. 사용자 앱에 바로 반영됩니다.');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (e) {
      showError(e?.message || '저장에 실패했습니다. 잠시 후 다시 시도해 주세요.');
    } finally {
      setSaving(false);
    }
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

      {/* 검증 오류 모달 — 확인 버튼으로 닫기 */}
      {errorMessage && (
        <div className="validation-modal-overlay" role="alertdialog" onClick={() => setErrorMessage('')}>
          <div className="validation-modal" onClick={(e) => e.stopPropagation()}>
            <div className="validation-modal-icon">{isSuccessMsg ? '✅' : '⚠️'}</div>
            <p className="validation-modal-text">{errorMessage}</p>
            <button className="validation-modal-confirm" onClick={() => setErrorMessage('')} autoFocus>
              확인
            </button>
          </div>
        </div>
      )}

      <section className="modern-gallery">
        <div className="gallery-main" style={{ backgroundImage: `url(${isEditing ? editData.images[activeImageIndex] || editData.images[0] : store.images[activeImageIndex] || store.images[0]})` }}>
          {isEditing && (
            <>
              {editData.images.length > 0 && (
                <button className="img-delete-btn" onClick={() => removeImage(activeImageIndex)} aria-label="이미지 삭제"><X size={16} aria-hidden="true" /></button>
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
              <p className="field-hint">최대 3개까지 선택할 수 있습니다. ({editData.categories.length}/3)</p>
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
              <>
                <input
                  className="input-modern"
                  type="tel"
                  inputMode="tel"
                  value={editData.phone}
                  onChange={e => {
                    // 숫자와 하이픈(-) 만 허용
                    const filtered = e.target.value.replace(/[^0-9-]/g, '');
                    setEditData({ ...editData, phone: filtered });
                  }}
                  placeholder="예: 02-1234-5678"
                />
                <p className="field-hint">숫자와 하이픈(-) 만 입력할 수 있습니다.</p>
              </>
            ) : (
              <div className="display-text">{store.phone}</div>
            )}
          </div>
        </div>

        {/* ── 메뉴 (2026-06-09: mobile 매장 상세와 노출 통일, 별도 페이지로 이동) ── */}
        {!isEditing && (
          <div className="detail-item">
            <label>메뉴</label>
            <div className="benefits-list">
              <div className="benefit-card clickable" onClick={() => navigate('/dashboard/menu')}>
                <CardAvatar variant="accent" size="sm">
                  <Utensils strokeWidth={2} />
                </CardAvatar>
                <span className="benefit-text">메뉴 관리 (등록·수정·번역)</span>
                <ChevronRight size={16} className="benefit-arrow" />
              </div>
            </div>
          </div>
        )}

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
            <>
              <textarea
                className="input-modern"
                rows="4"
                value={editData.description}
                onChange={e => setEditData({ ...editData, description: e.target.value })}
                placeholder="매장의 특징을 10자 이상 입력해주세요."
              />
              <p className={`field-hint ${(editData.description || '').trim().length < 10 ? 'warn' : ''}`}>
                {(editData.description || '').trim().length < 10
                  ? `최소 10자 이상 (현재 ${(editData.description || '').trim().length}자)`
                  : `${(editData.description || '').trim().length}자 입력됨`}
              </p>
            </>
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
                dbBenefits.map((b, idx) => (
                  <div key={idx} className="benefit-card clickable" onClick={() => navigate(b.kind === 'stamp' ? '/dashboard/stamps' : '/dashboard/coupons')}>
                    <CardAvatar variant="accent" size="sm">
                      <Gift strokeWidth={2} />
                    </CardAvatar>
                    <span className="benefit-text">{b.title || String(b)}</span>
                    <ChevronRight size={16} className="benefit-arrow" />
                  </div>
                ))
              ) : (
                <div className="empty-benefits">{t('store.empty_benefits')}</div>
              )}
            </div>
          </div>
        )}
        {/* 2026-06-09 — 비콘 섹션 제거 (정책: 매장관리에 비콘 노출 X, 운영자가 별도 발송). */}
      </section>

      <BottomActionBar>
        {!isEditing ? (
          <Button variant="primary" fullWidth onClick={handleEditStart}>{t('store.btn_edit')}</Button>
        ) : (
          <>
            <Button variant="outline" fullWidth onClick={() => { setIsEditing(false); window.scrollTo({ top: 0, behavior: 'smooth' }); }}>{t('store.btn_cancel')}</Button>
            <Button variant="primary" fullWidth onClick={handleSave} disabled={saving}>{saving ? '저장 중…' : t('store.btn_save')}</Button>
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
