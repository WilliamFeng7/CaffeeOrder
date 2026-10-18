import * as dd from 'dingtalk-jsapi';
import { createYudaoClient, type YudaoTokens } from '@shared/yudao-client';
import type { IconName } from '@/icons';
import type {
  AuthSession,
  CartItem,
  Category,
  MenuData,
  Order,
  OrderItem,
  Product,
  SelectedOption,
  ShopStatus,
  UserProfile,
} from '../types';
import { photoUrl, thumbUrl } from '../utils/photo';

interface BackendOption {
  id: number;
  name: string;
  nameEn: string | null;
  priceDelta: number;
  isDefault: boolean;
}

interface BackendGroup {
  id: number;
  name: string;
  nameEn: string | null;
  options: BackendOption[];
}

interface BackendMenuItem {
  id: number;
  name: string;
  nameEn: string | null;
  description: string | null;
  descriptionEn: string | null;
  price: number;
  categoryCode: string;
  imageUrl: string | null;
  recommended: boolean;
  soldOut: boolean;
  optionGroups: BackendGroup[];
}

interface BackendMenu {
  categories: { id: number; code: string; name: string; nameEn: string | null }[];
  items: BackendMenuItem[];
}

interface BackendOrderItem {
  itemId: number;
  name: string;
  nameEn: string | null;
  imageUrl: string | null;
  unitPrice: number;
  quantity: number;
  optionsText: string | null;
  options: SelectedOption[];
}

interface BackendOrder {
  id: number;
  orderNo: string;
  status: number;
  posOrderNo: string | null;
  aheadCount: number | null;
  totalPrice: number;
  createTime: number;
  items: BackendOrderItem[];
}

export interface StudentAuthConfig {
  corpId: string;
  passwordLoginEnabled: boolean;
}

const CATEGORY_ICONS: Record<string, IconName> = {
  seasonal: 'leaf',
  coffee: 'coffee',
  fruit: 'cup-straw',
  bakery: 'bread',
};

let unauthorizedHandler: () => void = () => undefined;
export const setUnauthorizedHandler = (handler: () => void) => {
  unauthorizedHandler = handler;
};

const client = createYudaoClient({
  baseUrl: '/app-api/cafe',
  tokenKey: 'otia.student.accessToken',
  storage: 'sessionStorage',
  onUnauthorized: () => unauthorizedHandler(),
  reauthenticate: async () => {
    try {
      return await loginWithDingTalk();
    } catch {
      return null;
    }
  },
});

const saveSession = (session: AuthSession): YudaoTokens => {
  client.setTokens(session);
  return session;
};

export const isDingTalk = () => dd.env.platform !== 'notInDingTalk';

async function getAuthConfig(): Promise<StudentAuthConfig> {
  return client.get<StudentAuthConfig>('/auth/dingtalk-config', { auth: false });
}

async function loginWithDingTalk(corpId?: string): Promise<AuthSession> {
  if (!isDingTalk()) throw new Error('请在钉钉中打开 OTIA Café');
  const resolvedCorpId = corpId || (await getAuthConfig()).corpId;
  if (!resolvedCorpId) throw new Error('钉钉登录尚未配置，请使用账号密码登录');

  let authCode: string;
  if (typeof dd.getAuthCode === 'function') {
    const result = await dd.getAuthCode({ corpId: resolvedCorpId });
    authCode = result.authCode;
  } else {
    const result = await dd.runtime.permission.requestAuthCode({ corpId: resolvedCorpId });
    authCode = result.code;
  }
  const session = await client.post<AuthSession>('/auth/dingtalk-login', { authCode }, { auth: false });
  saveSession(session);
  return session;
}

const toIso = (timestamp: number) => new Date(timestamp).toISOString();
const toYuan = (cents: number) => cents / 100;

const mapOrderItem = (item: BackendOrderItem): OrderItem => ({
  id: String(item.itemId),
  name: item.nameEn || item.name,
  nameCN: item.name,
  price: toYuan(item.unitPrice),
  image: photoUrl(item.imageUrl),
  thumb: thumbUrl(item.imageUrl),
  quantity: item.quantity,
  selectedOptions: item.options ?? [],
});

const mapOrder = (order: BackendOrder): Order => {
  const stage = order.status === 30 ? 'ready' : order.status === 20 ? 'processing' : 'created';
  const completed = order.status === 30;
  return {
    id: String(order.id),
    orderNo: order.orderNo,
    date: toIso(order.createTime),
    items: order.items.map(mapOrderItem),
    total: toYuan(order.totalPrice),
    posOrderNo: order.posOrderNo,
    aheadCount: order.aheadCount,
    isCompleted: completed,
    status: completed ? 'completed' : 'active',
    stage,
  };
};

export const api = {
  hasToken: () => client.getToken() !== null,
  isDingTalk,
  getAuthConfig,
  loginWithDingTalk,

  async loginWithPassword(studentNo: string, password: string): Promise<AuthSession> {
    const session = await client.post<AuthSession>(
      '/auth/password-login',
      { studentNo, password },
      { auth: false },
    );
    saveSession(session);
    return session;
  },

  async getMenu(): Promise<MenuData> {
    const menu = await client.get<BackendMenu>('/menu', { auth: false });
    const categories: Category[] = [
      { id: 'top', name: 'Top picks', nameCN: '店长推荐', icon: 'star' },
      ...menu.categories.map((category) => ({
        id: category.code,
        name: category.nameEn || category.name,
        nameCN: category.name,
        icon: CATEGORY_ICONS[category.code] ?? 'grid',
      })),
      { id: 'all', name: 'All', nameCN: '全部', icon: 'grid' },
    ];
    const products: Product[] = menu.items.map((item) => ({
      id: String(item.id),
      name: item.nameEn || item.name,
      nameCN: item.name,
      description: item.descriptionEn || '',
      descriptionCN: item.description || '',
      price: toYuan(item.price),
      category: item.categoryCode,
      image: photoUrl(item.imageUrl),
      thumb: thumbUrl(item.imageUrl),
      tags: item.recommended ? ['Best Seller'] : [],
      isPopular: item.recommended,
      soldOut: item.soldOut,
      optionGroups: item.optionGroups.map((group) => ({
        id: group.id,
        name: group.name,
        nameEn: group.nameEn || group.name,
        options: group.options.map((option) => ({
          id: option.id,
          name: option.name,
          nameEn: option.nameEn || option.name,
          priceDelta: toYuan(option.priceDelta),
          isDefault: option.isDefault,
        })),
      })),
    }));
    return { products, categories };
  },

  async getProfile(): Promise<UserProfile> {
    const profile = await client.get<{ studentNo: string; name: string; balance: number }>('/student/me');
    return { ...profile, balance: toYuan(profile.balance) };
  },

  async createOrder(items: CartItem[], idempotencyKey: string): Promise<Order> {
    const order = await client.post<BackendOrder>('/order/create', {
      items: items.map((item) => ({
        itemId: Number(item.id),
        quantity: item.quantity,
        optionIds: item.optionIds,
      })),
    }, { headers: { 'Idempotency-Key': idempotencyKey } });
    return mapOrder(order);
  },

  async getMyOrders(): Promise<Order[]> {
    const page = await client.get<{ list: BackendOrder[]; total: number }>('/order/page', {
      params: { pageNo: 1, pageSize: 100 },
    });
    return page.list.map(mapOrder);
  },

  async getQueue(): Promise<number> {
    const result = await client.get<{ waitingCount: number }>('/order/queue');
    return result.waitingCount;
  },

  getShopStatus: () => client.get<ShopStatus>('/shop/status', { auth: false }),
};
