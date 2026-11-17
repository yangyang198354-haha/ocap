<!-- MOD-123：我的申诉（自 Units.vue 原 84-96 行迁移） -->
<template>
  <div class="card">
    <h3 class="title">我的申诉</h3>
    <p v-if="!myAppeals.length" class="muted">暂无申诉</p>
    <div v-for="item in myAppeals" :key="item.id" class="list-item-top">
      <div class="row">
        <span>{{ item.unit?.specific_part }}</span>
        <el-tag size="small">{{ statusLabel('appeal', item.status) }}</el-tag>
        <span class="muted">提交 {{ formatDateTime(item.submitted_at) }}</span>
        <span v-if="item.decided_at" class="muted">处理 {{ formatDateTime(item.decided_at) }}</span>
      </div>
      <p v-if="item.status === 'REJECTED' && item.reject_reason" class="muted">驳回原因：{{ item.reject_reason }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { errorText, formatDateTime } from '@/shared/format'
import { statusLabel } from '@/shared/labels'
import { useHousingStore } from '@/stores/housing'

const store = useHousingStore()
const { myAppeals } = storeToRefs(store)

onMounted(async () => {
  try {
    await store.loadLists()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
})
</script>
