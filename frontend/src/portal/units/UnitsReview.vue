<!-- MOD-123：待我审批的同住人申请（自 Units.vue 原 26-35、207-215 行迁移） -->
<template>
  <div id="review" class="card">
    <h3 class="title">待我审批的同住人申请 <el-badge v-if="toReview.length" :value="toReview.length" /></h3>
    <p v-if="!toReview.length" class="muted">暂无待审批的同住人申请</p>
    <div v-for="item in toReview" :key="item.id" class="row list-item-top">
      <span>
        <router-link v-if="item.applicant?.id" :to="`/users/${item.applicant.id}/profile`">{{ item.applicant?.nickname || item.applicant?.account_no }}</router-link>
        <template v-else>{{ item.applicant?.nickname || item.applicant?.account_no }}</template>
        → {{ item.unit?.specific_part }}
      </span>
      <span class="muted">{{ formatDateTime(item.created_at) }}</span>
      <el-button size="small" type="primary" @click="decideResident(item.id, 'APPROVE')">通过</el-button>
      <el-button size="small" @click="decideResident(item.id, 'REJECT')">拒绝</el-button>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { unitApi } from '@/shared/api'
import { errorText, formatDateTime } from '@/shared/format'
import { useHousingStore } from '@/stores/housing'

const store = useHousingStore()
const { toReview } = storeToRefs(store)

async function decideResident(id, action) {
  try {
    await unitApi.decideResidentApplication(id, action)
    ElMessage.success('已处理')
    // 通过 refresh 同步更新侧栏角标（AC-214-03）
    await store.refresh()
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
