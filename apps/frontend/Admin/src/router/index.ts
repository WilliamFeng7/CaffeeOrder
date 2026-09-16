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
    if (to.meta.requiresAuth && !auth.isLoggedIn()) {
        next('/login')
    } else {
        next()
    }
})

export default router
