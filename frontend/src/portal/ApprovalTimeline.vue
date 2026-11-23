<template>
  <div>
    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="error" class="muted">{{ error }}</p>
    <template v-else-if="timeline">
      <div class="row" style="justify-content: space-between">
        <b>{{ timeline.subject_title }}</b>
        <el-tag size="small">{{ textOf(APPROVAL_STATUS_LABELS, timeline.status) }}</el-tag>
      </div>
      <div class="person-row" style="margin-top: 6px">
        <AuthImage :src="timeline.submitter?.avatar_url" :alt="submitterName" :size="28" />
        <span>提交人：<b>{{ submitterName }}</b></span>
        <span class="muted">提交于 {{ formatDateTime(timeline.submitted_at) }}</span>
      </div>
      <div v-for="step in timeline.steps" :key="step.order" class="card" style="margin-top: 8px">
        <div class="row" style="justify-content: space-between">
          <b>第 {{ step.order }} 步 · {{ step.name }}</b>
          <el-tag size="small">{{ textOf(STEP_STATUS_LABELS, step.status) }}</el-tag>
        </div>
        <p class="muted">
          {{ textOf(STEP_STRATEGY_LABELS, step.strategy) }} · 到达：{{ step.reached_at ? formatDateTime(step.reached_at) : '未开始' }}
        </p>
        <div class="person-row">
          <span class="muted">审批人：</span>
          <span v-for="a in step.approvers || []" :key="a.id" class="person-chip">
            <AuthImage :src="a.avatar_url" :alt="a.display_name" :size="24" />
            <span>{{ a.display_name }}</span>
          </span>
          <span v-if="!(step.approvers || []).length" class="muted">—</span>
        </div>
        <div v-for="(action, index) in step.actions" :key="index" class="list-item">
          <div class="row">
            <AuthImage :src="action.actor_avatar_url" :alt="action.actor_label" :size="24" />
            <b>{{ action.actor_label }}</b>
            <el-tag size="small" :type="action.action === 'REJECT' ? 'danger' : 'success'">
              {{ textOf(APPROVAL_ACTION_LABELS, action.action) }}
            </el-tag>
            <span class="muted">{{ formatDateTime(action.acted_at) }}</span>
          </div>
          <p v-if="action.comment" class="muted">备注：{{ action.comment }}</p>
        </div>
      </div>
      <p v-if="!timeline.steps.length" class="muted">该审批为半数以上参与者同意模式，请在决议详情查看投票结果。</p>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { approvalApi } from '@/shared/api'
import { errorText, formatDateTime } from '@/shared/format'
import { APPROVAL_ACTION_LABELS, APPROVAL_STATUS_LABELS, STEP_STATUS_LABELS, STEP_STRATEGY_LABELS, textOf } from '@/shared/labels'
import AuthImage from './parts/AuthImage.vue'

const props = defineProps({ instanceId: { type: Number, required: true } })
const timeline = ref(null)
const loading = ref(false)
const error = ref('')
const submitterName = computed(() => timeline.value?.submitter?.display_name || timeline.value?.submitter_label || '—')

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

<style scoped>
.person-row { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.person-chip { display: inline-flex; align-items: center; gap: 6px; }
</style>
