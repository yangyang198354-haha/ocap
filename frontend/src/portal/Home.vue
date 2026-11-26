<template>
  <div class="page home">
    <div class="home-grid">
      <section class="card hero home-hero" aria-label="欢迎" style="--i:0">
        <span class="home-hero-scan" aria-hidden="true" />
        <div class="home-hero-main">
          <div class="label">{{ todayText }}</div>
          <template v-if="layoutReady || meError">
            <h2 class="title home-greeting">你好，<span class="grad-text home-caret">{{ auth.me?.profile?.nickname || '业主' }}</span></h2>
            <p class="muted home-meta">当前身份：{{ identityText }}<el-button v-if="meError" link size="small" @click="retryMe">重试</el-button></p>
            <p v-if="auth.isGuest" class="muted home-meta"><router-link to="/units/pick" class="link">去认证</router-link></p>
          </template>
          <template v-else>
            <div class="sk-line hero-sk-title" aria-hidden="true" />
            <div class="sk-line hero-sk-meta" aria-hidden="true" />
          </template>
        </div>
      </section>

      <template v-if="layoutReady || meError">
        <template v-for="m in bodyModules" :key="m.key">
        <section v-if="m.key === 'housing'" class="card home-half home-housing" aria-label="我的房屋" :style="{ '--i': 0 }" @click="$router.push('/units')">
          <div class="card-head">
            <div class="card-head-main">
              <span class="card-icon"><UiIcon name="home" /></span>
              <h3 class="title title-flat">我的房屋 · {{ unitRows.length }}</h3>
            </div>
            <router-link to="/units" class="link card-link" @click.stop>房屋明细<span class="card-link-arrow">→</span></router-link>
          </div>
          <p class="muted">共 {{ unitRows.length }} 套（点击查看明细）</p>
        </section>

        <section v-else-if="m.key === 'pendingReview'" class="card home-half home-review" aria-label="待我处理" :style="{ '--i': 0 }">
          <div class="card-head">
            <div class="card-head-main">
              <span class="card-icon is-warning"><UiIcon name="task" /></span>
              <h3 class="title title-flat">待我处理 · {{ m.count }}</h3>
            </div>
            <router-link :to="m.to" class="link card-link">去处理<span class="card-link-arrow">→</span></router-link>
          </div>
          <p class="muted">有 {{ m.count }} 条同住人申请待审批</p>
        </section>

        <section v-else-if="m.key === 'pendingVotes'" class="card home-half home-votes" aria-label="待我表决" :style="{ '--i': 0 }">
          <div class="card-head">
            <div class="card-head-main">
              <span class="card-icon"><UiIcon name="vote" /></span>
              <h3 class="title title-flat">待我表决 · {{ m.count }}</h3>
            </div>
            <router-link :to="m.to" class="link card-link">全部<span class="card-link-arrow">→</span></router-link>
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

        <section v-else-if="m.key === 'pendingTasks'" class="card home-half home-todo" aria-label="待办审批" :style="{ '--i': 0 }">
          <div class="card-head">
            <div class="card-head-main">
              <span class="card-icon is-warning"><UiIcon name="task" /></span>
              <h3 class="title title-flat">待办审批 · {{ m.count }}</h3>
            </div>
            <router-link to="/tasks" class="link card-link">全部<span class="card-link-arrow">→</span></router-link>
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

        <section v-else-if="m.key === 'finance'" class="card home-half home-accounts" aria-label="财务公开" :style="{ '--i': 0 }" @click="$router.push('/reports')">
          <div class="card-head">
            <div class="card-head-main">
              <span class="card-icon"><UiIcon name="wallet" /></span>
              <h3 class="title title-flat">财务公开</h3>
            </div>
            <router-link to="/reports" class="link card-link" @click.stop>财务报表<span class="card-link-arrow">→</span></router-link>
          </div>
          <template v-if="!accountsError">
            <div class="label">启用账户合计</div>
            <div class="home-accounts-total mono">¥{{ accountsTotal }}</div>
            <div v-if="accounts.length" class="home-finance-chips">
              <span class="count-pill">{{ accounts.length }} 个账户</span>
            </div>
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

        <section v-else-if="m.key === 'management'" class="card home-half home-management" aria-label="管理快捷" :style="{ '--i': 0 }">
          <div class="card-head">
            <div class="card-head-main">
              <span class="card-icon"><UiIcon name="chart" /></span>
              <h3 class="title title-flat">管理快捷</h3>
            </div>
          </div>
          <div class="home-manage">
            <router-link to="/income" class="home-manage-item">
              <span class="home-manage-icon"><UiIcon name="income" /></span>
              <span class="home-manage-text"><b>收入表</b><small>查看与登记</small></span>
              <span class="home-manage-arrow">→</span>
            </router-link>
            <router-link to="/claims" class="home-manage-item">
              <span class="home-manage-icon"><UiIcon name="wallet" /></span>
              <span class="home-manage-text"><b>报销 / 备用金</b><small>申请与查看</small></span>
              <span class="home-manage-arrow">→</span>
            </router-link>
            <router-link to="/historical-expenses" class="home-manage-item">
              <span class="home-manage-icon"><UiIcon name="upload" /></span>
              <span class="home-manage-text"><b>历史支出导入</b><small>批量导入</small></span>
              <span class="home-manage-arrow">→</span>
            </router-link>
          </div>
        </section>

        <section v-else-if="m.key === 'polls'" class="card home-full home-poll" aria-label="投票与调查" :style="{ '--i': 0 }">
          <div class="card-head">
            <div class="card-head-main">
              <span class="card-icon"><UiIcon name="vote" /></span>
              <h3 class="title title-flat">投票与调查 · {{ openPolls ? openPolls.length : 0 }}</h3>
            </div>
            <router-link to="/polls" class="link card-link">查看全部<span class="card-link-arrow">→</span></router-link>
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
          <div v-else class="home-empty">
            <el-empty :image-size="48" description="暂无进行中的投票" />
            <router-link to="/polls" class="link card-link">去投票<span class="card-link-arrow">→</span></router-link>
          </div>
        </section>

        <section v-else-if="m.key === 'resolutions'" class="card home-full home-latest" aria-label="公开决议" :style="{ '--i': 0 }">
          <div class="card-head">
            <div class="card-head-main">
              <span class="card-icon"><UiIcon name="doc" /></span>
              <h3 class="title title-flat">公开决议 · {{ publicFeed.length }}</h3>
            </div>
            <router-link to="/resolutions" class="link card-link">查看全部<span class="card-link-arrow">→</span></router-link>
          </div>
          <div v-if="!publicFeed.length" class="home-empty">
            <el-empty :image-size="48" description="暂无公开决议" />
            <router-link to="/resolutions" class="link card-link">去查看<span class="card-link-arrow">→</span></router-link>
          </div>
          <div v-for="item in publicFeed" :key="`${item.source}-${item.id}`" class="list-item home-feed-item">
            <router-link :to="item.to">{{ item.title }}</router-link>
            <span class="tag" :class="item.source === 'REPRESENTATIVE' ? 'is-representative' : 'is-committee'">
              {{ item.source === 'REPRESENTATIVE' ? '业主代表决议' : '业委会决议' }}
            </span>
            <span class="home-feed-arrow" aria-hidden="true">→</span>
          </div>
        </section>

        <section v-else-if="m.key === 'info'" class="card home-full home-info" aria-label="信息公开" :style="{ '--i': 0 }">
          <div class="card-head">
            <div class="card-head-main">
              <span class="card-icon"><UiIcon name="doc" /></span>
              <h3 class="title title-flat">信息公开</h3>
            </div>
            <router-link to="/info" class="link card-link">查看全部<span class="card-link-arrow">→</span></router-link>
          </div>
          <div v-if="!infoPosts.length" class="home-empty">
            <el-empty :image-size="48" description="暂无公告" />
            <router-link to="/info" class="link card-link">去查看<span class="card-link-arrow">→</span></router-link>
          </div>
          <div v-for="item in infoPosts" :key="item.id" class="list-item home-feed-item">
            <router-link :to="`/info/${item.id}`">{{ item.title }}</router-link>
            <span class="home-feed-arrow" aria-hidden="true">→</span>
          </div>
        </section>
        </template>
      </template>
      <template v-else>
        <section v-for="n in 5" :key="`sk-${n}`" class="card home-skeleton" :class="n === 5 ? 'home-full' : 'home-half'" :style="{ '--i': 0 }" aria-hidden="true">
          <div class="sk-line sk-title" />
          <div class="sk-line" />
          <div class="sk-line sk-short" />
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
import { readIdentityCache, writeIdentityCache } from '@/shared/identityCache'
import { useAuthStore } from '@/stores/auth'
import UiIcon from './UiIcon.vue'

