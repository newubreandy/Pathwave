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

// ── 상수 / enum (StaffManagement.jsx 등에서 사용) ──────────────────────────

export const ROLES = Object.freeze({
  OWNER:   'owner',
  MANAGER: 'manager',
  STAFF:   'staff',
});

export const ROLE_LABELS = Object.freeze({
  [ROLES.OWNER]:   '대표',
  [ROLES.MANAGER]: '매니저',
  [ROLES.STAFF]:   '직원',
});

export const STATUS = Object.freeze({
  INVITED:  'invited',
  ACTIVE:   'active',
  DISABLED: 'disabled',
});

export const STATUS_LABELS = Object.freeze({
  [STATUS.INVITED]:  '초대됨',
  [STATUS.ACTIVE]:   '활성',
  [STATUS.DISABLED]: '비활성',
});


// ── 헬퍼 함수 ──────────────────────────────────────────────────────────────

/**
 * 이메일 형식 검증.
 * @returns {{ ok: boolean, message?: string }}
 */
export function validateEmail(email) {
  const trimmed = (email || '').trim();
  if (!trimmed) return { ok: false, message: '이메일을 입력해 주세요.' };
  // 단순 검증 — 운영에서는 더 정밀한 RFC 5322 검증 또는 백엔드 위임
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!re.test(trimmed)) {
    return { ok: false, message: '이메일 형식이 올바르지 않습니다.' };
  }
  return { ok: true };
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

  /**
   * 초대 만료 여부 — 초대 발송 후 7일 경과 판정.
   * 운영에서는 백엔드 invitations.expires_at 사용 권장 (본 함수는 UI 표시용 휴리스틱).
   */
  isInviteExpired(invitedAt) {
    if (!invitedAt) return false;
    try {
      const sent = new Date(invitedAt);
      if (Number.isNaN(sent.getTime())) return false;
      const days = (Date.now() - sent.getTime()) / (1000 * 60 * 60 * 24);
      return days > 7;
    } catch {
      return false;
    }
  },

  /** 직원의 role 업데이트 (사장 전용) */
  setRole(invitationId, role) {
    return apiClient.patch(`/api/staff/${invitationId}`, { role });
  },
};

export default StaffService;
