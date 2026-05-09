/**
 * mockStaff — 백엔드 미연동 환경 직원/관리자 더미 데이터.
 * StaffService.list() 가 API 실패 시 fallback 또는 데모용으로 사용.
 *
 * 사용처: StaffManagement.jsx (직원관리 탭).
 * TODO: 실제 백엔드 연결 후 제거.
 */

import { ROLES, STATUS } from './StaffService';

const now = Date.now();
const daysAgo = (n) => new Date(now - n * 24 * 60 * 60 * 1000).toISOString();

export const MOCK_STAFF = [
  // ── 대표 (사장 본인) — 항상 active ──
  {
    id: 'inv-1',
    email: 'webmaster@hotelh.com',
    name: '홍길동',
    role: ROLES.OWNER,
    status: STATUS.ACTIVE,
    invitedAt: daysAgo(120),
    activatedAt: daysAgo(120),
  },

  // ── 매니저 (운영 책임자) ──
  {
    id: 'inv-2',
    email: 'manager.kim@hotelh.com',
    name: '김민수',
    role: ROLES.MANAGER,
    status: STATUS.ACTIVE,
    invitedAt: daysAgo(85),
    activatedAt: daysAgo(83),
  },

  // ── 직원 1: 활성 ──
  {
    id: 'inv-3',
    email: 'staff.park@hotelh.com',
    name: '박지영',
    role: ROLES.STAFF,
    status: STATUS.ACTIVE,
    invitedAt: daysAgo(45),
    activatedAt: daysAgo(43),
  },

  // ── 직원 2: 활성 ──
  {
    id: 'inv-4',
    email: 'staff.lee@hotelh.com',
    name: '이서연',
    role: ROLES.STAFF,
    status: STATUS.ACTIVE,
    invitedAt: daysAgo(30),
    activatedAt: daysAgo(29),
  },

  // ── 직원 3: 초대됨 (수락 전) — 1일 전 초대 ──
  {
    id: 'inv-5',
    email: 'newbie.choi@hotelh.com',
    name: '최예진',
    role: ROLES.STAFF,
    status: STATUS.INVITED,
    invitedAt: daysAgo(1),
    activatedAt: null,
  },

  // ── 직원 4: 초대 만료 (8일 전 발송, 7일 초과) ──
  {
    id: 'inv-6',
    email: 'expired.jung@hotelh.com',
    name: '정승호',
    role: ROLES.STAFF,
    status: STATUS.INVITED,
    invitedAt: daysAgo(8),
    activatedAt: null,
  },

  // ── 직원 5: 비활성화 ──
  {
    id: 'inv-7',
    email: 'former.kang@hotelh.com',
    name: '강하늘',
    role: ROLES.STAFF,
    status: STATUS.DISABLED,
    invitedAt: daysAgo(180),
    activatedAt: daysAgo(178),
    disabledAt: daysAgo(15),
  },
];

export const findMockStaff = (id) => MOCK_STAFF.find((s) => s.id === id);
