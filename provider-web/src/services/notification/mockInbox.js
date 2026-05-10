/**
 * Notification Inbox mock — 시설관리자가 받은 알림 (운영자 수신).
 * 향후 GET /api/notifications/inbox 응답으로 대체.
 *
 * 카테고리 (13개):
 *   chat                     — 고객 채팅 알림
 *   coupon_depleted          — 쿠폰 소진
 *   stamp_depleted           — 스탬프 소진
 *   payment_completed        — 결제 완료
 *   payment_failed           — 결제 실패
 *   refund_request           — 환불 요청
 *   send_result              — 알림 발송 결과
 *   event_ending             — 이벤트 종료 예정
 *   coupon_expiring          — 쿠폰 유효기간 만료 예정
 *   stamp_low                — 스탬프 잔여 부족
 *   ad_approval              — 광고/혜택 승인 결과
 *   business_info_result     — 사업자정보 변경 승인/반려
 *   withdrawal_result        — 탈퇴 요청 처리결과
 */

import {
  MessageCircle, Ticket, Stamp, CreditCard, AlertTriangle,
  Undo2, Send, Calendar, Clock, BatteryLow,
  ShieldCheck, FileEdit, UserMinus,
} from 'lucide-react';

/* 카테고리별 메타 — 아이콘 / variant / 한글 라벨 */
export const NOTIFICATION_CATEGORIES = {
  chat:                 { icon: MessageCircle, variant: 'accent',  label: '고객 채팅' },
  coupon_depleted:      { icon: Ticket,        variant: 'warning', label: '쿠폰 소진' },
  stamp_depleted:       { icon: Stamp,         variant: 'warning', label: '스탬프 소진' },
  payment_completed:    { icon: CreditCard,    variant: 'success', label: '결제 완료' },
  payment_failed:       { icon: AlertTriangle, variant: 'danger',  label: '결제 실패' },
  refund_request:       { icon: Undo2,         variant: 'warning', label: '환불 요청' },
  send_result:          { icon: Send,          variant: 'info',    label: '발송 결과' },
  event_ending:         { icon: Calendar,      variant: 'info',    label: '이벤트 종료 예정' },
  coupon_expiring:      { icon: Clock,         variant: 'warning', label: '쿠폰 만료 예정' },
  stamp_low:            { icon: BatteryLow,    variant: 'warning', label: '스탬프 잔여 부족' },
  ad_approval:          { icon: ShieldCheck,   variant: 'success', label: '광고 승인 결과' },
  business_info_result: { icon: FileEdit,      variant: 'info',    label: '사업자정보 변경 결과' },
  withdrawal_result:    { icon: UserMinus,     variant: 'neutral', label: '탈퇴 요청 결과' },
};

const minutesAgo = (n) => new Date(Date.now() - n * 60_000).toISOString();
const hoursAgo   = (n) => new Date(Date.now() - n * 3_600_000).toISOString();
const daysAgo    = (n) => new Date(Date.now() - n * 86_400_000).toISOString();

/**
 * 시설 운영자 받은 알림 — 기준: 호텔H 기준 mock 14건.
 * 미확인(read_at=null) 4개, 읽음 10개, important 2개.
 */