const auth = useAuthStore()
// 刷新时优先用 5 分钟内的身份+计数缓存，首帧即最终布局；随后后台请求校准
const identityCache = auth.token ? readIdentityCache() : null
const resolutions = ref([])
// null 表示未取到（无权限或失败），区块显示空态；不编造数据
const tasks = ref(null)
const tasksCount = ref(Number(identityCache?.counts?.tasks) || 0)
const pendingVotesCount = ref(Number(identityCache?.counts?.votes) || 0)
const polls = ref(null)
const pendingReview = ref(Number(identityCache?.counts?.pendingReview) || 0)
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
  if (auth.isCommittee && tasksCount.value > 0) {
    list.push({ key: 'pendingTasks', kind: 'task', count: tasksCount.value, to: '/tasks' })
  }
  if (auth.isRepresentative && pendingVotesCount.value > 0) {
    list.push({ key: 'pendingVotes', kind: 'task', count: pendingVotesCount.value, to: '/polls' })
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
// IFC-441：身份/结构未就绪时渲染同构骨架；任务类模块（待办审批/待我处理/待表决）依赖异步计数，
// 计数返回前不渲染网格，避免卡片晚到把后面的卡片挤走；有带计数的缓存时直接放行，首帧即最终布局
const layoutReady = ref(Boolean(identityCache?.me?.identities && identityCache?.counts))

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
  pendingVotesCount.value = pendingVotes.value.length
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
  // 兜底：各请求均有独立 catch，正常不会走到这里；仅在极端挂起时 8s 后强制放行
  const guard = setTimeout(() => { layoutReady.value = true }, 8000)
  // 只有 /me 本次真实成功才续期缓存；后台校准失败时保留原 TTL，避免过期身份被无限延长
  let meFresh = false
  try {
    if (identityCache?.me?.identities) {
      // 已有缓存身份：先按缓存渲染，再后台校准，不阻塞首屏
      auth.fetchMe().then(() => { meFresh = true }).catch(() => {})
    } else {
      try {
        await auth.fetchMe()
        meFresh = true
        meError.value = false
      } catch (e) {
        meError.value = true
      }
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
      tasksCount.value = tasks.value?.length || 0
    }
    await loadRepVotes(polls.value || [])
  } finally {
    clearTimeout(guard)
    layoutReady.value = true
    // 记录本次结构与计数，供下次刷新首帧直接渲染（5 分钟 TTL）
    if (meFresh && auth.token && auth.me?.identities) {
      writeIdentityCache(auth.me, {
        pendingReview: pendingReview.value,
        tasks: tasksCount.value,
        votes: pendingVotesCount.value
      })
    }
  }
})
</script>

