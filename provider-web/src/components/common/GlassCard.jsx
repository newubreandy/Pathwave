import './GlassCard.css';

/**
 * GlassCard — 운영툴 카드 baseline.
 *
 * "glass" 라는 이름이지만 backdrop-filter blur 는 사용하지 않습니다.
 * 배경 위 반투명 white surface + 1px border 로 카드 경계만 만듭니다.
 * (Linear / Stripe Dashboard 톤)
 *
 * variant:
 *   default    — 기본 카드. 정보 나열용.
 *   prominent  — 신청 진행중 등 ‘액션이 필요한’ 카드.
 *   compact    — 운영중 카드 등 보기 전용. 가장 차분.
 *   warning    — 일시중지 / 점검 필요. 좌측 amber 라인.
 *   success    — 승인/완료 등 (현재 운영중은 compact 사용 권장).
 *   danger     — 해지/오류 등 좌측 red 라인.
 *
 * as       — 렌더 태그 (default 'div'). 'a' / 'button' 도 가능.
 * onClick  — 클릭 가능 카드. role/tabindex 자동 부여.
 * uniformHeight — true 면 같은 부모 안 카드들이 grid stretch 로 동일 높이.
 */
export default function GlassCard({
  variant = 'default',
  as: Tag = 'div',
  className = '',
  onClick,
  uniformHeight = false,
  children,
  ...rest
}) {
  const isInteractive = typeof onClick === 'function';
  const interactiveProps = isInteractive
    ? { role: 'button', tabIndex: 0, onKeyDown: (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick(e);
        }
      } }
    : {};

  return (
    <Tag
      className={[
        'pw-card',
        `pw-card--${variant}`,
        isInteractive ? 'pw-card--interactive' : '',
        uniformHeight ? 'pw-card--uniform' : '',
        className,
      ].filter(Boolean).join(' ')}
      onClick={onClick}
      {...interactiveProps}
      {...rest}
    >
      {children}
    </Tag>
  );
}
