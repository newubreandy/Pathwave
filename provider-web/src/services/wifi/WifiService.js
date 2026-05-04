/**
 * WifiService
 * 2차 백엔드 모듈: 매장 와이파이 설정 저장 및 QR 코드 데이터 생성 비즈니스 로직
 */
class WifiService {
  constructor() {
    this.wifiData = {
      ssid: '',
      password: '',
      security: 'WPA/WPA2'
    };
  }

  /**
   * 와이파이 설정 정보 조회
   * @returns {Promise<Object>}
   */
  async getWifiSettings() {
    return new Promise((resolve) => {
      setTimeout(() => {
        const saved = localStorage.getItem('pathwave_wifi');
        if (saved) {
          this.wifiData = JSON.parse(saved);
        }
        resolve({ ...this.wifiData });
      }, 300);
    });
  }

  /**
   * 와이파이 설정 정보 저장
   * @param {Object} data { ssid, password, security }
   * @returns {Promise<boolean>}
   */
  async saveWifiSettings(data) {
    return new Promise((resolve) => {
      setTimeout(() => {
        this.wifiData = { ...this.wifiData, ...data };
        localStorage.setItem('pathwave_wifi', JSON.stringify(this.wifiData));
        resolve(true);
      }, 300);
    });
  }

  /**
   * 와이파이 접속용 QR 코드 문자열 생성 (WIFI:T:WPA;S:mynetwork;P:mypass;;)
   * @param {Object} data 
   * @returns {string} QR 코드 데이터
   */
  generateQRString(data) {
    if (!data.ssid) return '';
    const type = data.security === 'NONE' ? 'nopass' : (data.security === 'WEP' ? 'WEP' : 'WPA');
    const escape = (str) => str.replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/:/g, '\\:');
    
    return `WIFI:T:${type};S:${escape(data.ssid)};P:${escape(data.password)};H:${data.hidden ? 'true' : 'false'};`;
  }
}

const wifiServiceInstance = new WifiService();
export default wifiServiceInstance;
