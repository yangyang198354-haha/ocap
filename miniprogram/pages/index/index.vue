<template>
  <ThemeRoot>
  <view class="home-grid">
    <view class="card hero home-hero">
      <view class="home-hero-scan" />
      <view class="home-hero-main">
        <view class="title home-greeting">你好，{{ auth.me?.profile?.nickname || '业主' }}</view>
        <view class="muted home-meta">身份：{{ identityText }}<text v-if="meError" class="link" @click="load"> 重试</text></view>
        <view v-if="auth.isGuest" class="muted home-meta" @click="go('/pages/units/index')"><text class="link">去认证</text></view>
      </view>
    </view>

    <block v-for="m in bodyModules" :key="m.key">
      <view v-if="m.key === 'housing'" class="card" @click="go('/pages/units/index')">
        <view class="title">我的房屋 · {{ unitRows.length }}</view>
        <view class="muted">共 {{ unitRows.length }} 套（点击查看明细）</view>
      </view>

      <view v-else-if="m.key === 'pendingReview'" class="card" @click="go('/pages/units/index?review=1')">
        <view class="title">待我处理 · {{ m.count }}</view>
        <view class="muted">有 {{ m.count }} 条同住人申请待审批</view>
      </view>

      <view v-else-if="m.key === 'pendingVotes'" class="card">
        <view class="title">待我表决 · {{ m.count }}</view>
        <view v-for="item in pendingVotes" :key="item.id" class="list-item"
              @click="go(`/pages/polls/detail?id=${item.id}`)">
          <text>{{ item.title }}</text>
          <text class="muted">{{ participationText(item.participation) }}</text>
        </view>
      </view>

      <view v-else-if="m.key === 'pendingTasks'" class="card home-todo">
        <view class="title">待办审批 · {{ m.count }}</view>
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

      <view v-else-if="m.key === 'finance'" class="card">
        <view class="title">财务公开</view>
        <view v-if="accountsError" class="muted">
          加载失败<text class="link" @click.stop="loadAccounts"> 重试</text>
        </view>
        <block v-else>
          <view class="label">启用账户合计</view>
          <view class="stat-value">¥{{ accountsTotal }}</view>
          <block v-if="!auth.isGuest && accounts.length">
            <view v-for="account in accounts" :key="account.id" class="list-item">
              <text>{{ account.name }}</text>
              <text class="muted">¥{{ account.balance }}</text>
            </view>
          </block>
          <view v-else-if="auth.isGuest" class="muted">明细请查看财务报表</view>
          <view v-else class="muted">暂无账户</view>
        </block>
      </view>

      <view v-else-if="m.key === 'management'" class="card">
        <view class="title">管理快捷</view>
        <view class="row">
          <button size="mini" @click="go('/pages/claims/index')">报销 / 备用金</button>
          <button size="mini" @click="go('/pages/approvals/index')">待我审批</button>
        </view>
      </view>

      <view v-else-if="m.key === 'polls'" class="card home-poll">
        <view class="title">投票与调查 · {{ openPolls ? openPolls.length : 0 }}</view>
        <view v-if="!poll" class="muted">暂无进行中的投票</view>
        <block v-else>
          <view class="home-poll-title">{{ poll.title }}</view>
          <view class="muted">
            {{ poll.kind === 'REP_VOTE' ? '业主代表投票' : '调查' }}<text v-if="poll.deadline"> · 截止 {{ poll.deadline }}</text>
          </view>
          <button class="btn" style="margin-top: 16rpx" @click="go(`/pages/polls/detail?id=${poll.id}`)">立即参与</button>
        </block>
      </view>

      <view v-else-if="m.key === 'resolutions'" class="card home-latest">
        <view class="title">公开决议 · {{ publicFeed.length }}</view>
        <view v-if="!publicFeed.length" class="muted">暂无公开决议</view>
        <view v-for="item in publicFeed" :key="`${item.source}-${item.id}`" class="list-item"
              @click="go(item.source === 'REPRESENTATIVE' ? `/pages/polls/detail?id=${item.id}` : `/pages/resolutions/detail?id=${item.id}`)">
          <text>{{ item.title }}</text>
          <text class="muted">{{ item.source === 'REPRESENTATIVE' ? '业主代表决议' : '业委会决议' }}</text>
        </view>
      </view>

      <view v-else-if="m.key === 'info'" class="card">
        <view class="title">信息公开</view>
        <view v-if="!infoPosts.length" class="muted">暂无公告</view>
        <view v-for="item in infoPosts" :key="item.id" class="list-item" @click="go(`/pages/info/detail?id=${item.id}`)">
          <text>{{ item.title }}</text>
        </view>
      </view>
    </block>
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
const pendingVotes = ref([])
const meError = ref(false)
const resolutions = ref([])
const infoPosts = ref([])
const accounts = ref([])
const accountsTotal = ref('0.00')
const accountsError = ref(false)
// null 表示未取到（无权限或失败），区块显示空态，不编造数据
const polls = ref(null)

// MOD-219 / IFC-443：与 Web 同名同序；任务类按固定优先级插入
const CONTENT_ORDER = {
  guest: ['resolutions', 'polls', 'info', 'finance'],
  resident: ['housing', 'polls', 'resolutions', 'info', 'finance'],
  owner: ['housing', 'polls', 'resolutions', 'info', 'finance'],
  representative: ['housing', 'polls', 'resolutions', 'finance', 'info'],
  committee: ['housing', 'finance', 'management', 'polls', 'resolutions', 'info']
}

