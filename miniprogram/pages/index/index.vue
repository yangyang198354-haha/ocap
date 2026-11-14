<template>
  <ThemeRoot>
  <view class="home-grid">
    <view class="card hero home-hero">
      <view class="home-hero-scan" />
      <view class="home-hero-main">
        <view class="title home-greeting">你好，{{ auth.me?.profile?.nickname || '业主' }}</view>
        <view class="muted home-meta">身份：{{ identityText }}</view>
      </view>
      <view class="home-metrics">
        <text class="chip">{{ countText(tasks) }} 项审批待办</text>
        <text class="chip">{{ countText(openPolls) }} 项进行中的投票</text>
      </view>
    </view>

    <view class="card home-todo">
      <view class="title">待办</view>
      <view v-if="!tasks || !tasks.length" class="muted">暂无审批待办</view>
      <view v-for="task in tasks || []" :key="task.instance_id" class="list-item">
        <text>{{ task.subject_title || task.scope }}</text>
        <view class="row" style="margin-top: 8rpx">
          <button size="mini" @click="decide(task, 'APPROVE')">同意</button>
          <button size="mini" @click="decide(task, 'REJECT')">拒绝</button>
        </view>
      </view>
    </view>

    <view class="home-stats">
      <view v-for="(s, i) in stats" :key="s.label" class="card home-stat" :class="i % 2 ? 'is-even' : 'is-odd'">
        <view class="label">{{ s.label }}</view>
        <view class="stat-value">{{ s.value }}</view>
      </view>
    </view>

    <view class="card">
      <view class="title">认证房屋</view>
      <view class="muted">共 {{ auth.me ? unitRows.length : '—' }} 套</view>
      <view v-if="!auth.me" class="muted">加载中…</view>
      <view v-else-if="!unitRows.length" class="muted">暂无已认证房屋</view>
      <view v-for="unit in unitRows" :key="unit.unit_id" class="list-item">
        <text>{{ unit.specific_part }}</text>
        <view class="muted" style="margin-top: 8rpx">
          {{ unit.unit_type_label || '未登记' }} · {{ unit.area_display || '未登记' }} · {{ unit.role_label || '产权业主' }}
        </view>
      </view>
    </view>

    <view class="home-quick">
      <view v-for="(q, i) in quick" :key="q.label" class="home-q" @click="q.open()">
        <text class="home-q-key">{{ String(i + 1).padStart(2, '0') }}</text>
        <text class="home-q-label">{{ q.label }}</text>
      </view>
    </view>

    <view class="card home-poll">
      <view class="title">进行中的投票</view>
      <view v-if="!poll" class="muted">暂无进行中的投票</view>
      <template v-else>
        <view class="home-poll-title">{{ poll.title }}</view>
        <view class="muted">截止 {{ poll.deadline }}</view>
        <button class="btn" style="margin-top: 16rpx" @click="go(`/pages/polls/detail?id=${poll.id}`)">立即参与</button>
      </template>
    </view>

    <view class="card home-latest">
      <view class="title">最新决议</view>
      <view v-if="!resolutions.length" class="muted">暂无公开决议</view>
      <view v-for="item in resolutions" :key="item.id" class="list-item" @click="go(`/pages/resolutions/detail?id=${item.id}`)">
        <text>{{ item.title }}</text>
        <text class="muted" style="margin-left: 12rpx">{{ item.status }}</text>
      </view>
    </view>
  </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '@/utils/api'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const tasks = ref(null)
const resolutions = ref([])
// null 表示未取到（无权限或失败），区块显示空态，不编造数据
const polls = ref(null)

const countText = (list) => (list ? list.length : '—')
const identityText = computed(() => {
  if (auth.me) return (auth.me.identities?.labels || []).join('、') || '游客'
  return '加载中…'
})
const unitRows = computed(() => auth.me?.identities?.units || [])
const openPolls = computed(() => (polls.value ? polls.value.filter((p) => p.status === 'OPEN') : null))
const poll = computed(() => openPolls.value?.[0] || null)
const stats = computed(() => [
  { label: '认证房屋', value: auth.me ? unitRows.value.length : '—' },
  { label: '审批待办', value: countText(tasks.value) },
  { label: '进行中投票', value: countText(openPolls.value) },
  { label: '近期公开决议', value: resolutions.value.length }
])
const quick = [
  { label: '我的房屋', open: () => go('/pages/units/index') },
  { label: '决议', open: () => tab('/pages/resolutions/index') },
  { label: '投票', open: () => tab('/pages/polls/index') },
  { label: '报销', open: () => go('/pages/claims/index') },
  { label: '手机号', open: () => go('/pages/phone/index') },
  { label: '信息公开', open: () => go('/pages/info/index') },
  { label: '我的', open: () => tab('/pages/me/index') }
]

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
    tasks.value = null
  }
  try {
    const data = await api.resolutions('public')
    resolutions.value = (data.results || data || []).slice(0, 5)
  } catch (e) {
    resolutions.value = []
  }
  try {
    const data = await api.polls()
    polls.value = data.results || data || []
  } catch (e) {
    polls.value = null
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
