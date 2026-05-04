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

  /** 메시지 페이지 조회 */
  listMessages(rid, { afterId, limit = 50 } = {}) {
    const params = new URLSearchParams();
    if (afterId !== undefined) params.set('after_id', afterId);
    params.set('limit', String(limit));
    const qs = params.toString();
    return apiClient.get(`/api/chat/rooms/${rid}/messages?${qs}`);
  },

  /** 메시지 전송 */
  sendMessage(rid, body) {
    return apiClient.post(`/api/chat/rooms/${rid}/messages`, { body });
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
   */
  subscribe(rid) {
    const token = localStorage.getItem('pathwave_token') || '';
    const url = `/api/chat/rooms/${rid}/stream?token=${encodeURIComponent(token)}`;
    return new EventSource(url, { withCredentials: false });
  },
};

export default ChatService;
