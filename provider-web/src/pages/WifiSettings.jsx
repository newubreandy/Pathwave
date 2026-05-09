import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Camera, Plus, X, ChevronLeft, ChevronRight, Search,
  Image as ImageIcon, Loader2,
  Wifi, Package, Truck, FileCheck2, PauseCircle, XCircle, ClipboardList,
  Clock,
} from 'lucide-react';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
import ConfirmModal from '../components/common/ConfirmModal';
import StatusBadge, {
  PROVIDER_STATUS_GROUPS,
  PROVIDER_HIDDEN_STATUSES,
  getProviderGroup,
  getProviderSection,
} from '../components/common/StatusBadge';
import PageShell from '../components/common/PageShell';
import SectionTabs from '../components/common/SectionTabs';
import GlassCard from '../components/common/GlassCard';
import GroupCard, { GroupCardItem } from '../components/common/GroupCard';
import MiniInfoPill from '../components/common/MiniInfoPill';
import StatusMessage from '../components/common/StatusMessage';
import MetricStrip from '../components/common/MetricStrip';
import CardAvatar from '../components/common/CardAvatar';
import { SkeletonCard } from '../components/common/Skeleton';
// StageProgress / stageMapping 은 list view 에서 제거 (사용자 요구: StatusBadge 텍스트 방식 유지).
// 슈퍼어드민 / 상세 화면에서 재사용 가능하도록 컴포넌트 자체는 유지.
import './WifiSettings.css';

/**
 * 상태 → 카드 좌측 아바타 맵핑.
 * provider 라벨 그룹과 1:1 정렬.
 *
 *   delivered/installed = 서비스대기 (운영중 탭) — Clock 아이콘 + info variant
 *   active              = 서비스중 (운영중 탭) — Wifi (live 섹션 별도 렌더)
 */
const STATUS_AVATAR = {
  submitted:        { icon: FileCheck2,  variant: 'info'    },
  receiving:        { icon: FileCheck2,  variant: 'info'    },
  beacon_setting:   { icon: Package,     variant: 'accent'  },
  shipping_ready:   { icon: Package,     variant: 'accent'  },
  service_ready:    { icon: Package,     variant: 'accent'  },
  shipping:         { icon: Truck,       variant: 'accent'  },
  delivered:        { icon: Clock,       variant: 'info'    },
  installed:        { icon: Clock,       variant: 'info'    },
  active:           { icon: Wifi,        variant: 'success' },
  paused:           { icon: PauseCircle, variant: 'warning' },
  terminated:       { icon: XCircle,     variant: 'neutral' },
};

const isServiceWaiting = (status) => status === 'delivered' || status === 'installed';

