<template>
  <div>
    <header style="background: #fff; border-bottom: 1px solid #e5e7eb">
      <div class="page row" style="padding: 12px 16px; justify-content: space-between">
        <router-link to="/" style="font-weight: 700; color: #1f2329">业主委员会</router-link>
        <nav class="row">
          <router-link to="/units">我的房屋</router-link>
          <router-link to="/resolutions">决议</router-link>
          <router-link to="/polls">投票/调查</router-link>
          <router-link to="/reports">财务报表</router-link>
          <router-link to="/tasks">待办</router-link>
          <router-link to="/me">个人中心</router-link>
          <el-button size="small" @click="logout">退出</el-button>
        </nav>
      </div>
    </header>
    <router-view />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

async function logout() {
  await auth.logout()
  router.replace('/login')
}
</script>
