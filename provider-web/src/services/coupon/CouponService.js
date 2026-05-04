/**
 * CouponService
 * 2차 백엔드 모듈: 쿠폰 이벤트 생성, 조회, 발급 비즈니스 로직
 */
class CouponService {
  constructor() {
    this.coupons = [
      {
        id: 1,
        title: '신규 고객 환영 10% 할인',
        status: 'active',
        discountType: 'percentage', // percentage, fixed
        discountValue: 10,
        validUntil: '2026-12-31'
      }
    ];
  }

  /**
   * 전체 쿠폰 목록 조회
   * @returns {Promise<Array>}
   */
  async getCoupons() {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([...this.coupons]);
      }, 300);
    });
  }

  /**
   * 쿠폰 상세 조회
   * @param {number|string} id 
   * @returns {Promise<Object>}
   */
  async getCouponById(id) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const coupon = this.coupons.find(c => c.id.toString() === id.toString());
        if (coupon) {
          resolve({ ...coupon });
        } else {
          reject(new Error('Coupon not found'));
        }
      }, 300);
    });
  }

  /**
   * 신규 쿠폰 생성
   * @param {Object} data 
   * @returns {Promise<Object>}
   */
  async createCoupon(data) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const newCoupon = {
          id: Date.now(),
          status: 'active',
          ...data
        };
        this.coupons.unshift(newCoupon);
        resolve({ ...newCoupon });
      }, 500);
    });
  }

  /**
   * 쿠폰 만료 처리
   * @param {number|string} id 
   * @returns {Promise<boolean>}
   */
  async expireCoupon(id) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const index = this.coupons.findIndex(c => c.id.toString() === id.toString());
        if (index !== -1) {
          this.coupons[index].status = 'expired';
          resolve(true);
        } else {
          reject(new Error('Coupon not found'));
        }
      }, 300);
    });
  }
}

const couponServiceInstance = new CouponService();
export default couponServiceInstance;
