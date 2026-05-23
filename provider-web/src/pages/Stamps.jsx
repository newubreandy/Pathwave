import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { Stamp, Plus, ChevronRight } from 'lucide-react';
import StoreService from '../services/store/StoreService';
import StampService from '../services/stamp/StampService';
import Button from '../components/common/Button';
import BottomActionBar from '../components/common/BottomActionBar';
import { useDialog } from '../components/common/DialogProvider';
import './Stamps.css';

/**
 * 매장 스탬프 정책 관리.
 *
 * 백엔드 모델: stamp_policy 는 매장당 1개의 active 정책. PUT upsert / DELETE 비활성.
 * (이전 mock 의 'paused/ended' 다중 상태는 백엔드 미지원 → active 1개로 단순화)
 */
const Stamps = () => {
  const { t } = useTranslation();
  const { confirm, alert } = useDialog();
  const navigate = useNavigate();

  const [fid, setFid] = useState(null);
  const [policy, setPolicy] = useState(null); // active 정책 1개 또는 null
  const [loading, setLoading] = useState(true);
  const [errMsg, setErrMsg] = useState('');

  const loadPolicy = useCallback(async (facilityId) => {
    try {
      const res = await StampService.getPolicy(facilityId);
      setPolicy(res.policy ?? null);
    } catch (err) {
      // 404 = 정책 없음 (정상). 그 외만 에러.
      const msg = String(err?.message || '');
      if (msg.includes('404') || msg.includes('없습니다')) {
        setPolicy(null);
      } else {
        setErrMsg(err?.message || '스탬프 정책을 불러오지 못했습니다.');
      }
    }
  }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await StoreService.list();
        const f = (res.facilities ?? [])[0];
        if (!alive) return;
        if (!f) { setErrMsg('등록된 매장이 없습니다.'); return; }
        setFid(f.id);
        await loadPolicy(f.id);
      } catch (err) {
        if (alive) setErrMsg(err?.message || '매장 정보를 불러오지 못했습니다.');
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [loadPolicy]);

  const handleAddClick = async () => {
    if (policy && policy.active) {
      await alert({
        title: '진행 중인 정책 존재',
        message: '현재 진행 중인 스탬프 정책이 있습니다. 새 정책을 등록하려면 기존 정책을 먼저 비활성화해 주세요.',
      });
      return;
    }
    navigate('/dashboard/stamps/new');
  };

  const handleDeactivate = async (e) => {
    e?.stopPropagation();
    e?.preventDefault();
    if (!fid) return;
    const ok = await confirm({
      title: '스탬프 정책 비활성',
      message: '이 정책을 비활성화하시겠습니까?\n적립 기록은 유지되지만 신규 적립은 중단됩니다.',
      danger: true,
      confirmText: '비활성',
    });
    if (!ok) return;
    try {
      await StampService.deactivatePolicy(fid);
      setPolicy(null);
    } catch (err) {
      await alert({
        title: '비활성 실패',
        message: err?.message || '정책 비활성에 실패했습니다.',
      });
    }
  };

  if (loading) {
    return (
      <div className="stamps-page">
        <div className="page-header-section">
          <h1 className="page-title">{t('stamp.title_list', '스탬프')}</h1>
        </div>
        <div className="empty-state"><p>로딩 중...</p></div>
      </div>
    );
  }

  return (
    <div className="stamps-page">
      <div className="page-header-section">
        <h1 className="page-title">{t('stamp.title_list', '스탬프')}</h1>
        <p className="sub-title">매장 스탬프 정책을 관리합니다. (매장당 1개의 active 정책)</p>
      </div>

      {errMsg && (
        <div style={{
          margin: 'var(--pw-space-4)',
          padding: 'var(--pw-space-3) var(--pw-space-4)',
          border: '1px solid var(--pw-error)',
          color: 'var(--pw-error)',
          borderRadius: 'var(--pw-radius-sm)',
          fontSize: 'var(--pw-caption-size)',
        }}>{errMsg}</div>
      )}

      <div className="stamp-list">
        {policy && policy.active ? (
          <Link to={`/dashboard/stamps/view/${policy.id}`} className="stamp-card">
            <div className="stamp-icon active">
              <Stamp size={24} />
            </div>
            <div className="stamp-info">
              <div className="stamp-info-head">
                <h3 className="stamp-name">
                  {policy.reward_description || policy.reward_coupon_title || '스탬프 정책'}
                </h3>
                <span className="stamp-status active">
                  {t('stamp.status_active', '스탬프 적립 중')}
                </span>
              </div>
              <div className="stamp-details">
                <div>{t('stamp.label_threshold', '목표 적립')}: {policy.reward_threshold}회</div>
                {policy.expires_days && (
                  <div>{t('stamp.label_expires_days', '유효기간')}: {policy.expires_days}일</div>
                )}
                {policy.reward_coupon_title && (
                  <div>{t('stamp.label_reward', '보상')}: {policy.reward_coupon_title}</div>
                )}
              </div>
              <button
                onClick={handleDeactivate}
                style={{
                  marginTop: 'var(--pw-space-3)',
                  padding: 'var(--pw-space-2) var(--pw-space-4)',
                  background: 'transparent',
                  border: '1px solid var(--pw-error)',
                  borderRadius: 'var(--pw-radius-sm)',
                  color: 'var(--pw-error)',
                  fontSize: 'var(--pw-caption-size)',
                  fontWeight: 600,
                  cursor: 'pointer',
                  width: 'fit-content',
                }}
              >
                정책 비활성
              </button>
            </div>
            <ChevronRight className="stamp-arrow" size={20} />
          </Link>
        ) : (
          <div className="empty-state">
            <p>등록된 스탬프 정책이 없습니다.</p>
          </div>
        )}
      </div>

      {/* active 정책이 없을 때만 등록 버튼 노출 */}
      {!(policy && policy.active) && (
        <BottomActionBar>
          <Button
            variant="primary"
            fullWidth
            icon={<Plus size={18} />}
            onClick={handleAddClick}
          >
            {t('stamp.title_add', '스탬프 정책 등록')}
          </Button>
        </BottomActionBar>
      )}
    </div>
  );
};

export default Stamps;
