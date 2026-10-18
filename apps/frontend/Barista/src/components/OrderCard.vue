<script setup lang="ts">
/**
 * 看板上的一张 App 订单，点开后在 OrderSheet 里操作。
 * next：最早的一张待录单，整块绿色，咖啡师先录它；waiting：其余待录单；making：制作中，收银单号打头。
 */
import { computed } from 'vue';
import type { BaristaOrder } from '../api';
import { clock, LONG_WAIT_MINUTES, waited, waitedMinutes } from '../time';

const props = defineProps<{
    order: BaristaOrder;
    now: number;
    variant: 'next' | 'waiting' | 'making';
    /** 刚来的新订单，底色闪一下。 */
    fresh?: boolean;
}>();

defineEmits<{ open: [] }>();

const waitText = computed(() => waited(props.order.createTime, props.now));
const longWait = computed(() => waitedMinutes(props.order.createTime, props.now) >= LONG_WAIT_MINUTES);
</script>

<template>
    <button type="button" class="card" :class="[variant, { flash: fresh }]" @click="$emit('open')">
        <div class="head">
            <span v-if="variant === 'making'" class="pos">{{ order.posOrderNo }}</span>
            <span v-else class="name">{{ order.studentName }}</span>
            <span class="meta">
                <span class="font-num tabular-nums">{{ clock(order.createTime) }}</span>
                <span :class="{ long: longWait }">{{ waitText }}</span>
            </span>
        </div>
        <p v-if="variant === 'making'" class="name">{{ order.studentName }}</p>

        <ul class="items">
            <li v-for="(item, index) in order.items" :key="index">
                <span class="item-name">{{ item.name }}</span>
                <span class="qty" :class="{ many: item.quantity > 1 }">×{{ item.quantity }}</span>
                <span v-if="item.optionsText" class="options">{{ item.optionsText }}</span>
            </li>
        </ul>

        <span v-if="variant === 'next'" class="cta">录单</span>
    </button>
</template>

<style scoped>
.card {
    display: flex;
    flex-direction: column;
    gap: 10px;
    width: 100%;
    padding: 16px 18px 18px;
    border: 1px solid theme('colors.line');
    border-radius: 18px;
    background: theme('colors.surface-light');
    color: theme('colors.text-main');
    text-align: left;
}

.head {
    display: flex;
    align-items: baseline;
    /* 列太窄时等待时长整体掉到第二行，名字和收银单号不被挤成竖排。 */
    flex-wrap: wrap;
    gap: 12px;
    min-width: 0;
}

.name {
    min-width: 0;
    font-size: 19px;
    font-weight: 600;
    line-height: 1.3;
    overflow-wrap: anywhere;
}

.pos {
    min-width: 0;
    font-family: theme('fontFamily.num');
    /* 32px 下 12 位的收银单号也能完整放进 iPad 横屏的一列。 */
    font-size: 32px;
    font-weight: 700;
    line-height: 1;
    font-variant-numeric: tabular-nums;
    /* 收银单号是念出来取餐的号，竖排断行就没法认了；长单号允许横向溢出也不竖排。 */
    white-space: nowrap;
}

.meta {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 4px 12px;
    margin-left: auto;
    flex-shrink: 0;
    font-size: 16px;
    color: theme('colors.text-sub');
}

.long {
    color: theme('colors.warning');
    font-weight: 600;
}

.items {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.items li {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    column-gap: 12px;
    align-items: baseline;
}

.item-name {
    font-size: 21px;
    font-weight: 600;
    line-height: 1.3;
}

.qty {
    font-family: theme('fontFamily.num');
    font-size: 19px;
    font-weight: 600;
    color: theme('colors.text-sub');
    font-variant-numeric: tabular-nums;
}

/* 两杯以上最容易漏看，单独标出来。 */
.qty.many {
    padding: 1px 10px;
    border-radius: 999px;
    background: theme('colors.secondary-soft');
    color: theme('colors.secondary-content');
}

.options {
    grid-column: 1 / -1;
    font-size: 17px;
    line-height: 1.35;
    color: theme('colors.text-sub');
}

.making .name {
    font-size: 18px;
    font-weight: 500;
    color: theme('colors.text-sub');
}

/* 最早的一张待录单：全看板唯一的大色块。 */
.next {
    --flash-color: theme('colors.primary-flash');
    gap: 14px;
    padding: 20px 22px 22px;
    border-color: theme('colors.primary');
    border-radius: 22px;
    background: theme('colors.primary');
    color: theme('colors.primary-content');
}

.next .name {
    font-size: 23px;
}

.next .meta,
.next .qty,
.next .options {
    color: theme('colors.on-primary-sub');
}

.next .meta {
    font-size: 17px;
}

.next .long {
    color: theme('colors.on-primary-warning');
}

.next .items {
    gap: 12px;
}

.next .item-name {
    font-size: 28px;
}

.next .qty {
    font-size: 23px;
}

.next .qty.many {
    background: theme('colors.surface-light');
    color: theme('colors.primary');
}

.next .options {
    font-size: 19px;
}

.cta {
    align-self: flex-end;
    display: inline-flex;
    align-items: center;
    height: 48px;
    padding: 0 26px;
    border-radius: 999px;
    background: theme('colors.surface-light');
    color: theme('colors.primary');
    font-size: 19px;
    font-weight: 600;
}

/* 刚来的新订单闪一圈焦糖色光环，配着提示音，一眼就看到。 */
.flash {
    animation: flashRing 2.2s ease-out;
}

@keyframes flashRing {
    0%, 45% {
        box-shadow: 0 0 0 5px rgba(200, 150, 62, 0.9);
    }
    100% {
        box-shadow: 0 0 0 5px rgba(200, 150, 62, 0);
    }
}

@media (prefers-reduced-motion: reduce) {
    .flash {
        animation: none;
    }
}
</style>
