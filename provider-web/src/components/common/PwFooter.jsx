import React from 'react';
import { useTranslation } from 'react-i18next';
import './PwFooter.css';

/**
 * PwFooter — 법인 정보 placeholder 푸터
 * 법인 설립 후 이 파일의 상수 값만 채우면 전체 반영됩니다.
 *
 * 현재는 모든 항목이 [법인 등록 후 채워질 예정] 상태입니다.
 */
const PwFooter = () => {
  const { t } = useTranslation();

  return (
    <footer className="pw-footer">
      <div className="pw-footer-inner">
        {/* 법인 정보 */}
        <dl className="pw-footer-info">
          <div className="pw-footer-row">
            <dt>{t('footer.company_name_label', '상호')}</dt>
            <dd>{t('footer.company_name', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.ceo_label', '대표자')}</dt>
            <dd>{t('footer.ceo', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.business_reg_label', '사업자등록번호')}</dt>
            <dd>{t('footer.business_reg', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.ecommerce_reg_label', '통신판매업신고')}</dt>
            <dd>{t('footer.ecommerce_reg', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.address_label', '주소')}</dt>
            <dd>{t('footer.address', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.phone_label', '전화')}</dt>
            <dd>{t('footer.phone', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.email_label', '이메일')}</dt>
            <dd>{t('footer.email', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.hosting_label', '호스팅')}</dt>
            <dd>{t('footer.hosting', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
        </dl>

        {/* 약관 링크 */}
        <div className="pw-footer-links">
          <a
            href="/terms"
            className="pw-footer-link"
            target="_blank"
            rel="noopener noreferrer"
          >
            {t('footer.terms', '이용약관')}
          </a>
          <span className="pw-footer-sep" aria-hidden="true" />
          <a
            href="/privacy"
            className="pw-footer-link pw-footer-link--bold"
            target="_blank"
            rel="noopener noreferrer"
          >
            {t('footer.privacy', '개인정보처리방침')}
          </a>
          <span className="pw-footer-sep" aria-hidden="true" />
          <a
            href="/location-terms"
            className="pw-footer-link"
            target="_blank"
            rel="noopener noreferrer"
          >
            {t('footer.location_terms', '위치기반서비스 약관')}
          </a>
        </div>

        <p className="pw-footer-copy">
          {t('footer.copyright', '© PathWave. All rights reserved.')}
        </p>
      </div>
    </footer>
  );
};

export default PwFooter;
