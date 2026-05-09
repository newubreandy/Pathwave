import './StatusMessage.css';

/**
 * StatusMessage — 카드 안 1~2줄 상태 안내.
 *
 * "현재 어디 단계인지" 한 줄로 알려주는 용도. 절대 타임라인/단계 나열 X.
 *   ⓘ 비콘 SN 매핑 진행 중입니다.
 *
 * tone:
 *   info     — 기본 (회색) — 안내성
 *   accent   — provider/admin accent (보라/그린) — ‘진행 중’ 강조
 *   warning  — 주의 (amber)
 *   danger   — 경고 (red)
 *
 * 메시지는 항상 2줄 clamp. 길어지면 카드 높이 들쭉날쭉 → 운영중 정보판 톤이 깨짐.
 * 긴 메시지는 상세보기에서 보여주세요.
 */
export default function StatusMessage({
  tone = 'info',
  children,
  updatedAt,
  className = '',
}) {
  if (!children && !updatedAt) return null;
  return (
    <div className={`pw-statusmsg pw-statusmsg--${tone} ${className}`} role="note">
      {children && <p className="pw-statusmsg-text">{children}</p>}
      {updatedAt && <span className="pw-statusmsg-time">{updatedAt}</span>}
    </div>
  );
}
