import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Camera, Plus, X, ChevronLeft, ChevronRight, Trash2, Edit3, Search, Image as ImageIcon, Loader2 } from 'lucide-react';
import WifiService from '../services/wifi/WifiService';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
import ConfirmModal from '../components/common/ConfirmModal';
import StatusBadge, {
  PROVIDER_STATUS_GROUPS,
  PROVIDER_HIDDEN_STATUSES,
  getProviderGroup,
} from '../components/common/StatusBadge';
import StatusTimeline from '../components/common/StatusTimeline';
import './WifiSettings.css';

// 워크플로우 정책 (사장님 콘솔):
//   - 결제 성공 후에만 신청건 생성 → 첫 status 는 'submitted'
//   - draft / payment_failed / info_requested / rejected 는 리스트 비노출 (PROVIDER_HIDDEN_STATUSES)
//   - 사장님 라벨은 6개 그룹: 신청완료 / 준비중 / 배송중 / 서비스중 / 일시중지 / 해지
//
// 데이터 구조:
//   - 단건 신청  : applicationGroupId 가 단독 — UI 그룹 헤더 생략
//   - 다건 신청  : 같은 applicationGroupId 로 묶이며 UI 그룹 헤더(신청번호/총수량/결제일) + 자식 카드
//
// status 필드 분리:
//   applicationStatus — 12개 세분 enum (호환 별칭 포함). StatusBadge 가 6개 그룹 라벨로 렌더
//   deviceStatus      — 운영 디바이스 상태 (정상/배터리부족/연결끊김) — 'active' 단계만 의미
//
// workflow 추가 필드:
//   statusMessage     — 슈퍼어드민/시스템이 남긴 안내
//   statusUpdatedAt   — 'YYYY.MM.DD HH:mm' 또는 ISO8601
//   statusHistory     — 후속 PR 활용

