<!-- MOD-179 / IFC-398：小程序“我的身份与房屋”面板；内含“身份与房屋/待我审批”子 Tab（ADR-169） -->
<template>
  <view>
    <view v-if="subTabs.length > 1" class="sub-tabs">
      <view
        v-for="st in subTabs"
        :key="st.key"
        class="sub-tab"
        :class="{ 'is-active': subTab === st.key }"
        @click="subTab = st.key"
      >
        {{ st.label }}<text v-if="st.count">（{{ st.count }}）</text>
      </view>
    </view>

    <view v-show="subTab === 'identity'">
      <view class="card">
        <view class="title">我的身份与房屋</view>
        <view class="muted">汇总身份：{{ housing.summary.label }}</view>
        <view v-if="!housing.units.length" class="muted">暂无已认证房屋</view>
        <view v-if="!housing.units.length" class="muted">您还没有认证任何专有部分，请先认证产权</view>
        <view v-for="unit in housing.units" :key="unit.unit_id" class="list-item">
          <view class="row">
            <text>{{ unit.specific_part }}</text>
            <text class="muted" style="margin-left: 12rpx">{{ unit.unit_type_label }} · {{ unit.area_display }}</text>
            <text class="muted" style="margin-left: 12rpx">{{ unit.role_label }}</text>
            <button v-if="unit.role === 'RESIDENT'" size="mini" style="margin-left: 12rpx" @click="leave(unit)">退出</button>
          </view>
          <view v-if="isOwner(unit)">
            <view class="muted">同住人：{{ unit.residents.length ? '' : '暂无' }}</view>
            <view v-for="r in unit.residents" :key="r.user_id" class="row" style="margin-top: 8rpx">
              <text>{{ r.nickname || r.account_no }}（{{ r.account_no }}）</text>
              <button size="mini" style="margin-left: 12rpx" @click="removeResident(unit, r)">移除</button>
            </view>
          </view>
        </view>
        <button class="btn" style="margin-top: 16rpx" @click="goCertify">认证产权</button>
      </view>

      <view class="card" id="certify">
        <view class="title">认证产权</view>
        <UnitPicker v-model="pickedUnitId" />
        <input v-model="certifyName" class="field mt-16" maxlength="64" placeholder="请输入您本人的姓名（须与业主清册登记的姓名一致）" />
        <button class="btn" style="margin-top: 20rpx" @click="certify">认证</button>
        <view class="muted">您本人的姓名与当前手机号和清册登记的同一位业主一致时可立即认证；不一致或没有手机号时，请在下方输入产权人名字并上传产权证明提交申诉。如需申请成为同住人，请使用"我的同住人申请"。</view>
      </view>
    </view>

    <view v-if="ownsAnyUnit" v-show="subTab === 'review'" id="review" class="card">
      <view class="title">待我审批的同住人申请<text v-if="toReview.length" class="muted">（{{ toReview.length }}）</text></view>
      <view v-if="!toReview.length" class="muted">暂无待审批的同住人申请</view>
      <view v-for="item in toReview" :key="item.id" class="list-item">
        <text>{{ item.applicant?.nickname || item.applicant?.account_no }} → {{ item.unit?.specific_part }}</text>
        <text class="muted" style="margin-left: 12rpx">{{ formatDateTime(item.created_at) }}</text>
        <view class="row" style="margin-top: 8rpx">
          <button size="mini" @click="decideResident(item.id, 'APPROVE')">通过</button>
          <button size="mini" @click="decideResident(item.id, 'REJECT')">拒绝</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import UnitPicker from '@/components/UnitPicker.vue'
import { api } from '@/utils/api'
import { confirmDanger } from '@/utils/confirm'
import { ROLE_LABELS, formatDateTime } from '@/utils/labels'
import { useAuthStore } from '@/store/auth'

const props = defineProps({
  housing: { type: Object, required: true },
  ownsAnyUnit: { type: Boolean, default: false },
  initialReview: { type: Boolean, default: false }
})
const emit = defineEmits(['refresh', 'appeal'])

const auth = useAuthStore()
const pickedUnitId = ref(null)
const certifyName = ref('')
const toReview = ref([])
const subTab = ref('identity')

const isOwner = (unit) => unit.role === 'HEAD' || unit.role === 'OWNER'
const subTabs = computed(() => {
  const tabs = [{ key: 'identity', label: '身份与房屋' }]
  if (props.ownsAnyUnit) tabs.push({ key: 'review', label: '待我审批', count: toReview.value.length })
  return tabs
})

function toast(title) {
  uni.showToast({ title, icon: 'none' })
}

const listOf = (data) => data?.results || data || []

function goCertify() {
  subTab.value = 'identity'
  uni.pageScrollTo?.({ selector: '#certify' })
}

async function loadReview() {
  if (!props.ownsAnyUnit) return
  try {
    toReview.value = listOf(await api.residentApplicationsToReview())
  } catch (e) {
    toast(e.message)
  }
}

async function certify() {
  if (!pickedUnitId.value) return toast('请先选择房号')
  const name = certifyName.value.trim()
  if (!name) return toast('请输入姓名')
  try {
    const result = await api.certify(pickedUnitId.value, name)
    toast(`认证成功，身份：${ROLE_LABELS[result.role] || result.role}`)
    await auth.fetchMe()
    emit('refresh')
  } catch (e) {
    if (e?.code === 'OWNER_NOT_MATCHED') {
      // 保留姓名并进入“我的认证与申述”的申诉 Tab，提示不含任何清册信息
      toast('姓名与手机号未能通过核对，请上传产权证明提交申诉')
      emit('appeal', name)
      return
    }
    toast(e.message)
  }
}

async function decideResident(id, decision) {
  try {
    await api.decideResidentApplication(id, decision)
    toast('已处理')
    await loadReview()
    emit('refresh')
  } catch (e) {
    toast(e.message)
  }
}

async function removeResident(unit, resident) {
  if (!(await confirmDanger('removeResident', { name: resident.nickname || resident.account_no }))) return
  try {
    await api.removeResident(unit.unit_id, resident.user_id)
    toast('已移除')
    emit('refresh')
  } catch (e) {
    toast(e.message)
  }
}

async function leave(unit) {
  if (!(await confirmDanger('leaveUnit', { name: unit.specific_part }))) return
  try {
    await api.leaveUnit(unit.unit_id)
    toast('已退出')
    await auth.fetchMe()
    emit('refresh')
  } catch (e) {
    toast(e.message)
  }
}

function applyInitialReview() {
  if (props.initialReview && props.ownsAnyUnit) subTab.value = 'review'
  else if (!props.ownsAnyUnit && subTab.value === 'review') subTab.value = 'identity'
}

watch(() => props.initialReview, applyInitialReview)
watch(() => props.ownsAnyUnit, (owns) => {
  applyInitialReview()
  if (owns) loadReview()
})
onMounted(async () => {
  await loadReview()
  applyInitialReview()
})
</script>

<style scoped>
.sub-tabs { display: flex; gap: 8rpx; margin-bottom: 16rpx; }
.sub-tab {
  flex: 1; text-align: center; padding: 16rpx 0; font-size: 26rpx; color: var(--muted);
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-md);
}
.sub-tab.is-active { color: var(--accent-text); font-weight: 650; border-color: currentColor; }
</style>
