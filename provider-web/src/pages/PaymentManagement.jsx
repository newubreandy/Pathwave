import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Plus, Check, Wifi, Bell, Gift, CreditCard, ArrowLeft, ArrowRight, Loader2, Download, X, Info, AlertTriangle, ShieldCheck } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import AuthService from '../services/auth/AuthService';
import BillingService from '../services/billing/BillingService';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
import ConfirmModal from '../components/common/ConfirmModal';
import { useDialog } from '../components/common/DialogProvider';
import SectionTabs from '../components/common/SectionTabs';
import './PaymentManagement.css';

/* ── 서비스 카탈로그 (백엔드 가격 일치: wifi 5000 / event 10000 / notification 3000 월 단가, VAT 별도) ── */
const SERVICE_CATALOG = [
  { id: 'wifi', name: 'wifi 서비스', label: 'Wifi', icon: Wifi, color: '#22C55E',
    desc: 'PathWave WiFi 서비스는 매장 방문 고객이 자동으로 매장 WiFi 에 접속할 수 있도록 지원하는 서비스입니다.',
    plans: [
      { id: 'wifi-monthly',  name: '월간', price: 5000,  unit: '원/월',  periodMonths: 1,  min: 1 },
      { id: 'wifi-yearly',   name: '연간', price: 54000, unit: '원/년', periodMonths: 12, min: 1, discount: '10%' },
    ],
  },
  { id: 'event', name: '이벤트 서비스', label: '이벤트', icon: Gift, color: '#4ADE80',
    desc: '서비스 시설에서 특정 위치에 방문하였을 경우 쿠폰 및 혜택을 제공할 수 있는 서비스입니다.',
    plans: [
      { id: 'event-monthly', name: '월간', price: 10000, unit: '원/월', periodMonths: 1,  min: 1 },
      { id: 'event-yearly',  name: '연간', price: 108000, unit: '원/년', periodMonths: 12, min: 1, discount: '10%' },
    ],
  },
  { id: 'notification', name: '알림 서비스', label: '알림', icon: Bell, color: '#F59E0B',
    desc: '서비스 시설에서 사용자에게 공지 등 별도의 알림을 발송할 수 있는 서비스입니다.',
    plans: [
      { id: 'noti-monthly', name: '월간', price: 3000,  unit: '원/월', periodMonths: 1,  min: 1 },
      { id: 'noti-yearly',  name: '연간', price: 32400, unit: '원/년', periodMonths: 12, min: 1, discount: '10%' },
    ],
  },
];

/**
 * type 코드 → UI 한글 라벨 (백엔드 service_type 포함).
 *   wifi → 와이파이
 *   event → 이벤트
 *   notification → 알림
 *   noti → 알림 (호환)
 *   push → 알림 (호환)
 */
