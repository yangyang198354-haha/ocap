<template>
  <div class="page home">
    <div class="home-grid">
      <section class="card hero home-hero" aria-label="欢迎">
        <span class="home-hero-scan" aria-hidden="true" />
        <div class="home-hero-main">
          <div class="label">{{ todayText }}</div>
          <h2 class="title home-greeting">你好，<span class="grad-text home-caret">{{ auth.me?.profile?.nickname || '业主' }}</span></h2>
          <p class="muted home-meta">当前身份：{{ identityText }}<el-button v-if="meError" link size="small" @click="retryMe">重试</el-button></p>
          <p class="muted home-meta">手机号：{{ auth.me?.profile?.phone || '未绑定' }}</p>
        </div>
        <div class="home-metrics">
          <span class="chip"><b class="mono">{{ countText(tasks) }}</b> 项审批待办</span>
          <span class="chip"><b class="mono">{{ countText(openPolls) }}</b> 项进行中的投票</span>
        </div>
      </section>

      <section class="card home-todo" aria-label="待办">
        <div class="card-head"><h3 class="title title-flat">待办</h3><router-link to="/tasks" class="link">全部</router-link></div>
        <el-empty v-if="!tasks || !tasks.length" :image-size="48" description="暂无审批待办" />
        <div v-for="task in (tasks || []).slice(0, 3)" :key="task.instance_id" class="todo-item">
          <span class="todo-icon"><UiIcon name="task" /></span>
          <div class="todo-body">
            <b>{{ task.title || task.subject_title || task.scope }}</b>
            <div class="meta"><span>{{ task.scope }}</span><span v-if="task.submitted_at">{{ task.submitted_at }}</span></div>
          </div>
        </div>
      </section>

      <section v-for="(s, i) in stats" :key="s.label" class="card home-stat" :class="i % 2 ? 'is-even' : 'is-odd'">
        <div class="label">{{ s.label }}</div>
        <div class="stat-value mono">{{ s.value }}</div>
        <div class="stat-note muted">{{ s.note }}</div>
      </section>

      <section class="card home-units" aria-label="认证房屋">
        <div class="card-head">
          <h3 class="title title-flat">认证房屋</h3>
          <span class="muted">共 {{ auth.me ? unitRows.length : '—' }} 套</span>
        </div>
        <p v-if="!auth.me" class="muted">{{ meError ? '加载失败，请重试' : '加载中…' }}</p>
        <el-empty v-else-if="!unitRows.length" :image-size="48" description="暂无已认证房屋" />
        <div v-for="unit in unitRows" :key="unit.unit_id" class="home-unit">
          <b>{{ unit.specific_part }}</b>
          <div class="meta">
            <span>{{ unit.unit_type_label || '未登记' }}</span>
            <span class="mono">{{ unit.area_display || '未登记' }}</span>
            <span class="tag">{{ unit.role_label || '产权业主' }}</span>
          </div>
        </div>
      </section>

      <nav class="home-quick" aria-label="快捷入口">
        <div class="home-quick-title title">快捷入口</div>
        <div class="home-quick-grid">
          <router-link v-for="(q, i) in quick" :key="q.to" :to="q.to" class="home-q">
            <span class="home-q-key mono" :data-k="String(i + 1).padStart(2, '0')" aria-hidden="true" />
            <span class="home-q-icon"><UiIcon :name="q.icon" /></span>
            <b>{{ q.label }}</b>
            <small>{{ q.hint }}</small>
          </router-link>
        </div>
      </nav>

      <section class="card home-poll" aria-label="进行中的投票">
        <div class="card-head">
          <h3 class="title title-flat">进行中的投票</h3>
          <span v-if="poll" class="tag is-warning"><i class="tag-dot" aria-hidden="true" />{{ poll.kind === 'REP_VOTE' ? '业主代表投票' : '调查' }}</span>
        </div>
        <template v-if="poll">
          <b class="home-poll-title">{{ poll.title }}</b>
          <div v-if="countdown" class="home-countdown" aria-label="距截止">
            <div><b class="mono">{{ pad(countdown.days) }}</b><span>天</span></div>
            <div><b class="mono">{{ pad(countdown.hours) }}</b><span>时</span></div>
            <div><b class="mono">{{ pad(countdown.minutes) }}</b><span>分</span></div>
          </div>
          <el-button type="primary" class="home-poll-btn" @click="$router.push(`/polls/${poll.id}`)">立即参与</el-button>
        </template>
        <el-empty v-else :image-size="48" description="暂无进行中的投票" />
      </section>

      <section class="card home-latest" aria-label="最新公开决议">
        <div class="card-head"><h3 class="title title-flat">最新公开决议</h3><router-link to="/resolutions" class="link">查看全部</router-link></div>
        <el-empty v-if="!resolutions.length" description="暂无公开决议" />
        <div v-for="item in resolutions" :key="item.id" class="list-item">
          <router-link :to="`/resolutions/${item.id}`">{{ item.title }}</router-link>
          <StatusTag class="muted-gap" :status="item.status" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { approvalApi, pollApi, resolutionApi } from '@/shared/api'
