/**
 * 咖啡师端的接口（见 docs/architecture.md 的 API map）。
 * 登录状态放在 localStorage：收银台的 iPad 刷新页面、重开 Safari 后不用重新登录。
 */
import { ref } from 'vue';
import { createYudaoClient, type YudaoTokens } from '@shared/yudao-client';

export const STATUS_WAITING = 10;
export const STATUS_MAKING = 20;
export const STATUS_DONE = 30;

export interface BaristaOrderItem {
    name: string;
    quantity: number;
    /** 规格文字，比如"冰 / 半糖"；没有规格时为空。 */
    optionsText: string | null;
}

export interface BaristaOrder {
    id: number;
    orderNo: string;
    status: number;
    /** 收银单号，回填前为 null。 */
    posOrderNo: string | null;
    studentName: string;
    /** 毫秒时间戳 */
    createTime: number;
    enteredTime: number | null;
    doneTime: number | null;
    totalPrice: number;
    cupCount: number;
    items: BaristaOrderItem[];
}

export interface Board {
    /** 待录单，下单早的在前 */
    waiting: BaristaOrder[];
    /** 制作中，下单早的在前 */
    making: BaristaOrder[];
    /** 当天最近制作完成的 10 单，新的在前 */
    recentDone: BaristaOrder[];
}

const USERNAME_KEY = 'otia.barista.username';

/** 是否已登录。令牌失效（刷新也换不到新令牌）时变为 false，页面回到登录。 */
export const signedIn = ref(false);
/** 回到登录页时给咖啡师看的原因。 */
export const signInNotice = ref('');

const client = createYudaoClient({
    baseUrl: '/admin-api',
    tokenKey: 'otia.barista.accessToken',
    storage: 'localStorage',
    refresh: { path: '/system/auth/refresh-token', tokenKey: 'otia.barista.refreshToken' },
    onUnauthorized: () => {
        signedIn.value = false;
        signInNotice.value = '登录已过期，请重新登录';
    },
});

signedIn.value = client.getToken() !== null;

export function lastUsername(): string {
    try {
        return localStorage.getItem(USERNAME_KEY) ?? '';
    } catch {
        return '';
    }
}

/** 登录并确认这个账号能打开看板；没有权限时不保留登录状态，把后端的提示抛给调用方。 */
export async function login(username: string, password: string): Promise<void> {
    const tokens = await client.post<YudaoTokens>('/system/auth/login', { username, password }, { auth: false });
    client.setTokens(tokens);
    try {
        await fetchBoard();
    } catch (error) {
        client.clearTokens();
        throw error;
    }
    try {
        localStorage.setItem(USERNAME_KEY, username);
    } catch {
        // 记不住账号名也不影响使用。
    }
    signInNotice.value = '';
    signedIn.value = true;
}

export async function logout(): Promise<void> {
    try {
        await client.post('/system/auth/logout', undefined, { timeout: 5000 });
    } catch {
        // 连不上后端也照样退出，本机不再保留令牌。
    }
    client.clearTokens();
    signInNotice.value = '';
    signedIn.value = false;
}

export const fetchBoard = (signal?: AbortSignal) => client.get<Board>('/cafe/barista/order/board', { signal });

/** 回填收银单号：待录单变为制作中；已经是制作中时是更正收银单号。 */
export const enterOrder = (id: number, posOrderNo: string) => client.put<boolean>('/cafe/barista/order/enter', { id, posOrderNo });

export const finishOrder = (id: number) => client.put<boolean>('/cafe/barista/order/done', { id });

export const undoFinishOrder = (id: number) => client.put<boolean>('/cafe/barista/order/undo-done', { id });
