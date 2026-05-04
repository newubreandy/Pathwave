import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Ticket, Plus, ChevronRight, MoreVertical } from 'lucide-react';
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

  const [activeMenuId, setActiveMenuId] = useState(null);

  const handleMenuClick = (e, id) => {
    e.stopPropagation();
    e.preventDefault();
    setActiveMenuId(activeMenuId === id ? null : id);
  };

  return (
    <div className="stamps-page" onClick={() => setActiveMenuId(null)}>
      <div className="page-header-section">
        <h1 className="page-title">{t('coupon.title_list', '쿠폰 관리')}</h1>
        <p className="sub-title">설치장소의 쿠폰을 관리합니다.</p>
      </div>

      <div className="stamp-list">
        {dummyCoupons.map((coupon) => (
          <Link to={`/dashboard/coupons/view/${coupon.id}`} key={coupon.id} className="stamp-card">
            <div className={`stamp-icon ${coupon.status}`}>
              <Ticket size={24} />
            </div>
            <div className="stamp-info">
              <h3 className="stamp-name">{coupon.name}</h3>
              <div className={`stamp-status ${coupon.status}`}>
                {coupon.status === 'active' ? '쿠폰 진행 중' : '쿠폰 진행 종료'}
              </div>
              <div className="stamp-details">
                <div>사용기간 : {coupon.period}</div>
              </div>
            </div>
            <ChevronRight className="stamp-arrow" size={20} />
            
            <button 
              className="stamp-menu-btn"
              onClick={(e) => handleMenuClick(e, coupon.id)}
            >
              <MoreVertical size={18} />
            </button>

            {activeMenuId === coupon.id && (
              <div className="stamp-context-menu">
                <button 
                  className="context-menu-item danger"
                  onClick={(e) => { e.stopPropagation(); e.preventDefault(); setActiveMenuId(null); }}
                >
                  삭제하기
                </button>
              </div>
            )}
          </Link>
        ))}
      </div>

      <BottomActionBar>
        <Button 
          variant="primary" 
          fullWidth 
          icon={<Plus size={18} />}
          onClick={() => navigate('/dashboard/coupons/add')}
        >
          쿠폰 등록
        </Button>
      </BottomActionBar>
    </div>
  );
};

export default Coupons;
