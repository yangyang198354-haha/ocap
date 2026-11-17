<!-- MOD-123：我的同住人申请（自 Units.vue 原 73-82 行迁移） -->
<template>
  <div class="card">
    <h3 class="title">我的同住人申请</h3>
    <p v-if="!myApplications.length" class="muted">暂无同住人申请</p>
    <div v-for="item in myApplications" :key="item.id" class="row list-item-top">
      <span>{{ item.unit?.specific_part }}</span>
      <el-tag size="small">{{ statusLabel('application', item.status) }}</el-tag>
      <span class="muted">提交 {{ formatDateTime(item.created_at) }}</span>
      <span v-if="item.decided_at" class="muted">处理 {{ formatDateTime(item.decided_at) }}</span>
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
const { myApplications } = storeToRefs(store)

onMounted(async () => {
  try {
    await store.loadLists()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
})
</script>
