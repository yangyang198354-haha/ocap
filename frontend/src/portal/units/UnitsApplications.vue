<!-- MOD-137：我的同住人申请（上方为发起区，ADR-134、Q-IP-18=A；下方为本人已提交的申请列表） -->
<template>
  <div class="card">
    <h3 class="title">我的同住人申请</h3>
    <p class="muted">申请成为同住人无需输入姓名，同住人须先有产权业主，由产权业主审批。</p>
    <UnitCascader v-model="pickedUnitId" />
    <div class="row" style="margin-top: 10px">
      <el-button type="primary" :disabled="!pickedUnitId" @click="applyResident">申请成为同住人</el-button>
    </div>
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
import { onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { errorText, formatDateTime } from '@/shared/format'
import { statusLabel } from '@/shared/labels'
import { unitApi } from '@/shared/api'
import { useHousingStore } from '@/stores/housing'
import UnitCascader from '../parts/UnitCascader.vue'

const store = useHousingStore()
const { myApplications } = storeToRefs(store)
const pickedUnitId = ref(null)

async function applyResident() {
  try {
    await unitApi.createResidentApplication({ unit_id: pickedUnitId.value })
    ElMessage.success('申请已提交，等待产权业主审批')
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
