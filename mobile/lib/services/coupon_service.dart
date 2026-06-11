import 'api_client.dart';

/// 쿠폰 도메인 API.
class CouponService {
  CouponService._();
  static final CouponService instance = CouponService._();
  factory CouponService() => instance;

  final _api = ApiClient.instance;

  /// 내 쿠폰 목록. 상태 필터: ?status=active|used|expired|all
  Future<List<Map<String, dynamic>>> myCoupons({String? status}) async {
    // 2026-06-09 — 백엔드 라우트 정합: /api/users/me/coupons
    final qs = (status != null && status.isNotEmpty) ? '?status=$status' : '';
    final data = await _api.get('/api/users/me/coupons$qs');
    return (data['coupons'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  /// 쿠폰 상세 (QR / 코드 / 할인 정책).
  Future<Map<String, dynamic>> get(int couponId) async {
    final data = await _api.get('/api/coupons/$couponId');
    return (data['coupon'] as Map?)?.cast<String, dynamic>() ?? {};
  }

  // 2026-06-11 — useCoupon 제거. backend /use 는 매장 직원 전용 (facility actor)
  // 정책: 사용자는 쿠폰 번호를 제시, 직원이 provider 콘솔에서 사용 처리.
}
