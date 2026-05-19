import 'api_client.dart';

/// Phase M — 법인 정보 (footer 자동 동기).
///
/// 슈퍼어드민이 admin-web 에서 입력하면 mobile / provider-web / admin-web
/// 모든 콘솔의 footer 가 동일한 값으로 동기화.
///
/// 백엔드: GET /api/company-info (공개, 인증 불필요)
class CompanyInfo {
  final String? companyName;
  final String? ceo;
  final String? bizNumber;
  final String? commerceNumber;
  final String? address;
  final String? phone;
  final String? email;
  final String? hosting;

  const CompanyInfo({
    this.companyName, this.ceo, this.bizNumber, this.commerceNumber,
    this.address, this.phone, this.email, this.hosting,
  });

  factory CompanyInfo.fromJson(Map<String, dynamic> j) => CompanyInfo(
        companyName:    j['company_name']    as String?,
        ceo:            j['ceo']             as String?,
        bizNumber:      j['biz_number']      as String?,
        commerceNumber: j['commerce_number'] as String?,
        address:        j['address']         as String?,
        phone:          j['phone']           as String?,
        email:          j['email']           as String?,
        hosting:        j['hosting']         as String?,
      );

  factory CompanyInfo.empty() => const CompanyInfo();
}

class CompanyInfoService {
  CompanyInfoService._();
  static final CompanyInfoService instance = CompanyInfoService._();
  factory CompanyInfoService() => instance;

  /// 부팅 후 1회 호출. 실패 시 [CompanyInfo.empty] 반환 — 앱은 정상 진행.
  Future<CompanyInfo> get() async {
    try {
      final res = await ApiClient.instance.get('/api/company-info');
      final ci = res['company_info'];
      if (ci is Map<String, dynamic>) return CompanyInfo.fromJson(ci);
      return CompanyInfo.empty();
    } catch (_) {
      return CompanyInfo.empty();
    }
  }
}
