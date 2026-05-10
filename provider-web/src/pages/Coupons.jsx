import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Ticket, Plus, ChevronRight } from 'lucide-react';
import BottomActionBar from '../components/common/BottomActionBar';
import Button from '../components/common/Button';
import '../pages/Stamps.css'; // 쿠폰/스탬프 리스트는 동일 카드 스타일 공유

const Coupons = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  // Dummy data
  const dummyCoupons = [
    {
      id: 1,
      name: '호텔H 썬베드 선착순 50명 무료 이용권 증정쿠폰',
      period: '2022.05.01 ~ 2022.05.31',
      status: 'active'
    },
    {
      id: 2,
      name: '아메리카노 무료 증정 쿠폰',
      period: '2022.04.01 ~ 2022.04.30',
      status: 'ended'
    }
  ];

  return (
    <div className="stamps-page">
      <div className="page-header-section">
        <h1 className="page-title">{t('coupon.title_list', '쿠폰 관리')}</h1>
        <p className="sub-title">설치장소의 쿠폰을 관리합니다.</p>
      </div>

      <div className="stamp-list">
        {dummyCoupons.map((coupon) => (
          // 스탬프 카드와 동일 구조 — 상태 배지를 제목 우측 (사용자 요구 2026-05-10)
          <Link to={`/dashboard/coupons/view/${coupon.id}`} key={coupon.id} className="stamp-card">
            <div className={`stamp-icon ${coupon.status}`}>
              <Ticket size={24} />
            </div>
            <div className="stamp-info">
              <div className="stamp-info-head">
                <h3 className="stamp-name">{coupon.name}</h3>
                <span className={`stamp-status ${coupon.status}`}>
                  {coupon.status === 'active' ? '쿠폰 진행 중' : '쿠폰 진행 종료'}
                </span>
              </div>
              <div className="stamp-details">
                <div>사용기간 : {coupon.period}</div>
              </div>
            </div>
            <ChevronRight className="stamp-arrow" size={20} />
          </Link>
        ))}
      </div>

      <BottomActionBar>
        <Button
          variant="primary"
          fullWidth
          icon={<Plus size={18} />}
          onClick={() => navigate('/dashboard/service-request?type=event')}
        >
          쿠폰 등록
        </Button>
      </BottomActionBar>
    </div>
  );
};

export default Coupons;
