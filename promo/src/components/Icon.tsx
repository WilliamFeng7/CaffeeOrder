import type { CSSProperties } from 'react';

/* One-stroke icons on a 24px grid, same drawing rules as the Student app:
   no fills, no inner detail, round caps. */
const PATHS: Record<string, string[]> = {
  house: ['M4.5 10.5 12 4.5l7.5 6v9h-15Z'],
  coffee: ['M5 9.5h11v4a5 5 0 0 1-5 5h-1a5 5 0 0 1-5-5Z', 'M16 11h1.25a2.25 2.25 0 0 1 0 4.5H16'],
  bell: ['M6.5 16.5v-5a5.5 5.5 0 0 1 11 0v5l1.5 1.5h-14Z', 'M10.5 20.75h3'],
  user: ['M12 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 1 0 0 7', 'M5.5 19.5a6.5 6.5 0 0 1 13 0'],
  star: ['M12 4.4l2.17 5.21 5.63.46-4.28 3.67 1.3 5.49L12 16.3l-4.82 2.93 1.3-5.49-4.28-3.67 5.63-.46Z'],
  leaf: ['M5.5 18.5C5.5 10.5 10.5 5.5 18.5 5.5c0 8-5 13-13 13Z', 'M5.5 18.5l7-7'],
  'cup-straw': ['M7 9h10l-1.25 10.5h-7.5Z', 'M13 9l1.5-5.5H17'],
  bread: ['M6.5 19.5V11.4A3.2 3.2 0 0 1 7.6 5.5h8.8a3.2 3.2 0 0 1 1.1 5.9v8.1Z'],
  grid: ['M5 5h5.25v5.25H5Z', 'M13.75 5H19v5.25h-5.25Z', 'M5 13.75h5.25V19H5Z', 'M13.75 13.75H19V19h-5.25Z'],
  bag: ['M5.5 8.5h13l-1 11h-11Z', 'M9 8.5V7a3 3 0 0 1 6 0v1.5'],
  receipt: ['M7 3.5h10v17H7Z', 'M10 9h4', 'M10 12.5h4'],
  history: ['M12 20a8 8 0 1 0 0-16 8 8 0 1 0 0 16', 'M12 8v4.5l3 2'],
  lock: ['M6.5 11h11v8.5h-11Z', 'M9 11V8.5a3 3 0 0 1 6 0V11'],
  search: ['M10.5 17.5a7 7 0 1 0 0-14 7 7 0 1 0 0 14', 'M15.5 15.5l4 4'],
  x: ['M6.5 6.5l11 11', 'M17.5 6.5l-11 11'],
  plus: ['M12 5.5v13', 'M5.5 12h13'],
  minus: ['M5.5 12h13'],
  check: ['M5 12.5l4.5 4.5L19 7.5'],
  'arrow-right': ['M5 12h14', 'M13.5 6.5 19 12l-5.5 5.5'],
  'arrow-left': ['M19 12H5', 'M10.5 6.5 5 12l5.5 5.5'],
  'arrow-up-right': ['M7 17 17 7', 'M9 7h8v8'],
  'caret-down': ['M6 9.5l6 6 6-6'],
  'caret-right': ['M9.5 6l6 6-6 6'],
  play: ['M8.5 5.8v12.4L19 12Z'],
  pause: ['M8.5 5.5v13', 'M15.5 5.5v13'],
  expand: ['M8.5 4.5h-4v4', 'M15.5 4.5h4v4', 'M8.5 19.5h-4v-4', 'M15.5 19.5h4v-4'],
  chat: ['M4.5 5.5h15v10h-7l-4 3v-3h-4Z'],
  card: ['M3.5 7h17v10h-17Z', 'M3.5 10.5h17'],
  sliders: ['M4 8h10', 'M18 8h2', 'M14 5.5v5', 'M4 16h4', 'M12 16h8', 'M8 13.5v5'],
  users: ['M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z', 'M3.5 19.5a5.5 5.5 0 0 1 11 0', 'M15.5 5.5a3 3 0 0 1 0 5.7', 'M17 14.5a5.5 5.5 0 0 1 3.5 5'],
  progress: ['M4 12h16', 'M4 12a2 2 0 1 0 4 0 2 2 0 0 0-4 0Z', 'M10 12a2 2 0 1 0 4 0 2 2 0 0 0-4 0Z', 'M16 12a2 2 0 1 0 4 0 2 2 0 0 0-4 0Z'],
  clock: ['M12 20a8 8 0 1 0 0-16 8 8 0 1 0 0 16Z', 'M12 7.5V12l3 2'],
  copy: ['M8.5 8.5h10v10h-10Z', 'M15.5 8.5V5.5h-10v10h3'],
  spark: ['M12 3.5l1.7 5.2 5.3 1.8-5.3 1.8L12 17.5l-1.7-5.2L5 10.5l5.3-1.8Z'],
  wifi: ['M4 9.5a12 12 0 0 1 16 0', 'M7 13a8 8 0 0 1 10 0', 'M10 16.2a4 4 0 0 1 4 0'],
  volume: ['M4 9.5h3.2L11.5 6v12L7.2 14.5H4Z', 'M15 9.2a4.2 4.2 0 0 1 0 5.6', 'M17.8 6.6a8 8 0 0 1 0 10.8'],
  'volume-off': ['M4 9.5h3.2L11.5 6v12L7.2 14.5H4Z', 'M15.5 9.5l4.5 4.5', 'M20 9.5l-4.5 4.5'],
};

export type IconName = keyof typeof PATHS;

export function Icon({
  name,
  size = 20,
  className,
  strokeWidth = 1.5,
  style,
}: {
  name: IconName;
  size?: number;
  className?: string;
  strokeWidth?: number;
  style?: CSSProperties;
}) {
  const isPlay = name === 'play';
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      style={style}
      fill={isPlay ? 'currentColor' : 'none'}
      stroke={isPlay ? 'none' : 'currentColor'}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {PATHS[name].map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  );
}
