import React, { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Camera, Plus, X, ChevronLeft, ChevronRight, Trash2, Edit3, Search, Image as ImageIcon, Loader2 } from 'lucide-react';
import WifiService from '../services/wifi/WifiService';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
import ConfirmModal from '../components/common/ConfirmModal';
import './WifiSettings.css';

const MOCK_PROFILES = [
  { id: 1, name: '로비정문1', message: 'Message', ssid: 'kt5G_1234789', password: 'Ezddd1@3356', date: '2022.03.15', image: null, status: 'ok', battery: 90, enabled: true },
  { id: 2, name: '수영장',   message: 'Message', ssid: 'kt5G_pool01',   password: 'Ezddd1@3356', date: '2022.03.10', image: null, status: 'ok', battery: 76, enabled: true },
  { id: 3, name: '1층카페',   message: 'Message', ssid: 'kt5G_cafe01',   password: 'Ezddd1@3356', date: '2022.02.28', image: null, status: 'low', battery: 22, enabled: true },
  { id: 4, name: '2층뷔페',   message: 'Message', ssid: 'kt5G_buffet',   password: 'Ezddd1@3356', date: '2022.02.20', image: null, status: 'ok', battery: 64, enabled: false },
  { id: 5, name: '5001호',   message: 'Message', ssid: 'kt5G_5001',     password: 'Ezddd1@3356', date: '2022.01.15', image: null, status: 'offline', battery: 0, enabled: true },
];

// 상태 라벨 + 색상
const STATUS_LABEL = {
  ok: '정상',
  low: '배터리 부족',
  offline: '연결 끊김',
};

