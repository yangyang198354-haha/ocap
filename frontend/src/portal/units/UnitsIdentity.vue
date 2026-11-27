<!-- MOD-136 / MOD-176：我的身份与房屋；身份与房屋 / 待我审批。 -->
<template>
  <div class="business-page housing-identity">
    <PageHead title="我的身份与房屋" description="查看认证身份、关联房屋与同住人申请" />

    <el-tabs v-model="tab" class="housing-tabs">
      <el-tab-pane label="我的身份与房屋" name="identity">
        <div v-if="housingError" class="card business-panel row">
          <span class="muted">加载失败，请重试</span>
          <el-button link size="small" @click="loadHousing">重试</el-button>
        </div>
        <template v-else>
          <section class="card business-panel business-summary business-enter housing-summary" aria-label="身份信息">
            <dl class="housing-field summary-identity">
              <dt>汇总身份：</dt><dd><el-tag class="summary-tag" size="large">{{ housing.summary.label }}</el-tag></dd>
            </dl>
            <dl class="housing-field real-names"><dt>真实姓名：</dt><dd>{{ (housing.real_names || []).join('、') || '—' }}</dd></dl>
            <el-button class="housing-certify" type="primary" @click="goPick">认证产权</el-button>
          </section>

          <section v-if="housing.units.length" aria-labelledby="linked-housing-title">
            <h2 id="linked-housing-title" class="title housing-section-title">已关联房屋（{{ housing.units.length }}）</h2>
            <div class="housing-grid">
              <article v-for="unit in housing.units" :key="unit.unit_id" class="card business-panel housing-property">
                <header class="housing-property-head">
                  <div class="housing-property-title">
                    <h3 class="title title-flat">{{ unit.specific_part }}</h3>
                    <div class="muted housing-property-meta">
                      <span>{{ unit.unit_type_label }}</span>
                      <span>{{ unit.area_display }}</span>
                    </div>
                  </div>
                  <el-tag class="housing-role" type="info">{{ unit.role_label }}</el-tag>
                </header>

                <div class="housing-property-details">
                  <p class="muted co-owners">共有产权人：{{ (unit.co_owners || []).length ? unit.co_owners.join('、') : '无' }}</p>
                  <div v-if="isOwner(unit)">
                    <p class="muted">同住人：{{ unit.residents.length ? '' : '暂无' }}</p>
                    <div v-for="r in unit.residents" :key="r.user_id" class="housing-resident row">
                      <span class="muted">实名：{{ r.real_name || '—' }}</span>
                      <router-link v-if="r.user_id" :to="'/users/' + r.user_id + '/profile'">{{ r.nickname || r.account_no }}（{{ r.account_no }}）</router-link>
                      <span v-else>{{ r.nickname || r.account_no }}（{{ r.account_no }}）</span>
                      <span class="muted">加入于 {{ formatDateTime(r.joined_at) }}</span>
                      <el-button type="danger" size="small" @click="removeResident(unit, r)">移除</el-button>
                    </div>
                  </div>
                  <el-button type="danger" v-if="unit.role === 'RESIDENT'" size="small" @click="leave(unit)">退出</el-button>
                </div>
              </article>
            </div>
          </section>
          <div v-else class="card business-panel housing-empty">
            <h2 class="title">暂无已认证房屋</h2>
            <p class="muted">
              您还没有认证任何专有部分，请先认证产权
              <el-button type="primary" link @click="goPick">认证产权</el-button>
            </p>
          </div>
        </template>
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
.housing-tabs :deep(.el-tabs__header) { margin-bottom: 20px; }
.housing-tabs :deep(.el-tabs__nav-wrap::after), .housing-tabs :deep(.el-tabs__active-bar) { display: none; }
.housing-tabs :deep(.el-tabs__item) {
  position: relative;
  height: auto;
  min-height: var(--hit-min);
  padding: 8px 14px !important;
  border-radius: var(--radius-btn);
  font-size: var(--text-nav-primary);
  line-height: var(--leading-nav-primary);
  color: var(--muted);
}
.housing-tabs :deep(.el-tabs__item.is-active) {
  background: var(--surface);
  color: var(--accent-text);
}
.housing-tabs :deep(.el-tabs__item.is-active::after) {
  content: "";
  position: absolute;
  inset: auto 14px 0;
  height: 2px;
  border-radius: 2px;
  background: var(--accent);
}
.review-tab-label { display: inline-flex; align-items: center; gap: 8px; }
.housing-summary {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr) auto;
  gap: 14px 20px;
  align-items: center;
  margin-bottom: 22px;
}
.housing-field { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 8px; margin: 0; }
.housing-field dt { color: var(--muted); }
.housing-field dd { min-width: 0; margin: 0; font-weight: 650; overflow-wrap: anywhere; }
.housing-certify { min-height: var(--hit-min); }
.housing-section-title { margin-block: 0 12px; }
.housing-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.housing-property {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 22px;
  min-height: 180px;
  margin-bottom: 0;
}
.housing-property-head { display: flex; flex-wrap: wrap; align-items: flex-start; justify-content: space-between; gap: 8px 12px; }
.housing-property-title { min-width: 0; overflow-wrap: anywhere; }
.housing-property-meta { display: flex; flex-wrap: wrap; gap: 4px 10px; margin-top: 4px; font-variant-numeric: tabular-nums; }
.housing-property-details { display: grid; gap: 6px; overflow-wrap: anywhere; }
.housing-property-details p, .housing-empty p { margin: 0; }
.housing-property-details > .el-button { justify-self: start; }
.housing-resident { gap: 4px 10px; margin-top: 6px; }
@media (max-width: 767.98px) {
  .housing-grid, .housing-summary { grid-template-columns: minmax(0, 1fr); }
  .housing-certify { justify-self: start; }
  .housing-property { min-height: 0; gap: 14px; }
}
</style>
