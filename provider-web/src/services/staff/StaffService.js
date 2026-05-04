/**
 * StaffService
 * 직원 관리 비즈니스 로직 (Mock 데이터)
 * 추후 REST API로 교체 예정
 */

const ROLES = {
  OWNER: 'OWNER',
  MANAGER: 'MANAGER',
  STAFF: 'STAFF',
};

const ROLE_LABELS = {
  [ROLES.OWNER]: '대표',
  [ROLES.MANAGER]: '관리자',
  [ROLES.STAFF]: '직원',
};

const STATUS = {
  ACTIVE: 'ACTIVE',
  INVITED: 'INVITED',
  DISABLED: 'DISABLED',
};

const STATUS_LABELS = {
  [STATUS.ACTIVE]: '활성',
  [STATUS.INVITED]: '초대중',
  [STATUS.DISABLED]: '비활성',
};

/* ── 역할별 권한 매트릭스 ── */
const PERMISSIONS = {
  [ROLES.OWNER]: {
    store: 'write',        // 매장안내
    chat: 'write',         // 채팅
    stamps: 'write',       // 스탬프
    coupons: 'write',      // 쿠폰
    wifi: 'write',         // 와이파이
    notifications: 'write',// 알림발송
    report: 'write',       // 리포트
    staff: 'write',        // 직원관리
    payments: 'write',     // 결제관리
    settings: 'write',     // 설정
    profile: 'write',      // 사업자정보
  },
  [ROLES.MANAGER]: {
    store: 'write',
    chat: 'write',
    stamps: 'write',
    coupons: 'write',
    wifi: 'read',
    notifications: 'read',
    report: 'read',
    staff: 'hidden',
    payments: 'hidden',
    settings: 'read',
    profile: 'hidden',
  },
  [ROLES.STAFF]: {
    store: 'write',
    chat: 'write',
    stamps: 'write',
    coupons: 'write',
    wifi: 'read',
    notifications: 'read',
    report: 'read',
    staff: 'hidden',
    payments: 'hidden',
    settings: 'read',
    profile: 'hidden',
  },
};

/* ── Mock 데이터 ── */
const STORAGE_KEY = 'pathwave_staff';

const DEFAULT_STAFF = [
  {
    id: 'sm_1',
    userId: 'u123',
    storeId: 'store_1',
    name: '홍길동',
    email: 'hong@hotelh.com',
    phone: '010-1234-5678',
    role: ROLES.OWNER,
    status: STATUS.ACTIVE,
    invitedAt: '2025-01-15',
    joinedAt: '2025-01-15',
    agreedTermsAt: '2025-01-15',
  },
  {
    id: 'sm_2',
    userId: 'u456',
    storeId: 'store_1',
    name: '신나라',
    email: 'shin@hotelh.com',
    phone: '010-9876-5432',
    role: ROLES.MANAGER,
    status: STATUS.ACTIVE,
    invitedAt: '2025-02-10',
    joinedAt: '2025-02-11',
    agreedTermsAt: '2025-02-11',
  },
  {
    id: 'sm_3',
    userId: null,
    storeId: 'store_1',
    name: '김알바',
    email: 'kim.alba@gmail.com',
    phone: '010-5555-1234',
    role: ROLES.STAFF,
    status: STATUS.INVITED,
    invitedAt: new Date().toISOString().split('T')[0],
    joinedAt: null,
    agreedTermsAt: null,
  },
];

/* ── 이메일 유효성 검증 ── */
const EMAIL_REGEX = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

const validateEmail = (email) => {
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
  // 도메인 부분 검증
  const domain = trimmed.split('@')[1];
  if (!domain || !domain.includes('.')) {
    return { valid: false, error: '유효한 이메일 도메인이 아닙니다.' };
  }
  return { valid: true, error: null };
};

class StaffService {
  constructor() {
    this._loadData();
  }

