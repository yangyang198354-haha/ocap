<template>
  <div class="page home">
    <div class="home-grid">
      <section class="card hero home-hero" aria-label="欢迎">
        <span class="home-hero-scan" aria-hidden="true" />
        <div class="home-hero-main">
          <div class="label">{{ todayText }}</div>
          <h2 class="title home-greeting">你好，<span class="grad-text home-caret">{{ auth.me?.profile?.nickname || '业主' }}</span></h2>
          <p class="muted home-meta">当前身份：{{ identityText }}<el-button v-if="meError" link size="small" @click="retryMe">重试</el-button></p>
          <p v-if="auth.isGuest" class="muted home-meta"><router-link to="/units/pick" class="link">去认证</router-link></p>
        </div>
      </section>

      <template v-for="m in bodyModules" :key="m.key">
        <section v-if="m.key === 'housing'" class="card home-half home-housing" aria-label="我的房屋" @click="$router.push('/units')">
          <div class="card-head">
            <h3 class="title title-flat">我的房屋 · {{ unitRows.length }}</h3>
            <router-link to="/units" class="link">房屋明细</router-link>
          </div>
          <p class="muted">共 {{ unitRows.length }} 套（点击查看明细）</p>
        </section>

        <section v-else-if="m.key === 'pendingReview'" class="card home-half" aria-label="待我处理">
          <div class="card-head">
            <h3 class="title title-flat">待我处理 · {{ m.count }}</h3>
            <router-link :to="m.to" class="link">去处理</router-link>
          </div>
          <p class="muted">有 {{ m.count }} 条同住人申请待审批</p>
        </section>

        <section v-else-if="m.key === 'pendingVotes'" class="card home-half" aria-label="待我表决">
          <div class="card-head">
            <h3 class="title title-flat">待我表决 · {{ m.count }}</h3>
            <router-link :to="m.to" class="link">全部</router-link>
          </div>
          <div v-for="item in pendingVotes" :key="item.id" class="todo-item is-link" @click="$router.push(`/polls/${item.id}`)">
            <span class="todo-icon"><UiIcon name="vote" /></span>
            <div class="todo-body">
              <b>{{ item.title }}</b>
              <div class="meta">
                <span>截止 {{ formatDateTime(item.deadline) }}</span>
                <span>{{ participationText(item.participation) }}</span>
              </div>
            </div>
          </div>
        </section>

        <section v-else-if="m.key === 'pendingTasks'" class="card home-half home-todo" aria-label="待办审批">
          <div class="card-head">
            <h3 class="title title-flat">待办审批 · {{ m.count }}</h3>
            <router-link to="/tasks" class="link">全部</router-link>
          </div>
          <div v-for="task in (tasks || []).slice(0, 3)" :key="task.instance_id"
               class="todo-item is-link" @click="$router.push('/tasks')">
            <span class="todo-icon"><UiIcon name="task" /></span>
            <div class="todo-body">
              <b>{{ task.title || task.subject_title || textOf(FLOW_SCOPE_TEXT, task.scope) }}</b>
              <div class="meta"><span>{{ textOf(FLOW_SCOPE_TEXT, task.scope) }}</span><span v-if="task.submitted_at">{{ formatDateTime(task.submitted_at) }}</span></div>
            </div>
          </div>
        </section>

        <section v-else-if="m.key === 'finance'" class="card home-half home-accounts" aria-label="财务公开" @click="$router.push('/reports')">
          <div class="card-head">
            <h3 class="title title-flat">财务公开</h3>
            <router-link to="/reports" class="link" @click.stop>财务报表</router-link>
          </div>
          <template v-if="!accountsError">
            <div class="label">启用账户合计</div>
            <div class="home-accounts-total mono">¥{{ accountsTotal }}</div>
            <div v-if="!auth.isGuest && accounts.length" class="home-account-list">
              <div v-for="account in accounts" :key="account.id" class="home-account-row">
                <span class="home-account-name">{{ account.name }}</span>
                <b class="mono">¥{{ account.balance }}</b>
              </div>
            </div>
            <p v-else-if="auth.isGuest" class="muted">明细请查看财务报表</p>
            <p v-else class="muted">暂无账户</p>
          </template>
          <p v-else class="muted">
            加载失败
            <el-button link type="primary" size="small" @click.stop="loadAccounts">重试</el-button>
          </p>
        </section>

        <section v-else-if="m.key === 'management'" class="card home-half" aria-label="管理快捷">
          <div class="card-head"><h3 class="title title-flat">管理快捷</h3></div>
          <div class="home-manage">
            <router-link to="/income" class="home-manage-item"><UiIcon name="income" /><span>收入表</span></router-link>
            <router-link to="/claims" class="home-manage-item"><UiIcon name="wallet" /><span>报销 / 备用金</span></router-link>
            <router-link to="/historical-expenses" class="home-manage-item"><UiIcon name="upload" /><span>历史支出导入</span></router-link>
          </div>
        </section>

        <section v-else-if="m.key === 'polls'" class="card home-full home-poll" aria-label="投票与调查">
          <div class="card-head">
            <h3 class="title title-flat">投票与调查 · {{ openPolls ? openPolls.length : 0 }}</h3>
            <router-link to="/polls" class="link">查看全部</router-link>
          </div>
          <template v-if="poll">
            <router-link :to="`/polls/${poll.id}`" class="home-poll-title">{{ poll.title }}</router-link>
            <div class="meta">
              <span>{{ poll.kind === 'REP_VOTE' ? '业主代表投票' : '调查' }}</span>
              <span v-if="poll.deadline">截止 {{ formatDateTime(poll.deadline) }}</span>
            </div>
            <div v-if="countdown" class="home-countdown" aria-label="距截止">
              <div><b class="mono">{{ pad(countdown.days) }}</b><span>天</span></div>
              <div><b class="mono">{{ pad(countdown.hours) }}</b><span>时</span></div>
              <div><b class="mono">{{ pad(countdown.minutes) }}</b><span>分</span></div>
            </div>
            <el-button type="primary" class="home-poll-btn" @click="$router.push(`/polls/${poll.id}`)">立即参与</el-button>
          </template>
          <el-empty v-else :image-size="48" description="暂无进行中的投票" />
        </section>

        <section v-else-if="m.key === 'resolutions'" class="card home-full home-latest" aria-label="公开决议">
          <div class="card-head"><h3 class="title title-flat">公开决议 · {{ publicFeed.length }}</h3><router-link to="/resolutions" class="link">查看全部</router-link></div>
          <el-empty v-if="!publicFeed.length" :image-size="48" description="暂无公开决议" />
          <div v-for="item in publicFeed" :key="`${item.source}-${item.id}`" class="list-item">
            <router-link :to="item.to">{{ item.title }}</router-link>
            <span class="tag" :class="{ 'is-warning': item.source === 'REPRESENTATIVE' }">
              {{ item.source === 'REPRESENTATIVE' ? '业主代表决议' : '业委会决议' }}
            </span>
          </div>
        </section>

        <section v-else-if="m.key === 'info'" class="card home-full home-info" aria-label="信息公开">
          <div class="card-head"><h3 class="title title-flat">信息公开</h3><router-link to="/info" class="link">查看全部</router-link></div>
          <el-empty v-if="!infoPosts.length" :image-size="48" description="暂无公告" />
          <div v-for="item in infoPosts" :key="item.id" class="list-item">
            <router-link :to="`/info/${item.id}`">{{ item.title }}</router-link>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { approvalApi, accountApi, infoApi, meApi, pollApi, resolutionApi } from '@/shared/api'
