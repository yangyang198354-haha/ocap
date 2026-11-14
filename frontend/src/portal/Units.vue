<template>
  <div class="page">
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

    <div id="review" class="card">
      <h3 class="title">待我审批的同住人申请 <el-badge v-if="toReview.length" :value="toReview.length" /></h3>
      <p v-if="!toReview.length" class="muted">暂无待审批的同住人申请</p>
      <div v-for="item in toReview" :key="item.id" class="row list-item-top">
        <span>{{ item.applicant?.nickname || item.applicant?.account_no }} → {{ item.unit?.specific_part }}</span>
        <span class="muted">{{ formatDateTime(item.created_at) }}</span>
        <el-button size="small" type="primary" @click="decideResident(item.id, 'APPROVE')">通过</el-button>
        <el-button size="small" @click="decideResident(item.id, 'REJECT')">拒绝</el-button>
      </div>
    </div>

    <div class="card">
      <h3 class="title">选择房屋</h3>
      <p class="muted">逐级选择你的专有部分，再选择下面的操作。</p>
      <UnitCascader v-model="pickedUnitId" />
      <div class="row" style="margin-top: 10px">
        <el-button type="primary" :disabled="!pickedUnitId" @click="certify">认证产权</el-button>
        <el-button :disabled="!pickedUnitId" @click="applyResident">申请成为同住人</el-button>
      </div>
      <p class="muted">清册登记手机号与当前手机号一致时可立即认证为产权业主；首位认证者为户主。若该户未登记你的手机号，请改用下方产权申诉。同住人须先有产权业主，由产权业主审批。</p>
    </div>

    <div class="card">
      <h3 class="title">认证申诉</h3>
      <p class="muted">清册手机号与当前手机号不一致时，可上传产权证明提交申诉，由管理员审核。</p>
      <div class="row" style="margin-top: 10px">
        <el-upload :show-file-list="false" :http-request="uploadProof" accept="image/*">
          <el-button>上传产权证明</el-button>
        </el-upload>
        <span class="muted" v-if="appeal.attachmentId">已上传</span>
        <el-button type="primary" :disabled="!pickedUnitId" @click="submitAppeal">提交申诉</el-button>
      </div>
    </div>

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
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { attachmentApi, meApi, unitApi } from '@/shared/api'
import { errorText, formatDateTime } from '@/shared/format'
import { confirmDanger } from '@/shared/confirm'
import { ROLE_LABELS, statusLabel } from '@/shared/labels'
import { useAuthStore } from '@/stores/auth'
import UnitCascader from './parts/UnitCascader.vue'

const auth = useAuthStore()
const pickedUnitId = ref(null)
const appeal = reactive({ attachmentId: null })
const housing = reactive({ summary: { code: 'GUEST', label: '游客' }, units: [], pending_review_count: 0 })
const toReview = ref([])
const myApplications = ref([])
const myAppeals = ref([])

const isOwner = (unit) => unit.role === 'HEAD' || unit.role === 'OWNER'

async function loadHousing() {
  try {
    Object.assign(housing, await meApi.housing())
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function loadLists() {
  try {
    const [review, applications, appeals] = await Promise.all([
      unitApi.residentApplicationsToReview(),
      unitApi.myResidentApplications(),
      unitApi.myAppeals()
    ])
    toReview.value = review.results || review || []
    myApplications.value = applications.results || applications || []
    myAppeals.value = appeals.results || appeals || []
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function refresh() {
  await Promise.all([loadHousing(), loadLists()])
}

async function certify() {
  try {
    const result = await unitApi.certify(pickedUnitId.value)
    ElMessage.success(`认证成功，身份：${ROLE_LABELS[result.role] || result.role}`)
    await auth.fetchMe()
    await refresh()
  } catch (e) {
    if (e?.code === 'PHONE_NOT_IN_REGISTRY') {
      ElMessage.warning('手机号与清册不一致，可提交产权申诉')
      return
    }
    ElMessage.error(errorText(e))
  }
}

async function uploadProof({ file }) {
  try {
    const uploaded = await attachmentApi.upload(file, 'APPEAL_PROOF')
    appeal.attachmentId = uploaded.id
    ElMessage.success('已上传')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function submitAppeal() {
  try {
    if (!appeal.attachmentId) return ElMessage.warning('请先上传产权证明')
    await unitApi.createAppeal({ unit_id: pickedUnitId.value, proof_ids: [appeal.attachmentId] })
    ElMessage.success('申诉已提交，等待管理员审核')
    await loadLists()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function applyResident() {
  try {
    await unitApi.createResidentApplication({ unit_id: pickedUnitId.value })
    ElMessage.success('申请已提交，等待产权业主审批')
    await loadLists()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function decideResident(id, action) {
  try {
    await unitApi.decideResidentApplication(id, action)
    ElMessage.success('已处理')
    await refresh()
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
    await refresh()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(async () => {
  await refresh()
  if (window.location.hash === '#review') document.getElementById('review')?.scrollIntoView?.()
})
</script>
