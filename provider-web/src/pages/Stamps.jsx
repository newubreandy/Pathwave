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
  // P3-b (2026-05-26): ConfirmModal 기반 confirm/alert (window.* 대신).
  const { confirm, alert, modal: confirmModal } = useConfirm();
  const [activeMenuId, setActiveMenuId] = useState(null);
  const [stampList, setStampList] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  // mock — 슈퍼어드민에서 매장별 스탬프 서비스 가입 여부 관리
  // TODO: 실제 백엔드 GET /api/store/services 응답으로 교체.
  // 데모용 true (등록된 스탬프 데이터 보이도록).
  const [isStampServiceActivated] = useState(true);
  useEffect(() => {
    loadStamps();
  }, []);

  const loadStamps = async () => {
    setIsLoading(true);
    try {
      // P9 (2026-05-26): MOCK_STAMPS 제거 — 실 백엔드 호출.
      // facility_id 는 로그인 사장 계정의 매장 (1계정=1매장 정책, AuthService).
      const user = AuthService.getCurrentUser();
      const fid = user?.facility_id || user?.facilityId || null;
      const res = await StampService.list(fid);
      const items = res?.stamps || res?.data || res || [];
      setStampList(Array.isArray(items) ? items : []);
    } catch (error) {
      console.error('Failed to load stamps', error);
      setStampList([]); // 빈 상태 — 사장이 신규 등록 가능
    } finally {
      setIsLoading(false);
    }
  };

  // 스탬프는 매장당 1개만 운영 가능. 정책:
  //   - active 가 있으면 신규 등록 X (수정 / 정지로 처리)
  //   - paused 가 있으면 → 신규 시 기존 적립 무효화 알림 후 진행
  //   - 모두 ended 거나 0건이면 신규 등록 자유롭게
  const activeStamp = stampList.find(s => s.status === 'active');
  const pausedStamp = stampList.find(s => s.status === 'paused');
  const canRegisterNew = !activeStamp; // active 가 없을 때만 등록 버튼 노출

  const handleAddClick = async () => {
    if (activeStamp) {
      // 정상적으로는 버튼이 안 보이지만 만약 클릭되면 안내.
      await alert({
        title: '진행 중인 스탬프 존재',
        desc:  '매장당 1개의 스탬프만 활성화할 수 있습니다.\n기존 스탬프를 정지 후 다시 시도해 주세요.',
      });
      return;
    }
    if (pausedStamp) {
      const ok = await confirm({
        title: '신규 스탬프 등록 — 기존 적립 무효',
        desc:  '일시정지된 기존 스탬프가 있습니다.\n신규 스탬프를 등록하시면 사용자가 적립한 기존 스탬프는 더 이상 적용되지 않습니다.\n\n계속 진행하시겠어요?',
        confirmText: '계속',
      });
      if (!ok) return;
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
      await alert({ title: '실패', desc: error.message });
    }
    setActiveMenuId(null);
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    e.preventDefault();
    const ok = await confirm({
      title: '스탬프 삭제',
      desc:  '이 스탬프를 목록에서 삭제하시겠습니까?\n(기록은 백데이터에 유지됩니다)',
      confirmText: '삭제',
    });
    if (ok) {
      try {
        await StampService.deleteStamp(id);
        loadStamps();
      } catch (error) {
        await alert({ title: '삭제 실패', desc: error.message || '잠시 후 다시 시도해 주세요.' });
      }
    }
    setActiveMenuId(null);
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
            // 사용자 요구 (2026-05-10): MoreVertical 메뉴 제거 + 상태 배지를 제목 우측으로.
            // 정지/삭제 액션은 상세보기 페이지에서. 사용기간은 유지.
            <Link to={`/dashboard/stamps/view/${stamp.id}`} key={stamp.id} className="stamp-card">
              <div className={`stamp-icon ${stamp.status}`}>
                <Stamp size={24} />
              </div>
              <div className="stamp-info">
                <div className="stamp-info-head">
                  <h3 className="stamp-name">{stamp.name}</h3>
                  <span className={`stamp-status ${stamp.status}`}>
                    {stamp.status === 'active' ? t('stamp.status_active', '스탬프 적립 중') : (stamp.status === 'paused' ? '스탬프 일시정지' : t('stamp.status_ended', '스탬프 적립 종료'))}
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

      {/* 등록 버튼 — 신청 진행중인 스탬프 (active) 가 없을 때만 노출.
          (paused / ended 인 경우 등록 가능, click 시 안내 다이얼로그) */}
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
      {/* P3-b: 공용 confirm/alert 모달 (ConfirmModal 통합) */}
      {confirmModal}
    </div>
  );
};

export default Stamps;
