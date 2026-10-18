<script setup lang="ts">
/**
 * 点开一张订单后的操作层，从屏幕底部升起。
 *
 * 待录单：照着收银系统的小票，用下面的数字键盘把收银单号填进来（收银单号可能带字母，
 * 这时点输入框用系统键盘）；确认后订单进入制作中。
 * 制作中：可以更正收银单号；饮品做好后点"制作完成"，学生端随即看到。
 * 制作完成：点错了可以撤回。
 *
 * "制作完成"和"撤回"都是两步的，第一下只是让按钮表态，3 秒内再点才真的执行——
 * 学生在学生端马上看得到，不希望误触。
 */
import { computed, onUnmounted, ref, watch } from 'vue';
import AppIcon from '@shared/components/AppIcon.vue';
import { useToastStore } from '@shared/toast';
import { YudaoError } from '@shared/yudao-client';
import {
    enterOrder,
    finishOrder,
    undoFinishOrder,
    STATUS_DONE,
    STATUS_MAKING,
    type BaristaOrder,
} from '../api';
import { clock, waited } from '../time';

const props = defineProps<{
    order: BaristaOrder;
    now: number;
}>();

const emit = defineEmits<{
    close: [];
    changed: [order: BaristaOrder];
}>();

const toast = useToastStore();

/** 收银单号编辑框：待录单一打开就在编辑态，制作中要点"更正收银单号"才进编辑态。 */
const posInput = ref('');
const editingPos = ref(false);
/** 请求进行中，禁用所有操作，防止连点出重复请求。 */
const busy = ref(false);
const failure = ref('');

/** 待确认的危险动作：'done' 制作完成 / 'undo' 撤回制作完成。3 秒不点就恢复原样。 */
const armed = ref<'' | 'done' | 'undo'>('');
let armTimer: number | undefined;
function arm(action: 'done' | 'undo') {
    armed.value = action;
    window.clearTimeout(armTimer);
    armTimer = window.setTimeout(() => { armed.value = ''; }, 3000);
}
onUnmounted(() => window.clearTimeout(armTimer));

// 看板轮询可能换了一张选中单，状态全部重来。
watch(() => props.order.id, (id, previous) => {
    if (id === previous) return;
    posInput.value = props.order.posOrderNo ?? '';
    editingPos.value = props.order.status !== STATUS_DONE && !props.order.posOrderNo;
    failure.value = '';
    armed.value = '';
}, { immediate: true });

const STATUS_LABEL: Record<number, string> = { 10: '待录单', 20: '制作中', 30: '制作完成' };
const statusLabel = computed(() => STATUS_LABEL[props.order.status] ?? '未知状态');

/** 分 → "15" / "15.5"。 */
const yuan = (fen: number) => {
    const value = fen / 100;
    return Number.isInteger(value) ? String(value) : value.toFixed(2).replace(/0$/, '');
};

const canSubmitPos = computed(() => posInput.value.trim().length > 0 && !busy.value);

function pressKey(key: string) {
    if (busy.value) return;
    failure.value = '';
    if (key === 'back') posInput.value = posInput.value.slice(0, -1);
    else if (key === 'clear') posInput.value = '';
    else if (posInput.value.length < 24) posInput.value += key;
}

/** 回填收银单号（待录单 → 制作中）或更正收银单号（制作中）。 */
async function submitPos() {
    const posOrderNo = posInput.value.trim();
    if (!posOrderNo || busy.value) return;
    busy.value = true;
    failure.value = '';
    try {
        await enterOrder(props.order.id, posOrderNo);
        const correcting = props.order.status === STATUS_MAKING;
        toast.success(correcting ? '收银单号已更正' : `已回填收银单号 ${posOrderNo}，开始制作`);
        emit('changed', { ...props.order, status: STATUS_MAKING, posOrderNo, enteredTime: Date.now() });
    } catch (error) {
        failure.value = error instanceof YudaoError ? error.msg : '回填失败，请重试';
    } finally {
        busy.value = false;
    }
}

/** 制作完成（两步）。 */
async function submitDone() {
    if (armed.value !== 'done') {
        arm('done');
        return;
    }
    armed.value = '';
    busy.value = true;
    try {
        await finishOrder(props.order.id);
        toast.success(`${props.order.posOrderNo} 制作完成`);
        emit('changed', { ...props.order, status: STATUS_DONE, doneTime: Date.now() });
    } catch (error) {
        toast.error(error instanceof YudaoError ? error.msg : '操作失败，请重试');
    } finally {
        busy.value = false;
    }
}

