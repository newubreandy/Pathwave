import './GroupCard.css';

/**
 * GroupCard — 다건 신청 묶음 헤더 + 자식 카드 컨테이너.
 *
 * 헤더는 “이 묶음 안에 뭐가 몇 개 있고 현재 어디까지 됐는지”
 * 2초 안에 이해되도록 설계 — 클립보드 아이콘 + 신청번호 + 결제완료 pill +
 * 부가 subtitle (수량 · 결제일 등). 결제일 자체를 별도 노출하지 않음.
 *
 * props:
 *   leading       — (optional) 헤더 좌측 슬롯. <CardAvatar> 권장.
 *   groupId       — 신청번호 (예: PW-20260509-001)
 *   total         — 묶음 안 wifi 수량 (header pill 안에서 noun 구성)
 *   paid          — true 면 “결제완료” pill 노출
 *   subtitle      — 헤더 아래 한 줄 부가 정보 ("3개 와이파이 · 2026.05.09")
 *   summary       — [{ label, count, tone }] — 그룹 진행률 chip (3개 이하 권장)
 *   children      — 자식 GlassCard 들
 */
export default function GroupCard({
  leading,
  groupId,
  // eslint-disable-next-line no-unused-vars -- 향후 collapse-toggle 버튼 등에서 사용 예정. 현재는 호출부 subtitle 으로 노출.
  total,
  paid = false,
  subtitle,
  summary = [],
  children,
  className = '',
}) {
  return (
    <section className={`pw-group ${className}`}>
      <header className="pw-group-header">
        <div className="pw-group-head-row">
          {leading && <span className="pw-group-leading">{leading}</span>}
          <div className="pw-group-head-text">
            <div className="pw-group-meta">
              <span className="pw-group-id">{groupId}</span>
              {paid && <span className="pw-group-paid">결제완료</span>}
            </div>
            {subtitle && (
              <span className="pw-group-subtitle">{subtitle}</span>
            )}
          </div>
          {summary.length > 0 && (
            <div className="pw-group-summary">
              {summary.map((s) => (
                <span
                  key={s.label}
                  className={`pw-group-chip pw-group-chip--${s.tone || 'default'}`}
                >
                  {s.label}
                  <strong>{s.count}</strong>
                </span>
              ))}
            </div>
          )}
        </div>
      </header>
      <div className="pw-group-children">
        {/* total 미사용 시 GroupCard 호출부에서 subtitle 로 재구성. */}
        {/* total prop 은 향후 collapse-toggle 버튼 노출 등에 사용 예정. */}
        {children}
      </div>
    </section>
  );
}
