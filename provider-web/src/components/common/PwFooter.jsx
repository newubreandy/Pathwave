import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './PwFooter.css';

/**
 * PwFooter — 3 콘솔 공통 푸터 (provider-web).
 *
 * memory/ui_legal_compliance + brand_strategy:
 * 한국 전자상거래법 §10 / 정보통신망법 §50 / 위치정보법 필수 노출.
 * footer.* i18n 키는 mobile / provider-web / admin-web 모두 동일.
 * 어드민이 한 번 입력 → 3 콘솔 자동 동기화.
 *
 * 약관 링크는 SPA 라우트 `/policy/:kind` 로 이동 (PolicyViewer).
 */
const PwFooter = () => {
  const { t } = useTranslation();

  return (
    <footer className="pw-footer">
      <div className="pw-footer-inner">
        {/* 1행: 법인 정보 */}
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
            <dt>{t('footer.biz_number_label', '사업자등록번호')}</dt>
            <dd>{t('footer.biz_number', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.commerce_label', '통신판매업신고')}</dt>
            <dd>{t('footer.commerce', '[법인 등록 후 채워질 예정]')}</dd>
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
            <dd>{t('footer.email', 'support@pathwave.co.kr')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.hosting_label', '호스팅 제공자')}</dt>
            <dd>{t('footer.hosting', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
        </dl>

        {/* 2행: 약관 + 지원 링크 */}
        <div className="pw-footer-links">
          <Link to="/policy/terms" className="pw-footer-link">
            {t('footer.terms_of_service', '이용약관')}
          </Link>
          <span className="pw-footer-sep" aria-hidden="true" />
          <Link to="/policy/privacy" className="pw-footer-link pw-footer-link--bold">
            {t('footer.privacy_policy', '개인정보처리방침')}
          </Link>
          <span className="pw-footer-sep" aria-hidden="true" />
          <Link to="/policy/location" className="pw-footer-link">
            {t('footer.location_terms', '위치기반서비스 이용약관')}
          </Link>
          <span className="pw-footer-sep" aria-hidden="true" />
          <Link to="/policy/marketing" className="pw-footer-link">
            {t('footer.marketing_terms', '마케팅 정보 수신')}
          </Link>
          <span className="pw-footer-sep" aria-hidden="true" />
          <Link to="/dashboard/support" className="pw-footer-link">
            {t('footer.faq', '자주 묻는 질문')}
          </Link>
          <span className="pw-footer-sep" aria-hidden="true" />
          <Link to="/dashboard/support" className="pw-footer-link">
            {t('footer.support', '고객센터')}
          </Link>
        </div>

        <p className="pw-footer-notice">
          {t('footer.notice_disclaimer',
             '※ PathWave 는 매장 멤버십 플랫폼으로, 매장에서 제공하는 정보·이벤트·혜택의 책임은 등록 업체에 있습니다.')}
        </p>

        <p className="pw-footer-copy">
          {t('footer.copyright', '© PathWave. All rights reserved.')}
        </p>
      </div>
    </footer>
  );
};

export default PwFooter;