const SERVICE_TYPE_LABEL = {
  wifi: '와이파이',
  event: '이벤트',
  notification: '알림',
  noti: '알림',
  push: '알림',
};

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
  const [pgError, setPgError] = useState('');
  const [orderNo, setOrderNo] = useState('');

  const service = SERVICE_CATALOG.find(s => s.id === selectedService);
  const plan = service?.plans.find(p => p.id === selectedPlan);
  const totalPrice = plan ? plan.price * quantity : 0;
  const vat = Math.round(totalPrice * 0.1);

  const canNext = () => {
    if (step === 0) return !!selectedService;
    if (step === 1) return !!selectedPlan && quantity >= 1;
    return true;
  };

  const handleNext = async () => {
    if (step === 3 && !pgDone) {
      // BillingService.createSubscription 호출
      setPgLoading(true);
      setPgError('');
      try {
        const res = await BillingService.createSubscription({
          serviceType: service.id,
          quantity,
          periodMonths: plan.periodMonths,
        });
        setOrderNo(res.payment?.order_no || '');
        setPgDone(true);
      } catch (err) {
        setPgError(err.message || '결제에 실패했습니다. 다시 시도해주세요.');
      } finally {
        setPgLoading(false);
      }
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
              {SERVICE_CATALOG.map(s => {
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
                {orderNo && <p>주문번호: {orderNo}</p>}
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
                {pgError && <p className="pay-pg-error" style={{ color: 'var(--pw-danger)', marginTop: 'var(--pw-space-3)', fontSize: 'var(--pw-label-size)' }}>{pgError}</p>}
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
   PCI 준수: 카드 전체번호/CVC 는 백엔드 전송·저장 금지.
   백엔드에는 card_brand + last4(끝 4자리)만 전송.
   ══════════════════════════════════════════ */
function CardChangeModal({ currentCard, onClose, onSuccess }) {
  const [form, setForm] = useState({
    issuer: '',          // 카드사
    number: '',          // 16자리 (입력만, 백엔드 미전송)
    expMonth: '',        // MM (입력만, 백엔드 미전송)
    expYear: '',         // YY (입력만, 백엔드 미전송)
    cvc: '',             // 3자리 (입력만, 절대 저장·전송 금지)
    holder: '',          // 카드 소유자 (입력만, 백엔드 미전송)
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
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

  const submit = async () => {
    setError('');
    if (!form.issuer.trim())                  return setError('카드사를 입력해주세요.');
    if (form.number.length !== 16)            return setError('카드번호 16자리를 입력해주세요.');
    if (!/^\d{2}$/.test(form.expMonth) || +form.expMonth < 1 || +form.expMonth > 12)
                                              return setError('유효한 만료월(MM)을 입력해주세요.');
    if (!/^\d{2}$/.test(form.expYear))        return setError('만료년(YY) 2자리를 입력해주세요.');
    if (form.cvc.length !== 3)                return setError('CVC 3자리를 입력해주세요.');
    if (!form.holder.trim())                  return setError('카드 소유자명을 입력해주세요.');

    // PCI 준수: card_brand + last4 만 전송. 전체번호/CVC/만료 는 전송하지 않는다.
    setLoading(true);
    try {
      await BillingService.registerCard(form.issuer, form.number.slice(-4));
      setSubmitted(true);
      setTimeout(() => { onSuccess?.(); onClose(); }, 1500);
    } catch (err) {
      setError(err.message || '카드 등록에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
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
                <button className="settings-modal-btn cancel" onClick={onClose} disabled={loading}>취소</button>
                <button className="settings-modal-btn confirm" onClick={submit} disabled={loading}>
                  {loading ? '처리 중...' : '변경하기'}
                </button>
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
const PaymentInfoTab = ({ onApply }) => {
  const { t } = useTranslation();
  const { alert } = useDialog();
  const navigate = useNavigate();

  // 카드 — BillingService.listCards() 로 active 카드 표시
  const [card, setCard] = useState(null);
  const [cardLoading, setCardLoading] = useState(true);
  const [cardError, setCardError] = useState('');

  // 구독 — 다음 결제 예정 계산용
  const [subscriptions, setSubscriptions] = useState([]);

  // 이메일 — 현재 로그인 유저
  const email = AuthService.getCurrentUser()?.email || '';

  const [autoPay, setAutoPay] = useState(false);
  const [showCardChange, setShowCardChange] = useState(false);

  const loadCard = async () => {
    setCardLoading(true);
    setCardError('');
    try {
      const res = await BillingService.listCards();
      const activeCard = (res.cards || []).find(c => c.active) || null;
      setCard(activeCard);
    } catch (err) {
      setCardError(err.message || '카드 정보를 불러올 수 없습니다.');
    } finally {
      setCardLoading(false);
    }
  };

  const loadSubscriptions = async () => {
    try {
      const res = await BillingService.listSubscriptions();
      setSubscriptions(res.subscriptions || []);
    } catch {
      // 구독 로드 실패는 무시 — 카드 섹션은 독립적으로 동작
    }
  };

  useEffect(() => {
    loadCard();
    loadSubscriptions();
  }, []);

  // 다음 결제 예정 — active 구독 중 가장 임박한 ends_at
  const activeSubscriptions = subscriptions.filter(s => s.status === 'active');
  const nextBilling = activeSubscriptions.length > 0
    ? activeSubscriptions.reduce((nearest, s) => {
        if (!nearest) return s;
        return new Date(s.ends_at) < new Date(nearest.ends_at) ? s : nearest;
      }, null)
    : null;

  const fmt = (n) => Number(n).toLocaleString();

  // PG provider label — VITE_PG_PROVIDER env var 또는 fallback
  const pgProvider = import.meta.env.VITE_PG_PROVIDER || 'sim';
  const pgLabel = pgProvider === 'toss' ? t('billing.pg_toss') : t('billing.pg_sim');

  const SERVICE_ROUTES = {
    wifi: '/dashboard/wifi',
    event: '/dashboard/coupons',
    notification: '/dashboard/notifications',
  };

  return (
    <>
      <div className="payment-content">
        {/* 결제 요약 — 좌(결제수단) / 우(다음 결제) 2-column */}
        <div className="payment-summary-grid">
          {/* 좌 — 결제 수단 */}
          <section className="payment-summary-card payment-method-card" aria-label={t('billing.cards_title')}>
            <h2 className="payment-summary-title">{t('billing.cards_title')}</h2>
            {cardLoading ? (
              <div style={{ padding: 'var(--pw-space-4)', color: 'var(--pw-text-hint)' }}>불러오는 중...</div>
            ) : cardError ? (
              <div style={{ color: 'var(--pw-danger)', fontSize: 'var(--pw-label-size)' }}>{cardError}</div>
            ) : card ? (
              <>
                <div className="payment-card">
                  <div className="payment-card-name">{card.card_brand}</div>
                  <div className="payment-card-number">{card.masked_card}</div>
                </div>
                <div className="payment-method-meta">
                  <div className="payment-method-meta-row">
                    <span className="payment-method-meta-label">{t('billing.autopay_consent_title')}</span>
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
                  {autoPay && (
                    <p className="pay-autopay-consent-note">{t('billing.autopay_consent_body')}</p>
                  )}
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
              <div className="payment-card-empty" onClick={() => setShowCardChange(true)}>
                <div className="payment-card-empty-icon"><Plus size={24} /></div>
                <span className="payment-card-empty-text">{t('billing.cards_empty')}</span>
              </div>
            )}
          </section>

          {/* 우 — 다음 결제 예정 (active 구독에서 유도) */}
          <section className="payment-summary-card payment-billing-card" aria-label="다음 결제 요약">
            <h2 className="payment-summary-title">다음 결제 예정</h2>
            {nextBilling ? (() => {
              const nextDate = new Date(nextBilling.ends_at);
              const dDay = Math.ceil((nextDate.getTime() - Date.now()) / 86_400_000);
              const nextDateLabel = `${nextDate.getFullYear()}.${String(nextDate.getMonth() + 1).padStart(2, '0')}.${String(nextDate.getDate()).padStart(2, '0')}`;
              return (
                <>
                  <div className="payment-billing-date-row">
                    <span className="payment-billing-date">{nextDateLabel}</span>
                    {dDay >= 0 && dDay <= 30 && (
                      <span className="payment-billing-dday">D-{dDay}</span>
                    )}
                  </div>
                  <div className="payment-billing-cycle">월간 정기결제</div>
                  <div className="payment-billing-amount">
                    <span className="payment-billing-amount-label">예상 청구액</span>
                    <span className="payment-billing-amount-value-wrap">
                      <span className="payment-billing-amount-value">{fmt(nextBilling.total_price)}</span>
                      <span className="payment-amount-unit">원</span>
                    </span>
                  </div>
                  <ul className="payment-billing-breakdown">
                    {activeSubscriptions.map((s) => (
                      <li key={s.id}>
                        <span className="payment-billing-breakdown-label">
                          {SERVICE_TYPE_LABEL[s.service_type] || s.service_type} {s.quantity}개
                        </span>
                        <span className="payment-billing-breakdown-amount">
                          {fmt(s.total_price)}
                          <span className="payment-amount-unit">원</span>
                        </span>
                      </li>
                    ))}
                  </ul>
                </>
              );
            })() : (
              <p style={{ color: 'var(--pw-text-hint)', fontSize: 'var(--pw-label-size)', padding: 'var(--pw-space-4) 0' }}>
                예정된 결제 없음
              </p>
            )}
          </section>
        </div>

        {/* 부가세 compliance 경고 박스 */}
        <div className="pay-compliance-warning">
          <AlertTriangle size={14} aria-hidden="true" />
          <span>{t('billing.compliance_warning')}</span>
        </div>

        {/* 이메일 + 안내문 */}
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

        {/* PG 정보 카드 */}
        <div className="pay-info-card">
          <div className="pay-info-card-header">
            <ShieldCheck size={16} aria-hidden="true" />
            <h3 className="pay-info-card-title">{t('billing.pg_info_title')}</h3>
          </div>
          <p className="pay-info-card-body">{t('billing.pg_info_body')}</p>
          <div className="pay-info-card-row">
            <span className="pay-info-card-label">{t('billing.pg_label')}</span>
            <span className="pay-info-card-value">{pgLabel}</span>
          </div>
        </div>

        {/* 환불 정책 카드 */}
        <div className="pay-info-card">
          <div className="pay-info-card-header">
            <Info size={16} aria-hidden="true" />
            <h3 className="pay-info-card-title">{t('billing.refund_policy_title')}</h3>
          </div>
          <ul className="pay-refund-list">
            <li>{t('billing.refund_policy_1')}</li>
            <li>{t('billing.refund_policy_2')}</li>
            <li>{t('billing.refund_policy_3')}</li>
          </ul>
        </div>

        {/* 서비스 구독 현황 — active 구독에서 유도 */}
        {SERVICE_CATALOG.map((svc) => {
          const activeSubs = activeSubscriptions.filter(s => s.service_type === svc.id);
          const totalQty = activeSubs.reduce((acc, s) => acc + (s.quantity || 0), 0);
          const targetRoute = SERVICE_ROUTES[svc.id] || null;
          return (
            <button
              key={svc.id}
              type="button"
              className="payment-service-section payment-service-section--clickable"
              onClick={() => targetRoute && navigate(targetRoute)}
            >
              <span className="payment-service-title">{svc.name}</span>
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

      {showCardChange && (
        <CardChangeModal
          currentCard={card}
          onClose={() => setShowCardChange(false)}
          onSuccess={loadCard}
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
  const { t } = useTranslation();
  const { alert } = useDialog();

  const [allPayments, setAllPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState('');
  const [visible, setVisible] = useState(PAGE_SIZE);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setFetchError('');
      try {
        const res = await BillingService.listPayments();
        setAllPayments(res.payments || []);
      } catch (err) {
        setFetchError(err.message || '결제 내역을 불러올 수 없습니다.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const items = allPayments.slice(0, visible);
  const hasMore = visible < allPayments.length;

  // paid_at ISO → 표시용 날짜 (YYYY.MM.DD)
  const fmtDate = (iso) => {
    if (!iso) return '-';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`;
  };

  // 영수증 다운로드 — 실서비스에선 GET /api/billing/{id}/receipt PDF.
  const downloadReceipt = (row) => {
    alert(`영수증 다운로드\n${fmtDate(row.paid_at)} · 주문번호: ${row.order_no} · ${Number(row.total).toLocaleString()}원`);
  };

  return (
    <div className="payment-content">
      <div className="payment-history-section">
        <div className="payment-history-note">※ 결제내역은 최대 2년(24개월)기간만 지원합니다.</div>
        {loading ? (
          <div style={{ padding: 'var(--pw-space-6)', color: 'var(--pw-text-hint)', textAlign: 'center' }}>불러오는 중...</div>
        ) : fetchError ? (
          <div style={{ color: 'var(--pw-danger)', padding: 'var(--pw-space-4)', fontSize: 'var(--pw-label-size)' }}>{fetchError}</div>
        ) : (
          <table className="payment-history-table">
            <thead>
              <tr>
                <th>일시</th>
                <th>주문번호</th>
                <th>{t('billing.amount_label')}</th>
                <th>상태</th>
                <th className="payment-history-receipt-col">영수증</th>
              </tr>
            </thead>
            <tbody>
              {items.length > 0 ? items.map((row) => (
                <tr key={row.id}>
                  <td>{fmtDate(row.paid_at)}</td>
                  <td>{row.order_no}</td>
                  <td>{Number(row.total).toLocaleString()}원</td>
                  <td>{row.status}</td>
                  <td className="payment-history-receipt-col">
                    <button
                      type="button"
                      className="payment-receipt-btn"
                      onClick={() => downloadReceipt(row)}
                      aria-label={`${fmtDate(row.paid_at)} 영수증 다운로드`}
                    >
                      <Download size={14} aria-hidden="true" />
                      <span>받기</span>
                    </button>
                  </td>
                </tr>
              )) : (
                <tr><td colSpan={5} className="payment-history-empty">{t('billing.payments_empty')}</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
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
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'info';
  const [showApply, setShowApply] = useState(false);

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
        <h1 className="page-title">{t('billing.title')}</h1>
        <p className="sub-title">결제 정보와 결제 내역을 관리합니다.</p>
      </div>
      <SectionTabs
        tabs={[
          { key: 'info',    label: '결제정보' },
          { key: 'history', label: t('billing.payments_title') },
        ]}
        value={activeTab}
        onChange={setActiveTab}
        ariaLabel="결제관리 카테고리"
      />
      {/* 탭 ↔ 콘텐츠 간격 — 다른 페이지(알림 인박스 등)와 동일 톤 (사용자 요구 2026-05-10) */}
      <div className="payment-tab-content">
        {activeTab === 'info' && <PaymentInfoTab onApply={() => setShowApply(true)} />}
        {activeTab === 'history' && <PaymentHistoryTab />}
      </div>
    </div>
  );
};

export default PaymentManagement;
