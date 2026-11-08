<template>
  <div class="page">
    <div class="card">
      <h3 class="title">财务</h3>
      <el-tabs v-model="tab">
        <el-tab-pane label="收入表" name="income" />
        <el-tab-pane label="报销/备用金" name="claims" />
        <el-tab-pane label="报表生成" name="reports" />
      </el-tabs>
    </div>
    <div class="card" v-if="tab === 'income'">
      <el-table :data="incomes" size="small">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="total_amount" label="金额" width="120" />
        <el-table-column prop="status" label="状态" width="110" />
        <el-table-column prop="period_start" label="开始" width="120" />
        <el-table-column prop="period_end" label="结束" width="120" />
      </el-table>
    </div>
    <div class="card" v-if="tab === 'claims'">
      <el-table :data="claims" size="small">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="type" label="类型" width="130" />
        <el-table-column prop="amount" label="金额" width="120" />
        <el-table-column prop="reason" label="事由" min-width="180" />
        <el-table-column prop="status" label="状态" width="110" />
      </el-table>
    </div>
    <div class="card" v-if="tab === 'reports'">
      <div class="row">
        <el-input v-model="period" placeholder="周期，如 2026-Q4 或 2026-ANNUAL" style="max-width: 240px" />
        <el-button type="primary" @click="generate">生成报表</el-button>
      </div>
      <p class="muted">报表按已生效收入与支出台账生成，周期唯一且生成后锁定。</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import { errorText } from '@/shared/format'

const tab = ref('income')
const incomes = ref([])
const claims = ref([])
const period = ref('')

async function load() {
  try {
    if (tab.value === 'income') {
      const data = await admin.incomeSheets()
      incomes.value = data.results || data || []
    } else if (tab.value === 'claims') {
      const data = await admin.claims()
      claims.value = data.results || data || []
    }
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function generate() {
  try {
    await admin.createReport(period.value)
    ElMessage.success('报表已生成')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

watch(tab, load)
onMounted(load)
</script>
