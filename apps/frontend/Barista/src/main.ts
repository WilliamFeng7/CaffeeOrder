
/**
 * main.ts
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './index.css'
import App from './App.vue'
import router from './router'
import { setUnauthorizedHandler } from '@shared/api-client'

// An expired/invalid token must land on *this* app's login screen. The shared
// client used to hard-redirect to '/login', which is wrong for the KDS: it is
// built into a sub-path in production, so staff were bounced to the Student
// app's login page instead of their own.
setUnauthorizedHandler(() => {
  void router.replace('/login');
});

// iOS Safari only applies :active styles once a touch listener exists, so
// without this the press feedback never shows on the iPad.
document.addEventListener('touchstart', () => {}, { passive: true });

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
