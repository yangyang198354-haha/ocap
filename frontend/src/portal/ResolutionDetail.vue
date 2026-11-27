<template>
  <div class="page">
    <div class="card" v-if="item">
      <PageHead :title="item ? item.title : '决议详情'" />
      <p class="muted">
        状态：<StatusTag :status="item.status" /> · 审批方式：{{ textOf(APPROVAL_MODE_TEXT, item.approval_mode) }}
        <span v-if="item.vote_deadline">· 表决截止：{{ formatDateTime(item.vote_deadline) }}</span>
      </p>
      <p style="white-space: pre-wrap">{{ item.content }}</p>
      <div class="row" v-if="item.attachments?.length">
        <el-link v-for="a in item.attachments" :key="a.id" :href="apiUrl(`/attachments/${a.id}/download`)" target="_blank">
          {{ a.name }}
        </el-link>
      </div>
      <div v-if="item.vote_counts" class="row" style="margin-top: 12px">
        <el-tag>同意 {{ item.vote_counts.agree }}</el-tag>
        <el-tag type="danger">反对 {{ item.vote_counts.disagree }}</el-tag>
        <el-tag type="info">弃权 {{ item.vote_counts.abstain }}</el-tag>
      </div>
      <div v-if="item.participation" class="participation-line mt-12">
        发起人：<router-link v-if="item.initiator?.id" :to="`/users/${item.initiator.id}/profile`">{{ item.initiator?.display_name }}</router-link><template v-else>{{ item.initiator?.display_name }}</template> · 已参与 {{ item.participation.voted }} / {{ item.participation.expected }}
      </div>
      <div class="mt-12">
        <ParticipantList :items="participants" :mode="item.approval_mode" />
      </div>
      <div class="row" v-if="item.approval_mode === 'HALF_MAJORITY' && item.status === 'PENDING' && auth.isCommittee" style="margin-top: 12px">
        <el-button type="success" @click="vote('AGREE')">同意</el-button>
        <el-button type="danger" @click="vote('DISAGREE')">反对</el-button>
        <el-button @click="vote('ABSTAIN')">弃权</el-button>
      </div>
      <div class="row" v-if="item.approval_instance_id" style="margin-top: 12px">
        <el-button size="small" @click="showTimeline = true">审批过程</el-button>
      </div>
      <div class="row" v-if="isInitiator" style="margin-top: 12px">
        <el-button type="danger" v-if="item.status === 'PENDING'" @click="withdraw">撤回</el-button>
        <el-button v-if="item.status === 'WITHDRAWN'" type="primary" @click="openResubmit">修改后重新提交</el-button>
        <el-button v-if="item.status === 'REJECTED'" type="primary" @click="newResolution">新建决议</el-button>
      </div>
      <p v-if="item.status === 'REJECTED'" class="muted">
        该决议已结束（{{ failReason }}），如需再次表决请新建决议。
      </p>
      <p v-if="item.origin_id" class="muted">
        重新发起自 <router-link :to="`/resolutions/${item.origin_id}`">{{ resNo(item.origin_id) }}</router-link>
      </p>
      <p v-if="item.reopened_by_id" class="muted">
        已由 <router-link :to="`/resolutions/${item.reopened_by_id}`">{{ resNo(item.reopened_by_id) }}</router-link> 重新发起
      </p>
    </div>
    <div class="card" v-else>
      <el-empty description="决议不存在或无权查看" />
    </div>

    <el-dialog v-model="showTimeline" title="审批过程" width="640px">
      <ApprovalTimeline v-if="item?.approval_instance_id" :instance-id="item.approval_instance_id" />
    </el-dialog>

    <el-dialog v-model="showResubmit" title="重新提交决议" width="560px">
      <el-input v-model="form.title" placeholder="标题" maxlength="200" />
      <el-input v-model="form.content" type="textarea" :rows="5" placeholder="内容" style="margin-top: 10px" />
      <el-select v-model="form.approval_flow_id" placeholder="审批流程" style="margin-top: 10px; width: 100%">
        <el-option v-for="f in flows" :key="f.id" :label="`${f.name}（${f.mode === 'HALF_MAJORITY' ? '半数以上参与者同意' : '指定负责人'}）`" :value="f.id" />
      </el-select>
      <el-date-picker
        v-if="needDeadline"
        v-model="form.vote_deadline"
        type="datetime"
        placeholder="表决截止时间（半数以上参与者同意必填）"
        style="margin-top: 10px; width: 100%"
      />
      <template #footer>
        <el-button @click="showResubmit = false">取消</el-button>
        <el-button type="primary" @click="resubmit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import PageHead from '@/shared/PageHead.vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { approvalApi, resolutionApi } from '@/shared/api'
