/**
 * types.ts
 * 
 * 前端类型定义文件 (Frontend Type Definitions).
 * 
 * 主要功能 (Core Features):
 * 1. 数据模型定义 (Data Models): 商品 (Product), 订单 (Order), 用户 (UserProfile).
 * 2. 状态类型定义 (State Types): 视图状态 (ViewState), 订单状态 (OrderStatus).
 * 3. 辅助接口 (Helper Interfaces): 语言 (Language), 购物车项 (CartItem).
 */

// 语言类型：支持英文 ('en') 和中文 ('cn')
export type Language = 'en' | 'cn';

/**
 * 商品接口定义 (Product Interface)
 * 对应后端 MenuItem 模型，用于前端展示。
 */
export interface Product {
  // 商品唯一标识 (对应数据库 ID)
  id: string;
  // 商品英文名称
  name: string;
  // 商品中文名称
  nameCN: string;
  // 商品英文描述
  description: string;
  // 商品中文描述
  descriptionCN: string;
  // 商品基础价格 (元)
  price: number;
  // 商品图片 URL: 原图 (详情面板、首页主推) 与 640px 小图 (卡片、缩略图)，见 utils/photo.ts
  image: string;
  thumb: string;
  // 商品所属类别 ID (如: 'coffee', 'bakery')
  category: string;
  // 商品标签列表 (如: ['Best Seller', 'New'])
  tags?: string[];
  // 是否为热门推荐商品 (用于首页展示)
  isPopular?: boolean;
  // 库存数量 (Inventory Count)
  inventoryCount?: number;
}

/**
 * 购物车商品接口 (Cart Item Interface)
 * 继承自 Product，扩展了购物车特有的属性 (数量、选中规格)。
 */
export interface CartItem extends Product {
  // 购物车条目唯一标识 (用于区分同商品不同规格)
  cartId: string;
  // 购买数量
  quantity: number;
  // 选中的杯型规格
  size?: 'Small' | 'Regular' | 'Large';
  // 选中的温度规格
  temperature?: 'Hot' | 'Iced' | 'Warm';
  // 选中的糖度 (如: '0%', 'Regular', '120%')
  sugar?: string;

}

/**
 * 订单状态类型 (Order Status Enum)
 * active: 进行中 (制作中/待取餐)
 * completed: 已完成
 */
export type OrderStatus = 'active' | 'completed';

/**
 * 后端原始状态 (Backend lifecycle stage)
 * `status` 只区分进行中/已结束；取餐页要区分「排队 / 制作中 / 请取餐」就看这个。
 */
export type OrderStage = 'created' | 'processing' | 'ready' | 'completed' | 'refunded';

/**
 * 订单接口定义 (Order Interface)
 * 包含订单的基础元数据和包含的商品列表。
 */
export interface Order {
  // 订单唯一标识 (数据库主键)
  id: string;
  // 订单 UUID (用于从外部系统查询或展示)
  uuid: string;
  order_no: string;
  // 下单时间 (ISO 8601 字符串)
  date: string;
  // 订单包含的商品列表
  items: CartItem[];
  // 订单总金额
  total: number;
  // 订单类型 (默认为堂食 'dine-in')
  type: 'dine-in';
  // 取餐号 (字母+数字组合，如 A101)
  pickupNumber: string;
  // 每日自增流水号 (1, 2, 3...)
  dailyNumber: number;
  // 订单是否完成标志 (true: 历史订单, false: 当前订单)
  isCompleted: boolean;
  // 订单状态 (枚举值)
  status: OrderStatus;
  // 后端原始状态
  stage: OrderStage;
  // 获得的积分 (预留字段)
  pointsEarned?: number;
}

/**
 * 底部导航栏状态类型 (Tab State)
 * 控制 BottomNav 组件的选中状态。
 */
export type TabState = 'home' | 'order' | 'pickup' | 'profile';

/**
 * 商品面板关闭原因 (Why the product sheet closes)
 * dismiss: 点关闭或背景; added: 加入购物车后; dragged: 下拉关闭 (already off-screen).
 */
export type SheetCloseReason = 'dismiss' | 'added' | 'dragged';

/**
 * 视图状态类型 (View State)
 * 控制 App.vue 主视图的切换 (包括 Tab 页面和其他全屏页面如结算页)。
 */
export type ViewState = TabState | 'checkout' | 'order-detail';

/**
 * 商品类别接口定义 (Category Interface)
 * 用于菜单分类导航。
 */
export interface Category {
  // 类别唯一标识
  id: string;
  // 类别英文名称
  name: string;
  // 类别中文名称
  nameCN: string;
}

/**
 * 用户个人信息接口定义 (User Profile Interface)
 * 对应后端 User 模型的前端展示部分。
 */
export interface UserProfile {
  // 显示昵称
  name: string;
  // 用户 UUID
  uuid: string;
  // 手机号
  phone: string;
  // 邮箱
  email: string;
  // 头像 URL
  avatar?: string;
  // 账户余额
  balance?: number;
  // 登录用户名 (账号)
  username?: string;
}