const profile = computed(() => {
  if (auth.isCommittee) return 'committee'
  if (auth.isRepresentative) return 'representative'
  if (auth.hasOwnerUnit) return 'owner'
  if (auth.hasResidentUnit) return 'resident'
  return 'guest'
})

const taskModules = computed(() => {
  const list = []
  if (auth.isCommittee && (tasks.value?.length || 0) > 0) {
    list.push({ key: 'pendingTasks', count: tasks.value.length })
  }
  if (auth.isRepresentative && pendingVotes.value.length > 0) {
    list.push({ key: 'pendingVotes', count: pendingVotes.value.length })
  }
  if (auth.hasOwnerUnit && pendingReview.value > 0) {
    list.push({ key: 'pendingReview', count: pendingReview.value })
  }
  return list
})

const bodyModules = computed(() => {
  const order = CONTENT_ORDER[profile.value]
  const out = []
  for (const key of order) {
    if (key === 'housing' && !unitRows.value.length) continue
    if (key === 'management' && !auth.isCommittee) continue
    out.push({ key, count: null })
    if (key === 'housing') out.push(...taskModules.value)
  }
  const hasHousing = order.includes('housing') && unitRows.value.length > 0
  if (!hasHousing) out.unshift(...taskModules.value)
  return out
})

const publicFeed = computed(() => {
  const committeeItems = resolutions.value.map((r) => ({
    id: r.id,
    title: r.title,
    source: 'COMMITTEE',
    sortAt: r.decided_at || r.created_at || ''
  }))
  const repItems = (polls.value || [])
    .filter((p) => p.kind === 'REP_VOTE' && p.status === 'CLOSED')
    .map((p) => ({ id: p.id, title: p.title, source: 'REPRESENTATIVE', sortAt: p.deadline || p.created_at || '' }))
  return [...committeeItems, ...repItems]
    .sort((a, b) => String(b.sortAt).localeCompare(String(a.sortAt)))
    .slice(0, 5)
})

const identityText = computed(() => {
  if (auth.me) return auth.identitySummary.label // C-34 / ADR-080：单一最高身份，与 Web、管理端同口径
  return meError.value ? '加载失败，请重试' : '加载中…'
})
const unitRows = computed(() => auth.me?.identities?.units || [])
const openPolls = computed(() => (polls.value ? polls.value.filter((p) => p.status === 'OPEN') : null))
const poll = computed(() => openPolls.value?.[0] || null)

const participationText = (state) => ({ VOTED: '已投票', NOT_VOTED: '未投票', UNKNOWN: '状态待确认' }[state] || '状态待确认')

function go(url) {
  uni.navigateTo({ url })
}

async function loadAccounts() {
  try {
    const data = await api.accounts({ status: 'ENABLED', recent: 0 })
    accounts.value = data?.accounts || []
    accountsTotal.value = data?.total_balance ?? '0.00'
    accountsError.value = false
  } catch (e) {
    accounts.value = []
    accountsTotal.value = '0.00'
    accountsError.value = true
  }
}

// IFC-439：只对前 3 条 OPEN REP_VOTE 取详情判断参与状态，失败降级 UNKNOWN
async function loadRepVotes(list) {
  if (!auth.isRepresentative) return
  const candidates = list.filter((p) => p.status === 'OPEN' && p.kind === 'REP_VOTE').slice(0, 3)
  const settled = await Promise.allSettled(candidates.map((p) => api.poll(p.id)))
  pendingVotes.value = settled
    .map((r, i) => {
      const p = candidates[i]
      if (r.status !== 'fulfilled') {
        return { id: p.id, title: p.title, participation: 'UNKNOWN' }
      }
      const detail = r.value || {}
      if (detail.can_respond === false) return null
      return { id: p.id, title: detail.title || p.title, participation: detail.my_response ? 'VOTED' : 'NOT_VOTED' }
    })
    .filter(Boolean)
}

async function load() {
  loadAccounts()
  try {
    await auth.fetchMe()
    meError.value = false // 未登录由 http 统一跳转；其余失败显示"加载失败，请重试"，不显示"游客"
  } catch (e) {
    meError.value = true
  }
  // 产权业主：待审批同住人申请数量（失败静默）；同住人不请求
  pendingReview.value = 0
  if (auth.hasOwnerUnit) {
    try {
      pendingReview.value = Number((await api.housing())?.pending_review_count) || 0
    } catch (e) {
      pendingReview.value = 0
    }
  }
  // 审批待办仅业委会成员可见（与接口权限一致）；非委员不发起请求
  tasks.value = null
  if (auth.isCommittee) {
    try {
      await taskPaging.reset()
      tasks.value = taskPaging.items.value
    } catch (e) {
      tasks.value = null
    }
  }
  const [resolutionResult, pollResult, infoResult] = await Promise.allSettled([
    api.resolutions('public', { page_size: 5 }),
    api.polls(),
    api.infoPosts({ page_size: 3 })
  ])
  resolutions.value = resolutionResult.status === 'fulfilled'
    ? (resolutionResult.value.results || resolutionResult.value || []).slice(0, 5)
    : []
  polls.value = pollResult.status === 'fulfilled'
    ? (pollResult.value.results || pollResult.value || [])
    : null
  infoPosts.value = infoResult.status === 'fulfilled'
    ? (infoResult.value.results || infoResult.value || []).slice(0, 3)
    : []
  await loadRepVotes(polls.value || [])
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
