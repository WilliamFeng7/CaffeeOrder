import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from 'react';

export function useInView<T extends HTMLElement>(options?: IntersectionObserverInit) {
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (typeof IntersectionObserver === 'undefined') {
      setInView(true);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setInView(true);
            observer.unobserve(entry.target);
          }
        }
      },
      { threshold: 0.12, rootMargin: '0px 0px -6% 0px', ...options },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [options]);

  return { ref, inView };
}

export function Reveal({
  children,
  delay = 0,
  className = '',
  group = false,
  style,
  'aria-hidden': ariaHidden,
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
  group?: boolean;
  style?: CSSProperties;
  'aria-hidden'?: boolean;
}) {
  const { ref, inView } = useInView<HTMLDivElement>();
  return (
    <div
      ref={ref}
      className={`${group ? 'reveal-group' : 'reveal'} ${inView ? 'is-in' : ''} ${className}`}
      aria-hidden={ariaHidden}
      style={{ '--reveal-delay': `${delay}ms`, ...style } as CSSProperties}
    >
      {children}
    </div>
  );
}
