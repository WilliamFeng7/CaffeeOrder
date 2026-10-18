/**
 * data.ts
 * 
 * 静态配置与初始数据 (Static Config & Initial Data).
 * 
 * 主要功能 (Core Features):
 * 1. 国际化字典 (TRANSLATIONS): 包含全站 UI 的中英对照文本。
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
    goodMorning: "Good morning,",
    goodAfternoon: "Good afternoon,",
    goodEvening: "Good evening,",
    homeSubtitle: "What are you having today?",
    open: "Open",
    closed: "Closed",
    trendingNow: "Trending now",
    fullMenu: "Full menu",
    bestSeller: "Best seller",

    // 通用 (General UI)
    downtownCafe: "OTIA Café",
    search: "Search",
    total: "Total",
    checkout: "Checkout",
    cart: "Your cart",
    cartEmpty: "Your cart is empty",
    removeItem: "Remove item",
    decrease: "Decrease quantity",
    increase: "Increase quantity",
    closeCart: "Close cart",
    addToCart: "Add to cart",
    sweetness: "Sweetness",
    reviewOrder: "Review order",
    items: "Items",
    subtotal: "Subtotal",
    orderSummary: "Order summary",
    securePayment: "Secure payment",
    pickupNum: "Receipt number",
    orderHistory: "Order history",
    noOrders: "No orders yet",
    completed: "Made",
    hot: "Hot",
    iced: "Iced",
    profile: "Profile",
    memberLevel: "Student card",
    balance: "Student card balance",
    language: "Language",
    viewDetailedHistory: "View detailed history",

    // 取餐页 (PickupView)
    currentOrders: "Current orders",
    pastOrders: "Past orders",
    queued: "Waiting for entry",
    preparing: "Preparing",
    ready: "Made",
    orderReady: "Made — show your receipt number at the counter",
    placing: "Placing order…",
    profileLoading: "Student information is still loading. Please try again shortly.",
    checkoutRecoveryError: "A previous payment attempt cannot be matched to this student. Contact café staff before ordering again.",
    paymentPending: "Payment status is being confirmed. Retrying safely checks this same order.",
    checkoutStorageError: "This browser cannot save a pending order safely. Enable browser storage and try again.",
    paymentRefunded: "The previous payment was refunded. You can place a new order.",
    waitingEntry: "Waiting for entry",
    queueNow: "Now in queue",
    ahead: (count: number) => `${count} ${count === 1 ? "order" : "orders"} ahead`,
    studentNo: "Student number",
    businessHours: "Business hours",
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
    fullMenu: "全部菜单",
    bestSeller: "热销",

    // 通用
    downtownCafe: "OTIA 咖啡店",
    search: "搜索",
    total: "总计",
    checkout: "去结算",
    cart: "购物车",
    cartEmpty: "购物车是空的",
    removeItem: "移除商品",
    decrease: "减少数量",
    increase: "增加数量",
    closeCart: "收起购物车",
    addToCart: "加入购物车",
    sweetness: "甜度",
    reviewOrder: "确认订单",
    items: "商品",
    subtotal: "小计",
    orderSummary: "订单金额",
    securePayment: "安全支付",
    pickupNum: "收银单号",
    orderHistory: "历史订单",
    noOrders: "暂无订单",
    completed: "制作完成",
    hot: "热",
    iced: "冰",
    profile: "个人中心",
    memberLevel: "学生卡",
    balance: "学生卡余额",
    language: "语言",
    viewDetailedHistory: "查看详细历史记录",

    // 取餐页
    currentOrders: "当前订单",
    pastOrders: "历史订单",
    queued: "待录单",
    preparing: "制作中",
    ready: "制作完成",
    orderReady: "制作完成，请凭收银单号到柜台取餐",
    placing: "正在下单…",
    profileLoading: "学生信息仍在加载，请稍后重试。",
    checkoutRecoveryError: "上一笔支付无法匹配到当前学号，请先联系咖啡厅工作人员再下单。",
    paymentPending: "支付结果仍在确认中；重新点击会安全查询同一笔订单。",
    checkoutStorageError: "此浏览器无法安全保存待确认订单，请启用浏览器存储后重试。",
    paymentRefunded: "上一笔扣款已确认退回，可以重新下单。",
    waitingEntry: "等待录单",
    queueNow: "现在排队",
    ahead: (count: number) => `前面还有 ${count} 单`,
    studentNo: "学号",
    businessHours: "营业时段",
  }
};

/**
 * 商品分类数据列表 (Categories)
 * 定义了菜单的类别结构。
 */
export const CATEGORIES: Category[] = reactive([
  { id: 'top', name: 'Top picks', nameCN: '店长推荐', icon: 'star' },
  { id: 'seasonal', name: 'Seasonal', nameCN: '当季新品', icon: 'leaf' },
  { id: 'coffee', name: 'Coffee', nameCN: '现磨咖啡', icon: 'coffee' },
  { id: 'fruit', name: 'Fruit tea', nameCN: '鲜果茶', icon: 'cup-straw' },
  { id: 'bakery', name: 'Bakery', nameCN: '烘焙轻食', icon: 'bread' },
  { id: 'all', name: 'All', nameCN: '全部', icon: 'grid' },
]);

/**
 * 全局商品数据列表 (Global Products List)
 * 这是一个响应式数组 (Reactive Array)。
 * 初始为空，应用程序启动后通过 api.getMenu() 从后端获取数据填充。
 * 其他组件 (如 HomeView, MenuView) 均引用此对象。
 */


export const PRODUCTS: Product[] = reactive([]);