<style scoped>
.todo-item.is-link { cursor: pointer; }
.todo-item.is-link:hover { border-color: var(--accent); }
.home-poll-title { color: var(--text); }
.home-accounts-total { font-size: 34px; font-weight: 700; letter-spacing: -0.02em; margin: 4px 0 6px; }
.home-finance-chips { display: flex; gap: 6px; margin-bottom: 6px; }
.home-account-list { display: flex; flex-direction: column; }
.home-account-row {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 10px 0; border-top: 1px solid var(--line); font-size: 13px;
}
.home-account-name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.home-manage { display: grid; grid-template-columns: 1fr; gap: 4px; }
.home-manage-item {
  display: flex; align-items: center; gap: 12px; padding: 10px 8px; min-height: 56px;
  color: var(--text); border: 0; border-radius: var(--radius-md); background: transparent;
  transition: background var(--motion-base, 220ms) var(--motion-ease, ease);
}
.home-manage-item:hover { background: var(--surface-tint, var(--glass)); }
.home-manage-icon {
  width: 40px; height: 40px; flex: none; display: grid; place-items: center;
  border-radius: 999px; background: var(--glass); color: var(--accent-text);
  transition: transform var(--motion-base, 220ms) var(--motion-ease, ease);
}
.home-manage-item:hover .home-manage-icon { transform: translateY(-1px) rotate(-4deg); }
.home-manage-text { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.home-manage-text b { font-size: 14px; font-weight: 600; }
.home-manage-text small { font-size: 12px; color: var(--muted); }
.home-manage-arrow {
  margin-left: auto; color: var(--muted);
  transition: transform var(--motion-base, 220ms) var(--motion-ease, ease), color var(--motion-base, 220ms) var(--motion-ease, ease);
}
.home-manage-item:hover .home-manage-arrow { transform: translateX(2px); color: var(--accent-text); }
.home-empty { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 4px 0 8px; }
.home-feed-item { display: flex; align-items: center; gap: 10px; }
.home-feed-item a { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.home-feed-item .tag { flex: none; }
.home-feed-item .home-feed-arrow { margin-left: auto; color: var(--muted); transition: transform var(--motion-base, 220ms) var(--motion-ease, ease); }
.home-feed-item:hover .home-feed-arrow { transform: translateX(2px); color: var(--accent-text); }
.home-feed-item .is-committee { color: var(--accent-text); background: var(--glass); }
.home-feed-item .is-representative { color: var(--accent-2); background: var(--glass); }
.card-icon.is-warning { color: var(--warning); }
/* 身份/结构加载骨架：Hero 与网格同一时刻用骨架占位，数据齐了再一起显示 */
.sk-line { height: 12px; border-radius: 8px; background: var(--glass); animation: sk-pulse 1.4s ease-in-out infinite; }
.hero-sk-title { width: 55%; height: 24px; margin: 6px 0; }
.hero-sk-meta { width: 40%; }
.home-skeleton { min-height: 128px; display: flex; flex-direction: column; justify-content: center; gap: 14px; }
.home-skeleton .sk-line.sk-title { width: 42%; height: 16px; }
.home-skeleton .sk-line.sk-short { width: 64%; }
@keyframes sk-pulse { 50% { opacity: .45; } }
html[data-perf="low"] .sk-line { animation: none; }
@media (prefers-reduced-motion: reduce) {
  .sk-line { animation: none; }
}
@media (min-width: 768px) {
  .home-accounts-total { font-size: 38px; }
}
</style>
