import React, { useState, useMemo, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, ChevronDown, ChevronUp, Plus, Minus, HelpCircle, X, Camera, Image as ImageIcon, Edit3, Trash2 } from 'lucide-react';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
import ConfirmModal from '../components/common/ConfirmModal';
import PwModal from '../components/common/PwModal.jsx';
import ServiceRequestService from '../services/ServiceRequestService';
import './ServiceRequest.css';

// 신청 가능 서비스 카테고리
const SERVICE_CATEGORIES = [
  {
    key: 'wifi',
    title: '와이파이 서비스등록',
    bullets: [
      'PathWave WiFi 서비스는 매장 방문 고객이 더욱 쉽고 빠르게 무선 네트워크에 연결할 수 있도록 지원합니다.',
      '설치 위치에 따라 여러 개의 WiFi 장치가 운영될 수 있습니다.',
      '서비스 설치 후 위치 기반 혜택 및 이벤트 기능을 사용할 수 있습니다.',
    ],
  },
  {
    key: 'stamp',
    title: '스탬프 서비스이용',
    bullets: [
      'PathWave WiFi 서비스 이용 시 추가로 이용 가능한 서비스입니다.',
      '매장 방문 / 결제 시 고객에게 스탬프를 적립해 주고, 일정 개수가 모이면 쿠폰 또는 혜택으로 자동 전환됩니다.',
      '스탬프 정책(적립 조건, 만료일, 보상 쿠폰)은 PathWave 운영자 콘솔에서 매장별로 설정합니다.',
    ],
  },
  {
    key: 'event',
    title: '쿠폰 서비스이용',
    bullets: [
      'PathWave WiFi 서비스 이용 시 추가로 이용 가능한 서비스입니다.',
      '매장 내 특정 위치에 방문한 고객에게 쿠폰 또는 혜택을 자동으로 제공할 수 있습니다.',
      '쿠폰 발급 시 별도의 알림 비용은 발생하지 않습니다.',
    ],
  },
  {
    key: 'noti',
    title: '알림 서비스이용',
    bullets: [
      'PathWave WiFi 서비스 이용 시 추가로 이용 가능한 서비스입니다.',
      '매장 공지 등 별도 알림을 발송할 수 있는 서비스입니다.',
      '알림은 100개 단위로 구매할 수 있습니다.',
    ],
  },
];

const WIFI_NOTICES = [
  '설치할 WiFi 자동접속 서비스 수량을 입력해 주세요.',
  '객실별로 별도의 WiFi 비밀번호를 제공하는 경우, 객실당 1개의 서비스가 필요합니다.',
  '여러 대의 WiFi 를 공용으로 운영하는 경우 출입구에만 설치해도 서비스를 이용할 수 있습니다.\n예) 카페 등 여러 층 공용 WiFi 를 한 번에 연결하려면 각 층 출입구에 1개씩 설치하면 됩니다.',
  '서비스 신청 후 WiFi 상세 정보를 입력해 주세요.',
];

// 시작일 + 2년 → 종료일
const calcEndDate = (startStr) => {
  if (!startStr) return '';
  const d = new Date(startStr);
  if (Number.isNaN(d.getTime())) return '';
  d.setFullYear(d.getFullYear() + 2);
  return d.toISOString().slice(0, 10);
};

// 빈 와이파이 아이템 — status 모델 포함
// NOTE: memo (설치 관련 메모) 는 사장님 신청 플로우에서는 제거.
//       향후 설치기사/슈퍼어드민 화면에서 별도 설계.
const makeEmptyWifi = (idSeed) => ({
  id: idSeed,
  location: '',
  ssid: '',
  password: '',
  startDate: '',
  endDate: '',
  contractPeriod: '2_YEAR',
  imageUrl: null,
  endDateManual: false,
  status: 'empty', // 'empty' | 'editing' | 'completed' | 'error'
});

// 필수값 검증
const isWifiItemFilled = (item) =>
  !!(item.location && item.ssid && item.password && item.startDate && item.endDate);

// P6 (2026-05-26): 미사용 OCR 패턴 추출 헬퍼 (SSID_PATTERNS / PW_PATTERNS /
// extractWifiInfoFromText) 제거. 실 OCR 도입 시 (Phase 2+) Tesseract.js
// 또는 백엔드 OCR API 응답을 그대로 사용.

