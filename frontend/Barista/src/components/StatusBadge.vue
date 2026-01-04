<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  status: string;
}>();

const config = computed(() => {
  switch (props.status.toLowerCase()) {
    case 'pending':
    case 'new':
      return { color: 'bg-kds-pending/10 text-kds-pending', icon: 'schedule', label: 'Pending' };
    case 'processing':
    case 'inprogress':
      return { color: 'bg-kds-processing/10 text-kds-processing', icon: 'coffee_maker', label: 'Processing' };
    case 'completed':
    case 'done':
      return { color: 'bg-kds-completed/10 text-kds-completed', icon: 'check_circle', label: 'Ready' };
    case 'cancelled':
      return { color: 'bg-gray-100 text-gray-500', icon: 'cancel', label: 'Cancelled' };
    default:
      return { color: 'bg-gray-100 text-gray-500', icon: 'help', label: props.status };
  }
});
</script>

<template>
  <div 
    class="flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium border border-current/10"
    :class="config.color"
  >
    <span class="material-symbols-rounded text-base">{{ config.icon }}</span>
    <span>{{ config.label }}</span>
  </div>
</template>
