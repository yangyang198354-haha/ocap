<!-- MOD-171 / IFC-392c：我的同住申请记录；字段与申诉记录一致，支持撤回与重新提交 -->
<template>
  <div>
    <p v-if="!myApplications.length" class="muted">暂无同住人申请</p>
    <div v-for="item in myApplications" :key="item.id" class="list-item-top">
      <div class="row">
        <span>{{ item.unit?.specific_part }}</span>
        <span class="muted">实名：{{ item.applicant_name || '—' }}</span>
        <el-tag size="small">{{ statusLabel('application', item.status) }}</el-tag>
        <span class="muted">提交 {{ formatDateTime(item.created_at) }}</span>
        <span v-if="item.decided_at" class="muted">处理 {{ formatDateTime(item.decided_at) }}</span>
        <span v-if="item.withdrawn_at" class="muted">撤回 {{ formatDateTime(item.withdrawn_at) }}</span>
        <el-button v-if="item.status === 'PENDING'" size="small" @click="withdraw(item)">撤回</el-button>
        <el-button v-if="item.status === 'WITHDRAWN'" size="small" type="primary" @click="$emit('resubmit', item)">
          重新提交
        </el-button>
      </div>
      <p v-if="item.previous_application_id" class="muted">重新提交自 #{{ item.previous_application_id }}</p>
      <template v-if="item.status === 'APPROVED' || item.status === 'REJECTED'">
        <p class="muted">处理结果：{{ statusLabel('application', item.status) }}</p>
        <p class="muted">处理备注：{{ item.decision_note || '—' }}</p>
      </template>
      <p v-if="item.status === 'REJECTED' && item.reject_reason" class="muted">驳回原因：{{ item.reject_reason }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage, ElMessageBox } from 'element-plus'
import { errorText, formatDateTime } from '@/shared/format'
import { statusLabel } from '@/shared/labels'
import { unitApi } from '@/shared/api'
import { useHousingStore } from '@/stores/housing'

defineEmits(['resubmit'])

const store = useHousingStore()
const { myApplications } = storeToRefs(store)

async function withdraw(item) {
  try {
    await ElMessageBox.confirm('撤回后该申请不可恢复，可修改信息后重新提交。确认撤回？', '撤回申请',
      { confirmButtonText: '撤回', cancelButtonText: '取消', type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await unitApi.withdrawResidentApplication(item.id)
    ElMessage.success('已撤回')
    await store.loadLists()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(async () => {
  try {
    await store.loadLists()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
})
</script>
