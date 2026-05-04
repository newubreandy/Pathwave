/**
 * LocationService
 * 1차 백엔드 모듈: 매장 위치, 사용자 위치 등 지리 정보 및 지도 렌더링 설정 처리
 * 현재 OpenStreetMap(Leaflet)과 연동되며, 추후 Google Maps나 카카오맵 API로 교체 시 이 모듈만 수정하면 됩니다.
 */
class LocationService {
  /**
   * 기본 좌표 가져오기 (초기 위치)
   */
  getDefaultCoordinates() {
    return { lat: 37.5665, lng: 126.9780 }; // 서울 시청
  }

  /**
   * 사용자의 현재 위치 가져오기 (브라우저 Geolocation API)
   * @returns {Promise<Object>} { lat, lng }
   */
  async getCurrentPosition() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error("Geolocation is not supported by this browser."));
        return;
      }
      
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          reject(error);
        },
        { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
      );
    });
  }

  /**
   * 두 좌표 간의 거리 계산 (Haversine formula)
   * @param {Object} coord1 { lat, lng }
   * @param {Object} coord2 { lat, lng }
   * @returns {number} 거리 (km)
   */
  calculateDistance(coord1, coord2) {
    const R = 6371; // Earth's radius in km
    const dLat = (coord2.lat - coord1.lat) * Math.PI / 180;
    const dLon = (coord2.lng - coord1.lng) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(coord1.lat * Math.PI / 180) * Math.cos(coord2.lat * Math.PI / 180) * 
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  }

  /**
   * 주소로 좌표 검색 (Geocoding - 모의 구현)
   * 실제 운영 시 Kakao Local API나 Google Geocoding API 연동
   * @param {string} address 
   * @returns {Promise<Object>} { lat, lng }
   */
  async geocodeAddress(address) {
    // TODO: 백엔드 지오코딩 API 연동
    return new Promise((resolve) => {
      setTimeout(() => {
        // 모의 좌표 반환
        resolve({ lat: 37.4979, lng: 127.0276 }); // 강남역
      }, 500);
    });
  }
}

export default new LocationService();
