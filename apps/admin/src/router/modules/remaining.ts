import { Layout } from '@/utils/routerHelper'
const remainingRouter: AppRouteRecordRaw[] = [
  { path: '/login', name: 'Login', component: () => import('@/views/Login/index.vue'), meta: { hidden: true, title: '登录' } },
  { path: '/', name: 'Home', component: Layout, meta: { hidden: true }, children: [
    { path: '', name: 'Welcome', component: () => import('@/views/Welcome/index.vue'), meta: { hidden: true, title: '管理端' } }
  ] },
  { path: '/user', name: 'UserProfileRoot', component: Layout, meta: { hidden: true }, children: [
    { path: 'profile', name: 'UserProfile', component: () => import('@/views/Profile/index.vue'), meta: { hidden: true, title: '个人信息' } }
  ] },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/views/Error/404.vue'), meta: { hidden: true, title: '页面不存在' } }
]
export default remainingRouter
