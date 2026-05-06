import React, { useState, useMemo, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, ChevronDown, Plus, Minus, FileSpreadsheet, HelpCircle } from 'lucide-react';
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

  // 와이파이 단계
  const [quantity, setQuantity] = useState(2);
  const [regMode, setRegMode] = useState('individual'); // 'individual' | 'bulk'
  const [individualProfiles, setIndividualProfiles] = useState([
    { id: 1, name: '로비정문1', message: 'Message', password: 'Ezddd1@3356' },
  ]);
  const [excelFileName, setExcelFileName] = useState('');
  const fileInputRef = useRef(null);

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

  // 모달
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
    else if (isDetailStep(step)) setStep('payment');
  };

  // 카테고리 카드 클릭 시 즉시 해당 상세 화면으로 이동
  const goToCategory = (key) => {
    setCategoryKey(key);
    setStep(key);
  };

  const handleExcelDownload = () => {
    // TODO: 백엔드에서 양식 제공
    alert('와이파이 일괄등록 엑셀 양식이 다운로드 됩니다.');
  };

  const handleExcelUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) setExcelFileName(file.name);
    e.target.value = '';
  };

  const handleAddIndividual = () => {
    const id = Date.now();
    setIndividualProfiles((prev) => [...prev, { id, name: '', message: '', password: '' }]);
  };

  const handleSubmit = () => {
    setConfirmMsg('서비스를 신청하시겠어요?\n신청 후 운영팀에서 검토하고 연락드립니다.');
  };

  const doSubmit = () => {
    // TODO: 백엔드 API 연동 — POST /api/service-requests
    console.log('[ServiceRequest] submit', { categoryKey, quantity, regMode, individualProfiles, excelFileName });
    setConfirmMsg(null);
    setSubmitted(true);
  };

  // ═══════════════════════════════════════
  // STEP 1 — 카테고리 선택 (시안 4번)
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
  // STEP 2 — 와이파이 신청 상세 (시안 1, 3번)
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
                  onClick={() => { setCategoryKey(c.key); setShowCategoryDropdown(false); }}
                >
                  {c.title}
                </button>
              ))}
            </div>
          )}

          {/* Quantity stepper */}
          <div className="sr-qty-row">
            <span className="sr-qty-label">Quantity</span>
            <div className="sr-qty-control">
              <button className="sr-qty-btn" onClick={() => setQuantity((q) => Math.max(1, q - 1))} aria-label="수량 감소">
                <Minus size={16} />
              </button>
              <span className="sr-qty-value">{String(quantity).padStart(2, '0')}</span>
              <button className="sr-qty-btn" onClick={() => setQuantity((q) => Math.min(99, q + 1))} aria-label="수량 증가">
                <Plus size={16} />
              </button>
            </div>
          </div>

          {/* 안내 */}
          <ul className="sr-notices">
            {WIFI_NOTICES.map((n, i) => <li key={i}>{n}</li>)}
          </ul>

          {/* 탭 */}
          <div className="sr-tabs">
            <button
              className={`sr-tab ${regMode === 'individual' ? 'active' : ''}`}
              onClick={() => setRegMode('individual')}
            >개별등록</button>
            <button
              className={`sr-tab ${regMode === 'bulk' ? 'active' : ''}`}
              onClick={() => setRegMode('bulk')}
            >일괄등록</button>
          </div>

          {/* 탭 컨텐츠 */}
          {regMode === 'individual' ? (
            <div className="sr-individual">
              <button className="sr-add-card" onClick={handleAddIndividual}>
                <Plus size={20} />
                <span>와이파이 개별등록</span>
              </button>
              {individualProfiles.map((p) => (
                <div key={p.id} className="sr-profile-card">
                  <div className="sr-profile-row"><span className="sr-profile-label">Name</span><span className="sr-profile-value">{p.name || '-'}</span></div>
                  <div className="sr-profile-row">
                    <span className="sr-profile-label">Message</span><span className="sr-profile-value">{p.message || '-'}</span>
                    <span className="sr-profile-label" style={{ marginLeft: 'auto' }}>PW</span><span className="sr-profile-value">{p.password || '-'}</span>
                  </div>
                  <ChevronRight size={16} className="sr-profile-arrow" />
                </div>
              ))}
            </div>
          ) : (
            <div className="sr-bulk">
              <button className="sr-bulk-download" onClick={handleExcelDownload}>
                엑셀 양식 다운받기
                <FileSpreadsheet size={16} />
              </button>
              <p className="sr-bulk-hint">※ 엑셀양식을 다운로드 후 파일을 첨부해 주시면 자동으로 입력됩니다.</p>
              <label className="sr-bulk-upload">
                {excelFileName ? excelFileName : '엑셀 양식 재 업로드'}
                <input
                  type="file"
                  accept=".xlsx,.xls,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                  onChange={handleExcelUpload}
                  ref={fileInputRef}
                  style={{ display: 'none' }}
                />
              </label>
            </div>
          )}
        </div>

        <BottomActionBar>
          <Button variant="primary" fullWidth onClick={handleNext}>다음</Button>
        </BottomActionBar>
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
          {/* 카테고리 dropdown (다른 서비스로 전환 가능) */}
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

          {/* 안내 */}
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
  // STEP 3 — 결제 / 약정 (시안 2번)
  // ═══════════════════════════════════════
  if (step === 'payment') {
    return (
      <div className="sr-page">
        <header className="sr-header">
          <button className="sr-back" onClick={handleBack}><ChevronLeft size={22} /></button>
          <h1 className="sr-title">서비스 신청</h1>
        </header>

        <div className="sr-body">
          {/* 신청 내역 요약 */}
          <section className="sr-pay-section">
            <h2 className="sr-pay-section-title">{selectedCategory?.title} 신청내역</h2>
            <button className="sr-pay-summary" onClick={() => setStep(categoryKey)}>
              <span>{categoryKey === 'wifi' ? `${quantity}개의 서비스이용 예정입니다.` : '서비스 신청 예정입니다.'}</span>
              <ChevronRight size={18} />
            </button>
          </section>

          {/* 결제방법 */}
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

          {/* 서비스기간 */}
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

          {/* 결제안내메일 */}
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
