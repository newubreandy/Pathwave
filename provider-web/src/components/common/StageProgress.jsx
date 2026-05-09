import { STAGE_LABELS } from './stageMapping';
import './StageProgress.css';

/**
 * StageProgress — 와이파이 신청 진행 4단계 스테퍼.
 *
 * 단계: 1 신청완료 → 2 준비중 → 3 배송중 → 4 배송완료
 *
 * "지금 어디 단계인지" 한눈에 보여주는 우측 플래그.
 * 사장님 콘솔에서는 stepper 만 (텍스트 라벨은 status badge 가 담당).
 * 슈퍼어드민에서는 더 상세하게 — showLabel=true 또는 별도 detail 컴포넌트.
 *
 * size: 'sm' (운영툴 inset row 안) | 'md' (단독 카드 / 상세 페이지)
 *
 * stage → applicationStatus 매핑은 ./stageMapping.js 의 getStageNumber 사용.
 */
export default function StageProgress({
  stage,           // 1..4
  size = 'sm',
  showLabel = false,
  className = '',
}) {
  const safeStage = Math.max(0, Math.min(4, stage || 0));
  return (
    <div
      className={`pw-stages pw-stages--${size} ${className}`}
      role="progressbar"
      aria-valuenow={safeStage}
      aria-valuemin={1}
      aria-valuemax={4}
      aria-label={`진행 단계 ${safeStage}/4 (${STAGE_LABELS[safeStage - 1] || ''})`}
    >
      {[1, 2, 3, 4].map((i) => {
        const isCurrent = i === safeStage;
        const isDone = i <= safeStage;
        return (
          <span
            key={i}
            className={[
              'pw-stage-dot',
              isCurrent ? 'is-current' : '',
              isDone ? 'is-done' : '',
            ].filter(Boolean).join(' ')}
          />
        );
      })}
      {showLabel && safeStage > 0 && (
        <span className="pw-stages-label">{STAGE_LABELS[safeStage - 1]}</span>
      )}
    </div>
  );
}