/** 撤回制作完成（两步），订单回到制作中。 */
async function submitUndo() {
    if (armed.value !== 'undo') {
        arm('undo');
        return;
    }
    armed.value = '';
    busy.value = true;
    try {
        await undoFinishOrder(props.order.id);
        toast.info(`${props.order.posOrderNo} 已撤回，回到制作中`);
        emit('changed', { ...props.order, status: STATUS_MAKING, doneTime: null });
    } catch (error) {
        toast.error(error instanceof YudaoError ? error.msg : '操作失败，请重试');
    } finally {
        busy.value = false;
    }
}

function requestClose() {
    if (!busy.value) emit('close');
}
</script>

<template>
<Teleport to="body">
  <Transition name="sheet" appear>
    <div class="fixed inset-0 z-40 flex items-end justify-center" role="dialog" aria-modal="true" :aria-label="`订单 ${order.orderNo}`">
      <!-- 遮罩 -->
      <div class="scrim absolute inset-0" @click="requestClose"></div>

      <div class="panel relative w-full max-w-[600px] max-h-[92vh] flex flex-col">
        <!-- 头部：状态、学生、时间 -->
        <div class="flex items-start gap-3 px-6 pt-5 pb-4">
          <span class="chip mt-1" :class="order.status === 10 ? 'chip-accent' : order.status === 20 ? 'chip-warm' : 'chip-quiet'">{{ statusLabel }}</span>
          <div class="min-w-0 flex-1">
            <p class="text-[22px] font-semibold leading-tight truncate">{{ order.studentName }}</p>
            <p class="mt-0.5 text-[14px] text-text-sub tabular-nums">{{ clock(order.createTime) }} 下单 · {{ waited(order.createTime, now) }}</p>
          </div>
          <button type="button" class="icon-btn -mr-2 -mt-1" aria-label="关闭" :disabled="busy" @click="requestClose">
            <AppIcon name="x" weight="light" class="text-[20px]" />
          </button>
        </div>

        <!-- 条目 -->
        <ul class="px-6 pb-2 overflow-y-auto">
          <li v-for="(item, index) in order.items" :key="index" class="flex items-baseline gap-3 py-2.5 border-t border-line first:border-t-0">
            <span class="min-w-0 flex-1">
              <span class="block text-[19px] font-medium">{{ item.name }}</span>
              <span v-if="item.optionsText" class="block mt-0.5 text-[15px] text-text-sub">{{ item.optionsText }}</span>
            </span>
            <span class="font-num text-[18px] font-semibold tabular-nums" :class="{ 'text-secondary-content': item.quantity > 1 }">×{{ item.quantity }}</span>
          </li>
        </ul>
        <p class="px-6 pb-4 text-[14px] text-text-sub tabular-nums">合计 ¥{{ yuan(order.totalPrice) }} · {{ order.cupCount }} 杯</p>

        <!-- 收银单号编辑：待录单回填，制作中更正 -->
        <div v-if="editingPos && order.status !== 30" class="px-6 pb-6 pt-1">
          <label class="eyebrow" for="pos-input">收银单号</label>
          <input
            id="pos-input"
            v-model="posInput"
            type="text"
            class="pos-input mt-2"
            :class="{ 'is-empty': !posInput }"
            placeholder="小票上的单号"
            autocomplete="off"
            autocapitalize="characters"
            spellcheck="false"
            maxlength="24"
            :disabled="busy"
            @keydown.enter="submitPos"
          />
          <div class="keypad mt-3" aria-hidden="true">
            <button v-for="key in ['1','2','3','4','5','6','7','8','9']" :key="key" type="button" class="key" @click="pressKey(key)">{{ key }}</button>
            <button type="button" class="key text-[15px] font-medium" @click="pressKey('clear')">清空</button>
            <button type="button" class="key" @click="pressKey('0')">0</button>
            <button type="button" class="key" aria-label="删除一位" @click="pressKey('back')"><AppIcon name="arrow-left" weight="light" class="text-[20px]" /></button>
          </div>
          <p v-if="failure" class="mt-3 text-[14px] text-danger" role="alert">{{ failure }}</p>
          <button type="button" class="btn btn-primary btn-lg w-full mt-4" :disabled="!canSubmitPos" @click="submitPos">
            <span v-if="busy" class="size-4 border-[1.5px] border-white/30 border-t-white rounded-full animate-spin" aria-hidden="true"></span>
            <template v-else>{{ order.status === 20 ? '保存收银单号' : '确认录单，开始制作' }}</template>
          </button>
          <button v-if="order.status === 20" type="button" class="btn btn-ghost w-full mt-2" :disabled="busy" @click="editingPos = false">取消更正</button>
        </div>

        <!-- 制作中：展示收银单号，更正或完成 -->
        <div v-else-if="order.status === 20" class="px-6 pb-6 pt-1">
          <p class="eyebrow">收银单号</p>
          <p class="mt-1 font-num text-[44px] font-bold leading-none tabular-nums overflow-wrap-anywhere">{{ order.posOrderNo }}</p>
          <div class="flex gap-2.5 mt-5">
            <button type="button" class="btn btn-outline h-13 px-5 text-[15px]" :disabled="busy" @click="editingPos = true">
              <AppIcon name="edit" weight="light" class="text-[16px]" />
              更正单号
            </button>
            <button type="button" class="btn flex-1 h-13 text-[17px]" :class="armed === 'done' ? 'btn-danger' : 'btn-primary'" :disabled="busy" @click="submitDone">
              <span v-if="busy" class="size-4 border-[1.5px] border-white/30 border-t-white rounded-full animate-spin" aria-hidden="true"></span>
              <template v-else>{{ armed === 'done' ? '再点一次，确认制作完成' : '制作完成' }}</template>
            </button>
          </div>
        </div>

        <!-- 制作完成：只能撤回 -->
        <div v-else class="px-6 pb-6 pt-1">
          <p class="eyebrow">收银单号</p>
          <p class="mt-1 font-num text-[32px] font-bold leading-none tabular-nums">{{ order.posOrderNo }}</p>
          <p class="mt-2 text-[14px] text-text-sub tabular-nums">{{ order.doneTime ? `${clock(order.doneTime)} 制作完成` : '' }}</p>
          <button type="button" class="btn w-full mt-5 h-13 text-[15px]" :class="armed === 'undo' ? 'btn-danger' : 'btn-outline'" :disabled="busy" @click="submitUndo">
            <span v-if="busy" class="size-4 border-[1.5px] border-current border-t-transparent rounded-full animate-spin" aria-hidden="true"></span>
            <template v-else>
              <AppIcon v-if="armed !== 'undo'" name="undo" weight="light" class="text-[16px]" />
              {{ armed === 'undo' ? '再点一次，确认撤回' : '撤回，回到制作中' }}
            </template>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</Teleport>
