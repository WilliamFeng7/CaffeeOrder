import type { RouteRecordRaw } from 'vue-router'
export const Layout = () => import('@/layout/Layout.vue')
const pages = import.meta.glob('../views/**/*.vue')
export const generateRoute = (menus: AppCustomRouteRecordRaw[]): AppRouteRecordRaw[] => menus.map(menu => {
  const route: AppRouteRecordRaw = {
    path: menu.path,
    name: menu.componentName || `Menu${menu.id}`,
    meta: { title: menu.name, hidden: !menu.visible, icon: menu.icon, noCache: !menu.keepAlive }
  }
  if (menu.children?.length) {
    route.component = Layout
    route.children = generateRoute(menu.children)
  } else {
    route.component = pages[`../views/${menu.component}.vue`] as RouteRecordRaw['component']
  }
  return route
})
export const flatMultiLevelRoutes = (routes: AppRouteRecordRaw[]) => routes

export const getRawRoute = (route: any) => route
