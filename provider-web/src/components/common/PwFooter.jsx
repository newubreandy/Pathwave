import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import CompanyInfoService from '../../services/companyInfo/CompanyInfoService';
import './PwFooter.css';

/**
 * PwFooter — 3 콘솔 공통 푸터 (provider-web).
 *
 * 사용자 정책 2026-05-27 — 푸터 구조:
 *   1행: 약관/지원 링크 (중앙)
 *        이용약관 / 개인정보처리방침 / 위치기반서비스 이용약관 / 마케팅 정보 수신
 *        / 자주 묻는 질문 / 고객센터
 *   2행: 법인 정보 inline (가로) — 호스팅 제공자 제외
 *        상호 · 대표자 · 사업자등록번호 · 통신판매업신고 · 주소 · 전화 · 이메일
 *   3행: 안내문 + copyright (한 줄)
 *
 * memory/ui_legal_compliance + brand_strategy:
 * 한국 전자상거래법 §10 / 정보통신망법 §50 / 위치정보법 필수 노출.
 *
 * 데이터 소스: GET /api/company-info → 슈퍼어드민 입력 법인 정보.
 */
const PwFooter = () => {
  const { t } = useTranslation();
  const [ci, setCi] = useState(null);

  useEffect(() => {
    let alive = true;
    CompanyInfoService.get()
      .then((data) => { if (alive) setCi(data.company_info || {}); })
      .catch(() => {}); // 실패해도 i18n fallback 사용
    return () => { alive = false; };
  }, []);

  const resolve = (apiField, i18nKey, i18nDefault) => {
    const v = ci?.[apiField];
    if (v && v.toString().trim()) return v;
    return t(i18nKey, i18nDefault);
  };

  // 법인 정보 entries — 호스팅·전화·이메일 제외 (사용자 정책 2026-05-27)
  // 이메일은 footer 링크 줄의 '고객센터' 로 대체 (고객센터에 문의작성 있음)
  const companyEntries = [
    ['상호',            resolve('company_name',    'footer.company_name', '[법인 등록 후 채워질 예정]')],
    ['대표자',          resolve('ceo',             'footer.ceo',          '[법인 등록 후 채워질 예정]')],
    ['사업자등록번호',  resolve('biz_number',      'footer.biz_number',   '[법인 등록 후 채워질 예정]')],
    ['통신판매업신고',  resolve('commerce_number', 'footer.commerce',     '[법인 등록 후 채워질 예정]')],
    ['주소',            resolve('address',         'footer.address',      '[법인 등록 후 채워질 예정]')],
  ];

  return (
    <footer className="pw-footer">
      <div className="pw-footer-inner">
        {/* 1행: 약관 + 지원 링크 (중앙 정렬) */}
        <nav className="pw-footer-links" aria-label="약관 및 고객 지원">
          <Link to="/policy/terms" className="pw-footer-link">
            {t('footer.terms_of_service', '이용약관')}
          </Link>
          <span className="pw-footer-sep" aria-hidden="true">|</span>
          <Link to="/policy/privacy" className="pw-footer-link pw-footer-link--bold">
            {t('footer.privacy_policy', '개인정보처리방침')}
          </Link>
          <span className="pw-footer-sep" aria-hidden="true">|</span>
          <Link to="/policy/location" className="pw-footer-link">
            {t('footer.location_terms', '위치기반서비스 이용약관')}
          </Link>
          <span className="pw-footer-sep" aria-hidden="true">|</span>
          <Link to="/policy/marketing" className="pw-footer-link">
            {t('footer.marketing_terms', '마케팅 정보 수신')}
          </Link>
          <span className="pw-footer-sep" aria-hidden="true">|</span>
          <Link to="/dashboard/support?tab=faq" className="pw-footer-link">
            {t('footer.faq', '자주 묻는 질문')}
          </Link>
          <span className="pw-footer-sep" aria-hidden="true">|</span>
          <Link to="/dashboard/support" className="pw-footer-link">
            {t('footer.support', '고객센터')}
          </Link>
        </nav>

        {/* 2행: 안내문 (약관 줄 아래 한 칸 띄움, 한 줄 짧게) */}
        <p className="pw-footer-notice">
          {t('footer.notice_disclaimer',
             '※ 매장에서 제공하는 정보·혜택의 책임은 등록 업체에 있습니다.')}
        </p>

        {/* 3행: 법인 정보 + copyright — 값만 간결하게 (라벨 숨김, 모바일 자동 wrap) */}
        <dl className="pw-footer-info">
          {companyEntries.map(([label, value]) => (
            <span key={label} className="pw-footer-entry">
              {/* 라벨은 a11y 만 유지 (screen reader), 시각 숨김 */}
              <dt className="sr-only">{label}</dt>
              <dd>{value}</dd>
            </span>
          ))}
          <span className="pw-footer-entry pw-footer-entry--copy">
            <dd>{t('footer.copyright', '© PathWave. All rights reserved.')}</dd>
          </span>
        </dl>
      </div>
    </footer>
  );
};

export default PwFooter;
