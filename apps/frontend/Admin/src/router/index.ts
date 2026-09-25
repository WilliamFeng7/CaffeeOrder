import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import { auth } from '@shared/auth'

// Lazy load views
const DashboardView = () => import('../views/DashboardView.vue')
const UserManager = () => import('../views/UserManager.vue')
const ProductManager = () => import('../views/ProductManager.vue')
const OrderManager = () => import('../views/OrderManager.vue')

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/login',
            name: 'login',
            component: LoginView
        },
        {
            path: '/',
            component: AdminLayout,
            meta: { requiresAuth: true },
            children: [
                {
                    path: '',
                    name: 'dashboard',
                    component: DashboardView
                },
                {
                    path: 'users',
                    name: 'users',
                    component: UserManager
                },
                {
                    path: 'products',
                    name: 'products',
                    component: ProductManager
                },
                {
                    path: 'orders',
                    name: 'orders',
                    component: OrderManager
                },
                {
                    path: 'finance',
                    name: 'finance',
                    component: () => import('../views/FinanceView.vue')
                },

                {
                    path: 'settings',
                    name: 'settings',
                    component: () => import('../views/SettingsView.vue')
                }
            ]
        }
    ]
})

router.beforeEach((to, _from, next) => {
    // Existence of a token is not enough - it must be an admin session, or the
    // console would render for a student/barista and then 403 on every request.
    const authorized = auth.hasRole('admin');

    if (to.meta.requiresAuth && !authorized) {
        if (auth.isLoggedIn()) {
            auth.clearToken();
        }
        next('/login')
    } else {
        next()
    }
})

export default router
