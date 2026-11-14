<!-- MOD-085 / IFC-271 / REQ-FUNC-159：报表明细（与 Web 报表详情同口径，不显示支出事由 summary） -->
<template>
  <ThemeRoot>
  <view>
    <view v-if="failed" class="card">
      <view class="muted">报表不存在或暂时无法查看</view>
    </view>
    <template v-else-if="report">
      <view class="card">
        <view class="title">{{ label(report) }} 报表</view>
        <view>收入合计：¥{{ report.total_income }}</view>
        <view>支出合计：¥{{ report.total_expense }}</view>
        <view>结余：¥{{ report.balance }}</view>
      </view>
      <view class="card">
        <view class="title">收支明细</view>
        <view v-if="!(report.detail || []).length" class="muted">本期暂无明细</view>
        <view v-for="(row, i) in report.detail || []" :key="i" class="list-item">
          <text>{{ row.occurred_on }}</text>
          <text style="margin-left: 12rpx">{{ entryTypeText(row.entry_type) }}</text>
          <text class="muted" style="margin-left: 12rpx">{{ row.direction === 'INCOME' ? '收入' : '支出' }}</text>
          <text style="margin-left: 12rpx">¥{{ row.amount }}</text>
        </view>
      </view>
    </template>
  </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api } from '@/utils/api'

const report = ref(null)
const failed = ref(false)

// 明细类型：报销 / 备用金 / 核销为系统类型，收入行的类型即收入类别（明细不含事由）
const ENTRY_TYPES = { REIMBURSEMENT: '报销', ADVANCE: '备用金', SETTLEMENT: '核销', INCOME: '收入' }
const entryTypeText = (t) => ENTRY_TYPES[t] || t || ''
const label = (r) => (r.period_type === 'YEAR' ? `${r.year} 年度` : `${r.year} 年第 ${r.quarter} 季度`)

onLoad(async (options) => {
  try {
    report.value = await api.report(options.id)
  } catch (e) {
    failed.value = true
  }
})
</script>