</template>

<style scoped>
.scrim {
    background: theme('colors.scrim');
}

.panel {
    background: theme('colors.surface-light');
    border-radius: theme('borderRadius.sheet') theme('borderRadius.sheet') 0 0;
    box-shadow: theme('boxShadow.sheet');
    /* iPad 横屏时底部贴着 Home 指示条，留出安全区。 */
    padding-bottom: env(safe-area-inset-bottom);
}

.sheet-enter-active,
.sheet-leave-active {
    transition: opacity var(--dur-enter) var(--ease-out);
}
.sheet-enter-active .panel {
    transition: transform var(--dur-enter) var(--ease-out);
}
.sheet-leave-active .panel {
    transition: transform var(--dur-exit, 200ms) var(--ease-in, ease-in);
}
.sheet-enter-from,
.sheet-leave-to {
    opacity: 0;
}
.sheet-enter-from .panel,
.sheet-leave-to .panel {
    transform: translateY(48px);
}

/* 收银单号输入框：大字号圆体数字，收银员隔着柜台也能核对。 */
.pos-input {
    width: 100%;
    height: 64px;
    padding: 0 20px;
    border: 1.5px solid theme('colors.line-strong');
    border-radius: theme('borderRadius.tile');
    background: theme('colors.background-light');
    font-family: theme('fontFamily.num');
    font-size: 30px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    letter-spacing: 0.02em;
    color: theme('colors.text-main');
    text-align: center;
    outline: none;
}
.pos-input:focus {
    border-color: theme('colors.primary');
    box-shadow: 0 0 0 4px rgba(27, 94, 71, 0.12);
}
.pos-input.is-empty {
    font-size: 18px;
    font-weight: 400;
}
.pos-input.is-empty::placeholder {
    color: theme('colors.text-sub');
}

/* 屏幕数字键盘：收银单号绝大多数是纯数字，不用调出系统键盘。 */
.keypad {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
}
.key {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 56px;
    border-radius: theme('borderRadius.tile');
    background: theme('colors.cream');
    font-family: theme('fontFamily.num');
    font-size: 24px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    color: theme('colors.text-main');
}
.key:active {
    background: theme('colors.cream-pressed');
}

@media (prefers-reduced-motion: reduce) {
    .sheet-enter-active,
    .sheet-leave-active,
    .sheet-enter-active .panel,
    .sheet-leave-active .panel {
        transition: none;
    }
}
</style>
