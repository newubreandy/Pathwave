import './SectionTabs.css';

/**
 * SectionTabs — pill 형태 탭.
 *
 * tabs: [{ key, label, count }, ...]
 * value: 현재 활성 탭 key
 * onChange: (newKey) => void
 * sticky: true 면 스크롤 시 상단 고정 (top 은 레이아웃 GNB 높이와 함께 계산)
 *
 * 카운트 배지는 라벨 옆에 inline. 배지가 없으면 (count === undefined) 숨김.
 * 활성 탭은 accent 컬러 + accent border. blur 없음.
 */
export default function SectionTabs({
  tabs,
  value,
  onChange,
  sticky = false,
  ariaLabel,
  className = '',
}) {
  const handleClick = (key) => {
    if (key === value) return;
    onChange?.(key);
  };

  return (
    <nav
      className={[
        'pw-tabs',
        sticky ? 'pw-tabs--sticky' : '',
        className,
      ].filter(Boolean).join(' ')}
      role="tablist"
      aria-label={ariaLabel}
    >
      <div className="pw-tabs-track">
        {tabs.map((t) => {
          const active = value === t.key;
          return (
            <button
              key={t.key}
              type="button"
              role="tab"
              aria-selected={active}
              className={`pw-tab ${active ? 'is-active' : ''}`}
              onClick={() => handleClick(t.key)}
            >
              <span className="pw-tab-label">{t.label}</span>
              {typeof t.count === 'number' && (
                <span className="pw-tab-count" aria-label={`${t.count}건`}>
                  {t.count}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
