<template>
  <div class="page">
    <div class="card">
      <h3 class="title">财务报表</h3>
      <p class="muted">季度/年度报表由业委会生成并锁定，所有用户可查看。</p>
    </div>
    <div class="card">
      <el-empty v-if="!reports.length" description="暂无已生成报表" />
      <div v-for="item in reports" :key="item.id" style="padding: 10px 0; border-bottom: 1px solid #f0f1f3">
        <a href="javascript:void(0)" @click="open(item)">{{ item.period }}</a>
        <span class="muted" style="margin-left: 8px">收入 ¥{{ item.total_income }} · 支出 ¥{{ item.total_expense }}</span>
      </div>
    </div>
    <div class="card" v-if="detail">
      <h4>{{ detail.period }} 报表</h4>
      <p>收入合计：¥{{ detail.total_income }}</p>
      <p>支出合计：¥{{ detail.total_expense }}</p>
      <p>结余：¥{{ detail.balance }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ledgerApi } from '@/shared/api'
import { errorText } from '@/shared/format'

const reports = ref([])
const detail = ref(null)

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

onMounted(load)
</script>
