<!-- MOD-136 / MOD-176：我的身份与房屋；页内双 Tab（身份与房屋 / 待我审批），复用 UnitsReview（ADR-167） -->
<template>
  <div>
    <PageHead title="我的身份与房屋" />
    <div class="card">
      <el-tabs v-model="tab">
        <el-tab-pane label="我的身份与房屋" name="identity">
          <div v-if="housingError" class="row">
            <span class="muted">加载失败，请重试</span>
            <el-button size="small" @click="loadHousing">重试</el-button>
          </div>
          <template v-else>
            <div class="row summary-row">
              <span class="summary-identity">汇总身份：<el-tag size="large" class="summary-tag">{{ housing.summary.label }}</el-tag></span>
              <span class="real-names">真实姓名：{{ (housing.real_names || []).join('、') || '—' }}</span>
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
              <p class="muted co-owners">共有产权人：{{ (unit.co_owners || []).length ? unit.co_owners.join('、') : '无' }}</p>
              <div v-if="isOwner(unit)">
                <p class="muted">同住人：{{ unit.residents.length ? '' : '暂无' }}</p>
                <div v-for="r in unit.residents" :key="r.user_id" class="row">
                  <span class="muted">实名：{{ r.real_name || '—' }}</span>
                  <router-link v-if="r.user_id" :to="`/users/${r.user_id}/profile`">{{ r.nickname || r.account_no }}（{{ r.account_no }}）</router-link>
                  <span v-else>{{ r.nickname || r.account_no }}（{{ r.account_no }}）</span>
                  <span class="muted">加入于 {{ formatDateTime(r.joined_at) }}</span>
                  <el-button size="small" @click="removeResident(unit, r)">移除</el-button>
                </div>
              </div>
            </div>
          </template>
          <div class="row" style="margin-top: 10px">
            <el-button type="primary" @click="goPick">认证产权</el-button>
          </div>
        </el-tab-pane>
        <el-tab-pane v-if="ownsAnyUnit" name="review">
          <template #label>
            <span class="review-tab-label">
              待我审批的同住人申请
              <el-badge v-if="pendingReviewCount" :value="pendingReviewCount" />
            </span>
          </template>
          <UnitsReview />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import PageHead from '@/shared/PageHead.vue'
import { onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { unitApi } from '@/shared/api'
import { errorText, formatDateTime } from '@/shared/format'
import { confirmDanger } from '@/shared/confirm'
import { useAuthStore } from '@/stores/auth'
import { useHousingStore } from '@/stores/housing'
import UnitsReview from './UnitsReview.vue'

const props = defineProps({ initialTab: { type: String, default: 'identity' } })
const auth = useAuthStore()
const store = useHousingStore()
const route = useRoute()
const router = useRouter()
const { housing, housingError, ownsAnyUnit, pendingReviewCount } = storeToRefs(store)
const tab = ref('identity')

const isOwner = (unit) => unit.role === 'HEAD' || unit.role === 'OWNER'
const goPick = () => router.push('/units/pick')

// AC-306-02：深链 /units/review（query.tab=review）或旧 hash #review 落到待审批 Tab；
// 非产权业主不存在该 Tab，回落默认（AC-300-03）。
async function applyInitialTab() {
  const wantsReview = props.initialTab === 'review' || route?.hash === '#review'
  if (wantsReview) {
    tab.value = ownsAnyUnit.value ? 'review' : 'identity'
    return
  }
  // 深链从 review 切回身份页（同一组件实例复用时）需显式回到默认 Tab
  if (props.initialTab === 'identity') tab.value = 'identity'
}

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

watch(() => props.initialTab, applyInitialTab)
watch(ownsAnyUnit, applyInitialTab)

onMounted(async () => {
  await loadHousing()
  await applyInitialTab()
})
</script>

<style scoped>
.summary-row { align-items: baseline; }
.summary-identity { font-size: 16px; }
.summary-tag { font-size: 15px; padding: 0 12px; }
.review-tab-label { display: inline-flex; align-items: center; gap: 8px; }
</style>
