import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './index.css'
import { setUnauthorizedHandler } from '@shared/api-client'

// Route an expired/invalid token to this app's own login view rather than a
// hardcoded root path (see the Barista entry for why the shared default was
// wrong for apps that are not served from '/').
setUnauthorizedHandler(() => {
  void router.replace('/login');
});

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