const MOCK_PROFILES = [
  // ── 기존 운영 중 와이파이 (단건 신청) ─────────────────────────
  { id: 1, name: '로비정문1', applicationGroupId: 'PW-20220315-001', applicationGroupSeq: 1, applicationGroupTotal: 1,
    paidAt: '2022.03.15 09:30',
    message: 'Message', ssid: 'kt5G_1234789', beaconSn: 'BCN-2024-0001', password: 'Ezddd1@3356', date: '2022.03.15', periodEnd: '2024.03.14', image: null,
    applicationStatus: 'active',
    statusMessage: '',
    statusUpdatedAt: '2024.03.20 10:00',
    statusHistory: [],
    deviceStatus: 'ok', battery: 90, enabled: true },
  { id: 2, name: '수영장', applicationGroupId: 'PW-20220310-002', applicationGroupSeq: 1, applicationGroupTotal: 1,
    paidAt: '2022.03.10 14:00',
    message: 'Message', ssid: 'kt5G_pool01', beaconSn: 'BCN-2024-0002', password: 'Ezddd1@3356', date: '2022.03.10', periodEnd: '2024.03.09', image: null,
    applicationStatus: 'active',
    statusMessage: '',
    statusUpdatedAt: '2024.03.15 14:00',
    statusHistory: [],
    deviceStatus: 'ok', battery: 76, enabled: true },
  { id: 3, name: '1층카페', applicationGroupId: 'PW-20220228-003', applicationGroupSeq: 1, applicationGroupTotal: 1,
    paidAt: '2022.02.28 11:00',
    message: 'Message', ssid: 'kt5G_cafe01', beaconSn: 'BCN-2024-0003', password: 'Ezddd1@3356', date: '2022.02.28', periodEnd: '2024.02.27', image: null,
    applicationStatus: 'active',
    statusMessage: '',
    statusUpdatedAt: '2024.03.05 11:20',
    statusHistory: [],
    deviceStatus: 'low', battery: 22, enabled: true },
  { id: 4, name: '5001호', applicationGroupId: 'PW-20220115-004', applicationGroupSeq: 1, applicationGroupTotal: 1,
    paidAt: '2022.01.15 10:00',
    message: 'Message', ssid: 'kt5G_5001', beaconSn: 'BCN-2024-0005', password: 'Ezddd1@3356', date: '2022.01.15', periodEnd: '2024.01.14', image: null,
    applicationStatus: 'active',
    statusMessage: '',
    statusUpdatedAt: '2024.02.01 10:00',
    statusHistory: [],
    deviceStatus: 'offline', battery: 0, enabled: true },

  // ── 일시중지 (단건) ───────────────────────────────────────────
  { id: 5, name: '2층뷔페', applicationGroupId: 'PW-20220220-005', applicationGroupSeq: 1, applicationGroupTotal: 1,
    paidAt: '2022.02.20 13:00',
    message: 'Message', ssid: 'kt5G_buffet', beaconSn: 'BCN-2024-0004', password: 'Ezddd1@3356', date: '2022.02.20', periodEnd: '2024.02.19', image: null,
    applicationStatus: 'paused',
    statusMessage: '배터리 점검을 위해 일시 중지되었습니다.',
    statusUpdatedAt: '2024.02.25 17:45',
    statusHistory: [],
    deviceStatus: 'ok', battery: 12, enabled: false },

  // ── 다건 신청 그룹 #1 — 신관 (3개) ────────────────────────────
  // 결제 1회로 3개 wifi 동시 신청. 각 wifiItem 단계 다양함.
  { id: 6, name: '신관 1층', applicationGroupId: 'PW-20260509-001', applicationGroupSeq: 1, applicationGroupTotal: 3,
    paidAt: '2026.05.09 09:00',
    message: '', ssid: 'kt5G_NW_F1', beaconSn: 'BCN-2026-0010', password: 'Ezddd1@8801', date: '2026.05.09', periodEnd: '2028.05.08', image: null,
    applicationStatus: 'beacon_setting',
    statusMessage: '비콘 SN 매핑 진행 중입니다.',
    statusUpdatedAt: '2026.05.09 14:22',
    statusHistory: [
      { status: 'beacon_setting', message: '비콘 SN 매핑 시작',          changedAt: '2026.05.09 14:22', changedBy: 'admin' },
      { status: 'receiving',      message: '슈퍼어드민이 신청을 확인했습니다.', changedAt: '2026.05.09 11:00', changedBy: 'admin' },
      { status: 'submitted',      message: '결제 완료 — 신청이 접수되었습니다.', changedAt: '2026.05.09 09:00', changedBy: 'system' },
    ],
    deviceStatus: 'ok', battery: 0, enabled: false },
  { id: 7, name: '신관 2층', applicationGroupId: 'PW-20260509-001', applicationGroupSeq: 2, applicationGroupTotal: 3,
    paidAt: '2026.05.09 09:00',
    message: '', ssid: 'kt5G_NW_F2', beaconSn: 'BCN-2026-0011', password: 'Ezddd1@8802', date: '2026.05.09', periodEnd: '2028.05.08', image: null,
    applicationStatus: 'shipping_ready',
    statusMessage: '출고 준비 중입니다.',
    statusUpdatedAt: '2026.05.09 16:10',
    statusHistory: [],
    deviceStatus: 'ok', battery: 0, enabled: false },
  { id: 8, name: '신관 루프탑', applicationGroupId: 'PW-20260509-001', applicationGroupSeq: 3, applicationGroupTotal: 3,
    paidAt: '2026.05.09 09:00',
    message: '', ssid: 'kt5G_NW_RF', beaconSn: 'BCN-2026-0012', password: 'Ezddd1@8803', date: '2026.05.09', periodEnd: '2028.05.08', image: null,
    applicationStatus: 'shipping',
    statusMessage: 'CJ대한통운 송장번호 1234-5678-9012로 배송 중입니다.',
    statusUpdatedAt: '2026.05.09 17:00',
    statusHistory: [],
    deviceStatus: 'ok', battery: 0, enabled: false },

  // ── 단건 신청 — 접수확인중 ───────────────────────────────────
  { id: 9, name: '별관 1층', applicationGroupId: 'PW-20260508-002', applicationGroupSeq: 1, applicationGroupTotal: 1,
    paidAt: '2026.05.08 18:30',
    message: '', ssid: 'kt5G_BR_F1', beaconSn: '', password: 'Ezddd1@8810', date: '2026.05.08', periodEnd: '2028.05.07', image: null,
    applicationStatus: 'submitted',
    statusMessage: '결제가 완료되었습니다. 슈퍼어드민이 신청을 확인하면 다음 단계로 진행됩니다.',
    statusUpdatedAt: '2026.05.08 18:30',
    statusHistory: [
      { status: 'submitted', message: '결제 완료 — 신청이 접수되었습니다.', changedAt: '2026.05.08 18:30', changedBy: 'system' },
    ],
    deviceStatus: 'ok', battery: 0, enabled: false },
];

