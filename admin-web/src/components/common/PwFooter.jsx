import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { companyInfoApi } from '../../services/companyInfo.js';

/**
 * PwFooter — 3 콘솔 공통 푸터.
 *
 * memory/ui_legal_compliance: 한국 전자상거래법 §10 / 정보통신망법 / 위치정보법
 * 필수 노출 사항.
 *
 * 데이터 소스 (Phase M):
 *   GET /api/company-info → company_name / ceo / biz_number / commerce_number
 *                            address / phone / email / hosting
 *   값이 null 이면 i18n 키의 fallback default 사용.
 *
 * 어드민 콘솔이므로 약관 링크는 슈퍼어드민용 /dashboard/policies (전체 정책 관리).
 */
export default function PwFooter() {
  const { t } = useTranslation();
  const [ci, setCi] = useState(null);

  useEffect(() => {
    let alive = true;
    companyInfoApi.get()
      .then((data) => { if (alive) setCi(data.company_info || {}); })
      .catch(() => {}); // 실패해도 i18n fallback 사용 — 페이지 자체는 죽지 않음
    return () => { alive = false; };
  }, []);

  /**
   * 우선순위: 1) DB 의 company_info 값 (비어있지 않으면)
   *           2) i18n 키 (`t(key, default)`)
   *           3) hard-coded default
   */
  const resolve = (apiField, i18nKey, i18nDefault) => {
    const v = ci?.[apiField];
    if (v && v.toString().trim()) return v;
    return t(i18nKey, i18nDefault);
  };

  const labelStyle = {
    color: 'var(--text-hint)',
    fontSize: 'var(--fs-xs)',
    marginRight: 6,
  };
  const valueStyle = {
    color: 'var(--text-secondary)',
    fontSize: 'var(--fs-xs)',
  };

  const InfoCell = ({ labelKey, labelDefault, value }) => (
    <span style={{ display: 'inline-flex', gap: 4 }}>
      <span style={labelStyle}>{t(labelKey, labelDefault)}</span>
      <span style={valueStyle}>{value}</span>
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
              {resolve('company_name', 'footer.company_name', '[법인 등록 후 채워질 예정]')}
            </strong>
          </span>
          <InfoCell labelKey="footer.ceo_label" labelDefault="대표자"
                    value={resolve('ceo', 'footer.ceo', '[법인 등록 후 채워질 예정]')} />
          <InfoCell labelKey="footer.biz_number_label" labelDefault="사업자등록번호"
                    value={resolve('biz_number', 'footer.biz_number', '[법인 등록 후 채워질 예정]')} />
          <InfoCell labelKey="footer.commerce_label" labelDefault="통신판매업신고"
                    value={resolve('commerce_number', 'footer.commerce', '[법인 등록 후 채워질 예정]')} />
        </div>

        {/* 주소 + 전화 + 이메일 + 호스팅 */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 20px', lineHeight: 1.6 }}>
          <InfoCell labelKey="footer.address_label" labelDefault="주소"
                    value={resolve('address', 'footer.address', '[법인 등록 후 채워질 예정]')} />
          <InfoCell labelKey="footer.phone_label" labelDefault="전화"
                    value={resolve('phone', 'footer.phone', '[법인 등록 후 채워질 예정]')} />
          <InfoCell labelKey="footer.email_label" labelDefault="이메일"
                    value={resolve('email', 'footer.email', 'support@pathwave.co.kr')} />
          <InfoCell labelKey="footer.hosting_label" labelDefault="호스팅 제공자"
                    value={resolve('hosting', 'footer.hosting', '[법인 등록 후 채워질 예정]')} />
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
