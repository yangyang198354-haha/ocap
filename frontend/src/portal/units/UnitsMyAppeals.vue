<!-- MOD-170 / IFC-392b：我的申诉记录；展示处理结果/备注/驳回原因，支持撤回与重新提交 -->
<template>
  <div>
    <p v-if="!myAppeals.length" class="muted">暂无申诉</p>
    <div v-for="item in myAppeals" :key="item.id" class="list-item-top">
      <div class="row">
        <span>{{ item.unit?.specific_part }}</span>
        <el-tag size="small">{{ statusLabel('appeal', item.status) }}</el-tag>
        <span class="muted">提交 {{ formatDateTime(item.submitted_at) }}</span>
        <span v-if="item.decided_at" class="muted">处理 {{ formatDateTime(item.decided_at) }}</span>
        <span v-if="item.withdrawn_at" class="muted">撤回 {{ formatDateTime(item.withdrawn_at) }}</span>
        <el-button v-if="item.status === 'PENDING'" size="small" @click="withdraw(item)">撤回</el-button>
        <el-button v-if="item.status === 'WITHDRAWN'" size="small" type="primary" @click="$emit('resubmit', item)">
          重新提交
        </el-button>
      </div>
      <p v-if="item.previous_appeal_id" class="muted">重新提交自 #{{ item.previous_appeal_id }}</p>
      <template v-if="item.status === 'APPROVED' || item.status === 'REJECTED'">
        <p class="muted">处理结果：{{ statusLabel('appeal', item.status) }}</p>
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
const { myAppeals } = storeToRefs(store)

async function withdraw(item) {
  try {
    await ElMessageBox.confirm('撤回后该申诉不可恢复，可修改信息后重新提交。确认撤回？', '撤回申诉',
      { confirmButtonText: '撤回', cancelButtonText: '取消', type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await unitApi.withdrawAppeal(item.id)
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
