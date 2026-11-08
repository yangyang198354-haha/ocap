<template>
  <view>
    <view class="card">
      <view class="title">你好，{{ auth.me?.profile?.nickname || '业主' }}</view>
      <view class="muted">身份：{{ (auth.me?.identities?.labels || []).join('、') || '游客' }}</view>
    </view>
    <view class="card row">
      <button size="mini" @click="go('/pages/units/index')">我的房屋</button>
      <button size="mini" @click="go('/pages/claims/index')">报销</button>
      <button size="mini" @click="tab('/pages/me/index')">我的</button>
    </view>
    <view class="card">
      <view class="title">待办</view>
      <view v-if="!tasks.length" class="muted">暂无审批待办</view>
      <view v-for="task in tasks" :key="task.instance_id" style="border-bottom: 1px solid #f0f1f3; padding: 12rpx 0">
        <text>{{ task.subject_title || task.scope }}</text>
        <view class="row" style="margin-top: 8rpx">
          <button size="mini" @click="decide(task, 'APPROVE')">同意</button>
          <button size="mini" @click="decide(task, 'REJECT')">拒绝</button>
        </view>
      </view>
    </view>
    <view class="card">
      <view class="title">最新决议</view>
      <view v-if="!resolutions.length" class="muted">暂无公开决议</view>
      <view v-for="item in resolutions" :key="item.id" style="padding: 12rpx 0; border-bottom: 1px solid #f0f1f3" @click="go(`/pages/resolutions/detail?id=${item.id}`)">
        <text>{{ item.title }}</text>
        <text class="muted" style="margin-left: 12rpx">{{ item.status }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '@/utils/api'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const tasks = ref([])
const resolutions = ref([])

function go(url) {
  uni.navigateTo({ url })
}

// tabBar 页面必须用 switchTab
function tab(url) {
  uni.switchTab({ url })
}

async function load() {
  try {
    await auth.fetchMe()
  } catch (e) {
    /* 未登录由 http 统一跳转 */
  }
  try {
    // 审批待办仅业委会成员可见，其他身份后端返回 403，此处按空处理
    const data = await api.tasks()
    tasks.value = data.results || data || []
  } catch (e) {
    tasks.value = []
  }
  try {
    const data = await api.resolutions('public')
    resolutions.value = (data.results || data || []).slice(0, 5)
  } catch (e) {
    resolutions.value = []
  }
}

async function decide(task, action) {
  try {
    await api.decide(task.instance_id, action)
    uni.showToast({ title: '已处理', icon: 'none' })
    load()
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

onShow(load)
</script>
