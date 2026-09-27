<script setup lang="ts">
/**
 * 24h trend of one measure at a time (orders or revenue), on one axis. The
 * two measures have different units, so the dashboard switches between them
 * instead of stacking two y-scales on one plot. Switching glides the line to
 * the new values; the first draw rises from the baseline.
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

const props = withDefaults(defineProps<{
    data: Array<{ hour: string; orders: number; revenue: number }>;
    metric?: 'orders' | 'revenue';
}>(), { metric: 'orders' });

const isMoney = computed(() => props.metric === 'revenue');

const chartData = computed(() => ({
    labels: props.data.map(d => d.hour),
    datasets: [
        {
            // One dataset whose values change, so a switch animates in place.
            label: isMoney.value ? '销售额' : '订单量',
            data: props.data.map(d => (isMoney.value ? d.revenue : d.orders)),
            borderColor: CHART_INK.primary,
            borderWidth: 2,
            backgroundColor: (ctx: ScriptableContext<'line'>) => softFill(ctx, CHART_INK.primaryRgb),
            fill: true,
            tension: 0.4,
            // Smooth without overshooting below zero between hours.
            cubicInterpolationMode: 'monotone' as const,
            pointRadius: 0,
            pointHoverRadius: 4,
            pointHoverBorderWidth: 2,
            pointHoverBackgroundColor: '#FFFFFF',
        },
    ],
}));

const chartOptions = computed(() => ({
    responsive: true,
    maintainAspectRatio: false,
    ...chartAnimation(),
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
        legend: { display: false },
        tooltip: {
            ...chartTooltip,
            callbacks: {
                label: (item: TooltipItem<'line'>) =>
                    isMoney.value ? `¥${Number(item.raw).toFixed(2)}` : `${item.raw} 笔`,
            },
        },
    },
    scales: {
        x: {
            grid: { display: false },
            border: { display: false },
            ticks: { color: CHART_TICKS, font: { size: 11 }, maxRotation: 0, autoSkipPadding: 12 },
        },
        // Counts and money never go below zero; without a floor an empty day
        // was drawn in the middle of a -1..1 axis.
        y: {
            beginAtZero: true,
            suggestedMax: isMoney.value ? 100 : 5,
            border: { display: false },
            grid: { color: CHART_GRID },
            ticks: {
                color: CHART_TICKS,
                font: { size: 11 },
                padding: 8,
                precision: 0,
                callback: (v: string | number) => (isMoney.value ? `¥${v}` : v),
            },
        },
    },
}));
</script>

<template>
  <div class="w-full h-full">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
