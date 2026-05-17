import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

/**
 * PwFooter — 3 콘솔 공통 푸터.
 *
 * memory/ui_legal_compliance: 한국 전자상거래법 §10 / 정보통신망법 / 위치정보법
 * 필수 노출 사항. footer.* i18n 키는 mobile / provider-web / admin-web 모두 동일.
 * 어드민에서 한 번 입력하면 3 콘솔 모두 동일 값.
 *
 * 약관 링크는 어드민 콘솔이므로 슈퍼어드민용 /dashboard/policies (전체 정책 관리)
 * 로 이동한다. 일반 사용자/사장님 푸터는 각 콘솔에서 정책 뷰어로 SPA 이동.
 */
export default function PwFooter() {
  const { t } = useTranslation();

  const labelStyle = {
    color: 'var(--text-hint)',
    fontSize: 'var(--fs-xs)',
    marginRight: 6,
  };
  const valueStyle = {
    color: 'var(--text-secondary)',
    fontSize: 'var(--fs-xs)',
  };

  const InfoCell = ({ labelKey, labelDefault, valueKey, valueDefault }) => (
    <span style={{ display: 'inline-flex', gap: 4 }}>
      <span style={labelStyle}>{t(labelKey, labelDefault)}</span>
      <span style={valueStyle}>{t(valueKey, valueDefault)}</span>
    </span>
  );

  const linkStyle = {
    color: 'var(--text-muted)',
    textDecoration: 'none',
    fontSize: 'var(--fs-xs)',
  };

  return (
    <footer style={{
      borderTop: '1px solid var(--border)',
      background: 'var(--bg-2)',
      padding: '24px 32px',
      marginTop: '48px',
    }}>
      <div style={{
        maxWidth: 1080, margin: '0 auto',
        display: 'flex', flexDirection: 'column', gap: 10,
      }}>
        {/* 회사명 + 대표자 + 사업자번호 + 통신판매업 */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 20px', lineHeight: 1.6 }}>
          <span>
            <strong style={valueStyle}>
              {t('footer.company_name', '[법인 등록 후 채워질 예정]')}
            </strong>
          </span>
          <InfoCell labelKey="footer.ceo_label" labelDefault="대표자"
                    valueKey="footer.ceo" valueDefault="[법인 등록 후 채워질 예정]" />
          <InfoCell labelKey="footer.biz_number_label" labelDefault="사업자등록번호"
                    valueKey="footer.biz_number" valueDefault="[법인 등록 후 채워질 예정]" />
          <InfoCell labelKey="footer.commerce_label" labelDefault="통신판매업신고"
                    valueKey="footer.commerce" valueDefault="[법인 등록 후 채워질 예정]" />
        </div>

        {/* 주소 + 전화 + 이메일 + 호스팅 */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 20px', lineHeight: 1.6 }}>
          <InfoCell labelKey="footer.address_label" labelDefault="주소"
                    valueKey="footer.address" valueDefault="[법인 등록 후 채워질 예정]" />
          <InfoCell labelKey="footer.phone_label" labelDefault="전화"
                    valueKey="footer.phone" valueDefault="[법인 등록 후 채워질 예정]" />
          <InfoCell labelKey="footer.email_label" labelDefault="이메일"
                    valueKey="footer.email" valueDefault="support@pathwave.co.kr" />
          <InfoCell labelKey="footer.hosting_label" labelDefault="호스팅 제공자"
                    valueKey="footer.hosting" valueDefault="[법인 등록 후 채워질 예정]" />
        </div>

        {/* 약관/지원 링크 + 저작권 */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          flexWrap: 'wrap', gap: '8px 16px',
          paddingTop: 8, borderTop: '1px solid var(--border)',
        }}>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Link to="/dashboard/policies" style={linkStyle}>
              {t('footer.terms_of_service', '이용약관')}
            </Link>
            <Link to="/dashboard/policies" style={linkStyle}>
              <strong>{t('footer.privacy_policy', '개인정보처리방침')}</strong>
            </Link>
            <Link to="/dashboard/policies" style={linkStyle}>
              {t('footer.location_terms', '위치기반서비스 이용약관')}
            </Link>
            <Link to="/dashboard/policies" style={linkStyle}>
              {t('footer.marketing_terms', '마케팅 정보 수신')}
            </Link>
            <Link to="/dashboard/faq" style={linkStyle}>
              {t('footer.faq', '자주 묻는 질문')}
            </Link>
            <Link to="/dashboard/support" style={linkStyle}>
              {t('footer.support', '고객센터')}
            </Link>
          </div>
          <span style={{ color: 'var(--text-hint)', fontSize: 'var(--fs-xs)' }}>
            {t('footer.copyright', '© PathWave. All rights reserved.')}
          </span>
        </div>
      </div>
    </footer>
  );
}
