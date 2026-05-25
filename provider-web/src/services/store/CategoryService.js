/**
 * CategoryService — 매장 업종 카테고리 (백엔드 API 연동).
 *
 * 백엔드: routes/categories.py
 *   GET /api/categories — active 카테고리 + group 분류
 *
 * 사장 가입 시 자유 입력 금지 (백엔드가 제공하는 목록만 사용).
 * 슈퍼어드민이 admin-web 에서 카테고리 추가/수정/비활성화.
 *
 * 캐싱
 * ----
 * 한 번 fetch 한 결과는 메모리에 유지. 새로고침 강제 시 refresh().
 * 자유 입력 (addCategory) 은 더 이상 지원 안 함 — 신규 카테고리는 슈퍼어드민 요청.
 */
import apiClient from '../apiClient';

class CategoryService {
  constructor() {
    this._cache    = null;   // [{id, name, group, ...}]
    this._loading  = null;   // 진행 중 Promise (중복 fetch 방지)
  }

  /**
   * 전체 카테고리 fetch (캐시). active 만.
   * @returns {Promise<{categories: Array, groups: Object}>}
   */
  async load() {
    if (this._cache) return this._cache;
    if (!this._loading) {
      this._loading = apiClient.get('/api/categories')
        .then((data) => {
          this._cache = {
            categories: data.categories || [],
            groups:     data.groups || {},
          };
          return this._cache;
        })
        .catch((err) => {
          this._loading = null;
          throw err;
        });
    }
    return this._loading;
  }

  /** 강제 새로고침 (관리자가 추가 후 또는 명시적 리로드) */
  async refresh() {
    this._cache = null;
    this._loading = null;
    return this.load();
  }

  /** 전체 카테고리 이름 배열 (동기 — load() 이후 호출) */
  getCategories() {
    return (this._cache?.categories || []).map((c) => c.name);
  }

  /** 그룹별 분류 (예: {'음식': ['한식전문점', ...], ...}) */
  getGroups() {
    return this._cache?.groups || {};
  }

  /** 키워드 검색 (소문자 부분 일치) */
  searchCategories(keyword) {
    const all = this.getCategories();
    if (!keyword) return all;
    const k = keyword.toLowerCase();
    return all.filter((c) => c.toLowerCase().includes(k));
  }

  /** ⚠️ 자유 입력 차단 — 신규 카테고리는 슈퍼어드민에 요청해야 함. */
  addCategory(_category) {
    console.warn(
      '[CategoryService] 자유 입력 차단됨. 신규 카테고리는 슈퍼어드민에 요청해 주세요.'
    );
  }
}

// 싱글톤
export default new CategoryService();
