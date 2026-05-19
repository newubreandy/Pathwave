import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import CompanyInfoService from '../../services/companyInfo/CompanyInfoService';
import './PwFooter.css';

/**
 * PwFooter — 3 콘솔 공통 푸터 (provider-web).
 *
 * memory/ui_legal_compliance + brand_strategy:
 * 한국 전자상거래법 §10 / 정보통신망법 §50 / 위치정보법 필수 노출.
 *
 * 데이터 소스 (Phase M):
 *   GET /api/company-info → 슈퍼어드민이 입력한 법인 정보
 *   값이 null/빈 문자열이면 i18n 키 fallback 사용
 *
 * 약관 링크는 SPA 라우트 `/policy/:kind` 로 이동 (PolicyViewer).
 */
const PwFooter = () => {
  const { t } = useTranslation();
  const [ci, setCi] = useState(null);

  useEffect(() => {
    let alive = true;
    CompanyInfoService.get()
      .then((data) => { if (alive) setCi(data.company_info || {}); })
      .catch(() => {}); // 실패해도 i18n fallback 사용 — 페이지는 죽지 않음
    return () => { alive = false; };
  }, []);

  /**
   * 우선순위: 1) DB company_info 값 (비어있지 않으면)
   *           2) i18n 키 (`t(key, default)`)
   *           3) hard-coded default
   */
  const resolve = (apiField, i18nKey, i18nDefault) => {
    const v = ci?.[apiField];
    if (v && v.toString().trim()) return v;
    return t(i18nKey, i18nDefault);
  };

  return (
    <footer className="pw-footer">
      <div className="pw-footer-inner">
        {/* 1행: 법인 정보 */}
        <dl className="pw-footer-info">
          <div className="pw-footer-row">
            <dt>{t('footer.company_name_label', '상호')}</dt>
            <dd>{resolve('company_name', 'footer.company_name', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.ceo_label', '대표자')}</dt>
            <dd>{resolve('ceo', 'footer.ceo', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.biz_number_label', '사업자등록번호')}</dt>
            <dd>{resolve('biz_number', 'footer.biz_number', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.commerce_label', '통신판매업신고')}</dt>
            <dd>{resolve('commerce_number', 'footer.commerce', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.address_label', '주소')}</dt>
            <dd>{resolve('address', 'footer.address', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.phone_label', '전화')}</dt>
            <dd>{resolve('phone', 'footer.phone', '[법인 등록 후 채워질 예정]')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.email_label', '이메일')}</dt>
            <dd>{resolve('email', 'footer.email', 'support@pathwave.co.kr')}</dd>
          </div>
          <div className="pw-footer-row">
            <dt>{t('footer.hosting_label', '호스팅 제공자')}</dt>
            <dd>{resolve('hosting', 'footer.hosting', '[법인 등록 후 채워질 예정]')}</dd>
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
          <Link to="/dashboard/support?tab=faq" className="pw-footer-link">
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
