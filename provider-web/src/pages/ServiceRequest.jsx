import React, { useState, useMemo, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, ChevronDown, ChevronUp, Plus, Minus, HelpCircle, X } from 'lucide-react';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
import ConfirmModal from '../components/common/ConfirmModal';
import './ServiceRequest.css';

// 신청 가능 서비스 카테고리 (시안 4번 + 스탬프)
const SERVICE_CATEGORIES = [
  {
    key: 'wifi',
    title: '와이파이 서비스등록',
    bullets: [
      '와이파이 서비스는 BE 서비스를 이용하는 사용자가 서비스시설에 들어왔을 경우 자동으로 서비스시설에서 제공중인 와이파이에 자동으로 접속하게 해주는 서비스 입니다.',
      '서비스 시설에 와이파이 제공 중계기가 여러대가 있어도 서비스에 가입하신 후 정보를 입력하시면 서비스 이용자는 한번의 인증으로 서비스 중인 와이파이를 끊김없이 이용할 수 있습니다.',
      '와이파이 서비스 설치 후 설치 위치별 이벤트 또는 혜택(쿠폰)을 사용자에게 알림 발송할 수 있습니다.',
    ],
  },
  {
    key: 'stamp',
    title: '스탬프 서비스이용',
    sample: 'SAMPLE',
    bullets: [
      '본 서비스는 와이파이 서비스 이용시 추가로 이용이 가능한 서비스 입니다.',
      '매장 방문 / 결제 시 사용자에게 스탬프를 적립해 주고, 일정 개수 모이면 쿠폰 / 혜택으로 자동 전환할 수 있습니다.',
      '스탬프 정책(적립 조건, 만료일, 보상 쿠폰)은 슈퍼어드민에서 매장별로 설정합니다.',
    ],
  },
  {
    key: 'event',
    title: '이벤트 서비스이용',
    sample: 'SAMPLE',
    bullets: [
      '본 서비스는 와이파이 서비스 이용시 추가로 이용이 가능한 서비스 입니다.',
      '서비스 시설에서 특정 위치에 방문하였을 경우 쿠폰 및 혜택을 제공할 수 있는 서비스 입니다.',
      '서비스 이용시 별도의 알림 비용은 발생하지 않습니다.',
    ],
  },
  {
    key: 'noti',
    title: '알림 서비스이용',
    sample: 'SAMPLE',
    bullets: [
      '본 서비스는 와이파이 서비스 이용시 추가로 이용이 가능한 서비스 입니다.',
      '서비스 시설에서 사용자에게 발송할 수 있는 알림 수로 공지 등 별도의 알림을 받을 경우 이용하실 수 있습니다.',
      '알림은 100개 단위로 구매가능합니다.',
    ],
  },
];

const WIFI_NOTICES = [
  '와이파이 자동접속 서비스 설치 수량을 입력하세요',
  '특정객실 예약(이용)자에 해당객실 와이파이 비밀번호를 제공 할 경우 1개의 서비스가 필요합니다.',
  '여러대의 와이파이를 공용으로 제공 할 경우 출입구에만 설치해도 서비스 이용이 가능합니다.\n예) 카페 등 여러층의 와이파이를 사용자가 한번에 이용할 수 있도록 할 경우, 각 층별 출입구에 한개씩 설치 후 서비스 이용가능',
  '서비스 신청 후 와이파이 정보를 입력해 주세요.',
];

// 시작일 + 2년 → 종료일
const calcEndDate = (startStr) => {
  if (!startStr) return '';
  const d = new Date(startStr);
  if (Number.isNaN(d.getTime())) return '';
  d.setFullYear(d.getFullYear() + 2);
  return d.toISOString().slice(0, 10);
};

// 빈 와이파이 아이템
const makeEmptyWifi = (idSeed) => ({
  id: idSeed,
  location: '',
  ssid: '',
  password: '',
  startDate: '',
  endDate: '',
  contractPeriod: '2_YEAR',
  memo: '',
  endDateManual: false, // 사용자가 종료일을 수동 변경했는지
});

const isWifiItemComplete = (item) =>
  !!(item.location && item.ssid && item.password && item.startDate && item.endDate);

