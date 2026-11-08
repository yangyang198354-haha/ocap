<template>
  <div class="page">
    <div class="card">
      <h2 class="title">你好，{{ auth.me?.profile?.nickname || '业主' }}</h2>
      <p class="muted">当前身份：{{ auth.identities.join('、') || '游客' }}</p>
      <p class="muted">手机号：{{ auth.me?.profile?.phone || '未绑定' }}</p>
    </div>
    <div class="card">
      <h3 class="title">快捷入口</h3>
      <div class="row">
        <el-button @click="$router.push('/units')">认证我的房屋</el-button>
        <el-button @click="$router.push('/resolutions')">查看决议</el-button>
        <el-button @click="$router.push('/polls')">参与投票</el-button>
        <el-button @click="$router.push('/reports')">财务报表</el-button>
        <el-button @click="$router.push('/claims')">报销 / 备用金</el-button>
        <el-button v-if="auth.isCommittee" @click="$router.push('/income')">收入表</el-button>
      </div>
    </div>
    <div class="card">
      <h3 class="title">最新公开决议</h3>
      <el-empty v-if="!resolutions.length" description="暂无公开决议" />
      <div v-for="item in resolutions" :key="item.id" style="padding: 8px 0; border-bottom: 1px solid #f0f1f3">
        <router-link :to="`/resolutions/${item.id}`">{{ item.title }}</router-link>
        <span class="muted" style="margin-left: 8px">{{ item.status }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { resolutionApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const resolutions = ref([])

onMounted(async () => {
  try {
    await auth.fetchMe()
  } catch (e) {
    /* 401 由 http 拦截器处理 */
  }
  try {
    const data = await resolutionApi.list('public', { page_size: 5 })
    resolutions.value = data.results || data || []
  } catch (e) {
    resolutions.value = []
  }
})
</script>
