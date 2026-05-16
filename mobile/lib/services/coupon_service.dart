import 'api_client.dart';

/// 쿠폰 도메인 API.
class CouponService {
  CouponService._();
  static final CouponService instance = CouponService._();
  factory CouponService() => instance;

  final _api = ApiClient.instance;

  /// 내 쿠폰 목록. 상태 필터: ?status=active|used|expired|all
  Future<List<Map<String, dynamic>>> myCoupons({String? status}) async {
    final qs = (status != null && status.isNotEmpty) ? '?status=$status' : '';
    final data = await _api.get('/api/coupons$qs');
    return (data['coupons'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  }

  /// 쿠폰 상세 (QR / 코드 / 할인 정책).
  Future<Map<String, dynamic>> get(int couponId) async {
    final data = await _api.get('/api/coupons/$couponId');
    return (data['coupon'] as Map?)?.cast<String, dynamic>() ?? {};
  }

  /// 쿠폰 사용 처리 (전자상거래법: 소비자 확인 후 사용 확정).
  Future<void> useCoupon(int couponId) async {
    await _api.post('/api/coupons/$couponId/use', {});
  }
}
