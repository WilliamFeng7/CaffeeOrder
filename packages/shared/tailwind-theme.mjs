/**
 * Shared visual tokens for Student / Admin / Barista: one minimal system.
 *
 * Warm white, near-black ink and a single green accent; hairlines and
 * whitespace separate things, shadows only lift what floats. Every text pair
 * meets 4.5:1 (text-sub also on the `cream` fill). Components use these names,
 * never raw hex values.
 */
export const colors = {
  primary: '#1B5E47',             // 森林绿: 主按钮、选中态 (the only accent)
  'primary-dark': '#154A38',      // pressed
  'primary-soft': '#EAF1ED',      // selected background
  'primary-content': '#FFFFFF',
  secondary: '#C8963E',           // 焦糖色: small icons only (star)
  'secondary-soft': '#F7EFE0',
  'secondary-content': '#7A5213', // text on secondary-soft
  'background-light': '#FAFAF7',  // warm white page
  'background-dark': '#0C1F1A',
  'surface-light': '#FFFFFF',     // panels
  cream: '#F2F1EC',               // image placeholders, inputs, segmented tracks
  line: '#E9E7E2',                // hairlines
  'line-strong': '#D6D3CC',       // input borders and strong hairlines
  'text-main': '#171C19',         // ink
  'text-sub': '#676C69',          // secondary text
  danger: '#B42318',
  'danger-soft': '#FDEDEB',
  warning: '#9A5B0B',
  'warning-soft': '#FCF1E3',
  wechat: '#07C160',
  alipay: '#1677FF',
};

export default {
  theme: {
    extend: {
      colors,
      borderRadius: {
        tile: '12px',   // images, inputs, small blocks
        card: '16px',   // cards, product photos
        sheet: '24px',  // sheets and dialogs
      },
      boxShadow: {
        card: '0 1px 2px rgba(23, 28, 25, 0.04)',
        float: '0 16px 40px -16px rgba(23, 28, 25, 0.35)',
        sheet: '0 -12px 40px rgba(23, 28, 25, 0.10)',
      },
    },
  },
};
