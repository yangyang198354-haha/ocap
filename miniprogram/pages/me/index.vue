<template>
  <ThemeRoot>
  <view>
    <view class="card">
      <view class="title">界面风格</view>
      <view class="row">
        <view
          v-for="item in theme.list"
          :key="item.key"
          class="theme-option"
          :class="{ 'is-selected': theme.current === item.key }"
          :data-theme-key="item.key"
          @click="pickTheme(item.key)"
        >
          <view class="theme-swatch"><view v-for="(c, i) in item.swatch" :key="i" :style="{ background: c }" /></view>
          <text class="theme-name">{{ item.name }}</text>
          <text v-if="theme.current === item.key" class="muted">已选</text>
        </view>
      </view>
    </view>
    <view class="card">
      <view class="title">{{ auth.me?.profile?.nickname || '业主' }}</view>
      <view class="muted">身份：{{ auth.me ? ((auth.me.identities?.labels || []).join('、') || '游客') : '加载中…' }}</view>
      <view class="muted">手机号：{{ auth.me?.profile?.phone || '未绑定' }}</view>
    </view>
    <view class="card">
      <view class="title">财务报表</view>
      <view v-if="!reports.length" class="muted">暂无已生成报表</view>
      <view v-for="item in reports" :key="item.id" class="list-item">
        <text>{{ label(item) }}</text>
        <text class="muted" style="margin-left: 12rpx">收入 ¥{{ item.total_income }} · 支出 ¥{{ item.total_expense }}</text>
      </view>
    </view>
    <view class="card">
      <button @click="go('/pages/units/index')">我的房屋</button>
      <button style="margin-top: 16rpx" @click="go('/pages/claims/index')">报销 / 备用金</button>
      <button style="margin-top: 16rpx" @click="go('/pages/phone/index')">{{ auth.me?.profile?.phone ? '更换手机号' : '绑定手机号' }}</button>
      <button style="margin-top: 16rpx" @click="go('/pages/profile-setup/index')">修改头像昵称</button>
      <button style="margin-top: 16rpx" @click="logout">退出登录</button>
    </view>
  </view>
  </ThemeRoot>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '@/utils/api'
import { useAuthStore } from '@/store/auth'
import { useThemeStore } from '@/store/theme'
import ThemeRoot from '@/components/ThemeRoot.vue'

const auth = useAuthStore()
const theme = useThemeStore()

// 点选即时生效；保存失败回滚并提示（AC-077-04）
async function pickTheme(key) {
  if (key === theme.current) return
  try {
    await theme.select(key)
  } catch (e) {
    uni.showToast({ title: '保存失败', icon: 'none' })
  }
}
const reports = ref([])

const label = (r) => (r.period_type === 'YEAR' ? `${r.year} 年度` : `${r.year} 年第 ${r.quarter} 季度`)

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
