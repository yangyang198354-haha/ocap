<template>
  <div class="admin-shell shell">
    <aside class="side admin-side">
      <router-link to="/admin" class="side-brand">
        <BrandMark :size="28" />
        <span class="side-brand-name brand-wordmark">{{ ADMIN_BRAND_TITLE }}</span>
      </router-link>
      <SideNav :menu="ADMIN_MENU" aria-label="管理端导航" />
    </aside>
    <div class="shell-main">
      <header class="admin-bar">
        <div class="admin-bar-inner">
          <button type="button" class="admin-menu-btn" aria-label="打开导航" @click="drawerOpen = true">
            <svg width="18" height="14" viewBox="0 0 18 14" aria-hidden="true">
              <path d="M1 1h16M1 7h16M1 13h16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
            </svg>
          </button>
          <AdminUserMenu />
        </div>
      </header>
      <main class="layout-main">
        <router-view />
      </main>
    </div>
    <el-drawer v-model="drawerOpen" direction="ltr" :with-header="false" size="min(280px, 85vw)" class="admin-drawer">
      <router-link to="/admin" class="side-brand">
        <BrandMark :size="28" />
        <span class="side-brand-name brand-wordmark">{{ ADMIN_BRAND_TITLE }}</span>
      </router-link>
      <SideNav :menu="ADMIN_MENU" aria-label="管理端导航（抽屉）" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ADMIN_BRAND_TITLE } from '@/brand/brand'
import BrandMark from '@/brand/BrandMark.vue'
import SideNav from '@/layout/SideNav.vue'
import { ADMIN_MENU } from '@/layout/menus'
import { useIsWide } from '@/layout/useBreakpoint'
import AdminUserMenu from './AdminUserMenu.vue'

const route = useRoute()
const drawerOpen = ref(false)
const isWide = useIsWide()

// 点击二级项后自动关闭抽屉（AC-231-03）；窗口变宽时关闭（AC-231-04）
watch(() => route.fullPath, () => { drawerOpen.value = false })
watch(isWide, (wide) => { if (wide) drawerOpen.value = false })
</script>
