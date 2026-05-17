import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../services/i18n_service.dart';
import '../utils/app_theme.dart';
import 'pw_card.dart';

/// PathWave 법인 정보 푸터 위젯.
///
/// memory/ui_legal_compliance: 한국 전자상거래법 §10 / 정보통신망법 §50 /
/// 위치정보법 필수 표기 사항. footer.* i18n 키는 3 콘솔 공통.
/// 어드민 i18n DB 에 한 번 입력 → mobile/provider-web/admin-web 자동 동기화.
class PwFooter extends StatelessWidget {
  const PwFooter({super.key});

  @override
  Widget build(BuildContext context) {
    final t = I18nService.instance;

    return PwCard(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
      color: AppTheme.surface,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 회사명 + 대표자
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
            t.t('footer.company_name', defaultValue: '[법인 등록 후 채워질 예정]'),
            style: const TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),

          _InfoRow(
            label: t.t('footer.ceo_label', defaultValue: '대표자'),
            value: t.t('footer.ceo', defaultValue: '[법인 등록 후 채워질 예정]'),
          ),
          _InfoRow(
            label: t.t('footer.biz_number_label', defaultValue: '사업자등록번호'),
            value: t.t('footer.biz_number', defaultValue: '[법인 등록 후 채워질 예정]'),
          ),
          _InfoRow(
            label: t.t('footer.commerce_label', defaultValue: '통신판매업신고'),
            value: t.t('footer.commerce', defaultValue: '[법인 등록 후 채워질 예정]'),
          ),
          _InfoRow(
            label: t.t('footer.address_label', defaultValue: '주소'),
            value: t.t('footer.address', defaultValue: '[법인 등록 후 채워질 예정]'),
          ),
          _InfoRow(
            label: t.t('footer.phone_label', defaultValue: '전화'),
            value: t.t('footer.phone', defaultValue: '[법인 등록 후 채워질 예정]'),
          ),
          _InfoRow(
            label: t.t('footer.email_label', defaultValue: '이메일'),
            value: t.t('footer.email', defaultValue: 'support@pathwave.co.kr'),
          ),
          _InfoRow(
            label: t.t('footer.hosting_label', defaultValue: '호스팅 제공자'),
            value: t.t('footer.hosting', defaultValue: '[법인 등록 후 채워질 예정]'),
          ),

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