export const MOCK_INBOX = [
  // ── important + 미확인 (상단 고정) ─────────────────────────────────
  {
    id: 'n-1',
    category: 'payment_failed',
    title: '결제 실패',
    body: '5월 결제가 실패했습니다. 카드 정보를 확인해주세요.',
    important: true,
    read_at: null,
    created_at: hoursAgo(2),
    payload: { service: 'wifi', amount: 1024100 },
  },
  {
    id: 'n-2',
    category: 'refund_request',
    title: '환불 요청 접수',
    body: '와이파이 5001호 환불 요청이 접수되었습니다.',
    important: true,
    read_at: null,
    created_at: hoursAgo(4),
    payload: { wifi_id: 4 },
  },

  // ── 일반 미확인 ─────────────────────────────────────────────────
  {
    id: 'n-3',
    category: 'chat',
    title: '신규 고객 채팅',
    body: '田中花子 님이 와이파이 비밀번호 문의를 남겼습니다.',
    important: false,
    read_at: null,
    created_at: minutesAgo(15),
    payload: { chat_id: 3 },
  },
  {
    id: 'n-4',
    category: 'send_result',
    title: '알림 발송 완료',
    body: '"여름맞이 전품목 10% 할인" 알림이 1,243명에게 전송됐습니다.',
    important: false,
    read_at: null,
    created_at: hoursAgo(1),
    payload: { campaign_id: 2, sent: 1243 },
  },

  // ── 읽음 ───────────────────────────────────────────────────────
  {
    id: 'n-5',
    category: 'business_info_result',
    title: '사업자정보 변경 승인',
    body: '대표자 연락처 변경 요청이 승인되어 반영되었습니다.',
    important: false,
    read_at: hoursAgo(20),
    created_at: hoursAgo(22),
    payload: { request_id: 'biz-1', result: 'approved' },
  },
  {
    id: 'n-6',
    category: 'coupon_depleted',
    title: '쿠폰 소진 임박',
    body: '"호텔H 썬베드 50명 무료 이용권" 잔여 5장.',
    important: false,
    read_at: daysAgo(1),
    created_at: daysAgo(1),
    payload: { coupon_id: 1, remaining: 5 },
  },
  {
    id: 'n-7',
    category: 'stamp_low',
    title: '스탬프 잔여 부족',
    body: '"호텔H 숙박 스탬프 이벤트" 잔여 12개. 보충을 권장합니다.',
    important: false,
    read_at: daysAgo(2),
    created_at: daysAgo(2),
    payload: { stamp_id: 1, remaining: 12 },
  },
  {
    id: 'n-8',
    category: 'event_ending',
    title: '이벤트 종료 D-3',
    body: '"호텔H 썬베드 선착순 50명 무료 이용권" 이 3일 후 종료됩니다.',
    important: false,
    read_at: daysAgo(2),
    created_at: daysAgo(2),
    payload: { coupon_id: 1, days_left: 3 },
  },
  {
    id: 'n-9',
    category: 'payment_completed',
    title: '결제 완료',
    body: '4월 와이파이 132개 결제가 완료되었습니다 (1,016,000원).',
    important: false,
    read_at: daysAgo(3),
    created_at: daysAgo(3),
    payload: { amount: 1016000 },
  },
  {
    id: 'n-10',
    category: 'ad_approval',
    title: '광고 승인 완료',
    body: '"여름맞이 10% 할인" 광고 발송이 승인되었습니다.',
    important: false,
    read_at: daysAgo(5),
    created_at: daysAgo(5),
    payload: { campaign_id: 2 },
  },
  {
    id: 'n-11',
    category: 'coupon_expiring',
    title: '쿠폰 만료 D-7',
    body: '"아메리카노 무료 증정 쿠폰" 이 7일 후 만료됩니다.',
    important: false,
    read_at: daysAgo(7),
    created_at: daysAgo(7),
    payload: { coupon_id: 2, days_left: 7 },
  },
  {
    id: 'n-12',
    category: 'stamp_depleted',
    title: '스탬프 종료',
    body: '"봄맞이 첫 방문 스탬프" 가 종료되었습니다.',
    important: false,
    read_at: daysAgo(14),
    created_at: daysAgo(14),
    payload: { stamp_id: 4 },
  },
  {
    id: 'n-13',
    category: 'withdrawal_result',
    title: '탈퇴 요청 반려',
    body: '미정산 결제건이 있어 탈퇴 요청이 반려되었습니다. 정산 후 재요청해주세요.',
    important: false,
    read_at: daysAgo(20),
    created_at: daysAgo(20),
    payload: { request_id: 'wd-1', result: 'rejected' },
  },
  {
    id: 'n-14',
    category: 'business_info_result',
    title: '주소 변경 반려',
    body: '제출한 사업자등록증에 변경된 주소가 확인되지 않습니다. 서류를 다시 첨부해주세요.',
    important: false,
    read_at: daysAgo(25),
    created_at: daysAgo(25),
    payload: { request_id: 'biz-0', result: 'rejected' },
  },
];

export const getUnreadCount = (list = MOCK_INBOX) =>
  list.filter((n) => n.read_at === null).length;
