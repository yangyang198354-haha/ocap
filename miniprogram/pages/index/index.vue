<template>
  <ThemeRoot>
  <view class="home-grid">
    <view class="card hero home-hero">
      <view class="home-hero-scan" />
      <view class="home-hero-main">
        <view class="title home-greeting">你好，{{ auth.me?.profile?.nickname || '业主' }}</view>
        <view class="muted home-meta">身份：{{ identityText }}<text v-if="meError" class="link" @click="load"> 重试</text></view>
        <view v-if="pendingReview > 0" class="home-meta" @click="go('/pages/units/index?review=1')">待审批同住人申请：{{ pendingReview }}</view>
      </view>
      <view class="home-metrics">
        <text class="chip">{{ countText(tasks) }} 项审批待办</text>
        <text class="chip">{{ countText(openPolls) }} 项进行中的投票</text>
      </view>
    </view>

    <view v-if="auth.isCommittee" class="card home-todo">
      <view class="title">待办</view>
      <view v-if="!tasks || !tasks.length" class="muted">暂无审批待办</view>
      <view v-for="task in tasks || []" :key="task.instance_id" class="list-item">
        <text>{{ task.subject_title || task.scope }}</text>
        <view class="row" style="margin-top: 8rpx">
          <button size="mini" @click="decide(task, 'APPROVE')">同意</button>
          <button size="mini" @click="decide(task, 'REJECT')">拒绝</button>
        </view>
      </view>
      <button v-if="taskPaging.hasMore.value" style="margin-top: 12rpx" @click="loadMoreTasks">加载更多</button>
      <view v-else-if="tasks && tasks.length" class="muted">没有更多了，共 {{ taskPaging.total.value }} 条</view>
    </view>

    <view class="home-stats">
      <view v-for="(s, i) in stats" :key="s.label" class="card home-stat" :class="i % 2 ? 'is-even' : 'is-odd'">
        <view class="label">{{ s.label }}</view>
        <view class="stat-value">{{ s.value }}</view>
      </view>
    </view>

    <view class="card" @click="go('/pages/units/index')">
      <view class="title">认证房屋</view>
      <view class="muted">共 {{ auth.me ? unitRows.length : '—' }} 套（点击查看明细）</view>
      <view v-if="!auth.me" class="muted">{{ meError ? '加载失败，请重试' : '加载中…' }}</view>
      <view v-else-if="!unitRows.length" class="muted">暂无已认证房屋，去认证产权</view>
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
import { usePaging } from '@/utils/paging'

const auth = useAuthStore()
// 待办：仅业委会成员（REQ-FUNC-157）；分页“加载更多”（REQ-FUNC-152）
const taskPaging = usePaging({ fetch: (params) => api.tasks(params) })
const tasks = ref(null)
const pendingReview = ref(0)
const meError = ref(false)
const resolutions = ref([])
// null 表示未取到（无权限或失败），区块显示空态，不编造数据
const polls = ref(null)

const countText = (list) => (list ? list.length : '—')
const identityText = computed(() => {
  if (auth.me) return auth.identitySummary.label // C-34 / ADR-080：单一最高身份，与 Web、管理端同口径
  return meError.value ? '加载失败，请重试' : '加载中…'
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
const quick = computed(() => [
  { label: '我的房屋', open: () => go('/pages/units/index') },
  { label: '决议', open: () => tab('/pages/resolutions/index') },
  { label: '投票', open: () => tab('/pages/polls/index') },
  ...(auth.isCommittee ? [{ label: '报销', open: () => go('/pages/claims/index') }] : []),
  { label: '手机号', open: () => go('/pages/phone/index') },
  { label: '信息公开', open: () => go('/pages/info/index') },
  { label: '我的', open: () => tab('/pages/me/index') }
])

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
    meError.value = false
  } catch (e) {
    meError.value = true // 未登录由 http 统一跳转；其余失败显示"加载失败，请重试"，不显示"游客"
  }
  // 产权业主：待审批同住人申请数量（失败静默，不影响首页其他区块）
  pendingReview.value = 0
  if ((auth.me?.identities?.units || []).some((u) => u.role === 'HEAD' || u.role === 'OWNER')) {
    try {
      pendingReview.value = Number((await api.housing())?.pending_review_count) || 0
    } catch (e) {
      pendingReview.value = 0
    }
  }
  // 审批待办仅业委会成员可见（与接口权限一致）；失败按空处理
  tasks.value = null
  if (auth.isCommittee) {
    try {
      await taskPaging.reset()
      tasks.value = taskPaging.items.value
    } catch (e) {
      tasks.value = null
    }
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

async function loadMoreTasks() {
  try {
    await taskPaging.loadMore()
    tasks.value = taskPaging.items.value
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
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
