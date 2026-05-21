import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../services/company_info_service.dart';
import '../services/i18n_service.dart';
import '../utils/app_theme.dart';
import 'pw_card.dart';

/// PathWave 법인 정보 푸터 위젯.
///
/// memory/ui_legal_compliance: 한국 전자상거래법 §10 / 정보통신망법 §50 /
/// 위치정보법 필수 표기 사항. footer.* i18n 키는 3 콘솔 공통.
///
/// 데이터 소스 (Phase M):
///   GET /api/company-info → 슈퍼어드민 입력값
///   값이 null/공백이면 i18n 키 fallback 사용 (어드민 미입력 단계 안전 처리)
///
/// 앱스토어 심사 정책 (Apple Guideline 2.3.10 / 4.0):
///   API + i18n 모두 비어있거나 `[...]` placeholder 패턴이면 해당 행을 숨김.
///   회사정보 7개 행이 모두 비어있으면 단일 안내 문구로 대체 → 빈 푸터 방지.
class PwFooter extends StatefulWidget {
  const PwFooter({super.key});

  @override
  State<PwFooter> createState() => _PwFooterState();
}

class _PwFooterState extends State<PwFooter> {
  CompanyInfo _ci = CompanyInfo.empty();

  @override
  void initState() {
    super.initState();
    CompanyInfoService.instance.get().then((ci) {
      if (mounted) setState(() => _ci = ci);
    });
  }

  /// placeholder/미설정 값 검출. 빈 문자열 또는 `[...]` 패턴이면 true.
  static bool _isPlaceholder(String v) {
    final s = v.trim();
    if (s.isEmpty) return true;
    if (s.startsWith('[') && s.endsWith(']')) return true;
    return false;
  }

  /// 우선순위: 1) DB company_info  2) i18n 키.
  /// 양쪽 모두 placeholder 면 빈 문자열 반환 → 호출부에서 행 숨김.
  String _resolve(String? apiValue, String i18nKey) {
    if (apiValue != null && apiValue.trim().isNotEmpty) return apiValue;
    final v = I18nService.instance.t(i18nKey, defaultValue: '');
    return _isPlaceholder(v) ? '' : v;
  }

  @override
  Widget build(BuildContext context) {
    final t = I18nService.instance;

    final companyName = _resolve(_ci.companyName, 'footer.company_name');
    final ceo         = _resolve(_ci.ceo, 'footer.ceo');
    final bizNumber   = _resolve(_ci.bizNumber, 'footer.biz_number');
    final commerce    = _resolve(_ci.commerceNumber, 'footer.commerce');
    final address     = _resolve(_ci.address, 'footer.address');
    final phone       = _resolve(_ci.phone, 'footer.phone');
    final emailRaw    = _resolve(_ci.email, 'footer.email');
    final email       = emailRaw.isNotEmpty ? emailRaw : 'support@pathwave.co.kr';
    final hosting     = _resolve(_ci.hosting, 'footer.hosting');

    // 회사정보 7개 행이 모두 비어있으면 단일 안내 문구로 대체.
    final allCorpEmpty = companyName.isEmpty
        && ceo.isEmpty && bizNumber.isEmpty && commerce.isEmpty
        && address.isEmpty && phone.isEmpty && hosting.isEmpty;

    return PwCard(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
      color: AppTheme.surface,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (allCorpEmpty) ...[
            Text(
              t.t('footer.empty_notice',
                defaultValue: '사업자 정보는 법인 등록 후 표시됩니다.'),
              style: const TextStyle(
                color: AppTheme.textHint,
                fontSize: 12,
                height: 1.5,
              ),
            ),
            const SizedBox(height: 6),
            _InfoRow(
              label: t.t('footer.email_label', defaultValue: '이메일'),
              value: email,
            ),
          ] else ...[
            if (companyName.isNotEmpty) ...[
              Text(
                t.t('footer.company_name_label', defaultValue: '상호'),
                style: const TextStyle(
                  color: AppTheme.textHint,
                  fontSize: 11,
                  letterSpacing: 0.3,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                companyName,
                style: const TextStyle(
                  color: AppTheme.textSecondary,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 12),
            ],

            if (ceo.isNotEmpty)
              _InfoRow(label: t.t('footer.ceo_label', defaultValue: '대표자'), value: ceo),
            if (bizNumber.isNotEmpty)
              _InfoRow(label: t.t('footer.biz_number_label', defaultValue: '사업자등록번호'), value: bizNumber),
            if (commerce.isNotEmpty)
              _InfoRow(label: t.t('footer.commerce_label', defaultValue: '통신판매업신고'), value: commerce),
            if (address.isNotEmpty)
              _InfoRow(label: t.t('footer.address_label', defaultValue: '주소'), value: address),
            if (phone.isNotEmpty)
              _InfoRow(label: t.t('footer.phone_label', defaultValue: '전화'), value: phone),
            _InfoRow(label: t.t('footer.email_label', defaultValue: '이메일'), value: email),
            if (hosting.isNotEmpty)
              _InfoRow(label: t.t('footer.hosting_label', defaultValue: '호스팅 제공자'), value: hosting),
          ],

          const SizedBox(height: 14),
          const Divider(color: AppTheme.border, height: 1),
          const SizedBox(height: 14),

          // 약관 + 지원 링크 (clickable)
          Wrap(
            spacing: 14,
            runSpacing: 8,
            children: [
              _PolicyLink(
                t.t('footer.terms_of_service', defaultValue: '이용약관'),
                onTap: () => context.push('/policy/terms'),
              ),
              _PolicyLink(
                t.t('footer.privacy_policy', defaultValue: '개인정보처리방침'),
                bold: true,
                onTap: () => context.push('/policy/privacy'),
              ),
              _PolicyLink(
                t.t('footer.location_terms', defaultValue: '위치기반서비스 이용약관'),
                onTap: () => context.push('/policy/location'),
              ),
              _PolicyLink(
                t.t('footer.marketing_terms', defaultValue: '마케팅 정보 수신'),
                onTap: () => context.push('/policy/marketing'),
              ),
              _PolicyLink(
                t.t('footer.faq', defaultValue: '자주 묻는 질문'),
                onTap: () => context.push('/support'),
              ),
              _PolicyLink(
                t.t('footer.support', defaultValue: '고객센터'),
                onTap: () => context.push('/support'),
              ),
            ],
          ),

          const SizedBox(height: 12),
          Text(
            t.t('footer.notice_disclaimer',
              defaultValue:
                '※ PathWave 는 매장 멤버십 플랫폼으로, 매장에서 제공하는 정보·이벤트·혜택의 책임은 등록 업체에 있습니다.'),
            style: const TextStyle(color: AppTheme.textHint, fontSize: 11, height: 1.5),
          ),

          const SizedBox(height: 12),
          Text(
            t.t('footer.copyright', defaultValue: '© PathWave. All rights reserved.'),
            style: const TextStyle(color: AppTheme.textHint, fontSize: 11),
          ),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;

  const _InfoRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 108,
            child: Text(
              label,
              style: const TextStyle(color: AppTheme.textHint, fontSize: 12),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
}

class _PolicyLink extends StatelessWidget {
  final String label;
  final bool bold;
  final VoidCallback? onTap;

  const _PolicyLink(this.label, {this.bold = false, this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(4),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
        child: Text(
          label,
          style: TextStyle(
            color: AppTheme.primaryLight,
            fontSize: 12,
            fontWeight: bold ? FontWeight.w700 : FontWeight.w500,
            decoration: TextDecoration.underline,
            decorationColor: AppTheme.primaryLight,
          ),
        ),
      ),
    );
  }
}
