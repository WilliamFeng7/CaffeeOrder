/**
 * main.ts
 * 
 * 应用程序入口文件。
 * 负责初始化 Vue 应用实例，引入全局样式，并挂载到 DOM 上。
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './index.css'
import App from './App.vue'
import router from './router'
import { setUnauthorizedHandler } from '@shared/api-client'
import { demoMode } from './demo'

// Expired/invalid token -> this app's login view, via the router (so it honours
// whatever base path the app is mounted at) instead of a hardcoded root URL.
setUnauthorizedHandler(() => {
  if (demoMode.value) {
    window.location.replace(import.meta.env.BASE_URL);
    return;
  }
  void router.replace('/login');
});

// iOS Safari only applies :active styles once a touch listener exists, so
// without this the press feedback never shows on iPhone / iPad.
document.addEventListener('touchstart', () => {}, { passive: true })

// Keep the iPad kiosk gesture behaviour, while phones retain pinch zoom.
document.addEventListener('gesturestart', (e) => {
  if (window.matchMedia('(min-width: 768px) and (min-height: 501px)').matches) e.preventDefault()
})

// 创建 Vue 应用实例
const app = createApp(App)

app.use(createPinia())
app.use(router)

// 挂载应用到页面根元素 (#app)
app.mount('#app')
