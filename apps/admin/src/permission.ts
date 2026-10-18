import router, { resetRouter } from './router'
import type { RouteRecordRaw } from 'vue-router'
import { getAccessToken } from '@/utils/auth'
import { useUserStoreWithOut } from '@/store/modules/user'
import { usePermissionStoreWithOut } from '@/store/modules/permission'
import { useDictStoreWithOut } from '@/store/modules/dict'
router.beforeEach(async to => {
  if (!getAccessToken()) return to.path === '/login' ? true : { path: '/login', query: { redirect: to.fullPath } }
  if (to.path === '/login') return '/'
  const user = useUserStoreWithOut()
  if (!user.getIsSetUser) {
    await user.setUserInfoAction()
    const permissions = usePermissionStoreWithOut()
    resetRouter()
    await permissions.generateRoutes()
    permissions.getAddRouters.forEach(route => router.addRoute(route as RouteRecordRaw))
    await useDictStoreWithOut().setDictMap()
    return { path: to.path, query: to.query, hash: to.hash, replace: true }
  }
  if (to.path === '/') {
    const first = usePermissionStoreWithOut().getRouters.find(route => !route.meta?.hidden)
    if (first?.children?.length) return `${first.path}/${first.children[0].path}`
    if (first) return first.path
  }
  return true
})
router.afterEach(to => { document.title = `${to.meta.title || '管理端'} · ${import.meta.env.VITE_APP_TITLE}` })
