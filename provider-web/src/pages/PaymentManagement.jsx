import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Plus, Check, Wifi, Bell, Gift, CreditCard, ArrowLeft, ArrowRight, Loader2, Download, X, Info } from 'lucide-react';
import AuthService from '../services/auth/AuthService';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
import ConfirmModal from '../components/common/ConfirmModal';
import SectionTabs from '../components/common/SectionTabs';
import './PaymentManagement.css';

/* ── Mock Data ── */
const MOCK_CARD = {
  name: '나라카드',
  number: '****-****-****-6789',
  expiry: '12/27',          // MM/YY
  autoPay: true,
};
const MOCK_EMAIL = 'ceo@hotelh.com';

/* 다음 결제 요약 mock — 실제 GET /api/billing/next 응답으로 대체.
   - nextDate ISO 문자열
   - amount 원
   - cycle: 결제 주기 라벨
   - breakdown: 서비스별 분해 (라벨 + 금액) */
const MOCK_BILLING_NEXT = {
  nextDate: '2026-06-12',
  amount: 1024100,
  cycle: '월간 정기결제',
  breakdown: [
    { service: 'wifi',  label: 'wifi 132개',     amount: 1016000 },
    { service: 'push',  label: '알림 발송 270건', amount: 8100 },
  ],
};

