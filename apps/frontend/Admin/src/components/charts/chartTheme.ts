/**
 * One look for the console's charts: brand green and amber on hairline grids,
 * an ink tooltip, and a single motion rule - the first draw rises from the
 * baseline (~0.9s), later data changes glide (450ms), and reduced motion gets
 * no chart animation at all.
 */
import type { ScriptableContext } from 'chart.js';

export const CHART_INK = {
    primary: '#1B5E47',
    primaryRgb: '27, 94, 71',
    secondary: '#C8963E',
    secondaryRgb: '200, 150, 62',
};

export const CHART_GRID = '#EFEDE8';
// Same as text-sub: ticks stay readable (5:1 on white).
export const CHART_TICKS = '#676C69';

export const chartTooltip = {
    backgroundColor: '#171C19',
    titleColor: 'rgba(255, 255, 255, 0.65)',
    bodyColor: '#FFFFFF',
    padding: 10,
    cornerRadius: 10,
    caretSize: 5,
    displayColors: false,
    titleFont: { size: 11 },
    bodyFont: { size: 13, weight: 'bold' as const },
};

/** A vertical wash under a line, fading to nothing at the baseline. */
export const softFill = (ctx: ScriptableContext<'line'>, rgb: string) => {
    const { chart } = ctx;
    const area = chart.chartArea;
    if (!area) return `rgba(${rgb}, 0.08)`;
    const gradient = chart.ctx.createLinearGradient(0, area.top, 0, area.bottom);
    gradient.addColorStop(0, `rgba(${rgb}, 0.16)`);
    gradient.addColorStop(1, `rgba(${rgb}, 0)`);
    return gradient;
};

/**
 * Spread into a chart's options (call it once per chart instance). The first
 * draw of a fresh options object rises from the baseline in 0.9s; every
 * later data update (the pages poll every 2s) glides in 450ms.
 */
export const chartAnimation = () => {
    const reduce = typeof window !== 'undefined'
        && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) return { animation: false as const };
    let drawn = false;
    return {
        animation: {
            duration: () => (drawn ? 450 : 900),
            easing: 'easeOutQuart' as const,
            onComplete: () => { drawn = true; },
        },
    };
};
