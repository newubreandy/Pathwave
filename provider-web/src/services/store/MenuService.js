/**
 * MenuService — 매장 메뉴 OCR + 항목 CRUD (D-4-b).
 *
 * 백엔드: routes/menu.py
 *   POST   /api/facilities/{fid}/menu/upload   — 이미지 b64 업로드 + OCR
 *   GET    /api/facilities/{fid}/menu?lang=    — lang 별 메뉴 항목
 *   POST   /api/facilities/{fid}/menu/items    — 수동 신규
 *   PATCH  /api/facility-menu-items/{id}       — 수정 (가격은 KRW 강제)
 *   DELETE /api/facility-menu-items/{id}       — 삭제 + 종속 번역 cascade
 */
import apiClient from '../apiClient';

const MenuService = {
  /** ko 메뉴 (또는 lang 별) 목록 */
  list(fid, lang = 'ko') {
    return apiClient.get(`/api/facilities/${fid}/menu?lang=${lang}`);
  },

  /** 사진 업로드 + OCR. payload: { image_b64, replace?: bool } */
  uploadImage(fid, payload) {
    return apiClient.post(`/api/facilities/${fid}/menu/upload`, payload);
  },

  /** 수동 신규 1건 */
  createItem(fid, payload) {
    return apiClient.post(`/api/facilities/${fid}/menu/items`, payload);
  },

  /** 항목 수정. body 에 변경할 필드만 보냄 */
  updateItem(iid, payload) {
    return apiClient.patch(`/api/facility-menu-items/${iid}`, payload);
  },

  /** 항목 삭제 (종속 번역 cascade) */
  deleteItem(iid) {
    return apiClient.delete(`/api/facility-menu-items/${iid}`);
  },

  /** File → base64 (data URL prefix 제외) */
  async fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result || '';
        const comma = result.indexOf(',');
        resolve(comma >= 0 ? result.slice(comma + 1) : result);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  },
};

export default MenuService;
