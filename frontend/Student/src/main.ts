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

// 创建 Vue 应用实例
const app = createApp(App)

app.use(createPinia())
app.use(router)

// 挂载应用到页面根元素 (#app)
app.mount('#app')
