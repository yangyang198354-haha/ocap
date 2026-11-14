<template>
  <ThemeRoot>
  <view>
    <view class="card">
      <view class="title">我的身份与房屋</view>
      <view class="muted">汇总身份：{{ housing.summary.label }}</view>
      <view v-if="!housing.units.length" class="muted">暂无已认证房屋</view>
      <view v-for="unit in housing.units" :key="unit.unit_id" class="list-item">
        <view class="row">
          <text>{{ unit.specific_part }}</text>
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
    </view>
    <view class="card" id="review">
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
    <view class="card">
      <view class="title">选择房屋</view>
      <UnitPicker v-model="pickedUnitId" />
      <button class="btn" style="margin-top: 20rpx" @click="certify">认证</button>
      <button style="margin-top: 16rpx" @click="applyResident">申请成为同住人</button>
      <view class="muted">微信登录且未绑定手机号时，请先到“我的 → 绑定/更换手机号”完成绑定。同住人须先有产权业主，由产权业主审批。</view>
    </view>
    <view class="card">
      <view class="title">认证申诉</view>
      <view class="muted">清册手机号与当前手机号不一致时，上传产权证明提交申诉，由管理员审核。</view>
      <button style="margin-top: 16rpx" @click="chooseProof">{{ proofId ? '已上传，重新选择' : '上传产权证明' }}</button>
      <button style="margin-top: 16rpx" @click="submitAppeal">提交申诉</button>
    </view>
    <view class="card">
      <view class="title">我的同住人申请</view>
      <view v-if="!myApplications.length" class="muted">暂无同住人申请</view>
      <view v-for="item in myApplications" :key="item.id" class="list-item">
        <text>{{ item.unit?.specific_part }}</text>
        <text class="muted" style="margin-left: 12rpx">{{ statusLabel('application', item.status) }}</text>
        <view class="muted">提交 {{ formatDateTime(item.created_at) }}<text v-if="item.decided_at"> · 处理 {{ formatDateTime(item.decided_at) }}</text></view>
      </view>
    </view>
    <view class="card">
      <view class="title">我的申诉</view>
      <view v-if="!myAppeals.length" class="muted">暂无申诉</view>
      <view v-for="item in myAppeals" :key="item.id" class="list-item">
        <text>{{ item.unit?.specific_part }}</text>
        <text class="muted" style="margin-left: 12rpx">{{ statusLabel('appeal', item.status) }}</text>
        <view class="muted">提交 {{ formatDateTime(item.submitted_at) }}<text v-if="item.decided_at"> · 处理 {{ formatDateTime(item.decided_at) }}</text></view>
        <view v-if="item.status === 'REJECTED' && item.reject_reason" class="muted">驳回原因：{{ item.reject_reason }}</view>
      </view>
    </view>
  </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import UnitPicker from '@/components/UnitPicker.vue'
import { reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '@/utils/api'
import { confirmDanger } from '@/utils/confirm'
import { ROLE_LABELS, formatDateTime, statusLabel } from '@/utils/labels'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const pickedUnitId = ref(null)
const proofId = ref('')
const housing = reactive({ summary: { code: 'GUEST', label: '游客' }, units: [], pending_review_count: 0 })
const toReview = ref([])
const myApplications = ref([])
const myAppeals = ref([])

const isOwner = (unit) => unit.role === 'HEAD' || unit.role === 'OWNER'

function toast(title) {
  uni.showToast({ title, icon: 'none' })
}

const listOf = (data) => data?.results || data || []

async function loadHousing() {
  try {
    Object.assign(housing, await api.housing())
  } catch (e) {
    toast(e.message)
  }
}

async function loadLists() {
  try {
    const [review, applications, appeals] = await Promise.all([
      api.residentApplicationsToReview(), api.myResidentApplications(), api.myAppeals()
    ])
    toReview.value = listOf(review)
    myApplications.value = listOf(applications)
    myAppeals.value = listOf(appeals)
  } catch (e) {
    toast(e.message)
  }
}

async function refresh() {
  await Promise.all([loadHousing(), loadLists()])
}

async function certify() {
  if (!pickedUnitId.value) return toast('请先选择房号')
  try {
    const result = await api.certify(pickedUnitId.value)
    toast(`认证成功，身份：${ROLE_LABELS[result.role] || result.role}`)
    await auth.fetchMe()
    await refresh()
  } catch (e) {
    if (e?.code === 'PHONE_NOT_IN_REGISTRY') {
      return toast('手机号与清册不一致，可提交产权申诉')
    }
    toast(e.message)
  }
}

async function applyResident() {
  if (!pickedUnitId.value) return toast('请先选择房号')
  try {
    await api.createResidentApplication({ unit_id: pickedUnitId.value })
    toast('申请已提交，等待产权业主审批')
    await loadLists()
  } catch (e) {
    toast(e.message)
  }
}

async function decideResident(id, decision) {
  try {
    await api.decideResidentApplication(id, decision)
    toast('已处理')
    await refresh()
  } catch (e) {
    toast(e.message)
  }
}

async function removeResident(unit, resident) {
  if (!(await confirmDanger('removeResident', { name: resident.nickname || resident.account_no }))) return
  try {
    await api.removeResident(unit.unit_id, resident.user_id)
    toast('已移除')
    await loadHousing()
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
    await refresh()
  } catch (e) {
    toast(e.message)
  }
}

function chooseProof() {
  uni.chooseImage({
    count: 1,
    success: async ({ tempFilePaths }) => {
      try {
        const uploaded = await api.upload(tempFilePaths[0], 'APPEAL_PROOF')
        proofId.value = uploaded.id
        toast('已上传')
      } catch (e) {
        toast(e.message)
      }
    }
  })
}

async function submitAppeal() {
  if (!pickedUnitId.value) return toast('请先选择房号')
  if (!proofId.value) return toast('请先上传产权证明')
  try {
    await api.createAppeal({ unit_id: pickedUnitId.value, proof_ids: [proofId.value] })
    toast('申诉已提交')
    await loadLists()
  } catch (e) {
    toast(e.message)
  }
}

onShow(refresh)
</script>
