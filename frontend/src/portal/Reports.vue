<template>
  <div class="page reports-page">
    <section class="card reports-hero">
      <div class="row row-between">
        <h3 class="title title-flat">财务报表</h3>
        <div v-if="auth.isCommittee" class="row">
          <el-select v-model="gen.period_type" style="width: 110px">
            <el-option label="季度" value="QUARTER" /><el-option label="年度" value="YEAR" />
          </el-select>
          <el-input-number v-model="gen.year" :min="2000" :max="2100" />
          <el-select v-if="gen.period_type === 'QUARTER'" v-model="gen.quarter" style="width: 90px">
            <el-option v-for="q in 4" :key="q" :label="`Q${q}`" :value="q" />
          </el-select>
          <el-button type="primary" @click="generate">重新生成</el-button>
        </div>
      </div>
      <p class="muted">季度/年度报表在周期结束后由系统自动生成，业委会成员可手动重新生成；所有用户可查看。点击报表条目以浮层查看详情。</p>
      <div class="reports-filter" role="group" aria-label="周期筛选">
        <button
          v-for="option in PERIOD_OPTIONS"
          :key="option.value"
          type="button"
          class="reports-filter-btn"
          :class="{ 'is-active': periodFilter === option.value }"
          @click="choosePeriod(option.value)"
        >
          {{ option.label }}
        </button>
      </div>
    </section>

    <section class="reports-accounts" aria-label="账户余额">
      <header class="reports-accounts-head">
        <div>
          <div class="label">账户余额合计（启用账户）</div>
          <div class="reports-total mono">¥{{ totalBalance }}</div>
        </div>
        <router-link to="/reports" class="link reports-refresh" @click.prevent="loadAccounts">刷新</router-link>
      </header>
      <p v-if="accountError" class="muted account-error">
        加载失败
        <el-button link type="primary" size="small" @click="loadAccounts">重试</el-button>
      </p>
      <div v-else-if="accounts.length" class="reports-account-grid">
        <AccountCard v-for="account in accounts" :key="account.id" :account="account" />
      </div>
      <el-empty v-else :image-size="48" description="暂无账户" />
    </section>

    <section class="card">
      <el-empty v-if="!reports.length" description="暂无已生成报表" />
      <div v-for="item in reports" :key="item.id" class="list-item reports-item">
        <div class="reports-item-main">
          <button type="button" class="reports-item-link" @click="open(item, $event)">
            {{ label(item) }}
          </button>
          <el-tag v-if="item.legacy" size="small" type="info">旧口径</el-tag>
          <el-tag v-if="item.stale" size="small" type="warning">已过期，待重新生成</el-tag>
        </div>
        <div class="muted reports-item-totals">
          <span>收入 ¥{{ item.total_income }}</span>
          <span>支出 ¥{{ item.total_expense }}</span>
          <span>结余 ¥{{ item.balance }}</span>
        </div>
      </div>
      <PagerBar :total="total" :page="page" :page-size="pageSize" @change="gotoPage" />
    </section>

    <ReportDetailDialog v-model="dialogVisible" :report-id="selectedId" :trigger-el="triggerEl" />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { accountApi, ledgerApi } from '@/shared/api'
import PagerBar from '@/shared/PagerBar.vue'
import AccountCard from './AccountCard.vue'
import ReportDetailDialog from './ReportDetailDialog.vue'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'
import { usePaging } from '@/shared/usePaging'

const PERIOD_OPTIONS = [
  { value: 'ALL', label: '全部' },
  { value: 'YEAR', label: '仅年报' },
  { value: 'QUARTER', label: '仅季报' }
]

const auth = useAuthStore()
const periodFilter = ref('ALL')
const accounts = ref([])
const totalBalance = ref('0.00')
const accountError = ref(false)
const dialogVisible = ref(false)
const selectedId = ref(null)
const triggerEl = ref(null)

const { items: reports, total, page, pageSize, reload, goto, resetAndLoad } = usePaging({
  fetch: (params) => ledgerApi.reports(params),
  filters: computed(() => (periodFilter.value === 'ALL' ? {} : { period_type: periodFilter.value }))
})
const gen = reactive({ period_type: 'QUARTER', year: new Date().getFullYear(), quarter: 1 })

const label = (r) => (r.period_type === 'YEAR' ? `${r.year} 年度` : `${r.year} 年第 ${r.quarter} 季度`)

async function loadReports() {
  try {
    await reload()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function gotoPage(n) {
  try {
    await goto(n)
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function choosePeriod(value) {
  if (periodFilter.value === value) return
  periodFilter.value = value
  try {
    await resetAndLoad()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function loadAccounts() {
  try {
    const data = await accountApi.summary({ status: 'ENABLED', recent: 10 })
    accounts.value = data?.accounts || []
    totalBalance.value = data?.total_balance ?? '0.00'
    accountError.value = false
  } catch (e) {
    accounts.value = []
    totalBalance.value = '0.00'
    accountError.value = true
  }
}

function open(item, event) {
  selectedId.value = item.id
  triggerEl.value = event?.currentTarget || null
  dialogVisible.value = true
}

async function generate() {
  const body = { period_type: gen.period_type, year: gen.year }
  if (gen.period_type === 'QUARTER') body.quarter = gen.quarter
  try {
    await ledgerApi.generate(body)
    ElMessage.success('报表已生成')
    await loadReports()
    await loadAccounts()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

watch(
  () => auth.me,
  () => loadAccounts(),
  { immediate: true }
)

onMounted(async () => {
  await auth.fetchMe().catch(() => null)
  loadReports()
})
</script>

<style scoped>
.reports-hero { display: flex; flex-direction: column; gap: 10px; }
.reports-filter { display: inline-flex; gap: 4px; padding: 3px; border: 1px solid var(--line); border-radius: var(--radius-btn); width: fit-content; }
.reports-filter-btn {
  min-height: 32px; padding: 0 14px; border: 0; border-radius: calc(var(--radius-btn) - 2px);
  background: transparent; color: var(--muted); font: inherit; font-size: 13px; cursor: pointer;
}
.reports-filter-btn.is-active { background: var(--glass); color: var(--accent-text); font-weight: 650; }
.reports-accounts { display: flex; flex-direction: column; gap: 12px; margin: 0 0 16px; }
.reports-accounts-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; }
.reports-total { font-size: 30px; font-weight: 700; letter-spacing: -0.01em; }
.reports-account-grid { display: grid; gap: 12px; grid-template-columns: minmax(0, 1fr); }
.account-error { margin: 0; }
.reports-item { display: flex; flex-direction: column; gap: 6px; }
.reports-item-main { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.reports-item-link {
  padding: 0; border: 0; background: transparent; color: var(--accent-text);
  font: inherit; font-size: 15px; font-weight: 600; cursor: pointer; text-align: left;
}
.reports-item-link:hover { text-decoration: underline; }
.reports-item-totals { display: flex; flex-wrap: wrap; gap: 4px 16px; }
@media (min-width: 768px) {
  .reports-account-grid { grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); }
}
</style>
