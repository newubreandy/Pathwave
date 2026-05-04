/**
 * StampService
 * 2차 백엔드 모듈: 스탬프 이벤트 생성, 조회, 활성/비활성 처리 비즈니스 로직
 */
class StampService {
  constructor() {
    // 로컬 상태로 목(Mock) 데이터 관리
    this.stamps = [
      {
        id: 1,
        name: '아메리카노 10잔 적립 이벤트',
        status: 'active', // active, paused, ended
        period: '2022.01.29 - 2022.03.30',
        benefit: '아메리카노 10잔 적립 이벤트'
      },
      {
        id: 2,
        name: '여름 시즌 한정 디저트 스탬프',
        status: 'ended',
        period: '2022.01.29 - 2022.03.30',
        benefit: '스탬프 테스트'
      }
    ];
  }

  /**
   * 전체 스탬프 목록 조회
   * @returns {Promise<Array>} 스탬프 목록
   */
  async getStamps() {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([...this.stamps]);
      }, 300);
    });
  }

  /**
   * 특정 스탬프 조회
   * @param {number|string} id 
   * @returns {Promise<Object>} 스탬프 상세 정보
   */
  async getStampById(id) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const stamp = this.stamps.find(s => s.id.toString() === id.toString());
        if (stamp) {
          resolve({ ...stamp });
        } else {
          reject(new Error('Stamp not found'));
        }
      }, 300);
    });
  }

  /**
   * 스탬프 상태 변경 (활성화/일시정지)
   * @param {number|string} id 
   * @returns {Promise<Object>} 변경된 스탬프 정보
   */
  async toggleStampStatus(id) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const index = this.stamps.findIndex(s => s.id.toString() === id.toString());
        if (index !== -1) {
          const currentStatus = this.stamps[index].status;
          if (currentStatus === 'ended') {
            reject(new Error('Cannot toggle ended stamp'));
            return;
          }
          const newStatus = currentStatus === 'active' ? 'paused' : 'active';
          
          // 만약 활성화하려는 경우, 다른 active 스탬프가 있는지 확인 (비즈니스 룰: 1개만 활성화 가능)
          if (newStatus === 'active' && this.stamps.some(s => s.status === 'active' && s.id.toString() !== id.toString())) {
            reject(new Error('Another stamp is already active'));
            return;
          }

          this.stamps[index].status = newStatus;
          resolve({ ...this.stamps[index] });
        } else {
          reject(new Error('Stamp not found'));
        }
      }, 300);
    });
  }

  /**
   * 스탬프 삭제
   * @param {number|string} id 
   * @returns {Promise<boolean>} 성공 여부
   */
  async deleteStamp(id) {
    return new Promise((resolve) => {
      setTimeout(() => {
        this.stamps = this.stamps.filter(s => s.id.toString() !== id.toString());
        resolve(true);
      }, 300);
    });
  }

  /**
   * 신규 스탬프 등록
   * @param {Object} stampData 
   * @returns {Promise<Object>} 생성된 스탬프
   */
  async createStamp(stampData) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (this.stamps.some(s => s.status === 'active')) {
          reject(new Error('Active stamp already exists'));
          return;
        }

        const newStamp = {
          id: Date.now(),
          name: stampData.title,
          status: 'active',
          period: `${stampData.startDate} - ${stampData.endDate}`,
          benefit: stampData.benefits?.[0]?.item || '새로운 이벤트',
          ...stampData
        };
        
        this.stamps.unshift(newStamp);
        resolve({ ...newStamp });
      }, 800);
    });
  }
}

// 싱글톤 인스턴스 반환
const stampServiceInstance = new StampService();
export default stampServiceInstance;
