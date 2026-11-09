<template>
  <div>
    <header class="topbar">
      <div class="page row topbar-inner">
        <router-link to="/" class="brand">业主委员会</router-link>
        <nav class="row topnav" aria-label="顶部导航">
          <router-link v-for="item in navItems" :key="item.to" :to="item.to" :class="{ 'is-active': isActive(item.to) }">{{ item.label }}</router-link>
          <el-button size="small" class="top-logout" @click="logout">退出</el-button>
        </nav>
      </div>
    </header>
    <main class="portal-main">
      <router-view />
    </main>
    <BottomTabBar />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import BottomTabBar from './BottomTabBar.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

// 导航项按身份显示，需要先取 /me
onMounted(() => {
  if (!auth.me) auth.fetchMe().catch(() => null)
})

const navItems = computed(() => [
  { label: '我的房屋', to: '/units' },
  { label: '决议', to: '/resolutions' },
  { label: '投票/调查', to: '/polls' },
  { label: '报销/备用金', to: '/claims' },
  ...(auth.isCommittee ? [{ label: '收入表', to: '/income' }] : []),
  { label: '财务报表', to: '/reports' },
  { label: '待办', to: '/tasks' },
  { label: '个人中心', to: '/me' }
])

// 当前页高亮（REQ-FUNC-080）：路径前缀匹配，所以 /resolutions/:id 仍高亮"决议"
const isActive = (to) => route.path === to || route.path.startsWith(`${to}/`)

async function logout() {
  await auth.logout()
  router.replace('/login')
}
</script>
