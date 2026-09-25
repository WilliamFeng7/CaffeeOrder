
import { createRouter, createWebHistory } from 'vue-router'
import { auth } from '@shared/auth'
import KDSView from '../views/KDSView.vue'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: KDSView,
            meta: { requiresAuth: true }
        },
        {
            path: '/login',
            name: 'login',
            component: LoginView
        }
    ]
})

// Navigation Guard
router.beforeEach((to, _from, next) => {
    // Uses the shared auth helper instead of re-hardcoding the storage key, and
    // requires a staff role rather than merely "some token is present".
    const authorized = auth.hasRole('barista', 'admin');

    if (to.meta.requiresAuth && !authorized) {
        if (auth.isLoggedIn()) {
            auth.clearToken();
        }
        next('/login');
    } else {
        next();
    }
})

export default router
