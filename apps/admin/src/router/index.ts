import type { App } from 'vue'
import type { RouteRecordRaw } from 'vue-router'
import { createRouter, createWebHistory } from 'vue-router'
import remainingRouter from './modules/remaining'
const router = createRouter({ history: createWebHistory(), routes: remainingRouter as RouteRecordRaw[], scrollBehavior: () => ({ top: 0 }) })
const baseNames = new Set(router.getRoutes().map(route => route.name))
export const resetRouter = () => router.getRoutes().forEach(route => { if (route.name && !baseNames.has(route.name)) router.removeRoute(route.name) })
export const setupRouter = (app: App<Element>) => app.use(router)
export default router
