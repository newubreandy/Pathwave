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
   * 주소로 좌표 검색 (Geocoding) — OSM Nominatim 사용 (2026-06-09).
   *
   * 비용 0 (Google Maps Platform 회피). Nominatim Usage Policy:
   *   - 무료 1 req/sec/IP — Rate Limit 자가 준수
   *   - User-Agent 필수 — 'PathWave/1.0 (admin@pathwave.app)' 송신
   *   - 결과 캐시 권장 — 같은 주소 24h 메모리 캐시
   *
   * @param {string} address
   * @returns {Promise<Object>} { lat, lng } — 실패 시 기본 좌표 fallback
   */
  async geocodeAddress(address) {
    if (!address || !address.trim()) {
      return this.getDefaultCoordinates();
    }
    const key = address.trim();
    if (this._geoCache && this._geoCache[key] &&
        (Date.now() - this._geoCache[key].ts) < 24 * 3600 * 1000) {
      return this._geoCache[key].coords;
    }
    try {
      const url = 'https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=kr&q='
                + encodeURIComponent(key);
      const res = await fetch(url, {
        headers: { 'User-Agent': 'PathWave/1.0 (admin@pathwave.app)' },
      });
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        const coords = {
          lat: parseFloat(data[0].lat),
          lng: parseFloat(data[0].lon),
        };
        this._geoCache = this._geoCache || {};
        this._geoCache[key] = { coords, ts: Date.now() };
        return coords;
      }
    } catch (e) {
      console.warn('[LocationService] Nominatim 실패:', e);
    }
    // 실패 시 기본(서울 시청). 운영 정책 — 사용자가 지도 클릭으로 보정.
    return this.getDefaultCoordinates();
  }
}

export default new LocationService();
