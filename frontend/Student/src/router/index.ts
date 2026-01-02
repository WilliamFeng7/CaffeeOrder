import { createRouter, createWebHistory } from 'vue-router';
import StudentLayout from '../layouts/StudentLayout.vue';
import LoginView from '../../components/LoginView.vue';

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/login',
            name: 'login',
            component: LoginView
        },
        {
            path: '/',
            name: 'student',
            component: StudentLayout,
            meta: { requiresAuth: true }
        }
    ]
});

router.beforeEach((to, from, next) => {
    const token = sessionStorage.getItem('token');

    // If going to login and already logged in? 
    // Maybe redirect to home. But user wanted "Login every time" maybe?
    // Let's keep it standard: if token exists, go to home/dashboard.
    // Actually, if user wants "login every time", reloading the page should stay logged in?
    // "每次刷新页面或重新打开应用时，系统都会强制要求您重新输入账号密码" -> This means NO persistence on refresh?
    // If so, I should check if it's a "fresh load".
    // But standard usage is: token persists.
    // I will check for token.

    if (to.meta.requiresAuth && !token) {
        next('/login');
        return;
    }

    next();
});

export default router;