import { remaining } from '@/shared/voteShare'
import { formatDateTime } from '@/shared/format'
import { FLOW_SCOPE_TEXT, textOf } from '@/shared/labels'
import { useAuthStore } from '@/stores/auth'
import UiIcon from './UiIcon.vue'

const auth = useAuthStore()
const resolutions = ref([])
// null 表示未取到（无权限或失败），区块显示空态；不编造数据
const tasks = ref(null)
const polls = ref(null)
const pendingReview = ref(0)
const pendingVotes = ref([])
const infoPosts = ref([])
const meError = ref(false)
const accounts = ref([])
const accountsTotal = ref('0.00')
const accountsError = ref(false)

// MOD-216 / IFC-437：角色档案决定内容尾部顺序；任务类模块按固定优先级插入
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
    list.push({ key: 'pendingTasks', kind: 'task', count: tasks.value.length, to: '/tasks' })
  }
  if (auth.isRepresentative && pendingVotes.value.length > 0) {
    list.push({ key: 'pendingVotes', kind: 'task', count: pendingVotes.value.length, to: '/polls' })
  }
  if (auth.hasOwnerUnit && pendingReview.value > 0) {
    list.push({ key: 'pendingReview', kind: 'task', count: pendingReview.value, to: '/units' })
  }
  return list
})

// IFC-437：content 恒渲染（含空态），task 数量 0 不进入清单
const bodyModules = computed(() => {
  const order = CONTENT_ORDER[profile.value]
  const out = []
  for (const key of order) {
    if (key === 'housing' && !unitRows.value.length) continue
    if (key === 'management' && !auth.isCommittee) continue
    out.push({ key, kind: 'content', count: null, to: null })
    if (key === 'housing') out.push(...taskModules.value)
  }
  // 无房屋的档案（游客）不会走到 housing 分支；任务模块兜底放在最前
  const hasHousing = order.includes('housing') && unitRows.value.length > 0
  if (!hasHousing) out.unshift(...taskModules.value)
  return out
})

const publicFeed = computed(() => {
  const committeeItems = resolutions.value.map((r) => ({
    id: r.id,
    title: r.title,
    source: 'COMMITTEE',
    to: `/resolutions/${r.id}`,
    sortAt: r.decided_at || r.created_at || ''
  }))
  const repItems = (polls.value || [])
    .filter((p) => p.kind === 'REP_VOTE' && p.status === 'CLOSED')
    .map((p) => ({
      id: p.id,
      title: p.title,
      source: 'REPRESENTATIVE',
      to: `/polls/${p.id}`,
      sortAt: p.deadline || p.created_at || ''
    }))
  return [...committeeItems, ...repItems]
    .sort((a, b) => String(b.sortAt).localeCompare(String(a.sortAt)))
    .slice(0, 5)
})

