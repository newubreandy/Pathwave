import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Plus, Check, Wifi, Bell, Gift, CreditCard, ArrowLeft, ArrowRight, Loader2 } from 'lucide-react';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
import ConfirmModal from '../components/common/ConfirmModal';
import './PaymentManagement.css';

/* ── Mock Data ── */
const MOCK_CARD = { name: '나라카드', number: '****-****-****-6789' };
const MOCK_EMAIL = 'ceo@hotelh.com';

const MOCK_SERVICES = [
  { id: 'wifi', name: 'wifi 서비스', label: 'Wifi', icon: Wifi, color: '#16A34A',
    desc: '와이파이 서비스는 BE 서비스를 이용하는 사용자가 서비스시설에 들어왔을 경우 자동으로 와이파이에 접속하게 해 주는 서비스입니다.',
    plans: [
      { id: 'wifi-monthly', name: '월간', price: 7700, unit: '원/월', min: 1 },
      { id: 'wifi-yearly', name: '연간', price: 77000, unit: '원/년', min: 1, discount: '17%' },
    ],
    items: [
      { id: 'wifi-1', quantity: 1, price: '7,700원', priceNote: 'VAT 포함', billingNote: '※ 매월 12일 결제', period: '2021.03.13 ~ 2023.03.12', appliedAt: '(신청일 2021.02.28)' },
      { id: 'wifi-2', quantity: 132, price: '1,016,000원', priceNote: 'VAT 포함', billingNote: '※ 매월 12일 결제', period: '2021.02.13 ~ 2023.02.12', appliedAt: '(신청일 2021.02.28)' },
    ],
  },
  { id: 'event', name: '이벤트 서비스', label: '이벤트', icon: Gift, color: '#3B82F6',
    desc: '서비스 시설에서 특정 위치에 방문하였을 경우 쿠폰 및 혜택을 제공할 수 있는 서비스입니다.',
    plans: [
      { id: 'event-basic', name: '기본', price: 6000, unit: '원/월', min: 1 },
    ],
    items: [],
  },
  { id: 'push', name: '알림 서비스', label: '알림', icon: Bell, color: '#F59E0B',
    desc: '서비스 시설에서 사용자에게 공지 등 별도의 알림을 발송할 수 있는 서비스입니다. 알림은 100개 단위로 구매 가능합니다.',
    plans: [
      { id: 'push-100', name: '100건', price: 6000, unit: '원', min: 100 },
      { id: 'push-500', name: '500건', price: 25000, unit: '원', min: 500, discount: '17%' },
    ],
    items: [],
  },
];

const MOCK_HISTORY = [
  { date: '2022.05.12', store: '상암점', amount: '1,024,100', type: 'wifi' },
  { date: '2022.04.12', store: '상암점', amount: '1,024,100', type: 'wifi' },
  { date: '2022.03.12', store: '상암점', amount: '6,000', type: 'push' },
  { date: '2022.03.12', store: '상암점', amount: '6,000', type: 'event' },
  { date: '2022.03.12', store: '상암점', amount: '1,024,100', type: 'wifi' },
  { date: '2022.02.12', store: '상암점', amount: '1,024,100', type: 'wifi' },
  { date: '2022.01.12', store: '상암점', amount: '1,024,100', type: 'wifi' },
  { date: '2021.12.12', store: '상암점', amount: '6,000', type: 'event' },
  { date: '2021.12.12', store: '상암점', amount: '6,000', type: 'event' },
  { date: '2021.12.12', store: '상암점', amount: '6,000', type: 'wifi' },
];

/* ══════════════════════════════════════════
   Step Indicator
   ══════════════════════════════════════════ */
const STEP_LABELS = ['서비스 선택', '플랜 선택', '주문 확인', '결제', '완료'];