import StatusTag from './StatusTag.vue'
import ApprovalTimeline from './ApprovalTimeline.vue'
import ParticipantList from './parts/ParticipantList.vue'
import { apiUrl } from '@/shared/http'
import { useAuthStore } from '@/stores/auth'
import { errorText, formatDateTime } from '@/shared/format'
import { APPROVAL_MODE_TEXT, textOf } from '@/shared/labels'
import { confirmDanger } from '@/shared/confirm'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const item = ref(null)
const participants = ref([])
const flows = ref([])
const showResubmit = ref(false)
const showTimeline = ref(false)
const form = reactive({ title: '', content: '', approval_flow_id: null, vote_deadline: null })

const isInitiator = computed(() => item.value && auth.me?.profile?.id === item.value.initiator?.id)
const needDeadline = computed(() => flows.value.find((f) => f.id === form.approval_flow_id)?.mode === 'HALF_MAJORITY')
// REQ-FUNC-275：失败原因区分“表决未过半 / 审批人拒绝”
const failReason = computed(() => (item.value?.approval_mode === 'HALF_MAJORITY' ? '表决未过半' : '审批人拒绝'))
const resNo = (id) => `R-${String(id).padStart(4, '0')}`

// REQ-FUNC-271：失败的决议只能新建，原单只读留痕
function newResolution() {
  router.push({ path: '/resolutions/mine', query: { origin: item.value.id } })
}

async function load() {
  try {
    item.value = await resolutionApi.detail(route.params.id)
  } catch (e) {
    ElMessage.error(errorText(e))
    return
  }
  await loadParticipants()
}

// 参与人列表（MOD-149）：失败不影响详情显示，按"暂无人参与"降级
async function loadParticipants() {
  participants.value = []
  if (item.value?.approval_mode !== 'HALF_MAJORITY') return
  try {
    const data = await resolutionApi.participants(route.params.id)
    participants.value = data?.results || []
  } catch (e) {
    participants.value = []
  }
}

async function vote(choice) {
  try {
    await resolutionApi.vote(route.params.id, choice)
    ElMessage.success('已提交意见')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function withdraw() {
  if (!(await confirmDanger('withdrawResolution'))) return
  try {
    await resolutionApi.withdraw(route.params.id)
    ElMessage.success('已撤回')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function openResubmit() {
  Object.assign(form, { title: item.value.title, content: item.value.content, approval_flow_id: null, vote_deadline: null })
  try {
    const data = await approvalApi.flows('RESOLUTION')
    flows.value = data.results || data || []
  } catch (e) {
    flows.value = []
  }
  showResubmit.value = true
}

async function resubmit() {
  const body = { title: form.title, content: form.content, approval_flow_id: form.approval_flow_id }
  if (needDeadline.value) body.vote_deadline = form.vote_deadline ? new Date(form.vote_deadline).toISOString() : null
  try {
    await resolutionApi.resubmit(route.params.id, body)
    showResubmit.value = false
    ElMessage.success('已重新提交')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(async () => {
  await auth.fetchMe().catch(() => null)
  load()
})
</script>