const ServiceRequest = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // 쿼리 파라미터 ?type=wifi|stamp|event|noti 로 진입하면 해당 상세 단계로 점프
  const initialType = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return params.get('type') || '';
  }, [location.search]);

  const [step, setStep] = useState(initialType || 'category'); // 'category' | 'wifi' | 'stamp' | 'event' | 'noti' | 'payment'
  const [categoryKey, setCategoryKey] = useState(initialType || 'wifi');
  const [showCategoryDropdown, setShowCategoryDropdown] = useState(false);

  // GNB '서비스 신청' 메뉴 재탭 시 카테고리 리스트로 복귀 (location.key 변경 감지)
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
  const [incompleteAlert, setIncompleteAlert] = useState(null); // { msg, idx }
  const [showApplicationModal, setShowApplicationModal] = useState(false);

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

  // ── 핸들러 ──
  const handleBack = () => {
    if (isDetailStep(step)) setStep('category');
    else if (step === 'payment') setStep(categoryKey);
    else navigate(-1);
  };

  const handleNext = () => {
    if (step === 'category') setStep(categoryKey);
    else if (step === 'wifi') openApplicationReview();
    else if (isDetailStep(step)) setStep('payment');
  };

  const goToCategory = (key) => {
    setCategoryKey(key);
    setStep(key);
  };

  // 수량 확정 — 빈 슬롯 만들어 등록 영역 노출
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

  // 추가하기 — confirm 알럿 → 확인 시 카드 추가
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

  // 카드 삭제 (수량도 같이 감소)
  const handleRemoveWifi = (idx) => {
    setWifiItems((prev) => prev.filter((_, i) => i !== idx));
    setQuantity((q) => Math.max(1, q - 1));
    setExpandedIndex(null);
  };

  // 카드 펼침 토글 (한 번에 하나만)
  const toggleExpand = (idx) => {
    setExpandedIndex((prev) => (prev === idx ? null : idx));
  };

  // 필드 업데이트 (시작일 변경 시 종료일 자동 +2년, 단 사용자가 수동 변경한 경우 유지)
  const updateField = (idx, field, value) => {
    setWifiItems((prev) =>
      prev.map((item, i) => {
        if (i !== idx) return item;
        if (field === 'startDate') {
          const updated = { ...item, startDate: value };
          if (!item.endDateManual) updated.endDate = calcEndDate(value);
          return updated;
        }
        if (field === 'endDate') {
          return { ...item, endDate: value, endDateManual: true };
        }
        return { ...item, [field]: value };
      })
    );
  };

  // 다음 → 신청내역 검증 + 팝업
  const openApplicationReview = () => {
    if (!quantityConfirmed) {
      setIncompleteAlert({ msg: '먼저 수량을 확정해 주세요.', idx: null });
      return;
    }
    const idx = wifiItems.findIndex((item) => !isWifiItemComplete(item));
    if (idx >= 0) {
      const item = wifiItems[idx];
      const missing = [];
      if (!item.location) missing.push('설치위치');
      if (!item.ssid) missing.push('와이파이 ID');
      if (!item.password) missing.push('와이파이 PW');
      if (!item.startDate) missing.push('서비스 시작일');
      if (!item.endDate) missing.push('서비스 종료일');
      setIncompleteAlert({
        msg: `Wi-Fi ${idx + 1} 카드에 누락된 항목이 있습니다.\n(${missing.join(' / ')})`,
        idx,
      });
      return;
    }
    setShowApplicationModal(true);
  };

  const handleIncompleteConfirm = () => {
    if (incompleteAlert?.idx != null) setExpandedIndex(incompleteAlert.idx);
    setIncompleteAlert(null);
  };

  // 신청내역 팝업 → 결제하기
  const handleGoPayment = () => {
    // TODO: 백엔드 API 연동 — POST /api/service-requests (draft 저장)
    // 페이로드 모양:
    // {
    //   facilityId, storeId, quantity, contractType: '2_YEAR',
    //   wifiItems: [{ installLocation, wifiId, wifiPassword, startDate, endDate, contractPeriod, memo, status }],
    //   paymentStatus: 'PENDING', applicationStatus: 'DRAFT'
    // }
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
        memo: it.memo,
        status: isWifiItemComplete(it) ? 'COMPLETE' : 'INCOMPLETE',
      })),
      paymentStatus: 'PENDING',
      applicationStatus: 'DRAFT',
    };
    console.log('[ServiceRequest] go to payment with', payload);
    setShowApplicationModal(false);
    setStep('payment');
  };

  const handleSubmit = () => {
    setConfirmMsg('서비스를 신청하시겠어요?\n신청 후 운영팀에서 검토하고 연락드립니다.');
  };

  const doSubmit = () => {
    // TODO: 백엔드 API 연동 — POST /api/service-requests (결제 후 최종 신청)
    setConfirmMsg(null);
    setSubmitted(true);
  };

  // ═══════════════════════════════════════
  // STEP 1 — 카테고리 선택
  // ═══════════════════════════════════════
  if (step === 'category') {
    return (
      <div className="sr-page">
        <header className="sr-header">
          <button className="sr-back" onClick={handleBack}><ChevronLeft size={22} /></button>
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
                {cat.sample && <span className="sr-cat-sample">{cat.sample}</span>}
                {!cat.sample && (
                  <span className="sr-cat-help">
                    <HelpCircle size={20} />
                  </span>
                )}
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
          <button className="sr-back" onClick={handleBack}><ChevronLeft size={22} /></button>
          <h1 className="sr-title">서비스 신청</h1>
        </header>

        <div className="sr-body">
          {/* 카테고리 dropdown */}
          <div className="sr-cat-select" onClick={() => setShowCategoryDropdown((v) => !v)}>
            <span className="sr-cat-select-title">{selectedCategory?.title}</span>
            <ChevronDown size={18} className={`sr-cat-select-arrow ${showCategoryDropdown ? 'open' : ''}`} />
          </div>
          {showCategoryDropdown && (
            <div className="sr-cat-dropdown">
              {SERVICE_CATEGORIES.map((c) => (
                <button
                  key={c.key}
                  className={`sr-cat-dropdown-item ${categoryKey === c.key ? 'active' : ''}`}
                  onClick={() => { setCategoryKey(c.key); setStep(c.key); setShowCategoryDropdown(false); }}
                >
                  {c.title}
                </button>
              ))}
            </div>
          )}

          {/* Quantity stepper + 확인 버튼 */}
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
                  const complete = isWifiItemComplete(item);
                  const isOpen = expandedIndex === idx;
                  return (
                    <div key={item.id} className={`sr-acc-card ${isOpen ? 'open' : ''}`}>
                      <button
                        type="button"
                        className="sr-acc-head"
                        onClick={() => toggleExpand(idx)}
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
                          <span className={`sr-acc-status ${complete ? 'done' : 'empty'}`}>
                            {complete ? '입력완료' : '미입력'}
                          </span>
                        </div>
                        {isOpen ? <ChevronUp size={18} className="sr-acc-toggle" /> : <ChevronDown size={18} className="sr-acc-toggle" />}
                      </button>

                      {isOpen && (
                        <div className="sr-acc-body">
                          <div className="sr-pf-group">
                            <label className="sr-pf-label">설치 위치 <span className="sr-pf-req">*</span></label>
                            <input
                              className="sr-input"
                              placeholder="예) 1층 로비, 2층 카페, 5001호"
                              value={item.location}
                              onChange={(e) => updateField(idx, 'location', e.target.value)}
                            />
                          </div>
                          <div className="sr-pf-group">
                            <label className="sr-pf-label">와이파이 ID (SSID) <span className="sr-pf-req">*</span></label>
                            <input
                              className="sr-input"
                              placeholder="kt5G_1234789"
                              value={item.ssid}
                              onChange={(e) => updateField(idx, 'ssid', e.target.value)}
                            />
                          </div>
                          <div className="sr-pf-group">
                            <label className="sr-pf-label">와이파이 PW <span className="sr-pf-req">*</span></label>
                            <input
                              className="sr-input"
                              placeholder="Ezddd1@3356"
                              value={item.password}
                              onChange={(e) => updateField(idx, 'password', e.target.value)}
                            />
                          </div>
                          <div className="sr-pf-row2">
                            <div className="sr-pf-group">
                              <label className="sr-pf-label">서비스 시작일 <span className="sr-pf-req">*</span></label>
                              <input
                                type="date"
                                className="sr-input"
                                value={item.startDate}
                                onChange={(e) => updateField(idx, 'startDate', e.target.value)}
                              />
                            </div>
                            <div className="sr-pf-group">
                              <label className="sr-pf-label">서비스 종료일 <span className="sr-pf-req">*</span></label>
                              <input
                                type="date"
                                className="sr-input"
                                value={item.endDate}
                                onChange={(e) => updateField(idx, 'endDate', e.target.value)}
                              />
                            </div>
                          </div>
                          <div className="sr-pf-group">
                            <label className="sr-pf-label">약정기간</label>
                            <div className="sr-pf-static">2년 (시작일 + 2년 자동 설정 · 종료일 직접 수정 가능)</div>
                          </div>
                          <div className="sr-pf-group">
                            <label className="sr-pf-label">비고</label>
                            <textarea
                              className="sr-textarea"
                              placeholder="설치 관련 메모 (선택)"
                              rows={2}
                              value={item.memo}
                              onChange={(e) => updateField(idx, 'memo', e.target.value)}
                            />
                          </div>
                          <div className="sr-acc-actions">
                            <button type="button" className="sr-acc-remove" onClick={() => handleRemoveWifi(idx)}>
                              이 와이파이 삭제
                            </button>
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

        <BottomActionBar>
          <Button variant="primary" fullWidth onClick={handleNext} disabled={!quantityConfirmed}>다음</Button>
        </BottomActionBar>

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

        {/* 누락 안내 */}
        <ConfirmModal
          isOpen={!!incompleteAlert}
          title="입력 정보 확인"
          desc={incompleteAlert?.msg || ''}
          singleButton confirmText="확인"
          onConfirm={handleIncompleteConfirm}
          onCancel={handleIncompleteConfirm}
        />

        {/* 신청내역 팝업 */}
        {showApplicationModal && (
          <div className="common-modal-overlay" onClick={() => setShowApplicationModal(false)}>
            <div className="sr-app-modal" onClick={(e) => e.stopPropagation()}>
              <header className="sr-app-modal-head">
                <h3>와이파이 서비스 신청내역 확인</h3>
                <button className="sr-app-modal-close" onClick={() => setShowApplicationModal(false)} aria-label="닫기">
                  <X size={18} />
                </button>
              </header>
              <div className="sr-app-modal-body">
                <div className="sr-app-summary">
                  <div className="sr-app-summary-row">
                    <span className="sr-app-summary-label">신청 시설</span>
                    <span className="sr-app-summary-value">호텔H 본점 (Mock)</span>
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
              <footer className="sr-app-modal-actions">
                <button className="sr-app-modal-btn" onClick={() => setShowApplicationModal(false)}>닫기</button>
                <button className="sr-app-modal-btn primary" onClick={handleGoPayment}>결제하기</button>
              </footer>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ═══════════════════════════════════════
  // STEP 2-B — 스탬프 / 이벤트 / 알림 신청 상세 (단순 안내 + 다음)
  // ═══════════════════════════════════════
  if (step === 'stamp' || step === 'event' || step === 'noti') {
    const cat = SERVICE_CATEGORIES.find((c) => c.key === step);
    return (
      <div className="sr-page">
        <header className="sr-header">
          <button className="sr-back" onClick={handleBack}><ChevronLeft size={22} /></button>
          <h1 className="sr-title">서비스 신청</h1>
        </header>

        <div className="sr-body">
          <div className="sr-cat-select" onClick={() => setShowCategoryDropdown((v) => !v)}>
            <span className="sr-cat-select-title">{cat?.title}</span>
            <ChevronDown size={18} className={`sr-cat-select-arrow ${showCategoryDropdown ? 'open' : ''}`} />
          </div>
          {showCategoryDropdown && (
            <div className="sr-cat-dropdown">
              {SERVICE_CATEGORIES.map((c) => (
                <button
                  key={c.key}
                  className={`sr-cat-dropdown-item ${categoryKey === c.key ? 'active' : ''}`}
                  onClick={() => { setCategoryKey(c.key); setStep(c.key); setShowCategoryDropdown(false); }}
                >
                  {c.title}
                </button>
              ))}
            </div>
          )}

          <ul className="sr-notices">
            {cat?.bullets.map((b, i) => <li key={i}>{b}</li>)}
          </ul>

          <div className="sr-soon-note">
            상세 설정은 서비스 신청 후 슈퍼어드민에서 매장별로 진행합니다.
          </div>
        </div>

        <BottomActionBar>
          <Button variant="primary" fullWidth onClick={handleNext}>다음</Button>
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
          <button className="sr-back" onClick={handleBack}><ChevronLeft size={22} /></button>
          <h1 className="sr-title">서비스 신청</h1>
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
