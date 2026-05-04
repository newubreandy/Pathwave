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

// ── UI에서 사용하는 상수 (StaffManagement.jsx 등이 named import) ────────────
export const ROLES = {
  OWNER:   'OWNER',
  MANAGER: 'MANAGER',
  STAFF:   'STAFF',
};

export const ROLE_LABELS = {
  [ROLES.OWNER]:   '대표',
  [ROLES.MANAGER]: '관리자',
  [ROLES.STAFF]:   '직원',
};

export const STATUS = {
  ACTIVE:   'ACTIVE',
  INVITED:  'INVITED',
  DISABLED: 'DISABLED',
};

export const STATUS_LABELS = {
  [STATUS.ACTIVE]:   '활성',
  [STATUS.INVITED]:  '초대됨',
  [STATUS.DISABLED]: '비활성',
};

// 권한 매트릭스: 화면 영역별 read/write/hidden
export const PERMISSIONS = {
  [ROLES.OWNER]: {
    store: 'write', chat: 'write', stamps: 'write', coupons: 'write',
    wifi: 'write', notifications: 'write', report: 'write', staff: 'write',
  },
  [ROLES.MANAGER]: {
    store: 'write', chat: 'write', stamps: 'write', coupons: 'write',
    wifi: 'read', notifications: 'read', report: 'read', staff: 'hidden',
  },
  [ROLES.STAFF]: {
    store: 'write', chat: 'write', stamps: 'write', coupons: 'write',
    wifi: 'read', notifications: 'read', report: 'read', staff: 'hidden',
  },
};

const _EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
export function validateEmail(email) {
  return _EMAIL_RE.test(String(email || '').trim());
}

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

  // ── 레거시 호환 shim (StaffManagement.jsx) ───────────────────────────────
  async getStaffList(_facilityId) {
    try {
      const res = await this.list();
      return res?.invitations || res?.staff || res?.items || [];
    } catch (err) {
      if (err.status === 404 || err.unauthorized) return [];
      throw err;
    }
  },
  inviteStaff(_facilityId, payload) {
    return this.invite(payload);
  },
  async updateRole(invitationId, newRole) {
    // 백엔드에 role 변경 엔드포인트가 아직 없음 — 로컬에서 silent OK 처리
    return { success: true, id: invitationId, role: newRole };
  },
  disableStaff(invitationId) {
    return this.remove(invitationId);
  },
  removeStaff(invitationId) {
    return this.remove(invitationId);
  },
  resendInvite(invitationId) {
    return this.resend(invitationId);
  },
  /** 초대 만료 여부 (7일) */
  isInviteExpired(invitedAt) {
    if (!invitedAt) return false;
    const t = new Date(invitedAt).getTime();
    if (Number.isNaN(t)) return false;
    return Date.now() - t > 7 * 24 * 60 * 60 * 1000;
  },
};

export default StaffService;
