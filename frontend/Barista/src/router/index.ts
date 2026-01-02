
import { createRouter, createWebHistory } from 'vue-router'
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
router.beforeEach((to, from, next) => {
    const token = sessionStorage.getItem('coffee_access_token');
    if (to.meta.requiresAuth && !token) {
        next('/login');
    } else {
        next();
    }
})

export default router
