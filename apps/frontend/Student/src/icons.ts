/**
 * icons.ts
 *
 * 超简约线条图标 (Ultra-minimal line icons) for the Student app. Each icon is
 * one to four strokes on a 24px grid - no fills, no inner detail (no steam
 * on the cup, no lines on the bag) - drawn with one stroke weight and round
 * ends by components/AppIcon.vue.
 *
 * The Admin and KDS apps keep the shared Phosphor set (packages/shared).
 */
export const ICONS = {
  // Navigation
  house: ['M4.5 10.5 12 4.5l7.5 6v9h-15Z'],
  coffee: ['M5 9.5h11v4a5 5 0 0 1-5 5h-1a5 5 0 0 1-5-5Z', 'M16 11h1.25a2.25 2.25 0 0 1 0 4.5H16'],
  bell: ['M6.5 16.5v-5a5.5 5.5 0 0 1 11 0v5l1.5 1.5h-14Z', 'M10.5 20.75h3'],
  user: ['M12 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 1 0 0 7', 'M5.5 19.5a6.5 6.5 0 0 1 13 0'],

  // Menu categories (the iPad sidebar)
  star: ['M12 4.4l2.17 5.21 5.63.46-4.28 3.67 1.3 5.49L12 16.3l-4.82 2.93 1.3-5.49-4.28-3.67 5.63-.46Z'],
  leaf: ['M5.5 18.5C5.5 10.5 10.5 5.5 18.5 5.5c0 8-5 13-13 13Z', 'M5.5 18.5l7-7'],
  'cup-straw': ['M7 9h10l-1.25 10.5h-7.5Z', 'M13 9l1.5-5.5H17'],
  bread: ['M6.5 19.5V11.4A3.2 3.2 0 0 1 7.6 5.5h8.8a3.2 3.2 0 0 1 1.1 5.9v8.1Z'],
  grid: ['M5 5h5.25v5.25H5Z', 'M13.75 5H19v5.25h-5.25Z', 'M5 13.75h5.25V19H5Z', 'M13.75 13.75H19V19h-5.25Z'],

  // Objects
  bag: ['M5.5 8.5h13l-1 11h-11Z', 'M9 8.5V7a3 3 0 0 1 6 0v1.5'],
  receipt: ['M7 3.5h10v17H7Z', 'M10 9h4', 'M10 12.5h4'],
  history: ['M12 20a8 8 0 1 0 0-16 8 8 0 1 0 0 16', 'M12 8v4.5l3 2'],
  lock: ['M6.5 11h11v8.5h-11Z', 'M9 11V8.5a3 3 0 0 1 6 0V11'],
  search: ['M10.5 17.5a7 7 0 1 0 0-14 7 7 0 1 0 0 14', 'M15.5 15.5l4 4'],
  eye: [
    'M2.5 12c2.2-4 5.4-6.5 9.5-6.5s7.3 2.5 9.5 6.5c-2.2 4-5.4 6.5-9.5 6.5S4.7 16 2.5 12Z',
    'M12 14.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 1 0 0 5',
  ],
  'eye-slash': [
    'M2.5 12c2.2-4 5.4-6.5 9.5-6.5s7.3 2.5 9.5 6.5c-2.2 4-5.4 6.5-9.5 6.5S4.7 16 2.5 12Z',
    'M4.5 4.5l15 15',
  ],

  // Actions
  x: ['M6.5 6.5l11 11', 'M17.5 6.5l-11 11'],
  plus: ['M12 5.5v13', 'M5.5 12h13'],
  minus: ['M5.5 12h13'],
  check: ['M5 12.5l4.5 4.5L19 7.5'],
  'arrow-right': ['M5 12h14', 'M13.5 6.5 19 12l-5.5 5.5'],
  'arrow-left': ['M19 12H5', 'M10.5 6.5 5 12l5.5 5.5'],
  'arrow-up-right': ['M7 17 17 7', 'M9 7h8v8'],
  'caret-down': ['M6 9.5l6 6 6-6'],
  'caret-right': ['M9.5 6l6 6-6 6'],
  trash: ['M5.5 7.5h13', 'M9 7.5V5.5h6v2', 'M7.5 7.5l.7 12h7.6l.7-12', 'M10.5 11v5', 'M13.5 11v5'],
} satisfies Record<string, string[]>;

export type IconName = keyof typeof ICONS;
export type IconWeight = 'light' | 'regular' | 'fill' | 'bold';