  _loadData() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      this.data = stored ? JSON.parse(stored) : [...DEFAULT_STAFF];
    } catch {
      this.data = [...DEFAULT_STAFF];
    }
  }

  _save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(this.data));
  }

  /**
   * 매장 직원 목록 조회
   */
  async getStaffList(storeId = 'store_1') {
    return new Promise((resolve) => {
      setTimeout(() => {
        const list = this.data.filter(m => m.storeId === storeId);
        // OWNER > MANAGER > STAFF, ACTIVE > INVITED > DISABLED
        const roleOrder = { OWNER: 0, MANAGER: 1, STAFF: 2 };
        const statusOrder = { ACTIVE: 0, INVITED: 1, DISABLED: 2 };
        list.sort((a, b) =>
          roleOrder[a.role] - roleOrder[b.role] ||
          statusOrder[a.status] - statusOrder[b.status]
        );
        resolve([...list]);
      }, 300);
    });
  }

  /**
   * 직원 초대
   */
  async inviteStaff(storeId, { email, name, phone, role }) {
    const validation = validateEmail(email);
    if (!validation.valid) {
      throw new Error(validation.error);
    }

    // 같은 매장 중복 초대 확인
    const existing = this.data.find(
      m => m.email === email.trim() && m.storeId === storeId
    );
    if (existing) {
      throw new Error('이미 초대된 이메일입니다.');
    }

    // 자기 초대 방지
    const currentUser = JSON.parse(localStorage.getItem('pathwave_user') || '{}');
    if (currentUser.email === email.trim()) {
      throw new Error('본인을 초대할 수 없습니다.');
    }

    return new Promise((resolve) => {
      setTimeout(() => {
        const newMember = {
          id: 'sm_' + Date.now(),
          userId: null,
          storeId,
          name: name.trim(),
          email: email.trim(),
          phone: phone.trim(),
          role: role || ROLES.STAFF,
          status: STATUS.INVITED,
          invitedAt: new Date().toISOString().split('T')[0],
          joinedAt: null,
          agreedTermsAt: null,
        };
        this.data.push(newMember);
        this._save();
        resolve(newMember);
      }, 500);
    });
  }

  /**
   * 역할 변경 (OWNER만 가능)
   */
  async updateRole(membershipId, newRole) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const member = this.data.find(m => m.id === membershipId);
        if (!member) {
          reject(new Error('멤버를 찾을 수 없습니다.'));
          return;
        }
        if (member.role === ROLES.OWNER) {
          reject(new Error('대표의 역할은 변경할 수 없습니다.'));
          return;
        }
        member.role = newRole;
        this._save();
        resolve({ ...member });
      }, 300);
    });
  }

  /**
   * 직원 비활성화
   */
  async disableStaff(membershipId) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const member = this.data.find(m => m.id === membershipId);
        if (!member) {
          reject(new Error('멤버를 찾을 수 없습니다.'));
          return;
        }
        if (member.role === ROLES.OWNER) {
          reject(new Error('대표는 비활성화할 수 없습니다.'));
          return;
        }
        member.status = STATUS.DISABLED;
        this._save();
        resolve({ ...member });
      }, 300);
    });
  }

  /**
   * 직원 삭제
   */
  async removeStaff(membershipId) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const idx = this.data.findIndex(m => m.id === membershipId);
        if (idx === -1) {
          reject(new Error('멤버를 찾을 수 없습니다.'));
          return;
        }
        if (this.data[idx].role === ROLES.OWNER) {
          reject(new Error('대표는 삭제할 수 없습니다.'));
          return;
        }
        const removed = this.data.splice(idx, 1)[0];
        this._save();
        resolve(removed);
      }, 300);
    });
  }

  /**
   * 초대 재발송
   */
  async resendInvite(membershipId) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const member = this.data.find(m => m.id === membershipId);
        if (!member) {
          reject(new Error('멤버를 찾을 수 없습니다.'));
          return;
        }
        if (member.status !== STATUS.INVITED) {
          reject(new Error('초대 상태의 직원만 재발송할 수 있습니다.'));
          return;
        }
        member.invitedAt = new Date().toISOString().split('T')[0];
        this._save();
        resolve({ ...member });
      }, 300);
    });
  }

  /**
   * 초대 만료 확인 (발송 당일 자정까지)
   */
  isInviteExpired(invitedAt) {
    if (!invitedAt) return true;
    const today = new Date().toISOString().split('T')[0];
    return invitedAt < today;
  }
}

export { ROLES, ROLE_LABELS, STATUS, STATUS_LABELS, PERMISSIONS, validateEmail };
export default new StaffService();
