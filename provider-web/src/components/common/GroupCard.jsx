import './GroupCard.css';

/**
 * GroupCard — 다건 신청 묶음 헤더 + 자식 카드 컨테이너.
 *
 * 헤더는 “이 묶음 안에 뭐가 몇 개 있고 현재 어디까지 됐는지”
 * 2초 안에 이해되도록 신청번호 / 수량 / 상태요약 만 노출.
 * 결제일 등 부수정보는 노출하지 않음 (상세보기 또는 자식 카드 메타에서).
 *
 * props:
 *   groupId      — 신청번호 (예: PW-20260509-001)
 *   total        — 묶음 안 wifi 수량
 *   summary      — [{ label: '준비중', count: 2, tone: 'accent' }, ...]
 *                  3개 이하 권장.
 *   children     — 자식 GlassCard 들
 */
export default function GroupCard({
  groupId,
  total,
  summary = [],
  children,
  className = '',
}) {
  return (
    <section className={`pw-group ${className}`}>
      <header className="pw-group-header">
        <div className="pw-group-meta">
          <span className="pw-group-id">{groupId}</span>
          <span className="pw-group-dot" aria-hidden="true">·</span>
          <span className="pw-group-total">{total}건</span>
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
      </header>
      <div className="pw-group-children">
        {children}
      </div>
    </section>
  );
}
