<template>
  <div class="admin-shell">
    <header class="admin-bar">
      <div class="page row topbar-inner">
        <span class="brand">业主委员会 · 管理后台</span>
        <nav class="row topnav admin-nav">
          <router-link v-for="item in navItems" :key="item.to" :to="item.to" active-class="is-active">
            {{ item.label }}
          </router-link>
          <AdminThemeSwitcher />
          <el-button size="small" @click="logout">退出</el-button>
        </nav>
      </div>
    </header>
    <router-view />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { setToken } from '@/shared/http'
import AdminThemeSwitcher from '@/theme/AdminThemeSwitcher.vue'
import { useAdminThemeStore } from '@/theme/adminStore'

const router = useRouter()

const navItems = [
  { label: '业主清册', to: '/admin/registry' },
  { label: '申诉', to: '/admin/appeals' },
  { label: '房屋关系', to: '/admin/memberships' },
  { label: '业委会席位', to: '/admin/seats' },
  { label: '审批流程', to: '/admin/flows' },
  { label: '财务', to: '/admin/finance' },
  { label: '账号', to: '/admin/users' },
  { label: '信息公开', to: '/admin/content/posts' },
  { label: '素材库', to: '/admin/content/media' },
  { label: 'AI 服务', to: '/admin/content/services' },
  { label: '平台账户', to: '/admin/content/platforms' },
  { label: '内容参数', to: '/admin/content/settings' },
  { label: '审计/配置', to: '/admin/audit' }
]

function logout() {
  setToken('', true)
  useAdminThemeStore().resetSession()
  router.replace('/admin/login')
}
</script>
