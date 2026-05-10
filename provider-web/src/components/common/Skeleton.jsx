import './Skeleton.css';

/**
 * Skeleton — 로딩 중 자리 모양 표시.
 *
 * 1초 이상 빈 화면 = "앱이 멈췄다" 신호. 스켈레톤으로 즉시 ‘앱은 살아있고
 * 곧 데이터가 온다’ 를 보여줘서 사용자 이탈/재시작 방지.
 *
 *   <Skeleton variant="card" count={3} />          // 와이파이 카드 자리 3개
 *   <Skeleton variant="text" width="60%" />         // 텍스트 한 줄
 *   <Skeleton variant="circle" size={40} />         // 아바타 자리
 *   <Skeleton variant="rect" width="100%" height={20} />
 *
 * shimmer 애니메이션은 reduced-motion 환경에서 자동으로 정적 배경으로 전환.
 */
export default function Skeleton({
  variant = 'text',
  count = 1,
  width,
  height,
  size,
  className = '',
}) {
  const items = Array.from({ length: count });

  const style = {};
  if (width)  style.width  = typeof width  === 'number' ? `${width}px`  : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;
  if (size)   { style.width = style.height = typeof size === 'number' ? `${size}px` : size; }

  return (
    <>
      {items.map((_, i) => (
        <span
          key={i}
          className={['pw-skel', `pw-skel--${variant}`, className].filter(Boolean).join(' ')}
          style={style}
          aria-hidden="true"
        />
      ))}
    </>
  );
}

/**
 * SkeletonCard — 와이파이 리스트 카드 자리 모양 (avatar + 제목 + pill 라인 + 메시지).
 * WifiSettings 같은 페이지에서 isLoading 시 즉시 사용.
 */
export function SkeletonCard({ count = 3 }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div className="pw-skel-card" key={i} aria-hidden="true">
          <Skeleton variant="rect" className="pw-skel-card-avatar" />
          <div className="pw-skel-card-body">
            <Skeleton variant="rect" className="pw-skel-card-title" />
            <div className="pw-skel-card-pills">
              <Skeleton variant="rect" className="pw-skel-pill" />
              <Skeleton variant="rect" className="pw-skel-pill pw-skel-pill--narrow" />
            </div>
            <Skeleton variant="rect" className="pw-skel-card-msg" />
          </div>
        </div>
      ))}
    </>
  );
}
