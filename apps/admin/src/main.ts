import '@/plugins/unocss'
import '@/plugins/svgIcon'
import 'element-plus/dist/index.css'
import '@/styles/index.scss'
import { createApp } from 'vue'
import { setupElementPlus } from '@/plugins/elementPlus'
import { setupI18n } from '@/plugins/vueI18n'
import { setupStore } from '@/store'
import { setupGlobCom } from '@/components'
import { setupRouter } from '@/router'
import { setupAuth, setupMountedFocus } from '@/directives'
import App from './App.vue'
import './permission'

// Remove legacy “remember password” values produced by older admin builds.
// Passwords must never be persisted in browser storage.
try {
  localStorage.removeItem('loginForm')
  sessionStorage.removeItem('loginForm')
} catch {
  // Storage can be unavailable in hardened browser contexts.
}

const start = async () => {
  const app = createApp(App)
  setupStore(app)
  await setupI18n(app)
  setupGlobCom(app)
  setupElementPlus(app)
  setupAuth(app)
  setupMountedFocus(app)
  setupRouter(app)
  app.mount('#app')
}
start()
