<script setup lang="ts">
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'vue-chartjs';
import { computed } from 'vue';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const props = defineProps<{
    data: Array<{ hour: string; orders: number; revenue: number }>;
}>();

const chartData = computed(() => ({
    labels: props.data.map(d => d.hour),
    datasets: [
        {
            label: '订单量 (笔)',
            data: props.data.map(d => d.orders),
            borderColor: '#103E32',
            backgroundColor: 'rgba(16, 62, 50, 0.1)',
            fill: true,
            tension: 0.4,
            // Smooth without overshooting below zero between hours.
            cubicInterpolationMode: 'monotone' as const,
            yAxisID: 'y'
        },
        {
            label: '销售额 (¥)',
            data: props.data.map(d => d.revenue),
            borderColor: '#DCCA98',
            backgroundColor: 'transparent',
            borderDash: [5, 5],
            tension: 0.4,
            cubicInterpolationMode: 'monotone' as const,
            yAxisID: 'y1'
        }
    ]
}));

// The dashboard refreshes every few seconds, so the chart must not replay a
// long entrance on each update: 300ms, and none at all under reduced motion.
const reduceMotion = typeof window !== 'undefined'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: reduceMotion ? (false as const) : { duration: 300 },
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
        // The card header already carries the legend.
        legend: {
            display: false,
        },
        tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            titleColor: '#333',
            bodyColor: '#666',
            borderColor: '#ddd',
            borderWidth: 1,
            padding: 10,
            displayColors: true,
        }
    },
    scales: {
        x: {
            grid: {
                display: false
            }
        },
        // Counts and money never go below zero; without a floor an empty day
        // was drawn in the middle of a -1..1 axis.
        y: {
            type: 'linear' as const,
            display: true,
            position: 'left' as const,
            beginAtZero: true,
            suggestedMax: 5,
            ticks: {
                precision: 0
            },
            grid: {
                color: '#f0f0f0'
            },
            title: {
                display: true,
                text: '订单量'
            }
        },
        y1: {
            type: 'linear' as const,
            display: true,
            position: 'right' as const,
            beginAtZero: true,
            suggestedMax: 100,
            grid: {
                drawOnChartArea: false,
            },
            title: {
                display: true,
                text: '销售额 (¥)'
            }
        },
    }
};
</script>

<template>
  <div class="w-full h-full">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
