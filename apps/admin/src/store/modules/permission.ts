import { defineStore } from 'pinia'
import { store } from '@/store'
import { generateRoute } from '@/utils/routerHelper'
import { CACHE_KEY, useCache } from '@/hooks/web/useCache'
const { wsCache } = useCache()
export const usePermissionStore = defineStore('permission', {
  state: () => ({ routers: [] as AppRouteRecordRaw[], addRouters: [] as AppRouteRecordRaw[] }),
  getters: { getRouters: state => state.routers, getAddRouters: state => state.addRouters },
  actions: { async generateRoutes() { this.routers = generateRoute(wsCache.get(CACHE_KEY.ROLE_ROUTERS) || []); this.addRouters = this.routers } }
})
export const usePermissionStoreWithOut = () => usePermissionStore(store)
