import 'package:flutter/material.dart';

import '../services/i18n_service.dart';
import '../utils/app_theme.dart';
import 'pw_card.dart';

/// PathWave 법인 정보 푸터 위젯.
///
/// 전자상거래법 §10 / 표시광고법 필수 표기 사항을 한 곳에 모아 둔다.
/// 실제 법인 데이터는 추후 단일 Dart 상수 또는 backend i18n 키로 채운다.
/// 현재는 모두 `[법인 등록 후 채워질 예정]` placeholder.
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
            t.t('footer.company_name_label', defaultValue: '회사명'),
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
            value: t.t('footer.email', defaultValue: '[법인 등록 후 채워질 예정]'),
          ),
          _InfoRow(
            label: t.t('footer.hosting_label', defaultValue: '호스팅 제공자'),
            value: t.t('footer.hosting', defaultValue: '[법인 등록 후 채워질 예정]'),
          ),

          const SizedBox(height: 14),
          const Divider(color: AppTheme.border, height: 1),
          const SizedBox(height: 14),

          // 약관 링크 행
          Wrap(
            spacing: 12,
            runSpacing: 6,
            children: [
              _PolicyLink(
                  t.t('footer.privacy_policy', defaultValue: '개인정보처리방침')),
              _PolicyLink(
                  t.t('footer.terms_of_service', defaultValue: '이용약관')),
              _PolicyLink(
                  t.t('footer.location_terms', defaultValue: '위치기반서비스 약관')),
            ],
          ),

          const SizedBox(height: 14),
          Text(
            t.t(
              'footer.copyright',
              defaultValue:
                  '© 2025 PathWave. All rights reserved.',
            ),
            style: const TextStyle(
              color: AppTheme.textHint,
              fontSize: 11,
            ),
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
              style: const TextStyle(
                color: AppTheme.textHint,
                fontSize: 12,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 12,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PolicyLink extends StatelessWidget {
  final String label;

  const _PolicyLink(this.label);

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: const TextStyle(
        color: AppTheme.primaryLight,
        fontSize: 12,
        decoration: TextDecoration.underline,
        decorationColor: AppTheme.primaryLight,
      ),
    );
  }
}
