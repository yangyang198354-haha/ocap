<template>
  <div>
    <header style="background: #111827; color: #fff">
      <div class="page row" style="padding: 12px 16px; justify-content: space-between">
        <strong>业主委员会 · 管理后台</strong>
        <nav class="row">
          <router-link style="color: #d1d5db" to="/admin/registry">业主清册</router-link>
          <router-link style="color: #d1d5db" to="/admin/appeals">申诉</router-link>
          <router-link style="color: #d1d5db" to="/admin/memberships">房屋关系</router-link>
          <router-link style="color: #d1d5db" to="/admin/seats">业委会席位</router-link>
          <router-link style="color: #d1d5db" to="/admin/flows">审批流程</router-link>
          <router-link style="color: #d1d5db" to="/admin/finance">财务</router-link>
          <router-link style="color: #d1d5db" to="/admin/users">账号</router-link>
          <router-link style="color: #d1d5db" to="/admin/audit">审计/配置</router-link>
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
