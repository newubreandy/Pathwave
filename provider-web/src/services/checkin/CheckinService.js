/**
 * CheckinService — P22-b (2026-05-26): provider 측 회원 QR 체크인 클라이언트.
 *
 * 백엔드 routes/checkin.py 호출 헬퍼.
 *
 * 엔드포인트
 * ---------
 * POST /api/checkin/verify
 *   - body: { token: '<member_qr_jwt>' }
 *   - 응답: { user_id, email, is_minor, actor: { sub_type, facility_id } }
 *
 * 사용
 * ----
 *   const result = await CheckinService.verify(scannedToken);
 *   if (result.success) {
 *     // result.user_id, email, is_minor 사용
 *   }
 */
import apiClient from '../apiClient';

const CheckinService = {
  /**
   * 회원 QR 토큰 검증. 손님 정보 반환.
   * @param {string} token — QR 코드에서 스캔한 JWT
   * @returns {Promise<{success, user_id, email, is_minor, actor, message?}>}
   */
  verify: (token) => apiClient.post('/api/checkin/verify', { token }),

  /**
   * A-1 (2026-05-29): 제로페이 결제 확정.
   * @param {string} token — 회원 QR JWT
   * @param {number} amount — 결제 금액 (원)
   * ⚠️ v1 placeholder — 실 제로페이 송금은 가맹점 키 도착 후.
   */
  zeropayCharge: (token, amount) =>
    apiClient.post('/api/checkin/zeropay-charge', { token, amount }),
};

export default CheckinService;
