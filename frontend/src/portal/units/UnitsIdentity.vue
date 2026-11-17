<!-- MOD-123：我的身份与房屋（自 Units.vue 原 3-24、217-238 行迁移，逻辑不变） -->
<template>
  <div class="card">
    <h3 class="title">我的身份与房屋</h3>
    <p>
      汇总身份：<el-tag>{{ housing.summary.label }}</el-tag>
    </p>
    <p v-if="!housing.units.length" class="muted">暂无已认证房屋</p>
    <div v-for="unit in housing.units" :key="unit.unit_id" class="list-item-top">
      <div class="row">
        <strong>{{ unit.specific_part }}</strong>
        <el-tag size="small" type="info">{{ unit.role_label }}</el-tag>
        <el-button v-if="unit.role === 'RESIDENT'" size="small" @click="leave(unit)">退出</el-button>
      </div>
      <div v-if="isOwner(unit)">
        <p class="muted">同住人：{{ unit.residents.length ? '' : '暂无' }}</p>
        <div v-for="r in unit.residents" :key="r.user_id" class="row">
          <span>{{ r.nickname || r.account_no }}（{{ r.account_no }}）</span>
          <span class="muted">加入于 {{ formatDateTime(r.joined_at) }}</span>
          <el-button size="small" @click="removeResident(unit, r)">移除</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { unitApi } from '@/shared/api'
import { errorText, formatDateTime } from '@/shared/format'
import { confirmDanger } from '@/shared/confirm'
import { useAuthStore } from '@/stores/auth'
import { useHousingStore } from '@/stores/housing'

const auth = useAuthStore()
const store = useHousingStore()
const { housing } = storeToRefs(store)

const isOwner = (unit) => unit.role === 'HEAD' || unit.role === 'OWNER'

async function loadHousing() {
  try {
    await store.loadHousing()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function removeResident(unit, resident) {
  if (!(await confirmDanger('removeResident', { name: resident.nickname || resident.account_no }))) return
  try {
    await unitApi.removeResident(unit.unit_id, resident.user_id)
    ElMessage.success('已移除')
    await loadHousing()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function leave(unit) {
  if (!(await confirmDanger('leaveUnit', { name: unit.specific_part }))) return
  try {
    await unitApi.leaveUnit(unit.unit_id)
    ElMessage.success('已退出')
    await auth.fetchMe()
    await store.refresh()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(loadHousing)
</script>
