/**
 * BillingService — 시설(매장) 결제·구독 백엔드 연동.
 *
 * 백엔드: routes/billing.py — /api/billing/*
 *   GET    /api/billing/cards                       — 등록 카드 목록
 *   POST   /api/billing/cards                       — 카드 등록 { card_brand, last4 }
 *   DELETE /api/billing/cards/<cid>                 — 카드 삭제
 *   GET    /api/billing/subscriptions               — 구독 목록
 *   POST   /api/billing/subscriptions               — 구독 신청
 *                                                     { service_type, quantity, period_months, receipt_email? }
 *   POST   /api/billing/subscriptions/<sid>/cancel  — 구독 해지
 *   POST   /api/billing/subscriptions/<sid>/extend  — 구독 연장
 *   GET    /api/billing/payments                    — 결제 내역
 *   POST   /api/billing/receipt-email               — 영수증 이메일 설정 { email }
 *
 * ⚠ PCI — 카드 전체번호(PAN)/CVC 는 절대 백엔드로 전송하거나 클라이언트에
 *   저장하지 않는다. POST /cards 는 card_brand + last4(끝 4자리)만 받는다
 *   (실 PG 연동 시 PG 위젯이 돌려주는 토큰/요약 형태).
 *
 * apiClient 는 응답 본문을 그대로 반환한다 (axios 식 res.data 아님).
 *   → 호출부는 res.cards / res.subscriptions / res.card 등으로 접근.
 */
import apiClient from '../apiClient';

const BillingService = {
  // ── 카드 ──────────────────────────────────────────────────────────────────
  /** 등록된 결제 카드 목록 */
  listCards() {
    return apiClient.get('/api/billing/cards');
  },

  /**
   * 카드 등록 — card_brand + 카드번호 끝 4자리만 전송 (PCI).
   * @param {string} cardBrand — 카드사 (예: '신한', 'KB국민')
   * @param {string} last4     — 카드번호 마지막 4자리 (숫자 4자)
   */
  registerCard(cardBrand, last4) {
    return apiClient.post('/api/billing/cards', { card_brand: cardBrand, last4 });
  },

  /** 카드 삭제 */
  deleteCard(cid) {
    return apiClient.delete(`/api/billing/cards/${cid}`);
  },

  // ── 구독 ──────────────────────────────────────────────────────────────────
  /** 내 서비스 구독 목록 */
  listSubscriptions() {
    return apiClient.get('/api/billing/subscriptions');
  },

  /**
   * 서비스 구독 신청 (+ 즉시 결제).
   * @param {Object} p
   * @param {('wifi'|'event'|'notification')} p.serviceType
   * @param {number} p.quantity      — 1 이상
   * @param {number} p.periodMonths  — 1 또는 12
   * @param {string} [p.receiptEmail]
   */
  createSubscription({ serviceType, quantity, periodMonths, receiptEmail }) {
    const body = {
      service_type: serviceType,
      quantity,
      period_months: periodMonths,
    };
    if (receiptEmail) body.receipt_email = receiptEmail;
    return apiClient.post('/api/billing/subscriptions', body);
  },

  /** 구독 해지 */
  cancelSubscription(sid) {
    return apiClient.post(`/api/billing/subscriptions/${sid}/cancel`, {});
  },

  /** 구독 연장 (동일 조건 재결제) */
  extendSubscription(sid) {
    return apiClient.post(`/api/billing/subscriptions/${sid}/extend`, {});
  },

  // ── 결제 내역 ──────────────────────────────────────────────────────────────
  /** 결제 내역 (최근 200건) */
  listPayments() {
    return apiClient.get('/api/billing/payments');
  },

  // ── 영수증 이메일 ──────────────────────────────────────────────────────────
  /** 이후 결제의 기본 영수증 이메일 설정 */
  setReceiptEmail(email) {
    return apiClient.post('/api/billing/receipt-email', { email });
  },
};

export default BillingService;
