<template>
  <el-dialog
    :model-value="modelValue"
    :title="title"
    width="min(92vw, 760px)"
    modal-class="report-dialog-modal"
    class="report-dialog"
    append-to-body
    destroy-on-close
    @update:model-value="onVisibleChange"
    @closed="restoreFocus"
  >
    <div v-if="errorText" class="report-error">
      <p class="error-text">{{ errorText }}</p>
      <el-button type="primary" @click="load">重试</el-button>
    </div>
    <div v-else-if="loading" class="report-loading muted">加载中…</div>
    <template v-else-if="report">
      <div class="row row-between report-toolbar">
        <div class="row">
          <span v-if="report.legacy" class="tag is-warning">旧口径（未重算）</span>
          <span v-if="report.stale" class="tag is-warning">已过期，待重新生成</span>
        </div>
      </div>
      <div class="report-metrics">
        <div class="report-metric">
          <span class="label">期初结余</span>
          <b class="mono">¥{{ display(report.opening_balance) }}</b>
        </div>
        <div class="report-metric">
          <span class="label">本期收入</span>
          <b class="mono is-income">¥{{ display(report.total_income) }}</b>
        </div>
        <div class="report-metric">
          <span class="label">本期支出</span>
          <b class="mono is-expense">¥{{ display(report.total_expense) }}</b>
        </div>
        <div class="report-metric">
          <span class="label">期末结余</span>
          <b class="mono is-strong">¥{{ display(report.closing_balance) }}</b>
        </div>
      </div>
      <div class="report-detail-scroll">
        <el-table class="report-detail-table" v-if="(report.detail || []).length" :data="report.detail" size="small">
          <el-table-column class-name="data-number" prop="occurred_on" label="日期" width="110" />
          <el-table-column label="方向" width="70">
            <template #default="{ row }">
              <span :class="row.direction === 'INCOME' ? 'is-income' : 'is-expense'">
                {{ row.direction === 'INCOME' ? '收入' : '支出' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="类型" min-width="100">
            <template #default="{ row }">{{ entryTypeText(row.entry_type) }}</template>
          </el-table-column>
          <el-table-column label="金额" min-width="125" align="right" class-name="report-money">
            <template #default="{ row }">
              <span :class="row.direction === 'INCOME' ? 'is-income' : 'is-expense'">¥{{ moneyText(row.amount) }}</span>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else :image-size="48" description="本期暂无收支明细" />
      </div>
    </template>
    <template #footer>
      <el-button @click="onVisibleChange(false)">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ledgerApi } from '@/shared/api'
import { errorText as toErrorText, moneyText } from '@/shared/format'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  reportId: { type: Number, default: null },
  accountId: { type: Number, default: null },
  triggerEl: { type: Object, default: null }
})
const emit = defineEmits(['update:modelValue'])

const report = ref(null)
const loading = ref(false)
const errorText = ref('')
const ENTRY_TYPES = { REIMBURSEMENT: '报销', ADVANCE: '备用金', SETTLEMENT: '核销', INCOME: '收入' }
const entryTypeText = (t) => ENTRY_TYPES[t] || t || '收支'
const display = (value) => (value === null || value === undefined ? '—' : moneyText(value))
const title = computed(() => {
  if (!report.value) return '报表详情'
  const r = report.value
  return r.period_type === 'YEAR' ? `${r.year} 年度报表` : `${r.year} 年第 ${r.quarter} 季度报表`
})

function onVisibleChange(visible) {
  emit('update:modelValue', visible)
}

function restoreFocus() {
  const el = props.triggerEl
  if (el && typeof el.focus === 'function') el.focus()
}

async function load() {
  if (!props.reportId) return
  loading.value = true
  errorText.value = ''
  try {
    report.value = await ledgerApi.reportDetail(props.reportId, props.accountId || null)
  } catch (e) {
    report.value = null
    errorText.value = toErrorText(e) || '报表详情加载失败'
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.modelValue, props.reportId],
  async ([visible]) => {
    if (!visible) return
    report.value = null
    errorText.value = ''
    await load()
  }
)
</script>

<style>
/* el-dialog 被 teleport 到 body，过渡覆盖必须用全局选择器（ADR-184） */
.report-dialog-modal { transition-duration: 260ms !important; }
@media (prefers-reduced-motion: reduce) {
  .report-dialog-modal { transition-duration: 0s !important; }
}
</style>

<style scoped>
.report-detail-table { font-size: 14px; }
.report-detail-table :deep(th.el-table__cell) { font-size: 13px; }
.report-detail-table :deep(td.report-money) { font-size: 15px; font-variant-numeric: tabular-nums; }
.report-toolbar { margin-bottom: 12px; min-height: 0; }
.report-metrics { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.report-metric {
  display: flex; flex-direction: column; gap: 4px; padding: 10px 12px;
  background: var(--glass); border: 1px solid var(--line); border-radius: var(--radius-md);
}
.report-metric b { font-size: 20px; }
.report-metric b.is-strong { font-size: 22px; color: var(--accent-text); }
.report-metric b.is-income, .is-income { color: var(--success); }
.report-metric b.is-expense, .is-expense { color: var(--danger); }
.report-detail-scroll { margin-top: 12px; max-height: 46vh; overflow-y: auto; }
.report-error { display: flex; flex-direction: column; align-items: flex-start; gap: 12px; }
.report-loading { padding: 24px 0; text-align: center; }
@media (min-width: 768px) {
  .report-metrics { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
</style>
