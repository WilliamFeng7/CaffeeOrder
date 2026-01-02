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
    data: Array<{ date: string; deposit: number; spending: number }>;
}>();

const chartData = computed(() => ({
    labels: props.data.map(d => d.date),
    datasets: [
        {
            label: '充值',
            data: props.data.map(d => d.deposit),
            borderColor: '#10B981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            fill: true,
            tension: 0.4,
        },
        {
            label: '消费',
            data: props.data.map(d => d.spending),
            borderColor: '#F87171',
            backgroundColor: 'rgba(248, 113, 113, 0.1)',
            fill: true,
            tension: 0.4,
        }
    ]
}));

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
        legend: {
            position: 'top' as const,
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
        y: {
            type: 'linear' as const,
            display: true,
            position: 'left' as const,
            grid: {
                color: '#f0f0f0'
            },
            title: {
                display: true,
                text: '金额 (¥)'
            }
        }
    }
};
</script>

<template>
  <div class="w-full h-full">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
