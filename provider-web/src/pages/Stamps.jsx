import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { Stamp, Plus, ChevronRight, MoreVertical } from 'lucide-react';
import StampService from '../services/stamp/StampService';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
import './Stamps.css';

const Stamps = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [activeMenuId, setActiveMenuId] = useState(null);
  const [stampList, setStampList] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => {
    loadStamps();
  }, []);

  const loadStamps = async () => {
    setIsLoading(true);
    try {
      const data = await StampService.getStamps();
      setStampList(data);
    } catch (error) {
      console.error('Failed to load stamps', error);
    } finally {
      setIsLoading(false);
    }
  };

  const hasActiveStamp = stampList.some(s => s.status === 'active');

  const handleAddClick = () => {
    if (hasActiveStamp) {
      alert('현재 진행 중인 스탬프가 있습니다. 매장당 1개의 스탬프만 활성화할 수 있으므로, 기존 스탬프를 정지 또는 종료한 후 다시 시도해 주세요.');
      return;
    }
    navigate('/dashboard/stamps/new');
  };

  const handleMenuClick = (e, id) => {
    e.stopPropagation();
    e.preventDefault();
    setActiveMenuId(activeMenuId === id ? null : id);
  };

  const handlePauseToggle = async (e, stamp) => {
    e.stopPropagation();
    e.preventDefault();
    try {
      await StampService.toggleStampStatus(stamp.id);
      loadStamps();
    } catch (error) {
      alert(error.message);
    }
    setActiveMenuId(null);
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    e.preventDefault();
    if (window.confirm('이 스탬프를 목록에서 삭제하시겠습니까? (기록은 백데이터에 유지됩니다)')) {
      try {
        await StampService.deleteStamp(id);
        loadStamps();
      } catch (error) {
        alert('삭제에 실패했습니다.');
      }
    }
    setActiveMenuId(null);
  };

  return (
    <div className="stamps-page" onClick={() => setActiveMenuId(null)}>
      <div className="page-header-section">
        <h1 className="page-title">{t('stamp.title_list', '스탬프')}</h1>
        <p className="sub-title">매장에서 사용하신 스탬프 입니다.</p>
      </div>

      <div className="stamp-list">
        {isLoading ? (
          <div className="empty-state">
            <p>로딩 중...</p>
          </div>
        ) : stampList.length > 0 ? (
          stampList.map((stamp) => (
            <Link to={`/dashboard/stamps/view/${stamp.id}`} key={stamp.id} className="stamp-card">
              <div className={`stamp-icon ${stamp.status}`}>
                <Stamp size={24} />
              </div>
              <div className="stamp-info">
                <h3 className="stamp-name">{stamp.name}</h3>
                <div className={`stamp-status ${stamp.status}`}>
                  {stamp.status === 'active' ? t('stamp.status_active', '스탬프 적립 중') : (stamp.status === 'paused' ? '스탬프 일시정지' : t('stamp.status_ended', '스탬프 적립 종료'))}
                </div>
                <div className="stamp-details">
                  <div>{t('stamp.label_period', '사용기간')} : {stamp.period}</div>
                </div>
              </div>
              <ChevronRight className="stamp-arrow" size={20} />
              
              <button 
                className="stamp-menu-btn"
                onClick={(e) => handleMenuClick(e, stamp.id)}
              >
                <MoreVertical size={18} />
              </button>

              {activeMenuId === stamp.id && (
                <div className="stamp-context-menu">
                  {stamp.status !== 'ended' && (
                    <button 
                      className="context-menu-item"
                      onClick={(e) => handlePauseToggle(e, stamp)} 
                    >
                      {stamp.status === 'active' ? '정지하기' : '활성화하기'}
                    </button>
                  )}
                  <button 
                    className="context-menu-item danger"
                    onClick={(e) => handleDelete(e, stamp.id)} 
                  >
                    삭제하기
                  </button>
                </div>
              )}
            </Link>
          ))
        ) : (
          <div className="empty-state">
            <p>등록된 스탬프 내역이 없습니다.</p>
          </div>
        )}
      </div>

      <BottomActionBar>
        <Button 
          variant="primary" 
          fullWidth 
          icon={<Plus size={18} />}
          onClick={handleAddClick} 
          disabled={hasActiveStamp}
        >
          {t('stamp.title_add', '스탬프 등록')}
        </Button>
      </BottomActionBar>
    </div>
  );
};

export default Stamps;
