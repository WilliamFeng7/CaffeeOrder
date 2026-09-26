<script setup lang="ts">
import AppIcon from '@shared/components/AppIcon.vue';
import { computed } from 'vue';
import type { IconName } from '@shared/icons';

const props = defineProps<{
  status: string;
}>();

const config = computed((): { color: string; icon: IconName; label: string } => {
  switch (props.status.toLowerCase()) {
    case 'pending':
    case 'new':
      return { color: 'bg-kds-pending/10 text-kds-pending', icon: 'clock', label: 'Pending' };
    case 'processing':
    case 'inprogress':
      return { color: 'bg-kds-processing/10 text-kds-processing', icon: 'coffee', label: 'Processing' };
    case 'completed':
    case 'done':
      return { color: 'bg-kds-completed/10 text-kds-completed', icon: 'check-circle', label: 'Ready' };
    case 'cancelled':
      return { color: 'bg-gray-100 text-gray-500', icon: 'x-circle', label: 'Cancelled' };
    default:
      return { color: 'bg-gray-100 text-gray-500', icon: 'question', label: props.status };
  }
});
</script>

<template>
  <div 
    class="flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium border border-current/10"
    :class="config.color"
  >
    <AppIcon :name="config.icon" class="text-base" />
    <span>{{ config.label }}</span>
  </div>
</template>
