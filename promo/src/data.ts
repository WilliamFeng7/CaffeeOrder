import latte from './assets/menu/latte.jpg';
import coconutLatte from './assets/menu/coconut-latte.jpg';
import macchiato from './assets/menu/macchiato.jpg';
import cheesecake from './assets/menu/cheesecake.jpg';
import croissant from './assets/menu/croissant.jpg';
import matcha from './assets/menu/matcha.jpg';
import coldbrew from './assets/menu/coldbrew.jpg';
import fruitTea from './assets/menu/fruit-tea.jpg';
import cappuccino from './assets/menu/cappuccino.jpg';
import espresso from './assets/menu/espresso.jpg';
import flatwhite from './assets/menu/flatwhite.jpg';

const IMAGES: Record<string, string> = {
  'latte.jpg': latte,
  'coconut-latte.jpg': coconutLatte,
  'macchiato.jpg': macchiato,
  'cheesecake.jpg': cheesecake,
  'croissant.jpg': croissant,
  'matcha.jpg': matcha,
  'coldbrew.jpg': coldbrew,
  'fruit-tea.jpg': fruitTea,
  'cappuccino.jpg': cappuccino,
  'espresso.jpg': espresso,
  'flatwhite.jpg': flatwhite,
};

export interface Drink {
  id: string;
  name: string;
  en: string;
  price: number;
  img: string;
  tag?: string;
  desc: string;
}

export const IMG = (file: string) => IMAGES[file];

export const DRINKS: Record<string, Drink> = {
  latte: {
    id: 'latte',
    name: '经典拿铁',
    en: 'Caffe Latte',
    price: 15,
    img: 'latte.jpg',
    tag: '热销',
    desc: '双份浓缩与蒸汽牛奶，入口顺滑，甜感干净。',
  },
  coconut: {
    id: 'coconut',
    name: '生椰拿铁',
    en: 'Iced Coconut Latte',
    price: 18,
    img: 'coconut-latte.jpg',
    tag: '当季',
    desc: '椰乳与浓缩分层，冰饮更清爽，搅开是另一杯。',
  },
  macchiato: {
    id: 'macchiato',
    name: '焦糖玛奇朵',
    en: 'Caramel Macchiato',
    price: 19,
    img: 'macchiato.jpg',
    tag: '店长推荐',
    desc: '焦糖、香草与浓缩，甜一点的时候点它。',
  },
  cheesecake: {
    id: 'cheesecake',
    name: '巴斯克芝士蛋糕',
    en: 'Basque Cheesecake',
    price: 22,
    img: 'cheesecake.jpg',
    desc: '外层微焦，里面是半融的芝士，配热美式刚好。',
  },
  croissant: {
    id: 'croissant',
    name: '黄油可颂',
    en: 'Butter Croissant',
    price: 12,
    img: 'croissant.jpg',
    desc: '每天现烤，层层酥脆，适合来不及吃早饭的上午。',
  },
  matcha: {
    id: 'matcha',
    name: '抹茶奶绿',
    en: 'Matcha Milk Green Tea',
    price: 17,
    img: 'matcha.jpg',
    desc: '抹茶与牛奶，微苦回甘，不含咖啡因。',
  },
  coldbrew: {
    id: 'coldbrew',
    name: '冷萃咖啡',
    en: 'Cold Brew',
    price: 20,
    img: 'coldbrew.jpg',
    desc: '十二小时慢萃，冰镇后更干净，下午的清醒。',
  },
  fruitTea: {
    id: 'fruit-tea',
    name: '鲜果茶',
    en: 'Citrus Fruit Tea',
    price: 15,
    img: 'fruit-tea.jpg',
    desc: '当季水果现泡，酸酸甜甜，不喝咖啡也能点。',
  },
};

export const FEATURED = DRINKS.latte;

export const MENU_PICKS = [DRINKS.latte, DRINKS.coconut, DRINKS.macchiato, DRINKS.cheesecake];

export const HOURS = '11:40–12:30 · 15:30–17:00';

export const FEATURES = [
  {
    icon: 'chat',
    title: '钉钉免登',
    body: '打开就是你的账号。学号自动带出，不用记密码，也不用再填一次。',
    index: '01',
  },
  {
    icon: 'sliders',
    title: '规格随你',
    body: '热或冰，无糖到多糖。选项来自菜单本身，价格随选随变。',
    index: '02',
  },
  {
    icon: 'card',
    title: '学生卡直付',
    body: '结算页就显示卡里余额，点一下完成付款，不用掏手机扫码。',
    index: '03',
  },
  {
    icon: 'receipt',
    title: '收银单号',
    body: '咖啡师录单后，收银单号直接出现在取餐页，凭它到柜台取餐。',
    index: '04',
  },
  {
    icon: 'progress',
    title: '三步进度',
    body: '待录单、制作中、制作完成。每 3 秒自己刷新，不用反复问。',
    index: '05',
  },
  {
    icon: 'users',
    title: '排队一眼看到',
    body: '首页告诉你现在还有几单在做，决定要不要现在下楼。',
    index: '06',
  },
] as const;

export const STAGES = [
  {
    id: 'created',
    label: '待录单',
    short: '刚付完款',
    title: '付款完成，等咖啡师录单',
    body: '订单已经到咖啡师端。还没有收银单号，所以先显示「等待录单」。',
  },
  {
    id: 'processing',
    label: '制作中',
    short: '单号已回填',
    title: '收银单号出现，前面还有 2 单',
    body: '咖啡师把订单录进收银系统并回填单号。你现在知道要等几单。',
  },
  {
    id: 'ready',
    label: '制作完成',
    short: '可以下楼了',
    title: '做好了，凭 A012 到柜台取餐',
    body: '订单变成绿色，学生端弹出提示。不用站在柜台前猜哪杯是你的。',
  },
] as const;

export type StageId = (typeof STAGES)[number]['id'];
