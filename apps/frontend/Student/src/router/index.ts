import { createRouter, createWebHistory } from 'vue-router';
import { api } from '../api';

const StudentLayout = () => import('../layouts/StudentLayout.vue');
const LoginView = () => import('../views/LoginView.vue');
if (!window.location.pathname.endsWith('/login')) void StudentLayout();

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        { path: '/login', name: 'login', component: LoginView },
        { path: '/', name: 'student', component: StudentLayout, meta: { requiresAuth: true } }
    ]
});

router.beforeEach((to) => {
    const loggedIn = api.hasToken();
    if (to.meta.requiresAuth && !loggedIn) return '/login';
    if (to.path === '/login' && loggedIn) return '/';
    return true;
});

export default router;
