/**
 * data.ts
 * 
 * 静态配置与初始数据 (Static Config & Initial Data).
 * 
 * 主要功能 (Core Features):
 * 1. 国际化字典 (TRANSLATIONS): 包含全站 UI 的中英对照文本。
 * 2. 选项翻译 (OPTION_TRANSLATIONS): 特殊选项(如糖度)的详细翻译。
 * 3. 静态分类 (CATEGORIES): 菜单类别的定义 (图标、中英名称)。
 * 4. 响应式商品列表 (PRODUCTS): 初始为空数组，后续由 API 填充。
 */

import { reactive } from 'vue';
import { Category, Product } from './types';

/**
 * 全局多语言翻译字典 (Global Translation Dictionary)
 * 键名为 English Key，值为包含 en/cn 的对象。
 * 用于整个应用程序的静态文本展示。
 */
export const TRANSLATIONS = {
  en: {
    // 底部导航栏
    navHome: "Home",
    navOrder: "Order",
    navPickup: "Pickup",
    navProfile: "Me",

    // 首页 (HomeView)
    goodMorning: "Good Morning,",
    goodAfternoon: "Good Afternoon,",
    goodEvening: "Good Evening,",
    homeSubtitle: "What are you having today?",
    open: "Open",
    closed: "Closed",
    trendingNow: "Trending Now",
    seeAll: "See All",
    bestSeller: "Best Seller",

    // 通用 (General UI)
    downtownCafe: "OTIA Café",
    search: "Search",
    total: "Total",
    checkout: "Checkout",
    addToCart: "Add to Cart",
    sweetness: "Sweetness",
    reviewOrder: "Review Order",
    items: "Items",
    subtotal: "Subtotal",
    pay: "Pay",
    securePayment: "Secure Payment",
    pickupNum: "Pickup Number",
    orderHistory: "Order History",
    noOrders: "No orders found",
    completed: "Completed",
    hot: "Hot",
    iced: "Iced",
    profile: "Profile",
    memberLevel: "Gold Member",
    balance: "Balance",
    signOut: "Sign Out",
    language: "Language",
    viewDetailedHistory: "View detailed history",

    // 取餐页 (PickupView)
    currentOrders: "Current Orders",
    pastOrders: "Past Orders",
    queued: "In Queue",
    preparing: "Preparing",
    ready: "Ready",
    orderReady: "Your order is ready — pickup number",
    placing: "Placing order…",
  },
  cn: {
    // 导航栏
    navHome: "首页",
    navOrder: "点餐",
    navPickup: "取餐",
    navProfile: "我的",

    // 首页
    goodMorning: "早上好，",
    goodAfternoon: "下午好，",
    goodEvening: "晚上好，",
    homeSubtitle: "今天想喝点什么？",
    open: "营业中",
    closed: "休息中",
    trendingNow: "热门推荐",
    seeAll: "全部",
    bestSeller: "热销",

    // 通用
    downtownCafe: "OTIA 咖啡店",
    search: "搜索",
    total: "总计",
    checkout: "去结算",
    addToCart: "加入购物车",
    sweetness: "甜度",
    reviewOrder: "确认订单",
    items: "商品",
    subtotal: "小计",
    pay: "支付",
    securePayment: "安全支付",
    pickupNum: "取餐号",
    orderHistory: "历史订单",
    noOrders: "暂无订单",
    completed: "已完成",
    hot: "热",
    iced: "冰",
    profile: "个人中心",
    memberLevel: "金牌会员",
    balance: "余额",
    signOut: "退出登录",
    language: "语言",
    viewDetailedHistory: "查看详细历史记录",

    // 取餐页
    currentOrders: "当前订单",
    pastOrders: "历史订单",
    queued: "排队中",
    preparing: "制作中",
    ready: "请取餐",
    orderReady: "您的饮品做好了，取餐号",
    placing: "正在下单…",
  }
};

/**
 * 选项翻译映射 (Option Translations)
 * 用于规格选择时的中英文展示。
 */
export const OPTION_TRANSLATIONS = {
  sugar: {
    '0%': { en: '0%', cn: '无糖' },
    '25%': { en: '25%', cn: '微糖' },
    '50%': { en: '50%', cn: '半糖' },
    'Regular': { en: 'Regular', cn: '标准' },
    '120%': { en: '120%', cn: '多糖' },
  }
};

/**
 * 商品分类数据列表 (Categories)
 * 定义了菜单的类别结构。
 */
export const CATEGORIES: Category[] = [
  { id: 'top', name: 'Top Picks', nameCN: '店长推荐', icon: 'star' },
  { id: 'seasonal', name: 'Seasonal', nameCN: '当季新品', icon: 'leaf' },
  { id: 'coffee', name: 'Coffee', nameCN: '现磨咖啡', icon: 'coffee' },
  { id: 'fruit', name: 'Fruit Tea', nameCN: '鲜果茶', icon: 'cup-straw' },
  { id: 'bakery', name: 'Bakery', nameCN: '烘焙轻食', icon: 'bread' },
  { id: 'all', name: 'All', nameCN: '全部', icon: 'grid' },
];

/**
 * 全局商品数据列表 (Global Products List)
 * 这是一个响应式数组 (Reactive Array)。
 * 初始为空，应用程序启动后通过 api.getMenu() 从后端获取数据填充。
 * 其他组件 (如 HomeView, MenuView) 均引用此对象。
 */


export const PRODUCTS: Product[] = reactive([]);
