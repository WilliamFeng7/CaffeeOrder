import { createApp } from 'vue';
import { createPinia } from 'pinia';
import './index.css';
import App from './App.vue';

// iOS Safari 只有在页面上存在 touch 监听后才应用 :active 样式，
// 没有这个，iPad 上的按压反馈永远不会显示。
document.addEventListener('touchstart', () => {}, { passive: true });

createApp(App).use(createPinia()).mount('#app');
