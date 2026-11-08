<template>
  <view>
    <view class="card">
      <view class="title">{{ auth.me?.user?.nickname || auth.me?.nickname || '业主' }}</view>
      <view class="muted">身份：{{ (auth.me?.identities || []).join('、') || '游客' }}</view>
      <view class="muted">手机号：{{ auth.me?.phone || '未绑定' }}</view>
    </view>
    <view class="card">
      <view class="title">财务报表</view>
      <view v-if="!reports.length" class="muted">暂无已生成报表</view>
      <view v-for="item in reports" :key="item.id" style="padding: 12rpx 0; border-bottom: 1px solid #f0f1f3">
        <text>{{ item.period }}</text>
        <text class="muted" style="margin-left: 12rpx">收入 ¥{{ item.total_income }} · 支出 ¥{{ item.total_expense }}</text>
      </view>
    </view>
    <view class="card">
      <button @click="go('/pages/units/index')">我的房屋</button>
      <button style="margin-top: 16rpx" @click="go('/pages/claims/index')">报销 / 备用金</button>
      <button style="margin-top: 16rpx" @click="logout">退出登录</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '@/utils/api'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const reports = ref([])

function go(url) {
  uni.navigateTo({ url })
}

async function load() {
  try {
    await auth.fetchMe()
  } catch (e) {
    /* 未登录由 http 统一跳转 */
  }
  try {
    const data = await api.reports()
    reports.value = (data.results || data || []).slice(0, 8)
  } catch (e) {
    reports.value = []
  }
}

function logout() {
  auth.clear()
  uni.reLaunch({ url: '/pages/login/index' })
}

onShow(load)
</script>