const StepIndicator = ({ current }) => (
  <div className="pay-step-indicator">
    {STEP_LABELS.map((label, i) => (
      <div key={i} className={`pay-step ${i < current ? 'done' : ''} ${i === current ? 'active' : ''}`}>
        <div className="pay-step-circle">
          {i < current ? <Check size={14} /> : i + 1}
        </div>
        <span className="pay-step-label">{label}</span>
        {i < STEP_LABELS.length - 1 && <div className="pay-step-line" />}
      </div>
    ))}
  </div>
);

/* ══════════════════════════════════════════
   서비스 신청 Flow (5 Steps)
   ══════════════════════════════════════════ */
const ServiceApplyFlow = ({ onBack, onComplete }) => {
  const [step, setStep] = useState(0);
  const [selectedService, setSelectedService] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [pgLoading, setPgLoading] = useState(false);
  const [pgDone, setPgDone] = useState(false);

  const service = MOCK_SERVICES.find(s => s.id === selectedService);
  const plan = service?.plans.find(p => p.id === selectedPlan);
  const totalPrice = plan ? plan.price * quantity : 0;
  const vat = Math.round(totalPrice * 0.1);

  const canNext = () => {
    if (step === 0) return !!selectedService;
    if (step === 1) return !!selectedPlan && quantity >= 1;
    return true;
  };

  const handleNext = () => {
    if (step === 3 && !pgDone) {
      // PG 결제 시뮬레이션
      setPgLoading(true);
      setTimeout(() => { setPgLoading(false); setPgDone(true); }, 2000);
      return;
    }
    if (step === 4) { onComplete(); return; }
    setStep(s => s + 1);
  };

  const handlePrev = () => {
    if (step === 0) { onBack(); return; }
    if (step === 4) { onComplete(); return; }
    setStep(s => s - 1);
  };

  return (
    <div className="common-form-page">
      <header className="common-form-header" style={{ marginBottom: 0 }}>
        <button className="back-btn d-md-none" onClick={onBack}>
          <ChevronLeft size={24} />
        </button>
        <h1>서비스 신청</h1>
      </header>

      <StepIndicator current={step} />

      <div className="payment-content">
        {/* Step 0: 서비스 선택 */}
        {step === 0 && (
          <div className="pay-step-content">
            <h2 className="pay-step-title">이용할 서비스를 선택하세요</h2>
            <div className="pay-service-grid">
              {MOCK_SERVICES.map(s => {
                const Icon = s.icon;
                return (
                  <div
                    key={s.id}
                    className={`pay-service-card ${selectedService === s.id ? 'selected' : ''}`}
                    onClick={() => { setSelectedService(s.id); setSelectedPlan(null); }}
                  >
                    <div className="pay-service-card-icon" style={{ background: `${s.color}14`, color: s.color }}>
                      <Icon size={24} />
                    </div>
                    <div className="pay-service-card-name">{s.name}</div>
                    <div className="pay-service-card-desc">{s.desc}</div>
                    {s.items.length > 0 && (
                      <span className="pay-service-card-badge">{s.items.reduce((a,b)=>a+b.quantity,0)}개 이용중</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Step 1: 플랜 선택 */}
        {step === 1 && service && (
          <div className="pay-step-content">
            <h2 className="pay-step-title">플랜을 선택하세요</h2>
            <div className="pay-plan-list">
              {service.plans.map(p => (
                <div
                  key={p.id}
                  className={`pay-plan-card ${selectedPlan === p.id ? 'selected' : ''}`}
                  onClick={() => setSelectedPlan(p.id)}
                >
                  <div className="pay-plan-info">
                    <div className="pay-plan-name">{p.name}</div>
                    <div className="pay-plan-price">{p.price.toLocaleString()}{p.unit}</div>
                  </div>
                  {p.discount && <span className="pay-plan-discount">{p.discount} 할인</span>}
                  <div className={`pay-plan-radio ${selectedPlan === p.id ? 'checked' : ''}`} />
                </div>
              ))}
            </div>
            {selectedPlan && (
              <div className="pay-quantity-section">
                <span className="pay-quantity-label">수량</span>
                <div className="pay-quantity-control">
                  <button className="pay-qty-btn" onClick={() => setQuantity(Math.max(1, quantity - 1))} disabled={quantity <= 1}>−</button>
                  <span className="pay-qty-value">{quantity}</span>
                  <button className="pay-qty-btn" onClick={() => setQuantity(quantity + 1)}>+</button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 2: 주문 확인 */}
        {step === 2 && service && plan && (
          <div className="pay-step-content">
            <h2 className="pay-step-title">주문 내용을 확인하세요</h2>
            <div className="pay-order-summary">
              <div className="pay-order-row">
                <span>서비스</span><span>{service.name}</span>
              </div>
              <div className="pay-order-row">
                <span>플랜</span><span>{plan.name}</span>
              </div>
              <div className="pay-order-row">
                <span>수량</span><span>{quantity}개</span>
              </div>
              <div className="pay-order-row">
                <span>단가</span><span>{plan.price.toLocaleString()}원</span>
              </div>
              <div className="pay-order-divider" />
              <div className="pay-order-row">
                <span>공급가액</span><span>{totalPrice.toLocaleString()}원</span>
              </div>
              <div className="pay-order-row">
                <span>부가세 (10%)</span><span>{vat.toLocaleString()}원</span>
              </div>
              <div className="pay-order-divider" />
              <div className="pay-order-row pay-order-total">
                <span>총 결제금액</span><span>{(totalPrice + vat).toLocaleString()}원</span>
              </div>
            </div>
            <p className="pay-order-notice">※ 결제 후 약정기간 동안 자동 갱신됩니다.</p>
          </div>
        )}

        {/* Step 3: PG 결제 */}
        {step === 3 && (
          <div className="pay-step-content pay-pg-section">
            {pgLoading ? (
              <div className="pay-pg-loading">
                <Loader2 size={40} className="pay-pg-spinner" />
                <p>결제를 진행하고 있습니다...</p>
                <p className="pay-pg-sub">잠시만 기다려주세요</p>
              </div>
            ) : pgDone ? (
              <div className="pay-pg-success">
                <div className="pay-pg-check"><Check size={32} /></div>
                <h3>결제가 완료되었습니다</h3>
                <p>주문번호: PW-{Date.now().toString().slice(-8)}</p>
              </div>
            ) : (
              <div className="pay-pg-ready">
                <div className="pay-pg-card-icon"><CreditCard size={40} /></div>
                <h3>PG 결제</h3>
                <p>등록된 카드로 결제를 진행합니다</p>
                <div className="pay-pg-amount">
                  <span>결제금액</span>
                  <strong>{(totalPrice + vat).toLocaleString()}원</strong>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 4: 완료 */}
        {step === 4 && (
          <div className="pay-step-content pay-complete-section">
            <div className="pay-complete-icon"><Check size={48} /></div>
            <h2>서비스 신청이 완료되었습니다</h2>
            <p>신청하신 서비스는 즉시 활성화됩니다.</p>
            <div className="pay-order-summary" style={{ marginTop: 'var(--pw-space-6)' }}>
              <div className="pay-order-row"><span>서비스</span><span>{service?.name}</span></div>
              <div className="pay-order-row"><span>플랜</span><span>{plan?.name}</span></div>
              <div className="pay-order-row"><span>수량</span><span>{quantity}개</span></div>
              <div className="pay-order-row pay-order-total"><span>결제금액</span><span>{(totalPrice + vat).toLocaleString()}원</span></div>
            </div>
          </div>
        )}
      </div>

      {/* 하단 액션 */}
      <BottomActionBar>
        {step < 4 && step !== 3 && (
          <Button variant="outline" size="large" fullWidth onClick={handlePrev}>
            {step === 0 ? '취소' : '이전'}
          </Button>
        )}
        {step < 4 && (
          <Button
            variant="primary" size="large" fullWidth
            onClick={handleNext}
            disabled={!canNext() || pgLoading}
            isLoading={pgLoading}
          >
            {step === 3 ? (pgDone ? '다음' : '결제하기') : step === 2 ? '결제 진행' : '다음'}
          </Button>
        )}
        {step === 4 && (
          <Button variant="primary" size="large" fullWidth onClick={handlePrev}>
            결제관리로 돌아가기
          </Button>
        )}
      </BottomActionBar>
    </div>
  );
};

/* ══════════════════════════════════════════
   결제정보 탭
   ══════════════════════════════════════════ */
const PaymentInfoTab = ({ card, email, services, onApply }) => {
  const [modal, setModal] = useState({ open: false, title: '', desc: '', onConfirm: null });
  const [editEmail, setEditEmail] = useState(false);
  const [emailValue, setEmailValue] = useState(email);

  const closeModal = () => setModal(m => ({ ...m, open: false }));

  const handleTerminate = () => {
    setModal({ open: true, title: '서비스 종료', desc: '해당 서비스를 종료하시겠습니까?\n종료 후에는 서비스를 이용할 수 없습니다.',
      onConfirm: () => { closeModal(); alert('서비스가 종료되었습니다.'); }
    });
  };

  const handleExtend = () => {
    setModal({ open: true, title: '서비스 연장', desc: '해당 서비스를 연장하시겠습니까?',
      onConfirm: () => { closeModal(); alert('서비스가 연장되었습니다.'); }
    });
  };

  return (
    <>
      <div className="payment-content">
        {/* 카드 정보 */}
        <div className="payment-card-section">
          {card ? (
            <>
              <div className="payment-card">
                <div className="payment-card-name">{card.name}</div>
                <div className="payment-card-number">{card.number}</div>
              </div>
              <div className="payment-card-change">카드교체</div>
            </>
          ) : (
            <div className="payment-card-empty" onClick={() => alert('PG사 카드 등록 화면으로 이동합니다.')}>
              <div className="payment-card-empty-icon"><Plus size={24} /></div>
              <span className="payment-card-empty-text">결제카드등록</span>
            </div>
          )}

          {/* 이메일 */}
          <div className="payment-email-row">
            <div className="payment-email-left">
              <span className="payment-email-label">E-Mail</span>
              {editEmail ? (
                <input
                  className="payment-email-input"
                  type="email" value={emailValue}
                  onChange={e => setEmailValue(e.target.value)}
                  autoFocus
                />
              ) : (
                <span className="payment-email-value">{emailValue || '-'}</span>
              )}
            </div>
            {editEmail ? (
              <div style={{ display: 'flex', gap: 4 }}>
                <Button variant="primary" size="small" onClick={() => setEditEmail(false)}>저장</Button>
                <Button variant="outline" size="small" onClick={() => { setEmailValue(email); setEditEmail(false); }}>취소</Button>
              </div>
            ) : (
              <button className="payment-email-change" onClick={() => setEditEmail(true)}>이메일 변경</button>
            )}
          </div>
          <div className="payment-email-note">※ 결제 및 공지 안내 메일 입니다.</div>
        </div>

        {/* 서비스 이용 내역 */}
        {services.map(service => (
          <div key={service.id} className="payment-service-section">
            <div className="payment-service-header">
              <span className="payment-service-title">{service.name}{service.items.length > 0 ? ' 이용내역' : ''}</span>
              <ChevronRight size={20} color="var(--pw-text-hint)" />
            </div>
            <div className="payment-service-summary">
              <span className="payment-service-name">{service.label}</span>
              <span className="payment-service-count">
                {service.items.length > 0 ? `${service.items.reduce((s, i) => s + i.quantity, 0)}개 이용중` : '0개 이용중'}
              </span>
            </div>
            {service.items.map(item => (
              <div key={item.id} className="payment-service-detail">
                <div className="payment-detail-row">
                  <span className="payment-detail-label">수량</span>
                  <div><span className="payment-detail-value">{item.quantity}개</span><span className="payment-detail-date"> {item.appliedAt}</span></div>
                </div>
                <div className="payment-detail-row">
                  <span className="payment-detail-label">결제금액</span>
                  <div>
                    <div className="payment-detail-value">{item.price} <span className="payment-detail-sub">({item.priceNote})</span></div>
                    <div className="payment-detail-sub">{item.billingNote}</div>
                  </div>
                </div>
                <div className="payment-detail-row">
                  <span className="payment-detail-label">약정기간</span>
                  <span className="payment-detail-value">{item.period}</span>
                </div>
                <div className="payment-service-actions">
                  <Button variant="outline" size="medium" fullWidth onClick={handleTerminate}>서비스종료</Button>
                  <Button variant="primary" size="medium" fullWidth onClick={handleExtend}>서비스 연장</Button>
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* 서비스 신청 CTA */}
      <BottomActionBar>
        <Button variant="primary" size="large" fullWidth onClick={onApply}>서비스 신청</Button>
      </BottomActionBar>

      <ConfirmModal isOpen={modal.open} title={modal.title} desc={modal.desc} onConfirm={modal.onConfirm} onCancel={closeModal} />
    </>
  );
};

/* ══════════════════════════════════════════
   결제내역 탭
   ══════════════════════════════════════════ */
const PaymentHistoryTab = () => (
  <div className="payment-content">
    <div className="payment-history-section">
      <div className="payment-history-note">※ 결제내역은 최대 2년(24개월)기간만 지원합니다.</div>
      <table className="payment-history-table">
        <thead><tr><th>일시</th><th>매장명</th><th>결제금액</th><th>누적</th></tr></thead>
        <tbody>
          {MOCK_HISTORY.length > 0 ? MOCK_HISTORY.map((row, i) => (
            <tr key={i}><td>{row.date}</td><td>{row.store}</td><td>{row.amount}</td><td>{row.type}</td></tr>
          )) : (
            <tr><td colSpan={4} className="payment-history-empty">결제내역이 없습니다.</td></tr>
          )}
        </tbody>
      </table>
    </div>
    <BottomActionBar>
      <Button variant="outline" size="large" fullWidth>더보기</Button>
    </BottomActionBar>
  </div>
);

/* ══════════════════════════════════════════
   Main
   ══════════════════════════════════════════ */
const PaymentManagement = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'info';
  const [showApply, setShowApply] = useState(false);
  const [card] = useState(MOCK_CARD);
  const [email] = useState(MOCK_EMAIL);

  const setActiveTab = (tab) => {
    tab === 'info' ? searchParams.delete('tab') : searchParams.set('tab', tab);
    setSearchParams(searchParams);
  };

  if (showApply) {
    return <ServiceApplyFlow onBack={() => setShowApply(false)} onComplete={() => setShowApply(false)} />;
  }

  return (
    <div className="common-form-page">
      <header className="common-form-header" style={{ marginBottom: 0 }}>
        <button className="back-btn d-md-none" onClick={() => navigate('/dashboard')}><ChevronLeft size={24} /></button>
        <h1>결제관리</h1>
      </header>
      <div className="payment-tabs">
        <button className={`payment-tab ${activeTab === 'info' ? 'active' : ''}`} onClick={() => setActiveTab('info')}>결제정보</button>
        <button className={`payment-tab ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>결제내역</button>
      </div>
      {activeTab === 'info' && <PaymentInfoTab card={card} email={email} services={MOCK_SERVICES} onApply={() => setShowApply(true)} />}
      {activeTab === 'history' && <PaymentHistoryTab />}
    </div>
  );
};

export default PaymentManagement;
