<script setup lang="ts">
/**
 * Money in (top-ups, green with a soft wash) against money spent (orders,
 * amber) per day, on one ¥ axis. The first draw rises from the baseline;
 * later updates glide.
 */
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
  type ScriptableContext,
  type TooltipItem,
} from 'chart.js';
import { Line } from 'vue-chartjs';
import { computed } from 'vue';
import { CHART_INK, CHART_GRID, CHART_TICKS, chartAnimation, chartTooltip, softFill } from './chartTheme';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

const props = defineProps<{
    data: Array<{ date: string; deposit: number; spending: number }>;
}>();

const line = {
    borderWidth: 2,
    tension: 0.4,
    // Smooth, but never overshooting the data (no dips below zero between days).
    cubicInterpolationMode: 'monotone' as const,
    pointRadius: 0,
    pointHoverRadius: 4,
    pointHoverBorderWidth: 2,
    pointHoverBackgroundColor: '#FFFFFF',
};

const chartData = computed(() => ({
    labels: props.data.map(d => d.date),
    datasets: [
        {
            ...line,
            label: '充值',
            data: props.data.map(d => d.deposit),
            borderColor: CHART_INK.primary,
            backgroundColor: (ctx: ScriptableContext<'line'>) => softFill(ctx, CHART_INK.primaryRgb),
            fill: true,
        },
        {
            ...line,
            label: '消费',
            data: props.data.map(d => d.spending),
            borderColor: CHART_INK.secondary,
            backgroundColor: 'transparent',
            fill: false,
        },
    ],
}));

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    ...chartAnimation(),
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
        // The card header carries the legend.
        legend: { display: false },
        tooltip: {
            ...chartTooltip,
            displayColors: true,
            boxWidth: 8,
            boxHeight: 8,
            boxPadding: 4,
            callbacks: {
                label: (item: TooltipItem<'line'>) => ` ${item.dataset.label}  ¥${Number(item.raw).toFixed(2)}`,
            },
        },
    },
    scales: {
        x: {
            grid: { display: false },
            border: { display: false },
            ticks: { color: CHART_TICKS, font: { size: 11 }, maxRotation: 0, autoSkipPadding: 12 },
        },
        y: {
            beginAtZero: true,
            suggestedMax: 100,
            border: { display: false },
            grid: { color: CHART_GRID },
            ticks: { color: CHART_TICKS, font: { size: 11 }, padding: 8, callback: (v: string | number) => `¥${v}` },
        },
    },
};
</script>

<template>
  <div class="w-full h-full">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
