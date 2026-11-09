<template>
  <div>
    <header class="admin-bar">
      <div class="page row topbar-inner">
        <strong>业主委员会 · 管理后台</strong>
        <nav class="row topnav admin-nav">
          <router-link to="/admin/registry">业主清册</router-link>
          <router-link to="/admin/appeals">申诉</router-link>
          <router-link to="/admin/memberships">房屋关系</router-link>
          <router-link to="/admin/seats">业委会席位</router-link>
          <router-link to="/admin/flows">审批流程</router-link>
          <router-link to="/admin/finance">财务</router-link>
          <router-link to="/admin/users">账号</router-link>
          <router-link to="/admin/audit">审计/配置</router-link>
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

const router = useRouter()

function logout() {
  setToken('', true)
  router.replace('/admin/login')
}
</script>
