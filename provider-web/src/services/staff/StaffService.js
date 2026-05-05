/**
 * StaffService — 직원 초대/관리 백엔드 연동.
 *
 * 백엔드: routes/staff.py — /api/staff/*
 *   POST /api/staff/invite       — 직원 초대 (이메일 발송)
 *   GET  /api/staff              — 초대 목록
 *   POST /api/staff/<iid>/resend — 초대 재발송
 *   DELETE /api/staff/<iid>      — 초대 철회 / 직원 비활성화
 *   POST /api/staff/accept       — 초대 수락 (직원이 사용)
 *   POST /api/staff/login        — 직원 로그인
 *   GET  /api/staff/me           — 현재 직원 정보
 *   GET  /api/staff/me/today     — 오늘의 활동
 */
import apiClient from '../apiClient';

export const ROLES = {
  OWNER: 'OWNER',
  MANAGER: 'MANAGER',
  STAFF: 'STAFF',
};

export const ROLE_LABELS = {
  [ROLES.OWNER]: '대표',
  [ROLES.MANAGER]: '관리자',
  [ROLES.STAFF]: '직원',
};

export const STATUS = {
  ACTIVE: 'ACTIVE',
  INVITED: 'INVITED',
  DISABLED: 'DISABLED',
};

export const STATUS_LABELS = {
  [STATUS.ACTIVE]: '활성',
  [STATUS.INVITED]: '초대중',
  [STATUS.DISABLED]: '비활성',
};

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const validateEmail = (email) => {
  if (!email || typeof email !== 'string') {
    return { valid: false, error: '이메일을 입력해 주세요.' };
  }
  const trimmed = email.trim();
  if (trimmed.length === 0) {
    return { valid: false, error: '이메일을 입력해 주세요.' };
  }
  if (trimmed.length > 254) {
    return { valid: false, error: '이메일이 너무 깁니다.' };
  }
  if (!EMAIL_REGEX.test(trimmed)) {
    return { valid: false, error: '유효한 이메일 형식이 아닙니다.' };
  }
  const domain = trimmed.split('@')[1];
  if (!domain || !domain.includes('.')) {
    return { valid: false, error: '유효한 이메일 도메인이 아닙니다.' };
  }
  return { valid: true, error: null };
};

const StaffService = {
  /** 직원 초대 (이메일 발송) */
  invite(payload) {
    return apiClient.post('/api/staff/invite', payload);
  },

  /** 초대 목록 조회 */
  list() {
    return apiClient.get('/api/staff');
  },

  /** 초대 재발송 */
  resend(invitationId) {
    return apiClient.post(`/api/staff/${invitationId}/resend`);
  },

  /** 초대 철회 / 직원 비활성화 */
  remove(invitationId) {
    return apiClient.delete(`/api/staff/${invitationId}`);
  },

  /** 직원 본인 — 초대 수락 */
  accept(payload) {
    return apiClient.post('/api/staff/accept', payload);
  },

  /** 직원 로그인 */
  login(email, password) {
    return apiClient.post('/api/staff/login', { email, password });
  },

  /** 현재 직원 정보 */
  me() {
    return apiClient.get('/api/staff/me');
  },

  /** 직원 오늘의 활동 (스탬프 적립/쿠폰 사용 등) */
  today() {
    return apiClient.get('/api/staff/me/today');
  },
};

export default StaffService;