async function loadAccounts() {
  try {
    const data = await accountApi.summary({ status: 'ENABLED', recent: 0 })
    accounts.value = data?.accounts || []
    accountsTotal.value = data?.total_balance ?? '0.00'
    accountsError.value = false
  } catch (e) {
    accounts.value = []
    accountsTotal.value = '0.00'
    accountsError.value = true
  }
}

// C-34 / ADR-080：单一最高身份取 identitySummary（与"我的"、管理端目录同口径）；加载中/失败不显示"游客"
const identityText = computed(() => {
  if (auth.me) return auth.identitySummary.label
  return meError.value ? '加载失败，请重试' : '加载中…'
})
const unitRows = computed(() => auth.me?.identities?.units || [])

const pad = (n) => String(n).padStart(2, '0')

const todayText = computed(() => {
  const d = new Date()
  const week = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()]
  return `${d.getFullYear()} · ${pad(d.getMonth() + 1)} · ${pad(d.getDate())} 周${week}`
})

const openPolls = computed(() => (polls.value ? polls.value.filter((p) => p.status === 'OPEN') : null))
const poll = computed(() => openPolls.value?.[0] || null)
const countdown = computed(() => {
  const r = remaining(poll.value?.deadline)
  return r && !r.expired ? r : null
})

const participationText = (state) => ({ VOTED: '已投票', NOT_VOTED: '未投票', UNKNOWN: '状态待确认' }[state] || '状态待确认')

// MOD-216 / IFC-439：只对前 3 条 OPEN REP_VOTE 取详情判断参与状态，失败降级 UNKNOWN
async function loadRepVotes(list) {
  if (!auth.isRepresentative) return
  const candidates = list.filter((p) => p.status === 'OPEN' && p.kind === 'REP_VOTE').slice(0, 3)
  const settled = await Promise.allSettled(candidates.map((p) => pollApi.detail(p.id)))
  pendingVotes.value = settled
    .map((r, i) => {
      const p = candidates[i]
      if (r.status !== 'fulfilled') {
        return { id: p.id, title: p.title, deadline: p.deadline, participation: 'UNKNOWN', eligible: true }
      }
      const detail = r.value || {}
      if (detail.can_respond === false) return null
      return {
        id: p.id,
        title: detail.title || p.title,
        deadline: detail.deadline || p.deadline,
        participation: detail.my_response ? 'VOTED' : 'NOT_VOTED',
        eligible: true
      }
    })
    .filter(Boolean)
}

async function retryMe() {
  meError.value = false
  try {
    await auth.fetchMe()
  } catch (e) {
    meError.value = true
  }
}

onMounted(async () => {
  loadAccounts()
  try {
    await auth.fetchMe()
    meError.value = false
  } catch (e) {
    meError.value = true
  }
  const [resolutionResult, pollResult, infoResult] = await Promise.allSettled([
    resolutionApi.list('public', { page_size: 5 }),
    pollApi.list(),
    infoApi.list({ page_size: 3 })
  ])
  resolutions.value = resolutionResult.status === 'fulfilled'
    ? (resolutionResult.value.results || resolutionResult.value || [])
    : []
  polls.value = pollResult.status === 'fulfilled'
    ? (pollResult.value.results || pollResult.value || [])
    : null
  infoPosts.value = infoResult.status === 'fulfilled'
    ? (infoResult.value.results || infoResult.value || [])
    : []
  // 产权业主：待审批同住人申请数量（失败静默，不影响首页其他区块）；同住人不请求
  if (auth.hasOwnerUnit) {
    try {
      const data = await meApi.housing()
      pendingReview.value = Number(data?.pending_review_count) || 0
    } catch (e) {
      pendingReview.value = 0
    }
  }
  // 仅业委会成员可访问审批待办（REQ-FUNC-157）；非委员不发起请求
  if (auth.isCommittee) {
    try {
      const data = await approvalApi.tasks()
      tasks.value = data.results || data || []
    } catch (e) {
      tasks.value = null
    }
  }
  await loadRepVotes(polls.value || [])
})
</script>

<style scoped>
.todo-item.is-link { cursor: pointer; }
.todo-item.is-link:hover { border-color: var(--accent); }
.home-poll-title { color: var(--text); }
.home-accounts-total { font-size: 30px; font-weight: 700; letter-spacing: -0.01em; margin: 4px 0 8px; }
.home-account-list { display: flex; flex-direction: column; }
.home-account-row {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 8px 0; border-top: 1px solid var(--line); font-size: 13px;
}
.home-account-name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.home-manage { display: grid; grid-template-columns: 1fr; gap: 8px; }
.home-manage-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px; min-height: var(--hit-min);
  color: var(--text); border: 1px solid var(--line); border-radius: var(--radius-md); background: var(--surface);
}
@media (min-width: 768px) {
  .home-accounts-total { font-size: 34px; }
  .home-manage { grid-template-columns: repeat(3, 1fr); }
}
</style>
