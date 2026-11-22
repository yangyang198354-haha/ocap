<!-- MOD-122 / MOD-178：窄屏“我的”总览页；入口收敛为“个人资料/系统设置”两项（IFC-397） -->
<template>
  <div class="page">
    <div class="card">
      <h3 class="title">我的</h3>
      <nav class="me-overview" aria-label="个人中心">
        <router-link v-for="item in PORTAL_USER_MENU" :key="item.key" :to="item.to" class="me-overview-item">
          <span>{{ item.label }}</span>
          <span class="muted" aria-hidden="true">›</span>
        </router-link>
      </nav>
      <button type="button" class="me-overview-item me-logout" @click="logoutNow">退出登录</button>
    </div>
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useHousingStore } from '@/stores/housing'
import { PORTAL_USER_MENU } from '@/layout/menus'
import { useIsWide } from '@/layout/useBreakpoint'

const router = useRouter()
const auth = useAuthStore()
const isWide = useIsWide()

// 窗口由窄变宽时进入个人资料页（AC-220-05）
watch(isWide, (wide) => {
  if (wide) router.replace('/me/profile')
})

async function logoutNow() {
  await auth.logout()
  useHousingStore().$reset()
  router.replace('/login')
}
</script>

<style scoped>
.me-overview { margin-top: 8px; }
.me-logout { margin-top: 16px; }
</style>
