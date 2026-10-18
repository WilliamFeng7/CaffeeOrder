import type { IconName } from '@/icons';

export type Language = 'en' | 'cn';

export interface ProductOption {
  id: number;
  name: string;
  nameEn: string;
  /** 加价，单位为元；请求后端时只传选项 ID。 */
  priceDelta: number;
  isDefault: boolean;
}

export interface ProductOptionGroup {
  id: number;
  name: string;
  nameEn: string;
  options: ProductOption[];
}

export interface SelectedOption {
  id?: number;
  groupName?: string;
  groupNameEn?: string;
  name: string;
  nameEn: string;
  priceDelta?: number;
}

export interface Product {
  id: string;
  name: string;
  nameCN: string;
  description: string;
  descriptionCN: string;
  /** 基础价格，单位为元。 */
  price: number;
  image: string;
  thumb: string;
  category: string;
  tags?: string[];
  isPopular?: boolean;
  soldOut: boolean;
  optionGroups: ProductOptionGroup[];
}

export interface CartItem extends Product {
  cartId: string;
  quantity: number;
  /** 包含规格加价后的单价。 */
  price: number;
  optionIds: number[];
  selectedOptions: SelectedOption[];
}

export interface OrderItem {
  id: string;
  name: string;
  nameCN: string;
  price: number;
  image: string;
  thumb: string;
  quantity: number;
  selectedOptions: SelectedOption[];
}

export type OrderStatus = 'active' | 'completed';
export type OrderStage = 'created' | 'processing' | 'ready';

export interface Order {
  id: string;
  orderNo: string;
  /** API 层把毫秒时间戳转成页面日期可解析的 ISO 字符串。 */
  date: string;
  items: OrderItem[];
  total: number;
  posOrderNo: string | null;
  aheadCount: number | null;
  isCompleted: boolean;
  status: OrderStatus;
  stage: OrderStage;
}

export type TabState = 'home' | 'order' | 'pickup' | 'profile';
export type SheetCloseReason = 'dismiss' | 'added' | 'dragged';
export type ViewState = TabState | 'checkout' | 'order-detail';

export interface Category {
  id: string;
  name: string;
  nameCN: string;
  icon: IconName;
}

export interface UserProfile {
  name: string;
  studentNo: string;
  /** 学生卡余额，单位为元。 */
  balance: number;
}

export interface BusinessHours {
  start: string;
  end: string;
}

export interface ShopStatus {
  open: boolean;
  banner: string;
  businessHours: BusinessHours[];
}

export interface MenuData {
  products: Product[];
  categories: Category[];
}

export interface AuthSession {
  accessToken: string;
  expiresTime: number;
  studentNo: string;
  name: string;
}

export interface ProductSelection {
  optionIds: number[];
  selectedOptions: SelectedOption[];
  price: number;
}
