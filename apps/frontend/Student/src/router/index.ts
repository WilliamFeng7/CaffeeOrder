import { createRouter, createWebHistory } from 'vue-router';
import { auth } from '@shared/auth';
import { demoMode, prepareStudentSession } from '../demo';

// Lazy-loaded route components for better initial load performance
const StudentLayout = () => import('../layouts/StudentLayout.vue');
const LoginView = () => import('../views/LoginView.vue');

// The guard waits for the session handshake before the route's chunk is even
// requested; start downloading the main screen alongside it instead.
if (!window.location.pathname.endsWith('/login')) void StudentLayout();

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

router.beforeEach(async (to, _from, next) => {
    await prepareStudentSession();
    if (demoMode.value && to.path === '/login') {
        next('/');
        return;
    }
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
