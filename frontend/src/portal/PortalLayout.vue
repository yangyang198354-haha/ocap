<template>
  <div class="shell portal-shell">
    <aside class="side">
      <router-link to="/" class="side-brand portal-side-brand">
        <BrandMark :size="28" />
        <BrandWordmark class="side-brand-name brand-wordmark" />
      </router-link>
      <SideNav :menu="menu" :badges="{ pendingReview: housing.pendingReviewCount }" />
    </aside>
    <div class="shell-main">
      <header class="topbar">
        <div class="topbar-inner row">
          <button type="button" class="portal-menu-btn" aria-label="打开主导航"
                  aria-controls="portal-nav-drawer" :aria-expanded="drawerOpen" @click="drawerOpen = true">
            <UiIcon name="menu" />
          </button>
          <router-link to="/" class="brand brand-wordmark brand-lockup">
            <BrandMark :size="28" />
            <BrandWordmark />
          </router-link>
          <div class="topbar-user"><PortalUserMenu /></div>
        </div>
      </header>
      <main class="portal-main layout-main" :class="{ 'business-page': route.path !== '/' }">
        <SubNavBar v-if="active.node && active.node.children" :items="active.node.children" :badges="{ pendingReview: housing.pendingReviewCount }" />
        <router-view />
      </main>
    </div>
    <BottomTabBar />
    <el-drawer v-model="drawerOpen" direction="ltr" size="min(300px, 84vw)" append-to-body
               class="portal-nav-drawer" title="主导航">
      <SideNav id="portal-nav-drawer" id-prefix="portal-drawer-sub" :menu="menu"
               :badges="{ pendingReview: housing.pendingReviewCount }" />
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useHousingStore } from '@/stores/housing'
import BrandMark from '@/brand/BrandMark.vue'
import BrandWordmark from '@/brand/BrandWordmark.vue'
import SideNav from '@/layout/SideNav.vue'
import SubNavBar from '@/layout/SubNavBar.vue'
import { PORTAL_MENU, resolveActive, visibleMenu } from '@/layout/menus'
import { useIsWide } from '@/layout/useBreakpoint'
import { useThemeStore } from '@/theme/store'
import PortalUserMenu from './PortalUserMenu.vue'
import BottomTabBar from './BottomTabBar.vue'
import UiIcon from './UiIcon.vue'

const route = useRoute()
const auth = useAuthStore()
const housing = useHousingStore()
const themeStore = useThemeStore()
const drawerOpen = ref(false)
const isWide = useIsWide('(min-width: 881px)')

// 菜单按身份显示，需要先取 /me；未加载时先显示全员项（AC-211-04）
const menu = computed(() => visibleMenu(PORTAL_MENU, { isCommittee: auth.isCommittee }))
const active = computed(() => resolveActive(PORTAL_MENU, route.path))

onMounted(async () => {
  // DEF-002：登录后 auth.me 只是登录响应的简要对象（无 identities），也要补取 /me，否则角标按"无房屋"刷成 0
  if (!auth.me || !auth.me.identities) await auth.fetchMe().catch(() => null)
  housing.refreshPendingBadge()
})

// 进入"我的房屋"各页时再静默刷新一次角标
watch(() => route.path, (path) => {
  if (path === '/units' || path.startsWith('/units/')) housing.refreshPendingBadge()
})

watch([() => route.fullPath, () => themeStore.current, isWide], () => { drawerOpen.value = false })
</script>

<style scoped>
.portal-menu-btn {
  display: none;
  place-items: center;
  flex: none;
  width: var(--hit-min);
  height: var(--hit-min);
  padding: 0;
  border: 1px solid var(--line);
  border-radius: var(--radius-btn);
  background: var(--surface);
  color: var(--accent-text);
  cursor: pointer;
}
</style>