// 상태 라벨 + 색상
const STATUS_LABEL = {
  ok: '정상',
  low: '배터리 부족',
  offline: '연결 끊김',
};

const WifiSettings = () => {
  const location = useLocation();
  const navigate = useNavigate();
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
      const nowKr = (() => {
        const d = new Date();
        const pad = (n) => String(n).padStart(2, '0');
        return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
      })();
      const newGroupId = `PW-${nowKr.slice(0, 10).replace(/\./g, '')}-${String(Date.now()).slice(-3)}`;
      const newProfile = {
        id: Date.now(),
        name: formData.name,
        message: 'Message',
        ssid: formData.ssid,
        beaconSn: '',
        password: formData.password,
        date: nowKr.slice(0, 10),
        periodEnd: '',
        image: previewUrl,
        // 신정책: 결제 완료 후에만 신청건 생성 → 첫 status 는 'submitted'
        // 본 mock 은 카드 단축 추가 모드 (결제 단계 없음) 라 동일 시점 submitted 로 부여
        applicationGroupId: newGroupId,
        applicationGroupSeq: 1,
        applicationGroupTotal: 1,
        paidAt: nowKr,
        applicationStatus: 'submitted',
        statusMessage: '결제가 완료되었습니다. 슈퍼어드민이 신청을 확인하면 다음 단계로 진행됩니다.',
        statusUpdatedAt: nowKr,
        statusHistory: [
          { status: 'submitted', message: '결제 완료 — 신청이 접수되었습니다.', changedAt: nowKr, changedBy: 'system' },
        ],
        deviceStatus: 'ok',
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

  // 사장님 콘솔 정책: 결제실패/추가정보 요청/반려 등은 리스트에서 비노출
  const visibleProfiles = profiles.filter(
    (p) => !PROVIDER_HIDDEN_STATUSES.has(p.applicationStatus)
  );

  const displayProfiles = activeFilter
    ? visibleProfiles.filter((p) => activeFilter.includes(p.name))
    : visibleProfiles;

  // 6개 그룹 카운트 (사장님 콘솔용 요약 영역)
  const groupCounts = displayProfiles.reduce((acc, p) => {
    const g = getProviderGroup(p.applicationStatus);
    if (!g) return acc;
    acc[g] = (acc[g] || 0) + 1;
    return acc;
  }, {});

  // applicationGroupId 로 묶기 (다건 신청 그룹 헤더용).
  // 동일 group 인 카드들이 연속으로 나타나도록 list 정렬은 유지하되 group 별 카드 그룹화.
  const groupedProfiles = (() => {
    const groups = []; // [{ groupId, items: [...] }]
    const indexById = new Map();
    for (const p of displayProfiles) {
      const gid = p.applicationGroupId || `__single_${p.id}`;
      if (!indexById.has(gid)) {
        indexById.set(gid, groups.length);
        groups.push({ groupId: gid, items: [], paidAt: p.paidAt, total: p.applicationGroupTotal || 1 });
      }
      groups[indexById.get(gid)].items.push(p);
    }
    return groups;
  })();

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
          <span className="wifi-count">총 {displayProfiles.length}개 와이파이</span>
          <button className="wifi-search-btn" onClick={openSearch}>
            <Search size={16} />
            검색
          </button>
        </div>

        {/* 신청 진행 현황판 — 6개 그룹 카운트 (사장님 콘솔 정책) */}
        {displayProfiles.length > 0 && (
          <div className="wifi-summary-bar" role="list" aria-label="신청 진행 현황">
            {Object.entries(PROVIDER_STATUS_GROUPS).map(([key, meta]) => {
              const count = groupCounts[key] || 0;
              if (count === 0) return null;
              return (
                <div
                  key={key}
                  className={`wifi-summary-chip pw-status-${meta.variant}`}
                  role="listitem"
                  title={meta.label}
                >
                  <span className="wifi-summary-label">{meta.label}</span>
                  <span className="wifi-summary-count">{count}</span>
                </div>
              );
            })}
          </div>
        )}

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

        {/* WiFi List — 다건 신청은 그룹 헤더 + 자식 카드, 단건은 카드만 */}
        <div className="wifi-list">
          {groupedProfiles.map((group) => {
            const isMulti = group.items.length > 1 || (group.items[0]?.applicationGroupTotal || 1) > 1;
            return (
              <div key={group.groupId} className={`wifi-group ${isMulti ? 'is-multi' : 'is-single'}`}>
                {isMulti && (
                  <div className="wifi-group-header">
                    <div className="wifi-group-header-main">
                      <span className="wifi-group-id">신청번호 {group.groupId}</span>
                      <span className="wifi-group-meta">
                        총 {group.items[0]?.applicationGroupTotal || group.items.length}개 와이파이
                        {group.paidAt && ` · 결제 ${group.paidAt}`}
                      </span>
                    </div>
                  </div>
                )}
                {group.items.map((p) => (
                  <div
                    key={p.id}
                    className={`wifi-list-item ${swipedId === p.id ? 'swiped' : ''}`}
                    onTouchStart={(e) => handleTouchStart(e, p.id)}
                    onTouchEnd={(e) => handleTouchEnd(e, p.id)}
                  >
                    <div className={`wifi-item-content ${!p.enabled ? 'is-disabled' : ''}`} onClick={() => openDetail(p)}>
                      {/* 좌측 — 설치위치(Name) + 신청/운영 상태 배지 + 메타 + 상태 타임라인 */}
                      <div className="wifi-item-name-block">
                        <div className="wifi-item-name-row">
                          <span className="wifi-item-name">{p.name}</span>
                          <StatusBadge status={p.applicationStatus} size="sm" mode="provider" />
                        </div>
                        <div className="wifi-item-meta">
                          {p.ssid && <span className="wifi-item-meta-pill">SSID {p.ssid}</span>}
                          {p.beaconSn && <span className="wifi-item-meta-pill">{p.beaconSn}</span>}
                          {p.periodEnd && <span className="wifi-item-meta-pill">~ {p.periodEnd}</span>}
                          {!isMulti && p.applicationGroupId && (
                            <span className="wifi-item-meta-pill subtle">신청 {p.applicationGroupId}</span>
                          )}
                        </div>
                        {/* workflow 상태 메시지 + 마지막 업데이트 — 'active' 단계는 우측 운영 dot 사용 */}
                        {(p.statusMessage || p.statusUpdatedAt) && p.applicationStatus !== 'active' && (
                          <StatusTimeline
                            status={p.applicationStatus}
                            statusMessage={p.statusMessage}
                            statusUpdatedAt={p.statusUpdatedAt}
                            compact
                            className="wifi-item-timeline"
                          />
                        )}
                      </div>

                      {/* 운영 상태 + 배터리 (우측 보조) — 사용중(active) 단계에서만 의미 있음 */}
                      <div className="wifi-item-status-block">
                        {p.applicationStatus === 'active' ? (
                          p.enabled ? (
                            <>
                              <span className={`wifi-status-dot ${p.deviceStatus}`} />
                              <span className="wifi-item-status">{STATUS_LABEL[p.deviceStatus] || '-'}</span>
                              <span className="wifi-item-battery">(배터리 {p.battery}%)</span>
                            </>
                          ) : (
                            <>
                              <span className="wifi-status-dot off-dot" />
                              <span className="wifi-item-status off">서비스 중단됨</span>
                              <span className="wifi-item-battery">(배터리 {p.battery}%)</span>
                            </>
                          )
                        ) : null}
                      </div>

                      <span className="wifi-item-detail-link">
                        상세보기 <ChevronRight size={16} />
                      </span>
                    </div>

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
            );
          })}
        </div>

        <BottomActionBar>
          <Button variant="primary" fullWidth icon={<Plus size={18} />} onClick={() => navigate('/dashboard/service-request?type=wifi')}>
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
