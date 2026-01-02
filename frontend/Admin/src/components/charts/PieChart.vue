<script setup lang="ts">
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js';
import { Pie } from 'vue-chartjs';
import { computed } from 'vue';

ChartJS.register(ArcElement, Tooltip, Legend);

const props = defineProps<{
    data: Array<{ name: string; value: number }>;
}>();

const chartData = computed(() => ({
    labels: props.data.map(d => d.name),
    datasets: [
        {
            backgroundColor: ['#103E32', '#DCCA98', '#EAB308', '#F87171', '#60A5FA'],
            data: props.data.map(d => d.value)
        }
    ]
}));

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'right' as const,
        }
    }
};
</script>

<template>
  <div class="w-full h-full">
    <Pie :data="chartData" :options="chartOptions" />
  </div>
</template>