const MOCK_SERVICES = [
  { id: 'wifi', name: 'wifi 서비스', label: 'Wifi', icon: Wifi, color: '#22C55E',
    desc: 'PathWave WiFi 서비스는 매장 방문 고객이 자동으로 매장 WiFi 에 접속할 수 있도록 지원하는 서비스입니다.',
    plans: [
      { id: 'wifi-monthly', name: '월간', price: 7700, unit: '원/월', min: 1 },
      { id: 'wifi-yearly', name: '연간', price: 77000, unit: '원/년', min: 1, discount: '17%' },
    ],
    items: [
      { id: 'wifi-1', quantity: 1, price: '7,700원', priceNote: 'VAT 포함', billingNote: '※ 매월 12일 결제', period: '2021.03.13 ~ 2023.03.12', appliedAt: '(신청일 2021.02.28)' },
      { id: 'wifi-2', quantity: 132, price: '1,016,000원', priceNote: 'VAT 포함', billingNote: '※ 매월 12일 결제', period: '2021.02.13 ~ 2023.02.12', appliedAt: '(신청일 2021.02.28)' },
    ],
  },
  { id: 'event', name: '이벤트 서비스', label: '이벤트', icon: Gift, color: '#4ADE80',
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

/**
 * type 코드 → UI 한글 라벨 (사용자 요구 2026-05-10).
 *   wifi → 와이파이
 *   event → 쿠폰
 *   push → 알림
 *   noti → 알림 (호환)
 */
const SERVICE_TYPE_LABEL = {
  wifi: '와이파이',
  event: '쿠폰',
  push: '알림',
  noti: '알림',
};

const MOCK_HISTORY = [
  { date: '2022.05.12', store: '상암점', amount: '1,024,100', type: 'wifi' },
  { date: '2022.04.12', store: '상암점', amount: '1,024,100', type: 'wifi' },
  { date: '2022.03.12', store: '상암점', amount: '6,000', type: 'push' },
  { date: '2022.03.12', store: '상암점', amount: '6,000', type: 'event' },
  { date: '2022.03.12', store: '상암점', amount: '1,024,100', type: 'wifi' },
  { date: '2022.02.12', store: '상암점', amount: '6,000', type: 'noti' },
  { date: '2022.02.12', store: '상암점', amount: '1,024,100', type: 'wifi' },
  { date: '2022.01.12', store: '상암점', amount: '1,024,100', type: 'wifi' },
  { date: '2021.12.12', store: '상암점', amount: '6,000', type: 'event' },
  { date: '2021.12.12', store: '상암점', amount: '6,000', type: 'event' },
  // ── 더보기 페이지 (2번째 page) ───────────────────────────
  { date: '2021.12.12', store: '상암점', amount: '6,000', type: 'wifi' },
  { date: '2021.11.12', store: '상암점', amount: '1,024,100', type: 'wifi' },
  { date: '2021.10.12', store: '상암점', amount: '6,000', type: 'event' },
  { date: '2021.09.12', store: '상암점', amount: '1,024,100', type: 'wifi' },
  { date: '2021.08.12', store: '상암점', amount: '6,000', type: 'noti' },
  { date: '2021.07.12', store: '상암점', amount: '1,024,100', type: 'wifi' },
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
                    <div className="pay-service-card-icon">
                      <Icon size={24} strokeWidth={2} />
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
   카드 교체 모달 (사용자 요구 2026-05-11)
   카드 정보 입력 → mock DB 저장 + 슈퍼어드민 변경 이력 저장.
   실서비스: PG 토큰화 (카드번호/CVC 직접 보관 X) + 백엔드 audit log.
   ══════════════════════════════════════════ */
function CardChangeModal({ currentCard, onClose }) {
  const [form, setForm] = useState({
    issuer: '',          // 카드사
    number: '',          // 16자리
    expMonth: '',        // MM
    expYear: '',         // YY
    cvc: '',             // 3자리
    holder: '',          // 카드 소유자
  });
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const onChange = (k) => (e) => {
    let v = e.target.value;
    if (k === 'number') v = v.replace(/[^0-9]/g, '').slice(0, 16);
    else if (k === 'expMonth' || k === 'expYear' || k === 'cvc') v = v.replace(/[^0-9]/g, '');
    if (k === 'expMonth') v = v.slice(0, 2);
    if (k === 'expYear')  v = v.slice(0, 2);
    if (k === 'cvc')      v = v.slice(0, 3);
    setForm((f) => ({ ...f, [k]: v }));
  };

  const submit = () => {
    setError('');
    if (!form.issuer.trim())                  return setError('카드사를 입력해주세요.');
    if (form.number.length !== 16)            return setError('카드번호 16자리를 입력해주세요.');
    if (!/^\d{2}$/.test(form.expMonth) || +form.expMonth < 1 || +form.expMonth > 12)
                                              return setError('유효한 만료월(MM)을 입력해주세요.');
    if (!/^\d{2}$/.test(form.expYear))        return setError('만료년(YY) 2자리를 입력해주세요.');
    if (form.cvc.length !== 3)                return setError('CVC 3자리를 입력해주세요.');
    if (!form.holder.trim())                  return setError('카드 소유자명을 입력해주세요.');

    // ── mock 저장 ──────────────────────────────────────────
    // 1) 결제 카드 정보 (요약: 카드사 + 마스킹 번호 + 만료) — localStorage
    const masked = `****-****-****-${form.number.slice(-4)}`;
    const newCard = {
      name: form.issuer,
      number: masked,
      expiry: `${form.expMonth}/${form.expYear}`,
      autoPay: currentCard?.autoPay ?? false,
    };
    try {
      localStorage.setItem('pathwave_payment_card', JSON.stringify(newCard));
    } catch {/* 저장 실패 무시 — UI 에는 영향 없음 */}

    // 2) 슈퍼어드민 변경 이력 audit log
    //    실서비스: POST /api/admin/audit/payment-card-change
    //    여기선 콘솔 + localStorage 큐로 보존 (mock).
    const user = AuthService.getCurrentUser();
    const auditEntry = {
      ts: new Date().toISOString(),
      actor: user?.id || user?.email || 'unknown',
      action: 'payment_card_change',
      before: currentCard ? { name: currentCard.name, number: currentCard.number } : null,
      after:  { name: newCard.name, number: newCard.number, expiry: newCard.expiry },
    };
    try {
      const queue = JSON.parse(localStorage.getItem('pathwave_audit_queue') || '[]');
      queue.push(auditEntry);
      localStorage.setItem('pathwave_audit_queue', JSON.stringify(queue));
    } catch {/* ignore */}
    // 디버깅용 — 실서비스 제거
    console.info('[audit] payment_card_change', auditEntry);

    setSubmitted(true);
    setTimeout(() => onClose(), 1500);
  };

  return (
    <div className="settings-modal-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="settings-modal-header">
          <h2 className="settings-modal-title">카드 교체</h2>
          <button className="settings-modal-close" onClick={onClose} aria-label="닫기">
            <X size={20} />
          </button>
        </div>

        <div className="settings-modal-body">
          {submitted ? (
            <div className="biz-modal-success">
              <div className="biz-modal-success-icon">✓</div>
              <p className="biz-modal-success-title">카드가 변경되었습니다</p>
              <p className="biz-modal-success-desc">
                다음 결제부터 새 카드로 청구됩니다. 변경 이력은 슈퍼어드민에 기록됩니다.
              </p>
            </div>
          ) : (
            <>
              <div className="biz-modal-notice">
                <Info size={14} aria-hidden="true" />
                <span>카드 정보는 PG사 보안 정책에 따라 토큰화되어 저장되며, 변경 이력은 슈퍼어드민에 기록됩니다.</span>
              </div>

              <div className="settings-modal-field">
                <label className="settings-modal-label">카드사</label>
                <input
                  type="text"
                  className="settings-modal-input"
                  value={form.issuer}
                  onChange={onChange('issuer')}
                  placeholder="예: 나라카드"
                />
              </div>

              <div className="settings-modal-field">
                <label className="settings-modal-label">카드 번호</label>
                <input
                  type="text"
                  inputMode="numeric"
                  className="settings-modal-input"
                  value={form.number}
                  onChange={onChange('number')}
                  placeholder="0000000000000000"
                  maxLength={16}
                />
              </div>

              <div className="card-change-grid">
                <div className="settings-modal-field">
                  <label className="settings-modal-label">유효기간</label>
                  <div className="card-change-expiry-row">
                    <input
                      type="text"
                      inputMode="numeric"
                      className="settings-modal-input"
                      value={form.expMonth}
                      onChange={onChange('expMonth')}
                      placeholder="MM"
                      maxLength={2}
                    />
                    <span className="card-change-slash">/</span>
                    <input
                      type="text"
                      inputMode="numeric"
                      className="settings-modal-input"
                      value={form.expYear}
                      onChange={onChange('expYear')}
                      placeholder="YY"
                      maxLength={2}
                    />
                  </div>
                </div>

                <div className="settings-modal-field">
                  <label className="settings-modal-label">CVC</label>
                  <input
                    type="password"
                    inputMode="numeric"
                    className="settings-modal-input"
                    value={form.cvc}
                    onChange={onChange('cvc')}
                    placeholder="3자리"
                    maxLength={3}
                  />
                </div>
              </div>

              <div className="settings-modal-field">
                <label className="settings-modal-label">카드 소유자</label>
                <input
                  type="text"
                  className="settings-modal-input"
                  value={form.holder}
                  onChange={onChange('holder')}
                  placeholder="카드에 표시된 이름"
                />
              </div>

              {error && <p className="settings-modal-error">{error}</p>}

              <div className="settings-modal-actions">
                <button className="settings-modal-btn cancel" onClick={onClose}>취소</button>
                <button className="settings-modal-btn confirm" onClick={submit}>변경하기</button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════
   결제정보 탭
   ══════════════════════════════════════════ */
const PaymentInfoTab = ({ card, email, services, onApply }) => {
  const navigate = useNavigate();
  const [modal, setModal] = useState({ open: false, title: '', desc: '', onConfirm: null });
  // 자동결제 토글 — 로컬 상태 mock. 실서비스에선 PUT /api/billing/auto-pay.
  const [autoPay, setAutoPay] = useState(card?.autoPay ?? false);
  // 카드 교체 모달 — 카드 정보 입력 후 mock DB 저장 + 슈퍼어드민 이력.
  const [showCardChange, setShowCardChange] = useState(false);

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

  // 다음 결제 D-day / 표시 문자열
  const nextDate = new Date(MOCK_BILLING_NEXT.nextDate);
  const dDay = Math.ceil((nextDate.getTime() - Date.now()) / 86_400_000);
  const nextDateLabel = `${nextDate.getFullYear()}.${String(nextDate.getMonth() + 1).padStart(2, '0')}.${String(nextDate.getDate()).padStart(2, '0')}`;
  const fmt = (n) => n.toLocaleString();

  return (
    <>
      <div className="payment-content">
        {/* 결제 요약 — 좌(결제수단) / 우(다음 결제) 2-column.
            모바일에서는 자동으로 세로 stack. (사용자 요구 2026-05-10 — A 안) */}
        <div className="payment-summary-grid">
          {/* 좌 — 결제 수단 */}
          <section className="payment-summary-card payment-method-card" aria-label="결제 수단">
            <h2 className="payment-summary-title">결제 수단</h2>
            {card ? (
              <>
                <div className="payment-card">
                  <div className="payment-card-name">{card.name}</div>
                  <div className="payment-card-number">{card.number}</div>
                </div>
                <div className="payment-method-meta">
                  <div className="payment-method-meta-row">
                    <span className="payment-method-meta-label">유효기간</span>
                    <span className="payment-method-meta-value">{card.expiry}</span>
                  </div>
                  <div className="payment-method-meta-row">
                    <span className="payment-method-meta-label">자동결제</span>
                    <label className="toggle-switch" htmlFor="payment-auto-pay">
                      <input
                        type="checkbox"
                        id="payment-auto-pay"
                        checked={autoPay}
                        onChange={() => setAutoPay((v) => !v)}
                      />
                      <span className="toggle-track" />
                      <span className="toggle-thumb" />
                      <span className="toggle-text">{autoPay ? 'ON' : 'OFF'}</span>
                    </label>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="small"
                  fullWidth
                  onClick={() => setShowCardChange(true)}
                >
                  카드 교체
                </Button>
              </>
            ) : (
              <div className="payment-card-empty" onClick={() => alert('PG사 카드 등록 화면으로 이동합니다.')}>
                <div className="payment-card-empty-icon"><Plus size={24} /></div>
                <span className="payment-card-empty-text">결제카드등록</span>
              </div>
            )}
          </section>

          {/* 우 — 다음 결제 요약 */}
          <section className="payment-summary-card payment-billing-card" aria-label="다음 결제 요약">
            <h2 className="payment-summary-title">다음 결제 예정</h2>
            <div className="payment-billing-date-row">
              <span className="payment-billing-date">{nextDateLabel}</span>
              {dDay >= 0 && dDay <= 30 && (
                <span className="payment-billing-dday">D-{dDay}</span>
              )}
            </div>
            <div className="payment-billing-cycle">{MOCK_BILLING_NEXT.cycle}</div>
            <div className="payment-billing-amount">
              <span className="payment-billing-amount-label">예상 청구액</span>
              <span className="payment-billing-amount-value-wrap">
                <span className="payment-billing-amount-value">{fmt(MOCK_BILLING_NEXT.amount)}</span>
                <span className="payment-amount-unit">원</span>
              </span>
            </div>
            <ul className="payment-billing-breakdown">
              {MOCK_BILLING_NEXT.breakdown.map((b) => (
                <li key={b.service}>
                  <span className="payment-billing-breakdown-label">{b.label}</span>
                  <span className="payment-billing-breakdown-amount">
                    {fmt(b.amount)}
                    <span className="payment-amount-unit">원</span>
                  </span>
                </li>
              ))}
            </ul>
          </section>
        </div>

        {/* 이메일 + 안내문 — 전체폭 별도 블록.
            이메일은 회사 정보의 일부. [이메일 변경] 클릭 시 회원정보 페이지(사람 아이콘)
            로 이동하여 회원정보 탭의 [변경하기] 버튼을 통해 사업자정보 변경 모달 진입.
            (사용자 요구 2026-05-11) */}
        <div className="payment-email-block">
          <div className="payment-email-row">
            <div className="payment-email-left">
              <span className="payment-email-label">E-Mail</span>
              <span className="payment-email-value">{email || '-'}</span>
            </div>
            <Button
              variant="outline"
              size="small"
              onClick={() => navigate('/dashboard/staff?tab=profile')}
            >
              이메일 변경
            </Button>
          </div>
          <div className="payment-email-note">
            ※ 결제 및 공지 안내 메일입니다. 변경은 회원정보의 [변경하기] → 슈퍼어드민 승인 절차를 거쳐 반영됩니다.
          </div>
        </div>

        {/* 서비스 이용 내역 — 한 줄 행으로 단순화 (사용자 요구 2026-05-11):
            "왼쪽 두 개 쓸필요 없고, 위에 흰색 한 줄만 + 우측 N개 이용중 >" */}
        {services.map((service) => {
          const totalQty = service.items.reduce((s, i) => s + i.quantity, 0);
          const targetRoute =
            service.id === 'wifi'  ? '/dashboard/wifi'
            : service.id === 'event' ? '/dashboard/coupons'
            : service.id === 'push'  ? '/dashboard/notifications'
            : null;
          return (
            <button
              key={service.id}
              type="button"
              className="payment-service-section payment-service-section--clickable"
              onClick={() => targetRoute && navigate(targetRoute)}
            >
              <span className="payment-service-title">{service.name}</span>
              <span className="payment-service-count">
                {totalQty}
                <span className="payment-service-count-unit">개 이용중</span>
              </span>
              <ChevronRight size={18} color="var(--pw-text-hint)" aria-hidden="true" />
            </button>
          );
        })}
      </div>

      {/* 서비스 신청 CTA */}
      <BottomActionBar>
        <Button variant="primary" size="large" fullWidth onClick={onApply}>서비스 신청</Button>
      </BottomActionBar>

      <ConfirmModal isOpen={modal.open} title={modal.title} desc={modal.desc} onConfirm={modal.onConfirm} onCancel={closeModal} />
      {showCardChange && (
        <CardChangeModal
          currentCard={card}
          onClose={() => setShowCardChange(false)}
        />
      )}
    </>
  );
};

/* ══════════════════════════════════════════
   결제내역 탭
   ══════════════════════════════════════════ */
const PAGE_SIZE = 10;

const PaymentHistoryTab = () => {
  // 사용자 요구 (2026-05-10): 10개 단위로 노출. 더 없을 때 버튼 숨김.
  const [visible, setVisible] = useState(PAGE_SIZE);
  const items = MOCK_HISTORY.slice(0, visible);
  const hasMore = visible < MOCK_HISTORY.length;

  // 영수증 다운로드 — mock. 실서비스에선 GET /api/billing/{id}/receipt PDF.
  const downloadReceipt = (row) => {
    alert(`영수증 다운로드 (mock)\n${row.date} · ${row.store} · ${row.amount}원`);
  };

  return (
    <div className="payment-content">
      <div className="payment-history-section">
        <div className="payment-history-note">※ 결제내역은 최대 2년(24개월)기간만 지원합니다.</div>
        <table className="payment-history-table">
          <thead>
            <tr>
              <th>일시</th>
              <th>매장명</th>
              <th>결제금액</th>
              <th>서비스 구분</th>
              <th className="payment-history-receipt-col">영수증</th>
            </tr>
          </thead>
          <tbody>
            {items.length > 0 ? items.map((row, i) => (
              <tr key={i}>
                <td>{row.date}</td>
                <td>{row.store}</td>
                <td>{row.amount}</td>
                <td>{SERVICE_TYPE_LABEL[row.type] || row.type}</td>
                <td className="payment-history-receipt-col">
                  <button
                    type="button"
                    className="payment-receipt-btn"
                    onClick={() => downloadReceipt(row)}
                    aria-label={`${row.date} 영수증 다운로드`}
                  >
                    <Download size={14} aria-hidden="true" />
                    <span>받기</span>
                  </button>
                </td>
              </tr>
            )) : (
              <tr><td colSpan={5} className="payment-history-empty">결제내역이 없습니다.</td></tr>
            )}
          </tbody>
        </table>
      </div>
      {/* 더 불러올 항목 있을 때만 버튼 노출. 활성 시 primary 톤. */}
      {hasMore && (
        <BottomActionBar>
          <Button
            variant="primary"
            size="large"
            fullWidth
            onClick={() => setVisible((v) => v + PAGE_SIZE)}
          >
            더보기
          </Button>
        </BottomActionBar>
      )}
    </div>
  );
};

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
    <div className="modern-page">
      <div className="page-header-section">
        <h1 className="page-title">결제관리</h1>
        <p className="sub-title">결제 정보와 결제 내역을 관리합니다.</p>
      </div>
      <SectionTabs
        tabs={[
          { key: 'info',    label: '결제정보' },
          { key: 'history', label: '결제내역' },
        ]}
        value={activeTab}
        onChange={setActiveTab}
        ariaLabel="결제관리 카테고리"
      />
      {/* 탭 ↔ 콘텐츠 간격 — 다른 페이지(알림 인박스 등)와 동일 톤 (사용자 요구 2026-05-10) */}
      <div className="payment-tab-content">
        {activeTab === 'info' && <PaymentInfoTab card={card} email={email} services={MOCK_SERVICES} onApply={() => setShowApply(true)} />}
        {activeTab === 'history' && <PaymentHistoryTab />}
      </div>
    </div>
  );
};

export default PaymentManagement;
