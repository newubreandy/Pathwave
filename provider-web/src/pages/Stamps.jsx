import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { Stamp, Plus, ChevronRight } from 'lucide-react';
import StampService from '../services/stamp/StampService';
import AuthService from '../services/auth/AuthService';
import Button from '../components/common/Button';
import { useConfirm } from '../hooks/useConfirm';
import BottomActionBar from '../components/common/BottomActionBar';
import './Stamps.css';

const Stamps = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { confirm, alert, modal: confirmModal } = useConfirm();
  const [stampList, setStampList] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [facilityId, setFacilityId] = useState(null);
  // mock — 슈퍼어드민에서 매장별 스탬프 서비스 가입 여부 관리
  // TODO: 실제 백엔드 GET /api/store/services 응답으로 교체.
  const [isStampServiceActivated] = useState(true);

  useEffect(() => {
    AuthService.me()
      .then((res) => {
        const fid = res?.facility_account?.facility_id ?? null;
        setFacilityId(fid);
        if (fid) loadStamps(fid);
        else setIsLoading(false);
      })
      .catch(() => setIsLoading(false));
  }, []);

  const loadStamps = async (fid) => {
    setIsLoading(true);
    try {
      const items = await StampService.list(fid);
      setStampList(Array.isArray(items) ? items : []);
    } catch (error) {
      console.error('Failed to load stamps', error);
      setStampList([]);
    } finally {
      setIsLoading(false);
    }
  };

  // 매장당 활성 정책 1개. active 만 list 에 오므로 length === 0 이면 신규 등록 가능.
  const canRegisterNew = stampList.length === 0;

  const handleAddClick = () => {
    navigate('/dashboard/stamps/new');
  };

  const handleEnd = async (e, stamp) => {
    e.stopPropagation();
    e.preventDefault();
    const ok = await confirm({
      title: '적립 종료',
      desc: '적립을 종료하시겠습니까? 신규 적립이 중단되며 기록은 유지됩니다.',
      confirmText: '종료',
    });
    if (ok) {
      try {
        await StampService.end(facilityId);
        loadStamps(facilityId);
      } catch (error) {
        await alert({ title: '종료 실패', desc: error.message || '잠시 후 다시 시도해 주세요.' });
      }
    }
  };

  // 스탬프 서비스 미가입 — 안내 + 신청하기 버튼만 노출
  if (!isStampServiceActivated) {
    return (
      <div className="stamps-page">
        <div className="page-header-section">
          <h1 className="page-title">{t('stamp.title_list', '스탬프')}</h1>
          <p className="sub-title">스탬프 서비스를 신청하시면 매장 방문/결제 시 사용자에게 스탬프를 적립해 줄 수 있습니다.</p>
        </div>

        <div className="stamp-empty-cta">
          <div className="stamp-empty-icon">
            <Stamp size={36} />
          </div>
          <h2 className="stamp-empty-title">스탬프 서비스가 아직 신청되지 않았습니다</h2>
          <p className="stamp-empty-desc">
            서비스 신청 후 슈퍼어드민에서 매장별 스탬프 정책(적립 조건 / 보상 쿠폰)을 설정해 드립니다.<br />
            지금 신청해서 매장 방문 고객에게 적립 혜택을 제공해 보세요.
          </p>
        </div>

        <BottomActionBar>
          <Button
            variant="primary"
            fullWidth
            icon={<Plus size={18} />}
            onClick={() => navigate('/dashboard/service-request?type=stamp')}
          >
            스탬프 서비스 신청
          </Button>
        </BottomActionBar>
      </div>
    );
  }

  return (
    <div className="stamps-page" onClick={() => {}}>
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
            <Link to={`/dashboard/stamps/edit/${stamp.id}`} key={stamp.id} className="stamp-card">
              <div className={`stamp-icon ${stamp.status}`}>
                <Stamp size={24} />
              </div>
              <div className="stamp-info">
                <div className="stamp-info-head">
                  <h3 className="stamp-name">{stamp.name}</h3>
                  <span className={`stamp-status ${stamp.status}`}>
                    {stamp.status === 'active'
                      ? t('stamp.status_active', '스탬프 적립 중')
                      : t('stamp.status_ended', '스탬프 적립 종료')}
                  </span>
                </div>
                <div className="stamp-details">
                  <div>{t('stamp.label_period', '사용기간')} : {stamp.period}</div>
                </div>
              </div>
              <ChevronRight className="stamp-arrow" size={20} />
            </Link>
          ))
        ) : (
          <div className="empty-state">
            <p>등록된 스탬프 내역이 없습니다.</p>
          </div>
        )}
      </div>

      {stampList.length > 0 && (
        <div style={{ padding: '0 var(--pw-space-4)', marginTop: 'var(--pw-space-4)' }}>
          <Button
            variant="outline"
            fullWidth
            onClick={(e) => handleEnd(e, stampList[0])}
          >
            적립 종료
          </Button>
        </div>
      )}

      {canRegisterNew && (
        <BottomActionBar>
          <Button
            variant="primary"
            fullWidth
            icon={<Plus size={18} />}
            onClick={handleAddClick}
          >
            {t('stamp.title_add', '스탬프 등록')}
          </Button>
        </BottomActionBar>
      )}
      {confirmModal}
    </div>
  );
};

export default Stamps;