import { remaining } from '@/shared/voteShare'
import { useAuthStore } from '@/stores/auth'
import StatusTag from './StatusTag.vue'
import UiIcon from './UiIcon.vue'

const auth = useAuthStore()
const resolutions = ref([])
// null 表示未取到（无权限或失败），区块显示空态；不编造数据
const tasks = ref(null)
const polls = ref(null)
const meError = ref(false)

const identityText = computed(() => {
  if (auth.me) return auth.identities.join('、') || '游客'
  return meError.value ? '加载失败，请重试' : '加载中…'
})
const unitRows = computed(() => auth.me?.identities?.units || [])

const pad = (n) => String(n).padStart(2, '0')
const countText = (list) => (list ? list.length : '—')

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

const stats = computed(() => [
  { label: '认证房屋', value: auth.me ? unitRows.value.length : '—', note: '已绑定的房屋数' },
  { label: '审批待办', value: countText(tasks.value), note: '待我审批的事项' },
  { label: '进行中的投票', value: countText(openPolls.value), note: '可参与的投票 / 调查' },
  { label: '近期公开决议', value: resolutions.value.length, note: `其中 ${resolutions.value.filter((r) => r.status === 'APPROVED').length} 项已通过` }
])

const quick = computed(() => [
  { label: '认证我的房屋', to: '/units', icon: 'key', hint: '绑定业主身份' },
  { label: '查看决议', to: '/resolutions', icon: 'doc', hint: '公开 / 我发起 / 待表决' },
  { label: '参与投票', to: '/polls', icon: 'vote', hint: '投票与调查' },
  { label: '待办', to: '/tasks', icon: 'task', hint: '审批事项' },
  { label: '财务报表', to: '/reports', icon: 'chart', hint: '季报 / 年报' },
  { label: '信息公开', to: '/info', icon: 'doc', hint: '公告与通知' },
  { label: '报销 / 备用金', to: '/claims', icon: 'wallet', hint: '发起申请' },
  ...(auth.isCommittee ? [{ label: '收入表', to: '/income', icon: 'income', hint: '收入登记与审批' }] : [])
])

async function retryMe() {
  meError.value = false
  try {
    await auth.fetchMe()
  } catch (e) {
    meError.value = true
  }
}

onMounted(async () => {
  try {
    await auth.fetchMe()
    meError.value = false
  } catch (e) {
    meError.value = true
  }
  try {
    const data = await resolutionApi.list('public', { page_size: 5 })
    resolutions.value = data.results || data || []
  } catch (e) {
    resolutions.value = []
  }
  // 仅用于首页区块展示；无权限（如非委员的审批待办 403）或失败时保持 null，区块显示空态
  try {
    const data = await approvalApi.tasks()
    tasks.value = data.results || data || []
  } catch (e) {
    tasks.value = null
  }
  try {
    const data = await pollApi.list()
    polls.value = data.results || data || []
  } catch (e) {
    polls.value = null
  }
})
</script>