const getAvatarForStatus = (status) =>
  STATUS_AVATAR[status] || { icon: Wifi, variant: 'neutral' };

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

  // ── 서비스대기 — 배송 완료 후 사용자 활성화 대기 (단건) ─────────
  { id: 11, name: '서관 1층', applicationGroupId: 'PW-20260507-003', applicationGroupSeq: 1, applicationGroupTotal: 1,
    paidAt: '2026.05.07 11:00',
    message: '', ssid: 'kt5G_WS_F1', beaconSn: 'BCN-2026-0020', password: 'Ezddd1@8820', date: '2026.05.07', periodEnd: '2028.05.06', image: null,
    applicationStatus: 'delivered',
    statusMessage: '배송이 완료되었습니다. 서비스 시작을 기다리는 중입니다.',
    statusUpdatedAt: '2026.05.09 10:30',
    statusHistory: [],
    deviceStatus: 'ok', battery: 100, enabled: false },

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
    shippingCarrier: 'CJ대한통운',
    shippingTrackingNo: '1234-5678-9012',
    statusMessage: '배송이 시작되었습니다. 도착까지 1~2일 소요됩니다.',
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
  // 리스트 탭 — 2개 탭 구조 (신청 진행중 / 운영중).
  // 일시중지·해지 항목은 운영중 탭 최하단에 합쳐서 노출 (해지일 순).
  const [activeTab, setActiveTab] = useState('inProgress'); // 'inProgress' | 'live'
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedChips, setSelectedChips] = useState(new Set());
  const [activeFilter, setActiveFilter] = useState(null); // filtered name after search
  // 헤더 인라인 검색 — 즉시 필터 (별도 view 진입 X). chip-style 고급 검색은 view='search' 로 분리 유지.
  const [inlineQuery, setInlineQuery] = useState('');
  // 첫 진입 로딩 — 실 API 연결 시 fetch 후 setIsLoading(false). 현재는 mock data 라 짧게 시뮬레이션.
  const [isLoading, setIsLoading] = useState(true);
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

  // GNB 의 "와이파이" 메뉴를 다시 탭하면 리스트로 복귀 (location.key 변경 감지).
  // location.key 가 변하면 리스트로 reset 되어야 하므로 effect 안 setState 가 의도된 동작.
  /* eslint-disable react-hooks/set-state-in-effect, react-hooks/exhaustive-deps */
  useEffect(() => {
    setView('list');
    setSelectedProfile(null);
    setIsEditing(false);
    setSaveConfirmMsg(null);
    setErrorMsg(null);
  }, [location.key]);

  // 첫 진입 시 가짜 로딩 (실 API 연동 시 fetch promise resolve 시점에 setIsLoading(false)).
  // 350ms 정도면 시각 피드백은 충분하면서 답답하지 않음.
  useEffect(() => {
    const t = setTimeout(() => setIsLoading(false), 350);
    return () => clearTimeout(t);
  }, []);
  /* eslint-enable react-hooks/set-state-in-effect, react-hooks/exhaustive-deps */

  // ── List Actions ──
  const openDetail = (profile) => {
    setSelectedProfile(profile);
    setFormData({ name: profile.name, ssid: profile.ssid, password: profile.password, image: profile.image });
    setPreviewUrl(profile.image);
    setIsEditing(false);
    setView('detail');
  };

  const handleDelete = (id) => {
    setProfiles(prev => prev.filter(p => p.id !== id));
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

  // 헤더 인라인 검색 — 와이파이 이름(설치 위치) 만 매칭.
  // SSID 부분 매칭은 의도치 않은 결과 (예: "1" → "kt5G_pool01") 를 만들어
  // 사장님 직관에 어긋남. SSID 까지 검색하려면 우측 "상세" 버튼의 chip-search 사용.
  const inlineFiltered = inlineQuery.trim()
    ? visibleProfiles.filter((p) => {
        const q = inlineQuery.trim().toLowerCase();
        return p.name.toLowerCase().includes(q);
      })
    : visibleProfiles;

  const displayProfiles = activeFilter
    ? inlineFiltered.filter((p) => activeFilter.includes(p.name))
    : inlineFiltered;

  // 섹션별로 카드 분리 (사장님 콘솔 — 4 섹션)
  const profilesBySection = displayProfiles.reduce((acc, p) => {
    const s = getProviderSection(p.applicationStatus);
    if (!s) return acc;
    (acc[s] = acc[s] || []).push(p);
    return acc;
  }, {});

  // 신청 진행중 섹션 안에서 applicationGroupId 로 묶기 + 그룹별 미니 카운트
  const buildInProgressGroups = (profiles) => {
    const groups = [];
    const indexById = new Map();
    for (const p of profiles) {
      const gid = p.applicationGroupId || `__single_${p.id}`;
      if (!indexById.has(gid)) {
        indexById.set(gid, groups.length);
        groups.push({
          groupId: gid,
          items: [],
          paidAt: p.paidAt,
          total: p.applicationGroupTotal || 1,
        });
      }
      groups[indexById.get(gid)].items.push(p);
    }
    // 그룹 안 라벨별 미니 카운트
    return groups.map((g) => {
      const labelCounts = {};
      g.items.forEach((p) => {
        const groupKey = getProviderGroup(p.applicationStatus);
        const meta = PROVIDER_STATUS_GROUPS[groupKey];
        if (meta) labelCounts[meta.label] = (labelCounts[meta.label] || 0) + 1;
      });
      return { ...g, labelCounts };
    });
  };

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
  // LIST VIEW — 운영툴 톤 (Linear / Stripe / Notion 다크 계열)
  //   탭 3개 (신청 진행중 / 운영중 / 점검·해지) — 각 탭은 카드 변형이 다름.
  //   - 신청 진행중 : prominent (좌측 accent 라인) + GroupCard 묶음
  //   - 운영중       : compact (가장 차분, 보기 전용, swipe X)
  //   - 점검·해지   : warning (일시중지) / 표준 (해지)
  //   StatusTimeline / 단계 나열 UI 는 list view 에서 사용 안 함 — 상세보기에서만.
  // ═════════════════════════════════════
  if (view === 'list') {
    const inProgressCount  = (profilesBySection.inProgress || []).length;
    const liveActiveCount  = (profilesBySection.live || []).length;
    const pausedCount      = (profilesBySection.paused || []).length;
    const terminatedCount  = (profilesBySection.terminated || []).length;
    // 운영중 탭은 active + paused + terminated 모두 포함 (점검·해지는 별도 탭 없음).
    const liveCount = liveActiveCount + pausedCount + terminatedCount;

    const tabDefs = [
      { key: 'inProgress',  label: '신청 진행중', count: inProgressCount },
      { key: 'live',        label: '운영중',     count: liveCount },
    ];

    // 상단 메트릭 — 진행 / 운영 / 점검·해지 (정보판 용도, 탭과 별개로 carry).
    const maintenanceCount = pausedCount + terminatedCount;
    const metricItems = [
      { label: '진행', value: inProgressCount,  unit: '건', tone: inProgressCount  > 0 ? 'accent'  : 'default' },
      { label: '운영', value: liveActiveCount,  unit: '건', tone: liveActiveCount  > 0 ? 'success' : 'default' },
      { label: '점검·해지', value: maintenanceCount, unit: '건', tone: maintenanceCount > 0 ? 'warning' : 'default' },
    ];

    // 운영중 탭 — 정렬 순서 (위 → 아래):
    //   1) 서비스대기 (delivered/installed) — 가장 위, 사용자 활성화 액션 필요
    //   2) 서비스중   (active)
    //   3) 일시중지   (paused)
    //   4) 해지       (terminated, 해지일 desc)
    const liveItems = profilesBySection.live || [];
    const liveWaiting = liveItems.filter((p) => isServiceWaiting(p.applicationStatus));
    const liveActive  = liveItems.filter((p) => p.applicationStatus === 'active');
    const sortedTerminated = (profilesBySection.terminated || [])
      .slice()
      .sort((a, b) => {
        // statusUpdatedAt 또는 paidAt 기준. ISO 또는 'YYYY.MM.DD HH:mm' 문자열 desc 정렬.
        const ka = a.statusUpdatedAt || a.paidAt || '';
        const kb = b.statusUpdatedAt || b.paidAt || '';
        return kb.localeCompare(ka);
      });

    // 활성 탭에 보여줄 섹션 키 (운영중은 3개 합쳐서 렌더)
    const totalCount =
      activeTab === 'inProgress'
        ? inProgressCount
        : liveCount;

    // ── 그룹 컨테이너 안 inset row 렌더 — RePlan 스타일 ──
    // 사용자 요구 (2026-05-09): 하단 상태 메시지 제거. 우측 플래그 = StatusBadge (이전 방식).
    // 슈퍼어드민 (admin-web) 에서는 statusMessage 도 노출 — 이 페이지는 사장님 콘솔.
    const renderWifiInsetRow = (p) => {
      const a = getAvatarForStatus(p.applicationStatus);
      const AvatarIcon = a.icon;
      const hasShipping = !!p.shippingTrackingNo;
      return (
        <GroupCardItem key={p.id} onClick={() => openDetail(p)}>
          <CardAvatar variant="accent" size="md">
            <AvatarIcon strokeWidth={2} />
          </CardAvatar>
          <div className="wifi-inset-body">
            <div className="wifi-inset-head">
              <span className="wifi-inset-title">{p.name}</span>
              {/* 우측 플래그 — 텍스트 배지 (준비중 / 배송중 / 신청완료 등) */}
              <StatusBadge status={p.applicationStatus} size="sm" mode="provider" />
            </div>
            <div className="pw-pill-row wifi-inset-pills">
              {p.ssid && <MiniInfoPill label="SSID" mono>{p.ssid}</MiniInfoPill>}
              {p.beaconSn && <MiniInfoPill mono variant="muted">{p.beaconSn}</MiniInfoPill>}
            </div>
            {hasShipping && (
              <div className="wifi-inset-shipping" role="note">
                <span className="wifi-inset-shipping-label">송장</span>
                <span className="wifi-inset-shipping-value">{p.shippingTrackingNo}</span>
              </div>
            )}
            {/* statusMessage 제거 — 사장님 콘솔에서는 stepper 만으로 충분.
                슈퍼어드민에서 같은 컴포넌트 재사용 시 prop 으로 분기 예정. */}
          </div>
          <ChevronRight size={16} className="wifi-inset-chevron" aria-hidden="true" />
        </GroupCardItem>
      );
    };

    // ── 카드 1장 렌더 — 좌측 아바타 + 본문 + 메시지 + chevron ──
    const renderWifiCard = (p, opts = {}) => {
      const { variant = 'default', section = 'inProgress' } = opts;
      // 메시지 tone — 운영중 active 면 accent, paused 면 warning, 그 외는 info
      const msgTone =
        section === 'paused' ? 'warning'
        : section === 'terminated' ? 'info'
        : section === 'inProgress' ? 'accent'
        : 'info';

      // 송장번호 — 배송중일 때만 별도 row 로 강조 (pill 아님)
      const hasShipping = !!p.shippingTrackingNo;

      // 운영중 탭은 active(서비스중) + delivered(서비스대기) 둘 다 들어옴.
      const isWaiting    = section === 'live' && isServiceWaiting(p.applicationStatus);
      const isActiveLive = section === 'live' && p.applicationStatus === 'active';
      // 서비스중일 때만 디바이스 상태 강조 (서비스대기는 device 정보 무관).
      const isOffline    = isActiveLive && p.enabled && p.deviceStatus === 'offline';
      const isLowBattery = isActiveLive && p.enabled && p.deviceStatus === 'low';
      const isDisabled   = isActiveLive && !p.enabled;

      // 좌측 아바타 —
      //   서비스대기 (delivered) = Clock + info — "활성화 대기 중"
      //   서비스중   (active)    = Wifi + 디바이스 상태 색조
      //   신청 진행중 = accent 통일 (그룹 헤더와 톤 매칭)
      //   일시중지 = warning, 해지 = neutral
      let avatarVariant, AvatarIcon;
      if (isWaiting) {
        AvatarIcon = Clock;
        avatarVariant = 'info';
      } else if (isActiveLive) {
        AvatarIcon = Wifi;
        avatarVariant =
          !p.enabled ? 'neutral'
          : p.deviceStatus === 'ok'      ? 'success'
          : p.deviceStatus === 'low'     ? 'warning'
          : p.deviceStatus === 'offline' ? 'danger'
          : 'neutral';
      } else if (section === 'inProgress') {
        const a = getAvatarForStatus(p.applicationStatus);
        AvatarIcon = a.icon;
        avatarVariant = 'accent';
      } else if (section === 'paused') {
        AvatarIcon = PauseCircle;
        avatarVariant = 'warning';
      } else { // terminated
        AvatarIcon = XCircle;
        avatarVariant = 'neutral';
      }

      return (
        <GlassCard
          key={p.id}
          variant={variant}
          uniformHeight
          onClick={() => openDetail(p)}
          className={[
            'wifi-card',
            `wifi-card--${section}`,
            isOffline ? 'wifi-card--offline' : '',
            isLowBattery ? 'wifi-card--low' : '',
            isDisabled ? 'wifi-card--disabled' : '',
          ].filter(Boolean).join(' ')}
        >
          {/* 카드 본문 — 좌측 아바타 + 우측 콘텐츠 row */}
          <div className="wifi-card-row">
            <CardAvatar variant={avatarVariant} size="md">
              <AvatarIcon strokeWidth={2} />
            </CardAvatar>

            <div className="wifi-card-body">
              <div className="wifi-card-head">
                <span className="wifi-card-title">{p.name}</span>
                {/* 모든 카드 공통 — 텍스트 배지 (준비중 / 배송중 / 신청완료 / 서비스중 / 일시중지 / 해지) */}
                <StatusBadge status={p.applicationStatus} size="sm" mode="provider" />
              </div>

              {/* MiniInfoPill 최대 2~3개 */}
              <div className="pw-pill-row wifi-card-pills">
                {p.ssid && <MiniInfoPill label="SSID" mono>{p.ssid}</MiniInfoPill>}
                {p.beaconSn && <MiniInfoPill mono variant="muted">{p.beaconSn}</MiniInfoPill>}
                {section === 'live' && p.enabled && (
                  <MiniInfoPill variant="muted">배터리 {p.battery}%</MiniInfoPill>
                )}
              </div>

              {/* 운영중 active — 디바이스 상태 한 줄 (정상/배터리부족/연결끊김/중단).
                  서비스대기(delivered) 는 device 정보 무관 → 노출 X. */}
              {isActiveLive && (
                <div className="wifi-card-device">
                  <span className="wifi-card-device-label">
                    {p.enabled ? (STATUS_LABEL[p.deviceStatus] || '-') : '중단'}
                  </span>
                  {p.statusUpdatedAt && (
                    <span className="wifi-card-device-time">{p.statusUpdatedAt}</span>
                  )}
                </div>
              )}

              {/* 신청 진행중 — 배송중 단계는 송장번호 row (택배사 비노출) */}
              {hasShipping && section === 'inProgress' && (
                <div className="wifi-card-shipping" role="note">
                  <span className="wifi-card-shipping-label">송장</span>
                  <span className="wifi-card-shipping-value">{p.shippingTrackingNo}</span>
                </div>
              )}

            </div>
          </div>

          {/* 상태 메시지 — 사장님 콘솔에서는 inProgress 에서 비노출 (우측 stepper 로 대체).
              운영중 / 일시중지 / 해지 는 메시지 노출 — 일시중지 사유 등 운영 안내 필요. */}
          {p.statusMessage && section !== 'inProgress' && (
            <StatusMessage tone={msgTone}>{p.statusMessage}</StatusMessage>
          )}

          {/* 카드 footer — 하단 우측 "상세보기 >" 링크 (가이드 v1.0) */}
          <div className="wifi-card-foot">
            <span className="wifi-card-detail">
              상세보기 <ChevronRight size={14} aria-hidden="true" />
            </span>
          </div>
        </GlassCard>
      );
    };

    return (
      <PageShell
        theme="provider"
        title="와이파이 관리"
        subtitle="신청·운영·점검 상태를 한 화면에서"
        actions={
          <div className="wifi-header-search">
            <Search size={16} className="wifi-header-search-icon" aria-hidden="true" />
            <input
              type="search"
              className="wifi-header-search-input"
              placeholder="와이파이 이름 검색"
              value={inlineQuery}
              onChange={(e) => setInlineQuery(e.target.value)}
              aria-label="와이파이 이름 검색"
            />
            {inlineQuery && (
              <button
                type="button"
                className="wifi-header-search-clear"
                onClick={() => setInlineQuery('')}
                aria-label="검색 지우기"
              >
                <X size={14} />
              </button>
            )}
            <button
              type="button"
              className="wifi-header-search-advanced"
              onClick={openSearch}
              aria-label="고급 검색 (chip 선택)"
            >
              상세
            </button>
          </div>
        }
      >
        {/* 상단 메트릭 — 3초 이해용 정보판 */}
        <MetricStrip items={metricItems} />

        {/* 검색 필터 활성 표시 (chip 검색 사용 시) */}
        {activeFilter && (
          <div className="wifi-active-filter">
            <div className="wifi-filter-chips">
              {activeFilter.map((name) => (
                <span key={name} className="wifi-filter-chip">{name}</span>
              ))}
            </div>
            <button className="wifi-clear-filter" onClick={clearFilter}>
              <X size={14} /> 필터 해제
            </button>
          </div>
        )}

        {/* 탭 — sticky pill */}
        <SectionTabs
          tabs={tabDefs}
          value={activeTab}
          onChange={(k) => {
            setActiveTab(k);
            window.scrollTo({ top: 0, behavior: 'auto' });
          }}
          sticky
          ariaLabel="와이파이 상태 탭"
        />

        {/* 로딩 skeleton — 첫 진입에만 (실 API 도착 전) */}
        {isLoading && (
          <div className="wifi-list" role="status" aria-label="와이파이 목록 로딩 중">
            <SkeletonCard count={3} />
          </div>
        )}

        {/* 빈 상태 (로딩 끝났는데도 0건) */}
        {!isLoading && totalCount === 0 && (
          <div className="wifi-tab-empty" role="status">
            <p>
              {activeTab === 'inProgress' && (inlineQuery
                ? `‘${inlineQuery}’ 이름의 신청을 찾을 수 없습니다.`
                : '현재 진행 중인 신청이 없습니다.\n새 와이파이를 신청해보세요.')}
              {activeTab === 'live'       && (inlineQuery
                ? `‘${inlineQuery}’ 이름의 와이파이를 찾을 수 없습니다.`
                : '운영 중인 서비스가 없습니다.\n신청 절차가 끝나면 이곳에 표시됩니다.')}
            </p>
          </div>
        )}

        {/* ── 신청 진행중 탭 ── */}
        {!isLoading && activeTab === 'inProgress' && totalCount > 0 && (() => {
          const groups = buildInProgressGroups(profilesBySection.inProgress || []);
          return (
            <div className="wifi-list wifi-list--inprogress">
              {groups.map((group) => {
                const total = group.items[0]?.applicationGroupTotal || group.items.length;
                const isMulti = total > 1;

                if (!isMulti) {
                  // 단건 신청 — GroupCard 사용 안 함, 바로 prominent 카드
                  return renderWifiCard(group.items[0], { variant: 'default', section: 'inProgress' });
                }

                // 다건 신청 — GroupCard (헤더에 클립보드 아바타 + 결제완료 pill + subtitle).
                // 가이드 v1.0 — 진행률 chip 제거, expand/collapse chevron 으로 단순화.
                const subtitle = `${total}개 와이파이${group.paidAt ? ` · 결제완료 ${group.paidAt.slice(0, 10)}` : ''}`;

                return (
                  <GroupCard
                    key={group.groupId}
                    variant="container"
                    leading={
                      <CardAvatar variant="accent" size="md" ariaLabel="신청 그룹">
                        <ClipboardList strokeWidth={2} />
                      </CardAvatar>
                    }
                    title={group.groupId}
                    paid
                    subtitle={subtitle}
                  >
                    {group.items.map(renderWifiInsetRow)}
                  </GroupCard>
                );
              })}
            </div>
          );
        })()}

        {/* ── 운영중 탭 — 사용자 요구 (2026-05-09):
              서비스대기(delivered) → 서비스중(active) → 일시중지 → 해지(일자순) ── */}
        {!isLoading && activeTab === 'live' && totalCount > 0 && (
          <div className="wifi-list wifi-list--live">
            {liveWaiting.map((p) =>
              renderWifiCard(p, { variant: 'compact', section: 'live' })
            )}
            {liveActive.map((p) =>
              renderWifiCard(p, { variant: 'compact', section: 'live' })
            )}
            {(profilesBySection.paused || []).map((p) =>
              renderWifiCard(p, { variant: 'warning', section: 'paused' })
            )}
            {sortedTerminated.map((p) =>
              renderWifiCard(p, { variant: 'default', section: 'terminated' })
            )}
          </div>
        )}

        <BottomActionBar sticky>
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
      </PageShell>
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
