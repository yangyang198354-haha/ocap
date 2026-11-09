<template>
  <div class="page">
    <div class="card">
      <div class="row" style="justify-content: space-between">
        <h3 class="title" style="margin: 0">财务报表</h3>
        <div class="row" v-if="auth.isCommittee">
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
    </div>
    <div class="card" v-if="detail">
      <h4>{{ label(detail) }} 报表</h4>
      <p>收入合计：¥{{ detail.total_income }}</p>
      <p>支出合计：¥{{ detail.total_expense }}</p>
      <p>结余：¥{{ detail.balance }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ledgerApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'

const auth = useAuthStore()
const reports = ref([])
const detail = ref(null)
const gen = reactive({ period_type: 'QUARTER', year: new Date().getFullYear(), quarter: 1 })

const label = (r) => (r.period_type === 'YEAR' ? `${r.year} 年度` : `${r.year} 年第 ${r.quarter} 季度`)

async function load() {
  try {
    const data = await ledgerApi.reports()
    reports.value = data.results || data || []
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
