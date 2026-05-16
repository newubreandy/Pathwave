import React from 'react';
import { useTranslation } from 'react-i18next';

/**
 * PwFooter — admin-web 법인 정보 placeholder 푸터
 * 한국 법령(전자상거래법 제10조, 정보통신망법 등) 사업자 정보 의무 노출.
 * 법인 등록 후 translation.json footer.* 키 값을 실제 데이터로 교체.
 */
export default function PwFooter() {
  const { t } = useTranslation();

  return (
    <footer style={{
      borderTop: '1px solid var(--border)',
      background: 'var(--bg-2)',
      padding: '24px 32px',
      marginTop: '48px',
    }}>
      <div style={{
        maxWidth: 960,
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
      }}>
        {/* 법인 정보 row */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '4px 20px',
          fontSize: 'var(--fs-xs)',
          color: 'var(--text-muted)',
          lineHeight: 1.6,
        }}>
          <span>
            <strong style={{ color: 'var(--text-secondary)' }}>
              {t('footer.company_name', { defaultValue: '[법인명 등록 후 채워질 예정]' })}
            </strong>
          </span>
          <span>
            {t('footer.ceo_label', { defaultValue: '대표' })}:{' '}
            {t('footer.ceo', { defaultValue: '[법인 등록 후 채워질 예정]' })}
          </span>
          <span>
            {t('footer.biz_no_label', { defaultValue: '사업자등록번호' })}:{' '}
            {t('footer.biz_no', { defaultValue: '[법인 등록 후 채워질 예정]' })}
          </span>
          <span>
            {t('footer.mail_order_label', { defaultValue: '통신판매업신고' })}:{' '}
            {t('footer.mail_order', { defaultValue: '[법인 등록 후 채워질 예정]' })}
          </span>
        </div>

        {/* 주소 / 연락처 row */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '4px 20px',
          fontSize: 'var(--fs-xs)',
          color: 'var(--text-muted)',
          lineHeight: 1.6,
        }}>
          <span>
            {t('footer.address_label', { defaultValue: '주소' })}:{' '}
            {t('footer.address', { defaultValue: '[법인 등록 후 채워질 예정]' })}
          </span>
          <span>
            {t('footer.tel_label', { defaultValue: '전화' })}:{' '}
            {t('footer.tel', { defaultValue: '[법인 등록 후 채워질 예정]' })}
          </span>
          <span>
            {t('footer.email_label', { defaultValue: '이메일' })}:{' '}
            {t('footer.email', { defaultValue: '[법인 등록 후 채워질 예정]' })}
          </span>
          <span>
            {t('footer.hosting_label', { defaultValue: '호스팅' })}:{' '}
            {t('footer.hosting', { defaultValue: '[법인 등록 후 채워질 예정]' })}
          </span>
        </div>

        {/* 하단 링크 / 저작권 row */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '8px 16px',
          fontSize: 'var(--fs-xs)',
          color: 'var(--text-hint)',
          paddingTop: 8,
          borderTop: '1px solid var(--border)',
        }}>
          <div style={{ display: 'flex', gap: 16 }}>
            <a
              href="/policies"
              style={{
                color: 'var(--text-muted)',
                textDecoration: 'none',
                transition: 'color 0.15s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--accent)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-muted)'; }}
            >
              {t('footer.privacy_link', { defaultValue: '개인정보처리방침' })}
            </a>
            <a
              href="/policies"
              style={{
                color: 'var(--text-muted)',
                textDecoration: 'none',
                transition: 'color 0.15s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--accent)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-muted)'; }}
            >
              {t('footer.terms_link', { defaultValue: '이용약관' })}
            </a>
          </div>
          <span>
            {t('footer.copyright', {
              defaultValue: '© {{year}} PathWave. All rights reserved.',
              year: new Date().getFullYear(),
            })}
          </span>
        </div>
      </div>
    </footer>
  );
}
