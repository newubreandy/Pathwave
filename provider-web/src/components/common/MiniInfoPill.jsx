import './MiniInfoPill.css';

/**
 * MiniInfoPill — 카드 안 작은 메타 정보용 알약.
 *
 *   <MiniInfoPill label="SSID">PathWave_Lobby</MiniInfoPill>
 *
 * 운영툴 톤 — pill 색상은 default(차분) / muted(가장 약함) 두 가지만.
 * 한 카드에 4개 이상 노출되지 않도록 호출부에서 제한할 것.
 *
 * label 은 작은 캡션 (선택). children 은 본문 값.
 * mono=true 면 SN/송장번호 등 monospace 적용.
 */
export default function MiniInfoPill({
  label,
  children,
  mono = false,
  variant = 'default', // default | muted
  className = '',
}) {
  return (
    <span
      className={[
        'pw-pill',
        `pw-pill--${variant}`,
        mono ? 'pw-pill--mono' : '',
        className,
      ].filter(Boolean).join(' ')}
    >
      {label && <span className="pw-pill-label">{label}</span>}
      <span className="pw-pill-value">{children}</span>
    </span>
  );
}
