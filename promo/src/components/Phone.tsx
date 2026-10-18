import type { CSSProperties, ReactNode } from 'react';

function StatusGlyphs() {
  return (
    <span className="status-right">
      <svg width="17" height="11" viewBox="0 0 17 11" fill="currentColor" aria-hidden="true">
        <rect x="0" y="7" width="3" height="4" rx="0.8" />
        <rect x="4.5" y="5" width="3" height="6" rx="0.8" />
        <rect x="9" y="2.5" width="3" height="8.5" rx="0.8" />
        <rect x="13.5" y="0" width="3" height="11" rx="0.8" />
      </svg>
      <svg width="15" height="11" viewBox="0 0 15 11" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" aria-hidden="true">
        <path d="M1 4.2a9.5 9.5 0 0 1 13 0" />
        <path d="M3.6 6.8a6 6 0 0 1 7.8 0" />
        <path d="M6.1 9.2a2.4 2.4 0 0 1 2.8 0" />
      </svg>
      <svg width="23" height="11" viewBox="0 0 23 11" fill="none" aria-hidden="true">
        <rect x="0.6" y="0.6" width="19" height="9.8" rx="2.6" stroke="currentColor" strokeWidth="1.1" opacity="0.45" />
        <rect x="2.2" y="2.2" width="14" height="6.6" rx="1.4" fill="currentColor" />
        <path d="M21 4v3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" opacity="0.45" />
      </svg>
    </span>
  );
}

/** 390×844 iPhone-style frame, scaled to any width. */
export function Phone({
  children,
  width = 360,
  className = '',
  style,
  screenClassName = '',
}: {
  children: ReactNode;
  width?: number;
  className?: string;
  style?: CSSProperties;
  screenClassName?: string;
}) {
  const scale = width / 390;
  return (
    <div
      className={`phone-wrap ${className}`}
      style={{ width, height: 844 * scale, ...style }}
    >
      <div style={{ width: 390, height: 844, transform: `scale(${scale})`, transformOrigin: 'top left' }}>
        <div className="phone">
          <div className={`phone-screen ${screenClassName}`}>{children}</div>
          <div className="phone-island" />
          <div className="phone-status">
            <span>9:41</span>
            <StatusGlyphs />
          </div>
        </div>
      </div>
    </div>
  );
}

export function formatMoney(n: number) {
  return n % 1 === 0 ? `¥${n}` : `¥${n.toFixed(2)}`;
}
