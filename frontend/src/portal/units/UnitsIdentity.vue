<!-- MOD-136：我的身份与房屋（/units 与 /me/identity 同页，ADR-132；底部嵌入"待我审批的同住人申请"，ADR-133） -->
<template>
  <div>
    <div class="card">
      <h3 class="title">我的身份与房屋</h3>
      <div v-if="housingError" class="row">
        <span class="muted">加载失败，请重试</span>
        <el-button size="small" @click="loadHousing">重试</el-button>
      </div>
      <template v-else>
        <div class="row">
          <span>汇总身份：<el-tag>{{ housing.summary.label }}</el-tag></span>
        </div>
        <p v-if="!housing.units.length" class="muted">暂无已认证房屋</p>
        <p v-if="!housing.units.length" class="muted">
          您还没有认证任何专有部分，请先认证产权
          <el-button type="primary" link @click="goPick">认证产权</el-button>
        </p>
        <div v-for="unit in housing.units" :key="unit.unit_id" class="list-item-top">
          <div class="row">
            <strong>{{ unit.specific_part }}</strong>
            <span class="muted">{{ unit.unit_type_label }}</span>
            <span class="muted">{{ unit.area_display }}</span>
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
      </template>
      <div class="row" style="margin-top: 10px">
        <el-button type="primary" @click="goPick">认证产权</el-button>
      </div>
    </div>
    <div v-if="ownsAnyUnit" style="margin-top: 16px">
      <UnitsReview />
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { unitApi } from '@/shared/api'
import { errorText, formatDateTime } from '@/shared/format'
import { confirmDanger } from '@/shared/confirm'
import { useAuthStore } from '@/stores/auth'
import { useHousingStore } from '@/stores/housing'
import UnitsReview from './UnitsReview.vue'

const auth = useAuthStore()
const store = useHousingStore()
const route = useRoute()
const router = useRouter()
const { housing, housingError, ownsAnyUnit } = storeToRefs(store)

const isOwner = (unit) => unit.role === 'HEAD' || unit.role === 'OWNER'
const goPick = () => router.push('/units/pick')

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

onMounted(async () => {
  await loadHousing()
  // 旧地址 /units#review、/units/review：数据加载后定位到底部卡片（无卡片时不动；jsdom 无 scrollIntoView，须容错）
  if (route?.hash === '#review') {
    await nextTick()
    document.getElementById('review')?.scrollIntoView?.()
  }
})
</script>
