<template>
  <div class="page">
    <div class="card">
      <div class="row" style="justify-content: space-between">
        <h3 class="title" style="margin: 0">财务报表</h3>
        <div class="row" v-if="auth.isCommittee">
          <router-link to="/historical-expenses"><el-button>历史支出导入</el-button></router-link>
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
      <p class="muted">季度/年度报表在周期结束后由系统自动生成，业委会成员可手动重新生成；所有用户可查看。</p>
    </div>
    <div class="card">
      <el-empty v-if="!reports.length" description="暂无已生成报表" />
      <div v-for="item in reports" :key="item.id" class="list-item">
        <a href="javascript:void(0)" @click="open(item)">{{ label(item) }}</a>
        <el-tag v-if="item.stale" size="small" type="warning" style="margin-left: 8px">已过期，待重新生成</el-tag>
        <span class="muted" style="margin-left: 8px">收入 ¥{{ item.total_income }} · 支出 ¥{{ item.total_expense }}</span>
      </div>
      <PagerBar :total="total" :page="page" :page-size="pageSize" @change="gotoPage" />
    </div>
    <div class="card" v-if="detail">
      <h4>{{ label(detail) }} 报表</h4>
      <p>收入合计：¥{{ detail.total_income }}</p>
      <p>支出合计：¥{{ detail.total_expense }}</p>
      <p>结余：¥{{ detail.balance }}</p>
      <el-table v-if="(detail.detail || []).length" :data="detail.detail" size="small" class="report-detail">
        <el-table-column prop="occurred_on" label="日期" width="120" />
        <el-table-column label="类型" min-width="120">
          <template #default="{ row }">{{ entryTypeText(row.entry_type) }}</template>
        </el-table-column>
        <el-table-column label="方向" width="80">
          <template #default="{ row }">{{ row.direction === 'INCOME' ? '收入' : '支出' }}</template>
        </el-table-column>
        <el-table-column label="金额" width="120">
          <template #default="{ row }">¥{{ row.amount }}</template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ledgerApi } from '@/shared/api'
import PagerBar from '@/shared/PagerBar.vue'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'
import { usePaging } from '@/shared/usePaging'

const auth = useAuthStore()
const { items: reports, total, page, pageSize, reload, goto } = usePaging({
  fetch: (params) => ledgerApi.reports(params)
})
const detail = ref(null)
// 明细类型：报销 / 备用金 / 核销为系统类型，收入行的类型即收入类别（明细不含事由，OQ-08）
const ENTRY_TYPES = { REIMBURSEMENT: '报销', ADVANCE: '备用金', SETTLEMENT: '核销', INCOME: '收入' }
const entryTypeText = (t) => ENTRY_TYPES[t] || t || ''
const gen = reactive({ period_type: 'QUARTER', year: new Date().getFullYear(), quarter: 1 })

const label = (r) => (r.period_type === 'YEAR' ? `${r.year} 年度` : `${r.year} 年第 ${r.quarter} 季度`)

async function load() {
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

async function open(item) {
  try {
    detail.value = await ledgerApi.reportDetail(item.id)
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function generate() {
  const body = { period_type: gen.period_type, year: gen.year }
  if (gen.period_type === 'QUARTER') body.quarter = gen.quarter
  try {
    detail.value = await ledgerApi.generate(body)
    ElMessage.success('报表已生成')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(async () => {
  await auth.fetchMe().catch(() => null)
  load()
})
</script>
