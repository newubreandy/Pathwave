/**
 * StoreService — 시설(매장) CRUD 백엔드 연동.
 *
 * 백엔드: routes/store.py — /api/facilities/*
 *   GET    /api/facilities                   — 내 매장 목록
 *   GET    /api/facilities/<fid>             — 매장 상세
 *   POST   /api/facilities                   — 매장 생성
 *   PATCH  /api/facilities/<fid>             — 매장 정보 수정
 *   DELETE /api/facilities/<fid>             — 매장 삭제
 *   POST   /api/store/<fid>/claim-beacon     — 비콘 SN 클레임 (Phase C)
 *     body: { serial_no, minor? }
 *     major 는 백엔드가 facility_id 로 자동 세팅.
 *     minor 미지정 시 백엔드가 매장 내 다음 순번 자동 할당.
 *   GET    /api/store/<fid>/beacons          — 비콘 목록 (major, minor 포함)
 */
import apiClient from '../apiClient';

const StoreService = {
  /** 내 매장 목록 */
  list() {
    return apiClient.get('/api/facilities');
  },

  /** 매장 상세 */
  get(fid) {
    return apiClient.get(`/api/facilities/${fid}`);
  },

  /**
   * 매장 생성.
   * @param {Object} payload — { name, category, address, phone, business_hours, description, ... }
   */
  create(payload) {
    return apiClient.post('/api/facilities', payload);
  },

  /** 매장 정보 수정 */
  update(fid, payload) {
    return apiClient.patch(`/api/facilities/${fid}`, payload);
  },

  /** 매장 삭제 */
  remove(fid) {
    return apiClient.delete(`/api/facilities/${fid}`);
  },

  /**
   * 비콘 SN 클레임 (Phase C) — 운영자가 발급한 비콘 시리얼을 본인 매장에 연결.
   * @param {string} fid        — 매장(시설) ID
   * @param {string} serialNo   — 비콘 시리얼 번호 (serial_no)
   * @param {number|null} minor — 비콘 번호(minor). null/undefined 이면 백엔드 자동 할당.
   */
  claimBeacon(fid, serialNo, minor) {
    const body = { serial_no: serialNo };
    if (minor !== null && minor !== undefined && minor !== '') {
      body.minor = Number(minor);
    }
    return apiClient.post(`/api/store/${fid}/claim-beacon`, body);
  },

  /**
   * 매장에 등록된 비콘 목록 조회 (Phase C).
   * 응답 각 항목에 major, minor 포함.
   * @param {string} fid — 매장(시설) ID
   */
  listBeacons(fid) {
    return apiClient.get(`/api/store/${fid}/beacons`);
  },

  // ── P-025 매장 다국어 캐시 (D 번들3-B) ─────────────────────────────────
  // 백엔드: GET/PUT/DELETE /api/facilities/<fid>/translations[/<lang>]
  //         POST /api/facilities/<fid>/translations/auto
  /** 매장의 캐시된 번역 전체 (lang 별 name/address/description) */
  listTranslations(fid) {
    return apiClient.get(`/api/facilities/${fid}/translations`);
  },
  /** 특정 lang 의 번역 upsert */
  upsertTranslation(fid, lang, payload) {
    return apiClient.put(`/api/facilities/${fid}/translations/${lang}`, payload);
  },
  /** 특정 lang 번역 삭제 (다음 조회 시 fallback / 자동 재생성) */
  deleteTranslation(fid, lang) {
    return apiClient.delete(`/api/facilities/${fid}/translations/${lang}`);
  },
  /** 자동 번역 트리거 (DeepL 등 외부 provider — stub 모드 가능) */
  autoTranslate(fid, payload = {}) {
    return apiClient.post(`/api/facilities/${fid}/translations/auto`, payload);
  },
};

export default StoreService;
