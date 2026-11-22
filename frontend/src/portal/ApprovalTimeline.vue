<template>
  <div>
    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="error" class="muted">{{ error }}</p>
    <template v-else-if="timeline">
      <div class="row" style="justify-content: space-between">
        <b>{{ timeline.subject_title }}</b>
        <el-tag size="small">{{ textOf(APPROVAL_STATUS_LABELS, timeline.status) }}</el-tag>
      </div>
      <p class="muted">提交于 {{ formatDateTime(timeline.submitted_at) }}</p>
      <div v-for="step in timeline.steps" :key="step.order" class="card" style="margin-top: 8px">
        <div class="row" style="justify-content: space-between">
          <b>第 {{ step.order }} 步 · {{ step.name }}</b>
          <el-tag size="small">{{ textOf(STEP_STATUS_LABELS, step.status) }}</el-tag>
        </div>
        <p class="muted">
          {{ textOf(STEP_STRATEGY_LABELS, step.strategy) }} · 到达：{{ step.reached_at ? formatDateTime(step.reached_at) : '未开始' }}
        </p>
        <p class="muted">审批人：{{ (step.approvers || []).map((a) => a.nickname).join('、') || '—' }}</p>
        <div v-for="(action, index) in step.actions" :key="index" class="list-item">
          <div class="row">
            <b>{{ action.actor_label }}</b>
            <el-tag size="small" :type="action.action === 'REJECT' ? 'danger' : 'success'">
              {{ textOf(APPROVAL_ACTION_LABELS, action.action) }}
            </el-tag>
            <span class="muted">{{ formatDateTime(action.acted_at) }}</span>
          </div>
          <p v-if="action.comment" class="muted">备注：{{ action.comment }}</p>
        </div>
      </div>
      <p v-if="!timeline.steps.length" class="muted">该审批为半数同意模式，请在决议详情查看投票结果。</p>
    </template>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { approvalApi } from '@/shared/api'
import { errorText, formatDateTime } from '@/shared/format'
import { APPROVAL_ACTION_LABELS, APPROVAL_STATUS_LABELS, STEP_STATUS_LABELS, STEP_STRATEGY_LABELS, textOf } from '@/shared/labels'

const props = defineProps({ instanceId: { type: Number, required: true } })
const timeline = ref(null)
const loading = ref(false)
const error = ref('')

async function load() {
  if (!props.instanceId) return
  loading.value = true
  error.value = ''
  try {
    timeline.value = await approvalApi.instance(props.instanceId)
  } catch (e) {
    timeline.value = null
    error.value = errorText(e)
  } finally {
    loading.value = false
  }
}

watch(() => props.instanceId, load, { immediate: true })
defineExpose({ reload: load })
</script>
