import { createRouter, createWebHistory } from 'vue-router';
import { auth } from '@shared/auth';

// Lazy-loaded route components for better initial load performance
const StudentLayout = () => import('../layouts/StudentLayout.vue');
const LoginView = () => import('../views/LoginView.vue');

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

router.beforeEach((to, _from, next) => {
    // A token alone is not authorization for this app: the guard must also
    // confirm the session belongs to a student, otherwise an admin/barista
    // token stored by any of the three apps would pass here.
    const authorized = auth.hasRole('student');

    if (to.meta.requiresAuth && !authorized) {
        if (auth.isLoggedIn()) {
            // Wrong-portal session: drop it so the login form is honest.
            auth.clearToken();
        }
        next('/login');
        return;
    }

    next();
});

export default router;
