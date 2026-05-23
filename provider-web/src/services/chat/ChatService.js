/**
 * ChatService — 매장 ↔ 회원 1:1 채팅 백엔드 연동.
 *
 * 백엔드: routes/chat.py
 *   POST /api/facilities/<fid>/chat/rooms        — 채팅방 생성/검색
 *   GET  /api/chat/rooms                         — 내 채팅방 목록
 *   GET  /api/chat/rooms/<rid>                   — 채팅방 상세
 *   GET  /api/chat/rooms/<rid>/messages          — 메시지 목록 (?after_id=, ?limit=)
 *   POST /api/chat/rooms/<rid>/messages          — 메시지 전송
 *   POST /api/chat/rooms/<rid>/read              — 읽음 처리
 *   GET  /api/chat/rooms/<rid>/stream            — SSE 스트림 (실시간 수신)
 */
import apiClient from '../apiClient';
import { getProviderLang } from '../translation/TranslationService';

const ChatService = {
  /** 회원과의 채팅방 생성 또는 조회 (사장이 시작) */
  openRoom(facilityId, payload) {
    return apiClient.post(`/api/facilities/${facilityId}/chat/rooms`, payload);
  },

  /** 내 채팅방 목록 */
  listRooms() {
    return apiClient.get('/api/chat/rooms');
  },

  /** 채팅방 상세 */
  getRoom(rid) {
    return apiClient.get(`/api/chat/rooms/${rid}`);
  },

  /**
   * 메시지 페이지 조회.
   * ``?lang`` (P8b) — viewer 언어. 백엔드가 lazy 번역해서 ``translated_text`` 필드를 같이 줌.
   */
  listMessages(rid, { afterId, limit = 50 } = {}) {
    const params = new URLSearchParams();
    if (afterId !== undefined) params.set('after_id', afterId);
    params.set('limit', String(limit));
    params.set('lang',  getProviderLang());
    return apiClient.get(`/api/chat/rooms/${rid}/messages?${params.toString()}`);
  },

  /**
   * 메시지 전송.
   * ``lang_hint`` (P8b) — 작성자(매장 측) 단말 언어. 백엔드가 ``body_lang`` 으로 저장.
   */
  sendMessage(rid, body) {
    return apiClient.post(`/api/chat/rooms/${rid}/messages`, {
      body,
      lang_hint: getProviderLang(),
    });
  },

  /** 읽음 처리 */
  markRead(rid) {
    return apiClient.post(`/api/chat/rooms/${rid}/read`);
  },

  /**
   * SSE 실시간 메시지 구독 — EventSource 인스턴스를 돌려준다.
   * 사용:
   *   const es = ChatService.subscribe(rid);
   *   es.addEventListener('message', e => { ... });
   *   es.close();   // 정리
   *
   * 주의: EventSource는 Authorization 헤더를 직접 못 붙이므로
   *       토큰 인증은 쿼리스트링으로 전달.
   * ``lang`` (P8b) — SSE 연결 시작 시 viewer 언어를 한 번에 결정.
   */
  subscribe(rid) {
    const token = localStorage.getItem('pathwave_token') || '';
    const lang  = getProviderLang();
    const url = `/api/chat/rooms/${rid}/stream`
      + `?token=${encodeURIComponent(token)}`
      + `&lang=${encodeURIComponent(lang)}`;
    return new EventSource(url, { withCredentials: false });
  },
};

export default ChatService;
