import './CardAvatar.css';

/**
 * CardAvatar — 카드 좌측 상태 아이콘 박스 (Toss / Linear 톤).
 *
 * "이 카드가 뭔지" 를 1초 안에 시각적으로 알려주는 앵커.
 * 텍스트만 나열되면 카드들이 다 똑같이 보임 — 좌측 컬러 박스가 시선 진입점.
 *
 * variant 색조:
 *   accent  — 신청 진행중 (보라/그린, theme accent)
 *   info    — 신청완료 / 일반 알림
 *   success — 서비스중
 *   warning — 일시중지 / 점검
 *   danger  — 해지 / 오류
 *   neutral — 비활성
 *
 * size: 'sm' (32px) | 'md' (40px, default) | 'lg' (48px)
 *
 * children 으로 lucide-react 아이콘 그대로 받음.
 *   <CardAvatar variant="success"><Wifi /></CardAvatar>
 */
export default function CardAvatar({
  variant = 'neutral',
  size = 'md',
  className = '',
  children,
  ariaLabel,
}) {
  return (
    <span
      className={[
        'pw-avatar',
        `pw-avatar--${variant}`,
        `pw-avatar--${size}`,
        className,
      ].filter(Boolean).join(' ')}
      role={ariaLabel ? 'img' : 'presentation'}
      aria-label={ariaLabel}
      aria-hidden={ariaLabel ? undefined : true}
    >
      {children}
    </span>
  );
}
