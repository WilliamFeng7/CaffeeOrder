<script setup lang="ts">
import { useUserStore } from '@/store/modules/user'
import { usePermissionStore } from '@/store/modules/permission'
import { resetRouter } from '@/router'
const user = useUserStore()
const permission = usePermissionStore()
const route = useRoute()
const router = useRouter()
const mobileMenu = ref(false)
const logout = async () => { await user.loginOut(); resetRouter(); await router.replace('/login') }
watch(() => route.path, () => { mobileMenu.value = false })
</script>

<template>
  <div class="admin-shell">
    <aside class="sidebar" :class="{ 'is-open': mobileMenu }" aria-label="管理端导航">
      <a class="brand" href="/" aria-label="OTIA Café 管理端首页">
        <span class="brand-mark"><Icon icon="ep:coffee" :size="23" /></span>
        <span class="brand-copy">OTIA Café<small>管理后台</small></span>
      </a>
      <div class="sidebar-nav">
        <ElMenu :default-active="route.path" router :default-openeds="['/cafe', '/system']" @select="mobileMenu = false">
          <template v-for="entry in permission.getRouters" :key="entry.path">
            <ElSubMenu v-if="!entry.meta?.hidden && entry.children?.length" :index="entry.path">
              <template #title><Icon :icon="String(entry.meta?.icon || 'ep:menu')" /><span>{{ entry.meta?.title }}</span></template>
              <ElMenuItem v-for="child in entry.children" :key="child.path" :index="`${entry.path}/${child.path}`">{{ child.meta?.title }}</ElMenuItem>
            </ElSubMenu>
          </template>
        </ElMenu>
      </div>
      <div class="sidebar-note">
        <span>OTIA Café</span>
        <small>北京外国语大学附属杭州橄榄树学校</small>
      </div>
    </aside>
    <button v-if="mobileMenu" class="nav-scrim" aria-label="关闭导航" @click="mobileMenu = false"></button>

    <div class="workspace">
      <header class="topbar">
        <ElButton class="nav-toggle" aria-label="打开导航" @click="mobileMenu = !mobileMenu"><Icon icon="ep:expand" /></ElButton>
        <div class="topbar-title"><span>OTIA Café</span><strong>{{ route.meta.title || '管理端' }}</strong></div>
        <div class="account">
          <span class="account-name">{{ user.getUser.nickname }}</span>
          <span class="account-divider" aria-hidden="true"></span>
          <ElButton text @click="router.push('/user/profile')"><Icon icon="ep:user" />个人信息</ElButton>
          <ElButton text @click="logout"><Icon icon="ep:switch-button" />退出登录</ElButton>
        </div>
      </header>
      <main id="main-content" class="main-content"><RouterView /></main>
    </div>
  </div>
</template>

<style scoped>
.admin-shell { min-height: 100vh; display: flex; }
.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 30;
  display: flex;
  flex-direction: column;
  width: var(--otia-sidebar-width);
  flex-shrink: 0;
  color: var(--otia-sidebar-text);
  background: var(--otia-sidebar-bg);
  border-right: 1px solid var(--otia-border);
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 78px;
  padding: 18px;
  color: var(--otia-text);
  border-bottom: 1px solid var(--otia-border);
}
.brand-mark {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  color: #fff;
  background: var(--otia-accent);
  border-radius: 9px;
}
.brand-copy { color: var(--otia-text); font-size: 19px; font-weight: 650; letter-spacing: -.02em; line-height: 1.2; }
.brand-copy small { display: block; margin-top: 4px; color: var(--otia-sidebar-muted); font-size: 11px; font-weight: 450; letter-spacing: .08em; }
.sidebar-nav { padding: 12px 10px; }
.sidebar :deep(.el-menu) { border-right: 0; background: transparent; }
.sidebar :deep(.el-menu-item),
.sidebar :deep(.el-sub-menu__title) {
  position: relative;
  height: 42px;
  margin: 2px 0;
  color: var(--otia-sidebar-text);
  border-radius: 7px;
  line-height: 42px;
  transition: color .18s ease, background-color .18s ease;
}
.sidebar :deep(.el-sub-menu__title) { color: var(--otia-sidebar-muted); font-size: 13px; font-weight: 600; }
.sidebar :deep(.el-menu-item) { padding-left: 40px !important; font-size: 14px; }
.sidebar :deep(.el-menu-item:hover),
.sidebar :deep(.el-sub-menu__title:hover) { color: var(--otia-text); background: var(--otia-sidebar-hover); }
.sidebar :deep(.el-menu-item.is-active) {
  color: var(--otia-sidebar-active-text);
  background: var(--otia-sidebar-active);
  font-weight: 600;
}
.sidebar :deep(.el-menu-item.is-active::before) {
  position: absolute;
  top: 10px;
  bottom: 10px;
  left: 0;
  width: 3px;
  content: '';
  background: var(--otia-accent);
  border-radius: 0 3px 3px 0;
}
.sidebar :deep(.el-sub-menu.is-active > .el-sub-menu__title) { color: var(--otia-sidebar-active-text); }
.sidebar :deep(.el-sub-menu .el-menu) { background: transparent; }
.sidebar :deep(.el-sub-menu__title .iconify) { margin-right: 10px; }
.sidebar-note { margin: auto 18px 18px; padding-top: 16px; color: var(--otia-sidebar-muted); border-top: 1px solid var(--otia-border); font-size: 12px; line-height: 1.65; }
.sidebar-note span { display: block; margin-bottom: 3px; color: var(--otia-sidebar-text); font-weight: 600; }
.sidebar-note small { display: block; color: var(--otia-sidebar-muted); font-size: 11px; line-height: 1.65; }
.workspace { min-width: 0; flex: 1; margin-left: var(--otia-sidebar-width); }
.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 64px;
  padding: 0 28px;
  background: rgb(255 255 255 / 94%);
  border-bottom: 1px solid var(--otia-border);
  backdrop-filter: blur(10px);
}
.topbar-title { display: flex; align-items: baseline; gap: 10px; }
.topbar-title > span { color: var(--otia-muted); font-size: 12px; }
.topbar-title strong { color: var(--otia-text); font-size: 15px; font-weight: 620; }
.account { margin-left: auto; display: flex; align-items: center; gap: 10px; font-size: 13px; }
.account-name { color: var(--otia-text-secondary); font-weight: 550; }
.account-divider { width: 1px; height: 18px; margin: 0 4px; background: var(--otia-border); }
.account :deep(.el-button) { color: var(--otia-muted); }
.account :deep(.el-button:hover) { color: var(--otia-accent); background: var(--otia-accent-soft); }
.main-content { max-width: 1500px; margin: auto; padding: 28px 32px 40px; }
.nav-toggle, .nav-scrim { display: none; }

@media (max-width: 900px) {
  .sidebar { transform: translateX(-100%); transition: transform .2s ease; }
  .sidebar.is-open { transform: translateX(0); }
  .workspace { margin-left: 0; }
  .nav-toggle { display: inline-flex; }
  .nav-scrim { display: block; position: fixed; inset: 0; z-index: 29; border: 0; background: rgb(23 62 50 / 38%); }
  .topbar { min-height: 64px; padding: 10px 14px; gap: 8px; }
  .topbar-title > span, .account-name, .account-divider { display: none; }
  .account { gap: 0; }
  .main-content { padding: 24px 14px 36px; }
}
</style>