const ServiceRequest = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // 쿼리 파라미터 ?type=wifi|stamp|event|noti 로 진입하면 해당 상세 단계로 점프
  const initialType = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return params.get('type') || '';
  }, [location.search]);

  const [step, setStep] = useState(initialType || 'category');
  const [categoryKey, setCategoryKey] = useState(initialType || 'wifi');
  const [showCategoryDropdown, setShowCategoryDropdown] = useState(false);

  // GNB '서비스 신청' 메뉴 재탭 시 카테고리 리스트로 복귀
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const t = params.get('type');
    if (t) {
      setCategoryKey(t);
      setStep(t);
    } else {
      setStep('category');
    }
    setShowCategoryDropdown(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.key]);

  // 와이파이 단계
  const [quantity, setQuantity] = useState(2);
  const [quantityConfirmed, setQuantityConfirmed] = useState(false);
  const [wifiItems, setWifiItems] = useState([]);
  const [expandedIndex, setExpandedIndex] = useState(null);

  // 모달 / 알럿
  const [addConfirmOpen, setAddConfirmOpen] = useState(false);
  const [resetConfirmIdx, setResetConfirmIdx] = useState(null); // 재작성 confirm 대상 idx
  const [removeConfirmIdx, setRemoveConfirmIdx] = useState(null); // 삭제 confirm 대상 idx
  const [saveErrorMsg, setSaveErrorMsg] = useState(null); // 저장 검증 실패
  const [nextConfirmOpen, setNextConfirmOpen] = useState(false); // 신청내역 진입 1차 확인
  const [showApplicationModal, setShowApplicationModal] = useState(false);

  // P6 (2026-05-26): mock OCR 제거 — 정직한 수동입력. SSID/PW 는 점주가 직접 입력.

  // 결제 단계 (mock)
  const [card] = useState({
    name: '나라카드',
    no: '1234 - 2345 - 3456 - 4567',
    mmyy: '05/27',
    cvc: '123',
    familyName: 'Shin',
    firstName: 'nara',
  });
  const [period] = useState({ start: '2021.02.13', end: '2023.02.12', payment: '1,024,100원 / 월', billDay: '매월 12일 결제' });
  const [email] = useState('ceo@hotelh.com');

  const [confirmMsg, setConfirmMsg] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const selectedCategory = SERVICE_CATEGORIES.find((c) => c.key === categoryKey);
  const isDetailStep = (s) => ['wifi', 'stamp', 'event', 'noti'].includes(s);

  // 모든 카드 입력완료 (저장 통과) — 다음 버튼 노출 조건
  const allCompleted =
    quantityConfirmed &&
    wifiItems.length > 0 &&
    wifiItems.length === quantity &&
    wifiItems.every((it) => it.status === 'completed');

  // ── 핸들러 ──
  const handleBack = () => {
    if (isDetailStep(step)) setStep('category');
    else if (step === 'payment') setStep(categoryKey);
    else navigate(-1);
  };

  const handleNextOnNonWifi = () => {
    if (step === 'category') setStep(categoryKey);
    else if (isDetailStep(step)) setStep('payment');
  };

  const goToCategory = (key) => {
    setCategoryKey(key);
    setStep(key);
  };

  // 수량 확정
  const handleConfirmQuantity = () => {
    setQuantityConfirmed(true);
    setWifiItems((prev) => {
      if (prev.length >= quantity) return prev.slice(0, quantity);
      const need = quantity - prev.length;
      const additions = Array.from({ length: need }, (_, i) => makeEmptyWifi(Date.now() + i));
      return [...prev, ...additions];
    });
    setExpandedIndex(0);
  };

  // 추가하기 confirm
  const handleAddClick = () => setAddConfirmOpen(true);
  const handleAddConfirm = () => {
    setWifiItems((prev) => {
      const next = [...prev, makeEmptyWifi(Date.now())];
      setExpandedIndex(next.length - 1);
      return next;
    });
    setQuantity((q) => q + 1);
    setAddConfirmOpen(false);
  };

  // 삭제 — confirm 알럿
  const handleRemoveClick = (idx) => {
    if (wifiItems.length <= 1) {
      setSaveErrorMsg('최소 1개의 와이파이는 유지되어야 합니다. 삭제 대신 재작성을 사용하세요.');
      return;
    }
    setRemoveConfirmIdx(idx);
  };
  const handleRemoveConfirmed = () => {
    const idx = removeConfirmIdx;
    if (idx == null) return;
    setWifiItems((prev) => prev.filter((_, i) => i !== idx));
    setQuantity((q) => Math.max(1, q - 1));
    setExpandedIndex(null);
    setRemoveConfirmIdx(null);
  };

  // 재작성 — confirm 알럿
  const handleResetClick = (idx) => setResetConfirmIdx(idx);
  const handleResetConfirmed = () => {
    const idx = resetConfirmIdx;
    if (idx == null) return;
    setWifiItems((prev) =>
      prev.map((it, i) =>
        i === idx
          ? { ...makeEmptyWifi(it.id) }
          : it
      )
    );
    setResetConfirmIdx(null);
  };

  // 카드 펼침 토글 (한 번에 하나만)
  const toggleExpand = (idx) => {
    setExpandedIndex((prev) => (prev === idx ? null : idx));
  };

  // 필드 업데이트 — 입력 시 status='editing' 으로 자동 전환
  const updateField = (idx, field, value) => {
    setWifiItems((prev) =>
      prev.map((item, i) => {
        if (i !== idx) return item;
        let updated = { ...item };
        if (field === 'startDate') {
          updated.startDate = value;
          if (!item.endDateManual) updated.endDate = calcEndDate(value);
        } else if (field === 'endDate') {
          updated.endDate = value;
          updated.endDateManual = true;
        } else {
          updated[field] = value;
        }
        // 상태: completed/error → editing 으로 되돌림 (사용자가 다시 수정 시작)
        if (updated.status === 'completed' || updated.status === 'error') {
          updated.status = 'editing';
        } else if (updated.status === 'empty') {
          updated.status = 'editing';
        }
        return updated;
      })
    );
  };

  // 저장 — 해당 카드 검증 → completed 또는 error
  const handleSaveWifi = (idx) => {
    const item = wifiItems[idx];
    if (!item) return;
    if (!isWifiItemFilled(item)) {
      const missing = [];
      if (!item.location) missing.push('설치위치');
      if (!item.ssid) missing.push('와이파이 ID');
      if (!item.password) missing.push('와이파이 PW');
      if (!item.startDate) missing.push('서비스 시작일');
      if (!item.endDate) missing.push('서비스 종료일');
      setWifiItems((prev) => prev.map((it, i) => (i === idx ? { ...it, status: 'error' } : it)));
      setSaveErrorMsg(`Wi-Fi ${idx + 1} 카드의 필수 정보가 누락되었습니다.\n(${missing.join(' / ')})`);
      return;
    }
    setWifiItems((prev) => prev.map((it, i) => (i === idx ? { ...it, status: 'completed' } : it)));

    // 저장 후: 다음 미입력 카드 자동 펼침. 없으면 접기
    setTimeout(() => {
      setWifiItems((latest) => {
        const nextIdx = latest.findIndex((it, i) => i !== idx && it.status !== 'completed');
        setExpandedIndex(nextIdx >= 0 ? nextIdx : null);
        return latest;
      });
    }, 0);
  };

  // ── 사진 선택 / 제거 ──
  // P6 (2026-05-26): mock OCR 자동입력 제거. 사진은 참고용으로만 저장하고
  // SSID / 비밀번호는 점주가 직접 입력. 실 OCR 도입 시 (Phase 2+) 별도 PR.
  const handleImageChangeForCard = (idx) => (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    setWifiItems((prev) => prev.map((it, i) => (i === idx ? { ...it, imageUrl: url } : it)));
    const inputEl = e.target;
    setTimeout(() => { if (inputEl) inputEl.value = ''; }, 0);
  };

  const handleRemoveImage = (idx) => {
    setWifiItems((prev) => prev.map((it, i) => (i === idx ? { ...it, imageUrl: null } : it)));
  };

  // 다음 → 1차 확인 알럿 → 신청내역 팝업
  const handleNextClick = () => {
    setNextConfirmOpen(true);
  };
  const handleNextConfirmed = () => {
    setNextConfirmOpen(false);
    setShowApplicationModal(true);
  };

  // 신청내역 팝업 → 결제하기
  const handleGoPayment = () => {
    const payload = {
      facilityId: null,
      storeId: null,
      quantity,
      contractType: '2_YEAR',
      wifiItems: wifiItems.map((it) => ({
        installLocation: it.location,
        wifiId: it.ssid,
        wifiPassword: it.password,
        startDate: it.startDate,
        endDate: it.endDate,
        contractPeriod: it.contractPeriod,
        imageUrl: it.imageUrl,
        status: it.status,
      })),
      paymentStatus: 'PENDING',
      applicationStatus: 'DRAFT',
    };
    // TODO: 백엔드 연동 — POST /api/service-requests (draft 저장 + imageUrl 은 별도 업로드 후 URL 회신)
    console.log('[ServiceRequest] go to payment with', payload);
    setShowApplicationModal(false);
    setStep('payment');
  };

  const handleSubmit = () => {
    setConfirmMsg('서비스를 신청하시겠어요?\n신청 후 운영팀에서 검토하고 연락드립니다.');
  };

  const doSubmit = async () => {
    setConfirmMsg(null);
    // P-A: 신청 내역(설치위치 + WiFi)을 백엔드에 저장 → 슈퍼어드민이 비콘 매칭.
    try {
      await ServiceRequestService.submit({
        serviceType: categoryKey,
        wifiItems,
      });
      setSubmitted(true);
    } catch (err) {
      setConfirmMsg(err?.message || '신청 접수 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.');
    }
  };

  // 카드 헤더 status 라벨
  const statusLabel = (s) => {
    if (s === 'completed') return '입력완료';
    if (s === 'error') return '오류';
    if (s === 'editing') return '입력중';
    return '미입력';
  };

  // ═══════════════════════════════════════
  // STEP 1 — 카테고리 선택
  // ═══════════════════════════════════════
  if (step === 'category') {
    return (
      <div className="sr-page">
        {/* 최상위 단계 — GNB 탭으로 접근 가능하므로 back 버튼 노출 X.
            내부 단계 (wifi/stamp/event/noti/payment) 에서만 back 사용. */}
        <header className="sr-header sr-header--top">
          <h1 className="sr-title">서비스 신청</h1>
        </header>

        <div className="sr-body">
          {SERVICE_CATEGORIES.map((cat) => (
            <button
              key={cat.key}
              className={`sr-cat-block ${categoryKey === cat.key ? 'active' : ''}`}
              onClick={() => goToCategory(cat.key)}
            >
              <div className="sr-cat-head">
                <span className="sr-cat-title">{cat.title}</span>
                <ChevronRight size={18} className="sr-cat-arrow" />
              </div>
              <div className="sr-cat-body">
                <span className="sr-cat-help">
                  <HelpCircle size={20} />
                </span>
                <ul className="sr-cat-bullets">
                  {cat.bullets.map((b, i) => <li key={i}>{b}</li>)}
                </ul>
              </div>
            </button>
          ))}
        </div>

        <ConfirmModal
          isOpen={submitted}
          title="신청 완료"
          desc={"신청이 접수되었습니다.\n운영팀 검토 후 등록한 연락처로 안내드립니다."}
          singleButton confirmText="확인"
          onConfirm={() => { setSubmitted(false); navigate('/dashboard'); }}
          onCancel={() => { setSubmitted(false); navigate('/dashboard'); }}
        />
      </div>
    );
  }

  // ═══════════════════════════════════════
  // STEP 2 — 와이파이 신청 상세 (개별 등록 + 아코디언)
  // ═══════════════════════════════════════
  if (step === 'wifi') {
    return (
      <div className="sr-page">
        <header className="sr-header">
          <button className="sr-back" onClick={handleBack} aria-label="뒤로 가기">
            <ChevronLeft size={22} />
          </button>
          <h1 className="sr-title">와이파이 서비스등록</h1>
        </header>

        <div className="sr-body">
          {/* 카테고리 헤더 — 1:1 매핑이므로 dropdown 으로 변경 X.
              사용자 요구 (2026-05-10): "아코디언에서 서비스 변경하면서 신청하게 안해도 됨". */}

          {/* Quantity stepper + 확인 */}
          <div className="sr-qty-row">
            <span className="sr-qty-label">Quantity</span>
            <div className="sr-qty-control">
              <button className="sr-qty-btn" onClick={() => setQuantity((q) => Math.max(1, q - 1))} aria-label="수량 감소" disabled={quantityConfirmed}>
                <Minus size={16} />
              </button>
              <span className="sr-qty-value">{String(quantity).padStart(2, '0')}</span>
              <button className="sr-qty-btn" onClick={() => setQuantity((q) => Math.min(99, q + 1))} aria-label="수량 증가" disabled={quantityConfirmed}>
                <Plus size={16} />
              </button>
            </div>
            {!quantityConfirmed ? (
              <button className="sr-qty-confirm" onClick={handleConfirmQuantity}>확인</button>
            ) : (
              <button className="sr-qty-confirm ghost" onClick={() => setQuantityConfirmed(false)}>수량 변경</button>
            )}
          </div>

          {/* 안내 */}
          <ul className="sr-notices">
            {WIFI_NOTICES.map((n, i) => <li key={i}>{n}</li>)}
          </ul>

          {/* 수량 확정 후 등록 영역 */}
          {quantityConfirmed && (
            <>
              <div className="sr-quantity-display">
                선택 수량은 <strong>{quantity}개</strong>입니다.
              </div>

              <div className="sr-individual">
                {wifiItems.map((item, idx) => {
                  const isOpen = expandedIndex === idx;
                  return (
                    <div key={item.id} className={`sr-acc-card ${isOpen ? 'open' : ''} sr-acc-status-${item.status}`}>
                      <div
                        role="button"
                        tabIndex={0}
                        className="sr-acc-head"
                        onClick={() => toggleExpand(idx)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleExpand(idx); }
                        }}
                        aria-expanded={isOpen}
                      >
                        <div className="sr-acc-head-main">
                          <span className="sr-acc-num">Wi-Fi {idx + 1}</span>
                          <div className="sr-acc-head-info">
                            <span className={`sr-acc-loc ${item.location ? '' : 'empty'}`}>
                              {item.location || '설치위치 미입력'}
                            </span>
                            <span className={`sr-acc-ssid ${item.ssid ? '' : 'empty'}`}>
                              {item.ssid || 'ID 미입력'}
                            </span>
                          </div>
                          <span className={`sr-acc-status ${item.status}`}>
                            {statusLabel(item.status)}
                          </span>
                        </div>
                        {/* 우측 액션: completed && collapsed → [수정][삭제] / 그 외 → chevron */}
                        {item.status === 'completed' && !isOpen ? (
                          <div className="sr-acc-head-actions" onClick={(e) => e.stopPropagation()}>
                            <button
                              type="button"
                              className="sr-acc-head-btn"
                              onClick={() => setExpandedIndex(idx)}
                              aria-label="수정"
                            >
                              <Edit3 size={14} />
                              <span>수정</span>
                            </button>
                            <button
                              type="button"
                              className="sr-acc-head-btn danger"
                              onClick={() => handleRemoveClick(idx)}
                              aria-label="삭제"
                            >
                              <Trash2 size={14} />
                              <span>삭제</span>
                            </button>
                          </div>
                        ) : (
                          isOpen
                            ? <ChevronUp size={18} className="sr-acc-toggle" />
                            : <ChevronDown size={18} className="sr-acc-toggle" />
                        )}
                      </div>

                      {isOpen && (
                        <div className="sr-acc-body">
                          <div className="wifi-field-group">
                            <label className="wifi-field-label">설치 위치 *</label>
                            <input
                              type="text"
                              className="wifi-field-input"
                              placeholder="설치하려는 와이파이 위치를 입력하세요"
                              value={item.location}
                              onChange={(e) => updateField(idx, 'location', e.target.value)}
                            />
                            <span className="wifi-field-hint">예) 1층 로비, 2층 카페, 5001호</span>
                          </div>

                          {/* 사진 미리보기 영역 — 기존 와이파이 입력/수정 화면과 동일 */}
                          <div className="wifi-photo-area sr-acc-photo-area">
                            {item.imageUrl ? (
                              <div className="wifi-photo-preview">
                                <img src={item.imageUrl} alt={`Wi-Fi ${idx + 1} 공유기 사진`} />
                                <button
                                  type="button"
                                  className="wifi-photo-remove"
                                  onClick={(e) => { e.stopPropagation(); handleRemoveImage(idx); }}
                                  aria-label="사진 제거"
                                >
                                  <X size={16} />
                                </button>
                              </div>
                            ) : (
                              <div className="wifi-photo-placeholder">
                                <div className="wifi-photo-icon">
                                  <Camera size={28} color="var(--pw-primary)" />
                                </div>
                                <p className="wifi-photo-title">공유기 뒷면의 와이파이정보를 촬영하세요!</p>
                                <p className="wifi-photo-desc">※ 직접입력하기 어려우실 경우 공유기 뒷면의 와이파이 정보를 촬영하시면 입력을 도와드립니다!</p>
                              </div>
                            )}
                          </div>

                          {/* 사진 액션 — 사진 영역 아래 (기존 화면과 동일) */}
                          <div className="wifi-photo-actions sr-acc-photo">
                            <label className="wifi-photo-action">
                              <ImageIcon size={16} /> 앨범에서 선택
                              <input
                                type="file"
                                accept="image/jpeg,image/png,image/webp,image/heic,image/heif,image/gif"
                                onChange={handleImageChangeForCard(idx)}
                                className="wifi-photo-action-input"
                              />
                            </label>
                            <label className="wifi-photo-action">
                              <Camera size={16} /> 카메라 촬영
                              <input
                                type="file"
                                accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
                                capture="environment"
                                onChange={handleImageChangeForCard(idx)}
                                className="wifi-photo-action-input"
                              />
                            </label>
                          </div>
                          {/* P6: OCR 자동입력 제거 — SSID/PW 는 수동 입력 (사진은 참고용) */}
                          {item.imageUrl && (
                            <div className="wifi-ocr-status sr-acc-ocr">
                              ⓘ 사진은 참고용입니다. ID 와 비밀번호는 아래에 직접 입력해 주세요.
                            </div>
                          )}

                          <div className="wifi-field-group">
                            <label className="wifi-field-label">ID *</label>
                            <input
                              type="text"
                              className="wifi-field-input"
                              placeholder="해당와이파이의 ID를 입력해 주세요"
                              value={item.ssid}
                              onChange={(e) => updateField(idx, 'ssid', e.target.value)}
                            />
                            <span className="wifi-field-hint">예) kt5g_1234789</span>
                          </div>

                          <div className="wifi-field-group">
                            <label className="wifi-field-label">PW *</label>
                            <input
                              type="text"
                              className="wifi-field-input"
                              placeholder="해당와이파이의 비밀번호를 입력해 주세요"
                              value={item.password}
                              onChange={(e) => updateField(idx, 'password', e.target.value)}
                            />
                            <span className="wifi-field-hint">예) ezddd1@3356</span>
                          </div>

                          <div className="sr-acc-row2">
                            <div className="wifi-field-group">
                              <label className="wifi-field-label">서비스 시작일 *</label>
                              <input
                                type="date"
                                className="wifi-field-input"
                                value={item.startDate}
                                onChange={(e) => updateField(idx, 'startDate', e.target.value)}
                              />
                            </div>
                            <div className="wifi-field-group">
                              <label className="wifi-field-label">서비스 종료일 *</label>
                              <input
                                type="date"
                                className="wifi-field-input"
                                value={item.endDate}
                                onChange={(e) => updateField(idx, 'endDate', e.target.value)}
                              />
                            </div>
                          </div>

                          <div className="wifi-field-group sr-acc-last-field">
                            <label className="wifi-field-label">약정기간</label>
                            <p className="sr-acc-readonly">2년 약정 · 시작일 + 2년 자동 설정 (종료일 직접 수정 가능)</p>
                          </div>

                          {/* HIG/MD3 우선순위 — Primary: 저장 / Secondary: 재작성 / Destructive(삭제) 는 저장 후 헤더에서만 노출 */}
                          <div className="sr-acc-actions">
                            <Button variant="outline" onClick={() => handleResetClick(idx)}>재작성</Button>
                            <Button variant="primary" onClick={() => handleSaveWifi(idx)}>저장</Button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}

                <button type="button" className="sr-add-card" onClick={handleAddClick}>
                  <Plus size={20} />
                  <span>추가하기</span>
                </button>
              </div>
            </>
          )}
        </div>

        {/* 다음 버튼 — 모든 카드 입력완료(저장됨) 시에만 노출 */}
        {allCompleted && (
          <BottomActionBar>
            <Button variant="primary" fullWidth onClick={handleNextClick}>다음</Button>
          </BottomActionBar>
        )}

        {/* 추가하기 confirm */}
        <ConfirmModal
          isOpen={addConfirmOpen}
          title="와이파이 추가"
          desc={`현재 선택 수량은 ${quantity}개입니다.\n1개를 추가하시겠습니까?`}
          confirmText="추가"
          cancelText="취소"
          onConfirm={handleAddConfirm}
          onCancel={() => setAddConfirmOpen(false)}
        />

        {/* 재작성 confirm */}
        <ConfirmModal
          isOpen={resetConfirmIdx != null}
          title="입력 내용 초기화"
          desc={'입력한 와이파이 정보를 초기화하시겠습니까?\n사진 / 위치 / ID / PW / 서비스 기간이 모두 비워집니다.'}
          confirmText="초기화"
          cancelText="취소"
          onConfirm={handleResetConfirmed}
          onCancel={() => setResetConfirmIdx(null)}
        />

        {/* 삭제 confirm — 저장된 와이파이만 삭제 동작이 노출되므로 destructive 강조 */}
        <ConfirmModal
          isOpen={removeConfirmIdx != null}
          title="와이파이 삭제"
          desc={'등록된 와이파이를 삭제하시겠습니까?\n선택 수량도 1개 감소합니다.'}
          confirmText="삭제"
          cancelText="취소"
          onConfirm={handleRemoveConfirmed}
          onCancel={() => setRemoveConfirmIdx(null)}
        />

        {/* 저장 검증 실패 / 안내 */}
        <ConfirmModal
          isOpen={!!saveErrorMsg}
          title="입력 정보 확인"
          desc={saveErrorMsg || ''}
          singleButton confirmText="확인"
          onConfirm={() => setSaveErrorMsg(null)}
          onCancel={() => setSaveErrorMsg(null)}
        />

        {/* 다음 버튼 — 신청내역 진입 1차 확인 */}
        <ConfirmModal
          isOpen={nextConfirmOpen}
          title="신청 정보 확인"
          desc={'입력한 와이파이 정보가 정확한지 확인해 주세요.\n신청 후 정보가 잘못된 경우 설치 및 비콘 배송이 지연될 수 있습니다.\n신청내역을 확인하시겠습니까?'}
          confirmText="확인"
          cancelText="취소"
          onConfirm={handleNextConfirmed}
          onCancel={() => setNextConfirmOpen(false)}
        />

        {/* 신청내역 팝업 */}
        <PwModal
          open={showApplicationModal}
          onClose={() => setShowApplicationModal(false)}
          title="와이파이 서비스 신청내역 확인"
          size="md"
          footer={
            <>
              <button className="sr-app-modal-btn" onClick={() => setShowApplicationModal(false)}>닫기</button>
              <button className="sr-app-modal-btn primary" onClick={handleGoPayment}>결제하기</button>
            </>
          }
        >
          <div className="sr-app-modal-body">
            <div className="sr-app-summary">
              <div className="sr-app-summary-row">
                <span className="sr-app-summary-label">신청 시설</span>
                {/* TODO: 실 매장 정보 연동 — 현재는 mock 표시 */}
                <span className="sr-app-summary-value">호텔H 본점</span>
              </div>
              <div className="sr-app-summary-row">
                <span className="sr-app-summary-label">총 신청 수량</span>
                <span className="sr-app-summary-value"><strong>{quantity}개</strong></span>
              </div>
              <div className="sr-app-summary-row">
                <span className="sr-app-summary-label">약정기간</span>
                <span className="sr-app-summary-value">2년</span>
              </div>
              <div className="sr-app-summary-row">
                <span className="sr-app-summary-label">예상 결제금액</span>
                <span className="sr-app-summary-value sr-app-amount">월 {(quantity * 12100).toLocaleString()}원 <span className="sr-app-vat">(VAT 포함)</span></span>
              </div>
            </div>

            <h4 className="sr-app-list-title">와이파이 목록</h4>
            <div className="sr-app-list">
              {wifiItems.map((item, idx) => (
                <div key={item.id} className="sr-app-list-row">
                  <div className="sr-app-list-num">Wi-Fi {idx + 1}</div>
                  <div className="sr-app-list-fields">
                    <div className="sr-app-list-line">
                      <span className="sr-app-list-label">위치</span>
                      <span className="sr-app-list-value">{item.location}</span>
                    </div>
                    <div className="sr-app-list-line">
                      <span className="sr-app-list-label">SSID</span>
                      <span className="sr-app-list-value">{item.ssid}</span>
                    </div>
                    <div className="sr-app-list-line">
                      <span className="sr-app-list-label">기간</span>
                      <span className="sr-app-list-value">{item.startDate} ~ {item.endDate}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </PwModal>
      </div>
    );
  }

  // ═══════════════════════════════════════
  // STEP 2-B — 스탬프 / 쿠폰(event) / 알림
  // ═══════════════════════════════════════
  if (step === 'stamp' || step === 'event' || step === 'noti') {
    const cat = SERVICE_CATEGORIES.find((c) => c.key === step);
    return (
      <div className="sr-page">
        <header className="sr-header">
          <button className="sr-back" onClick={handleBack} aria-label="뒤로 가기">
            <ChevronLeft size={22} />
          </button>
          <h1 className="sr-title">{cat?.title || '서비스 신청'}</h1>
        </header>

        <div className="sr-body">
          {/* 카테고리 dropdown 제거 (2026-05-10): 1:1 매핑 — 진입 시 해당 서비스만 노출. */}

          <ul className="sr-notices">
            {cat?.bullets.map((b, i) => <li key={i}>{b}</li>)}
          </ul>

          <div className="sr-soon-note">
            상세 설정은 서비스 신청 후 슈퍼어드민에서 매장별로 진행합니다.
          </div>
        </div>

        <BottomActionBar>
          <Button variant="primary" fullWidth onClick={handleNextOnNonWifi}>다음</Button>
        </BottomActionBar>
      </div>
    );
  }

  // ═══════════════════════════════════════
  // STEP 3 — 결제 / 약정
  // ═══════════════════════════════════════
  if (step === 'payment') {
    return (
      <div className="sr-page">
        <header className="sr-header">
          <button className="sr-back" onClick={handleBack} aria-label="뒤로 가기">
            <ChevronLeft size={22} />
          </button>
          <h1 className="sr-title">결제</h1>
        </header>

        <div className="sr-body">
          <section className="sr-pay-section">
            <h2 className="sr-pay-section-title">{selectedCategory?.title} 신청내역</h2>
            <button className="sr-pay-summary" onClick={() => setStep(categoryKey)}>
              <span>{categoryKey === 'wifi' ? `${quantity}개의 서비스이용 예정입니다.` : '서비스 신청 예정입니다.'}</span>
              <ChevronRight size={18} />
            </button>
          </section>

          <section className="sr-pay-section">
            <h2 className="sr-pay-section-title">결제방법</h2>
            <div className="sr-pay-card">
              <div className="sr-pay-row"><span className="sr-pay-label">Card Name</span><span className="sr-pay-value">{card.name}</span><ChevronDown size={16} className="sr-pay-row-arrow" /></div>
              <div className="sr-pay-row"><span className="sr-pay-label">Card No</span><span className="sr-pay-value">{card.no}</span></div>
              <div className="sr-pay-row sr-pay-row-split">
                <div><span className="sr-pay-label">MM/YY</span><span className="sr-pay-value">{card.mmyy}</span></div>
                <div><span className="sr-pay-label">CVC</span><span className="sr-pay-value">{card.cvc} ⓘ</span></div>
              </div>
              <div className="sr-pay-row sr-pay-row-split">
                <div><span className="sr-pay-label">Family Name</span><span className="sr-pay-value">{card.familyName}</span></div>
                <div><span className="sr-pay-label">Name</span><span className="sr-pay-value">{card.firstName}</span></div>
              </div>
            </div>
          </section>

          <section className="sr-pay-section">
            <h2 className="sr-pay-section-title">서비스기간</h2>
            <div className="sr-pay-card">
              <div className="sr-pay-row">
                <span className="sr-pay-label">Period</span>
                <span className="sr-pay-value">{period.start} ~ {period.end}</span>
                <button className="sr-pay-row-action">변경</button>
              </div>
              <p className="sr-pay-note">※ 최초 2년 약정이며, 2년 이후 1년 단위로 추가 할 수 있습니다.</p>
              <div className="sr-pay-row">
                <span className="sr-pay-label">Payment</span>
                <span className="sr-pay-value">{period.payment} <span className="sr-pay-vat">(VAT 포함)</span></span>
              </div>
              <p className="sr-pay-note">※ {period.billDay}</p>
            </div>
          </section>

          <section className="sr-pay-section">
            <h2 className="sr-pay-section-title">결제안내메일</h2>
            <div className="sr-pay-card">
              <div className="sr-pay-row">
                <span className="sr-pay-label">E-Mail</span>
                <span className="sr-pay-value sr-pay-email">{email}</span>
                <button className="sr-pay-row-action">이메일 변경</button>
              </div>
              <p className="sr-pay-note">※ 결제 및 공지 안내 메일 입니다.</p>
            </div>
          </section>
        </div>

        <BottomActionBar>
          <Button variant="outline" fullWidth onClick={() => setStep(categoryKey)}>이전 단계</Button>
          <Button variant="primary" fullWidth onClick={handleSubmit}>서비스 신청</Button>
        </BottomActionBar>

        <ConfirmModal
          isOpen={!!confirmMsg}
          title="서비스 신청"
          desc={confirmMsg || ''}
          confirmText="신청"
          cancelText="취소"
          onConfirm={doSubmit}
          onCancel={() => setConfirmMsg(null)}
        />
        <ConfirmModal
          isOpen={submitted}
          title="신청 완료"
          desc={"신청이 접수되었습니다.\n운영팀 검토 후 등록한 연락처로 안내드립니다."}
          singleButton confirmText="확인"
          onConfirm={() => { setSubmitted(false); navigate('/dashboard/wifi'); }}
          onCancel={() => { setSubmitted(false); navigate('/dashboard/wifi'); }}
        />
      </div>
    );
  }

  return null;
};

export default ServiceRequest;
