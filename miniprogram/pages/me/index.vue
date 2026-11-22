<!-- MOD-180 / IFC-399：小程序“我的”页；个人设置/系统设置分组（ADR-169、REQ-FUNC-313） -->
<template>
  <ThemeRoot>
  <view>
    <view class="card">
      <view class="title">{{ auth.me?.profile?.nickname || '业主' }}</view>
      <view class="profile-tags">
        <text v-if="realName" class="real-name">实名：{{ realName }}</text>
        <view v-if="realName" class="tag is-success">✓ 已实名认证</view>
        <view class="tag">身份：{{ auth.me ? auth.identitySummary.label : '加载中…' }}</view>
      </view>
      <view v-if="!housingUnits.length" class="muted">暂无已认证房屋</view>
      <view v-for="u in housingUnits" :key="u.unit_id" class="muted">{{ u.specific_part }}（{{ u.role_label }}）</view>
      <view class="muted">手机号：{{ auth.me?.profile?.phone || '未绑定' }}</view>
    </view>

    <view v-for="group in MP_USER_GROUPS" :key="group.key" class="card">
      <view class="title">{{ group.label }}</view>
      <view class="settings-list">
        <view v-for="item in group.items" :key="item.key" class="settings-item" @click="onMenu(item)">
          <text>{{ item.label }}</text>
          <text class="muted" aria-hidden="true">›</text>
        </view>
      </view>

      <view v-if="group.key === 'system'" id="theme-options" class="theme-options">
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
    </view>

    <view class="card">
      <view class="title">财务报表</view>
      <view v-if="!reports.length" class="muted">暂无已生成报表</view>
      <view v-for="item in reports" :key="item.id" class="list-item" @click="openReport(item)">
        <text>{{ label(item) }}</text>
        <text class="muted" style="margin-left: 12rpx">收入 ¥{{ item.total_income }} · 支出 ¥{{ item.total_expense }}</text>
      </view>
      <button v-if="hasMore" style="margin-top: 16rpx" @click="loadMore">加载更多</button>
      <view v-else-if="reports.length" class="muted">没有更多了，共 {{ total }} 条</view>
    </view>

    <view class="card">
      <button @click="go('/pages/units/index')">我的房屋</button>
      <button v-if="auth.isCommittee" style="margin-top: 16rpx" @click="go('/pages/claims/index')">报销 / 备用金</button>
      <button style="margin-top: 16rpx" @click="logout">退出登录</button>
    </view>
  </view>
  </ThemeRoot>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '@/utils/api'
import { usePaging } from '@/utils/paging'
import { useAuthStore } from '@/store/auth'
import { useThemeStore } from '@/store/theme'
import { MP_USER_GROUPS } from '@/utils/menu'
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
const housingUnits = ref([])
const realName = ref('')
const { items: reports, total, hasMore, loadMore, reset } = usePaging({
  fetch: (params) => api.reports(params)
})

const label = (r) => (r.period_type === 'YEAR' ? `${r.year} 年度` : `${r.year} 年第 ${r.quarter} 季度`)

function go(url) {
  uni.navigateTo({ url })
}

function onMenu(item) {
  if (item.action === 'theme') {
    uni.pageScrollTo?.({ selector: '#theme-options' })
    return
  }
  if (item.url) go(item.url)
}

function openReport(item) {
  uni.navigateTo({ url: `/pages/reports/detail?id=${item.id}` })
}

async function load() {
  try {
    await auth.fetchMe()
  } catch (e) {
    /* 未登录由 http 统一跳转 */
  }
  try {
    housingUnits.value = (await api.housing()).units || []
  } catch (e) {
    housingUnits.value = []
  }
  try {
    // IFC-377：复用本人 profile，实名仅在本人开启且存在时返回（C-84）
    realName.value = (await api.profile()).real_name || ''
  } catch (e) {
    // AC-276-03：实名数据失败时静默降级，不影响昵称与身份
    realName.value = ''
  }
  try {
    await reset()
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

<style scoped>
.profile-tags { display: flex; flex-wrap: wrap; align-items: center; gap: 8rpx 12rpx; margin: 8rpx 0; }
.real-name { color: var(--text); font-weight: 650; font-size: 26rpx; }
.settings-list { display: flex; flex-direction: column; }
.settings-item {
  display: flex; align-items: center; justify-content: space-between; min-height: 88rpx;
  border-bottom: 1px solid var(--line); font-size: 28rpx;
}
.settings-item:last-child { border-bottom: 0; }
.theme-options { margin-top: 16rpx; }
</style>
