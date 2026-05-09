/**
 * mockStamps — 백엔드 미연동 환경에서 사용하는 스탬프 카드 더미 데이터.
 * Stamps.jsx (목록) / StampForm.jsx (상세·수정) 양쪽에서 import.
 *
 * TODO: StampService.list() / get(id) 백엔드 연동 후 제거.
 */

export const MOCK_STAMPS = [
  {
    id: 1,
    name: '호텔H 숙박 스탬프 이벤트',
    status: 'active',
    period: '2026.05.01 ~ 2026.07.31',
    accumStart: '2026-05-01',
    accumEnd: '2026-07-31',
    paymentAmount: 50000,
    benefits: [
      { id: 1, count: '10회차', desc: '1박 무료 숙박권' },
    ],
  },
  {
    id: 2,
    name: '카페 아메리카노 적립',
    status: 'active',
    period: '2026.04.01 ~ 2026.12.31',
    accumStart: '2026-04-01',
    accumEnd: '2026-12-31',
    paymentAmount: 4500,
    benefits: [
      { id: 1, count: '8회차', desc: '아메리카노 1잔 무료' },
    ],
  },
  {
    id: 3,
    name: '런치 스페셜 스탬프',
    status: 'paused',
    period: '2026.03.01 ~ 2026.06.30',
    accumStart: '2026-03-01',
    accumEnd: '2026-06-30',
    paymentAmount: 12000,
    benefits: [
      { id: 1, count: '5회차', desc: '다음 식사 30% 할인' },
    ],
  },
  {
    id: 4,
    name: '봄맞이 첫 방문 스탬프',
    status: 'ended',
    period: '2026.01.15 ~ 2026.02.28',
    accumStart: '2026-01-15',
    accumEnd: '2026-02-28',
    paymentAmount: 0,
    benefits: [
      { id: 1, count: '3회차', desc: '디저트 무료' },
    ],
  },
];

export const findMockStamp = (id) => {
  const numId = Number(id);
  return MOCK_STAMPS.find((s) => s.id === numId);
};
