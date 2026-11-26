<template>
  <div class="shell">
    <aside class="side">
      <router-link to="/" class="side-brand">
        <BrandMark :size="28" />
        <span class="side-brand-name brand-wordmark">{{ BRAND_NAME }}</span>
      </router-link>
      <SideNav :menu="menu" :badges="{ pendingReview: housing.pendingReviewCount }" />
    </aside>
    <div class="shell-main">
      <header class="topbar">
        <div class="topbar-inner row">
          <router-link to="/" class="brand brand-wordmark brand-lockup"><BrandMark :size="28" />{{ BRAND_NAME }}</router-link>
          <div class="topbar-user"><PortalUserMenu /></div>
        </div>
      </header>
      <main class="portal-main layout-main">
        <SubNavBar v-if="active.node && active.node.children" :items="active.node.children" :badges="{ pendingReview: housing.pendingReviewCount }" />
        <router-view />
      </main>
    </div>
    <BottomTabBar />
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useHousingStore } from '@/stores/housing'
import { BRAND_NAME } from '@/brand/brand'
import BrandMark from '@/brand/BrandMark.vue'
import SideNav from '@/layout/SideNav.vue'
import SubNavBar from '@/layout/SubNavBar.vue'
import { PORTAL_MENU, resolveActive, visibleMenu } from '@/layout/menus'
import PortalUserMenu from './PortalUserMenu.vue'
import BottomTabBar from './BottomTabBar.vue'

const route = useRoute()
const auth = useAuthStore()
const housing = useHousingStore()

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
</script>