const WifiSettings = () => {
  const location = useLocation();
  const [profiles, setProfiles] = useState(MOCK_PROFILES);
  const [view, setView] = useState('list'); // 'list' | 'search' | 'detail' | 'add'
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [swipedId, setSwipedId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedChips, setSelectedChips] = useState(new Set());
  const [activeFilter, setActiveFilter] = useState(null); // filtered name after search
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [saveConfirmMsg, setSaveConfirmMsg] = useState(null); // 저장 시 안내 (ID/PW + enabled)
  const [errorMsg, setErrorMsg] = useState(null);             // 검증 실패 모달
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrDone, setOcrDone] = useState(false);

  const [formData, setFormData] = useState({
    name: '', ssid: '', password: '', image: null
  });
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  const touchStartX = useRef(0);
  const touchCurrentX = useRef(0);

  // GNB 의 "와이파이" 메뉴를 다시 탭하면 리스트로 복귀 (location.key 변경 감지)
  useEffect(() => {
    setView('list');
    setSelectedProfile(null);
    setIsEditing(false);
    setSaveConfirmMsg(null);
    setErrorMsg(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.key]);

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

  // 저장 입력 검증 (필수값)
  const validateWifi = () => {
    if (!(formData.name || '').trim()) return 'Name(와이파이 위치)을 입력해주세요.';
    if (!(formData.ssid || '').trim()) return 'ID(SSID)는 필수 입력입니다.';
    if (!(formData.password || '').trim()) return 'PW(비밀번호)는 필수 입력입니다.';
    return null;
  };

  // 저장 클릭 → 검증 → 안내 모달
  const handleSave = () => {
    const err = validateWifi();
    if (err) {
      setErrorMsg(err);
      return;
    }
    // 추가 모드는 안내 없이 바로 저장
    if (view === 'add') {
      doSave();
      return;
    }
    // 수정 모드: 비사용 + ID/PW 통신사 안내 통합
    const messages = [];
    if (selectedProfile && selectedProfile.enabled === false) {
      messages.push('와이파이를 비사용 상태로 저장합니다. 저장 후 매장 와이파이 서비스가 중단됩니다.');
    }
    messages.push('와이파이 정보는 통신사에서 제공한 아이디 / 비밀번호입니다. 통신사에서 제공한 정보와 다를 시 서비스가 되지 않습니다.');
    messages.push('저장하시겠어요?');
    setSaveConfirmMsg(messages.join('\n\n'));
  };

  // 안내 모달 확인 시 실제 저장
  const doSave = () => {
    if (view === 'add') {
      const newProfile = {
        id: Date.now(),
        name: formData.name,
        message: 'Message',
        ssid: formData.ssid,
        password: formData.password,
        date: new Date().toISOString().slice(0, 10).replace(/-/g, '.'),
        image: previewUrl,
        status: 'ok',
        battery: 100,
        enabled: true,
      };
      setProfiles(prev => [...prev, newProfile]);
    } else if (selectedProfile) {
      setProfiles(prev => prev.map(p =>
        p.id === selectedProfile.id
          ? {
              ...p,
              name: formData.name,
              ssid: formData.ssid,
              password: formData.password,
              image: previewUrl,
              enabled: selectedProfile.enabled,
            }
          : p
      ));
    }
    setSaveConfirmMsg(null);
    setView('list');
  };

  // ── 사진 선택 + OCR (자동 ID/PW 추출) ──
  // TODO: 실제 OCR 연동 (백엔드 API 또는 Tesseract.js). 현재는 1초 후 mock 결과 자동 입력
  const runOcrMock = async (imageUrl) => {
    console.log('[OCR mock] start', imageUrl);
    setOcrLoading(true);
    await new Promise((r) => setTimeout(r, 1000));
    const mockResult = {
      ssid: 'kt5G_AUTO' + Math.floor(Math.random() * 9000 + 1000),
      password: 'Ezddd1@' + Math.floor(Math.random() * 9000 + 1000),
    };
    console.log('[OCR mock] result', mockResult);
    // 함수형 업데이트로 stale state 방지
    setFormData((prev) => ({ ...prev, ssid: mockResult.ssid, password: mockResult.password }));
    setOcrLoading(false);
    setOcrDone(true);
    setTimeout(() => setOcrDone(false), 2500);
  };

  const handleImageChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    // 같은 파일 재선택 가능하도록 reset (OCR 시작 전에 처리)
    const inputEl = e.target;
    setTimeout(() => { if (inputEl) inputEl.value = ''; }, 0);
    // 사진 선택 시 자동 OCR 실행
    await runOcrMock(url);
  };

  const removeImage = () => {
    setPreviewUrl(null);
    setFormData(prev => ({ ...prev, image: null }));
  };

  // ── 토글 (활성/비활성) ──
  const toggleEnabled = (id, e) => {
    if (e) e.stopPropagation();
    setProfiles((prev) => prev.map((p) => (p.id === id ? { ...p, enabled: !p.enabled } : p)));
    if (selectedProfile && selectedProfile.id === id) {
      setSelectedProfile((prev) => ({ ...prev, enabled: !prev.enabled }));
    }
  };

  // ── 수정 진입 — 안내 모달 없이 바로 수정 모드 (안내는 저장 시점) ──
  const startEdit = () => {
    setIsEditing(true);
    // 화면 위로 스크롤 — 사용자가 모드 전환을 인지할 수 있도록
    window.scrollTo({ top: 0, behavior: 'smooth' });
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
          <Button variant="primary" fullWidth onClick={confirmSearch}>
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
              <div className={`wifi-item-content ${!p.enabled ? 'is-disabled' : ''}`} onClick={() => openDetail(p)}>
                {/* 이름 (좌) */}
                <div className="wifi-item-name-block">
                  <span className="wifi-item-label">Name</span>
                  <span className="wifi-item-name">{p.name}</span>
                </div>

                {/* 상태 + 배터리 (우측 보조) — 비사용일 때도 배터리 노출 */}
                <div className="wifi-item-status-block">
                  {p.enabled ? (
                    <>
                      <span className={`wifi-status-dot ${p.status}`} />
                      <span className="wifi-item-status">{STATUS_LABEL[p.status] || '-'}</span>
                    </>
                  ) : (
                    <>
                      <span className="wifi-status-dot off-dot" />
                      <span className="wifi-item-status off">서비스 중단됨</span>
                    </>
                  )}
                  <span className="wifi-item-battery">(배터리 {p.battery}%)</span>
                </div>

                {/* 상세보기 링크 (가장 우측) */}
                <span className="wifi-item-detail-link">
                  상세보기 <ChevronRight size={16} />
                </span>
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
          <Button variant="primary" fullWidth icon={<Plus size={18} />} onClick={openAdd}>
            와이파이 신청하기
          </Button>
        </BottomActionBar>

        <ConfirmModal
          isOpen={!!deleteConfirm}
          title="와이파이 삭제"
          desc="이 와이파이 정보를 삭제하시겠습니까?"
          confirmText="삭제"
          cancelText="취소"
          onConfirm={() => handleDelete(deleteConfirm)}
          onCancel={() => setDeleteConfirm(null)}
        />
      </div>
    );
  }

  // ═════════════════════════════════════
  // DETAIL / ADD VIEW — Figma "와이파이 상세" / "와이파이 추가"
  // ═════════════════════════════════════
  const isAddMode = view === 'add';
  const canEdit = isEditing || isAddMode;
  const title = isAddMode
    ? '와이파이 신청하기'
    : isEditing
      ? '와이파이 수정'
      : '와이파이 상세';

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
        {isAddMode && (
          <div className="wifi-request-notice">
            아래 정보를 입력하시면 운영팀 검토 후 매장에 와이파이 정보가 등록됩니다.
          </div>
        )}
        {/* Name */}
        <div className="wifi-field-group">
          <label className="wifi-field-label">Name</label>
          <div className="wifi-name-row">
            <input
              type="text"
              className="wifi-field-input"
              placeholder="설정하고자 하는 와이파이 위치를 입력하세요"
              value={formData.name}
              onChange={e => setFormData({ ...formData, name: e.target.value })}
              disabled={!canEdit}
            />
            {selectedProfile && !isAddMode && (
              <div className="wifi-name-toggle">
                <span className="wifi-name-toggle-label">사용</span>
                <button
                  className={`wifi-toggle ${selectedProfile.enabled ? 'on' : 'off'}`}
                  onClick={() => toggleEnabled(selectedProfile.id)}
                  role="switch"
                  aria-checked={selectedProfile.enabled}
                  title={selectedProfile.enabled ? '서비스 ON — 클릭 시 OFF' : '서비스 OFF — 클릭 시 ON'}
                >
                  <span className="wifi-toggle-thumb" />
                </button>
              </div>
            )}
          </div>
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

        {/* Photo actions — label 로 input 감싸 iOS Safari/Android 모두 안정 동작
            accept 을 명시적 이미지 MIME 로 좁혀 파일 선택 옵션 최소화 */}
        {canEdit && (
          <div className="wifi-photo-actions">
            <label className={`wifi-photo-action ${ocrLoading ? 'is-disabled' : ''}`}>
              <ImageIcon size={14} /> 앨범에서 선택
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp,image/heic,image/heif,image/gif"
                onChange={handleImageChange}
                disabled={ocrLoading}
                className="wifi-photo-action-input"
              />
            </label>
            <label className={`wifi-photo-action ${ocrLoading ? 'is-disabled' : ''}`}>
              <Camera size={14} /> 카메라 촬영
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
                capture="environment"
                onChange={handleImageChange}
                disabled={ocrLoading}
                className="wifi-photo-action-input"
              />
            </label>
          </div>
        )}

        {!canEdit && (
          <div className="wifi-photo-actions">
            <button className="wifi-photo-action" disabled>앨범에서 선택</button>
            <button className="wifi-photo-action" disabled>카메라 촬영</button>
          </div>
        )}

        {/* OCR 인식 안내 */}
        {ocrLoading && (
          <div className="wifi-ocr-status">
            <Loader2 size={14} className="wifi-ocr-spin" /> 사진에서 와이파이 정보 인식 중...
          </div>
        )}
        {ocrDone && (
          <div className="wifi-ocr-status done">
            ✓ 사진에서 ID / PW 자동 입력했습니다. 확인 후 수정해주세요.
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
              신청하기
            </Button>
          </>
        ) : canEdit ? (
          <>
            <Button variant="outline" fullWidth onClick={() => setIsEditing(false)}>취소</Button>
            <Button variant="primary" fullWidth onClick={handleSave}>
              저장
            </Button>
          </>
        ) : (
          <>
            <Button variant="outline" fullWidth onClick={() => setView('list')}>닫기</Button>
            <Button variant="primary" fullWidth onClick={startEdit}>
              수정
            </Button>
          </>
        )}
      </BottomActionBar>

      <ConfirmModal
        isOpen={!!deleteConfirm}
        title="와이파이 삭제"
        desc="이 와이파이 정보를 삭제하시겠습니까?"
        confirmText="삭제"
        cancelText="취소"
        onConfirm={() => handleDelete(deleteConfirm)}
        onCancel={() => setDeleteConfirm(null)}
      />

      {/* 저장 확인 모달 (ID/PW 안내 + 비사용 안내 통합) */}
      <ConfirmModal
        isOpen={!!saveConfirmMsg}
        title="와이파이 정보 저장"
        desc={saveConfirmMsg || ''}
        confirmText="저장"
        cancelText="취소"
        onConfirm={doSave}
        onCancel={() => setSaveConfirmMsg(null)}
      />

      {/* 검증 실패 모달 */}
      <ConfirmModal
        isOpen={!!errorMsg}
        title="입력 확인"
        desc={errorMsg || ''}
        singleButton
        confirmText="확인"
        onConfirm={() => setErrorMsg(null)}
        onCancel={() => setErrorMsg(null)}
      />
    </div>
  );
};

export default WifiSettings;
