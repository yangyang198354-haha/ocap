<template>
  <div class="page">
    <div class="card" v-if="item">
      <h3 class="title">{{ item.title }}</h3>
      <p class="muted">
        状态：{{ item.status }} · 审批方式：{{ item.approval_mode }}
        <span v-if="item.vote_deadline">· 表决截止：{{ item.vote_deadline }}</span>
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
      <div class="row" v-if="item.approval_mode === 'HALF_MAJORITY' && item.status === 'PENDING' && auth.isCommittee" style="margin-top: 12px">
        <el-button type="success" @click="vote('AGREE')">同意</el-button>
        <el-button type="danger" @click="vote('DISAGREE')">反对</el-button>
        <el-button @click="vote('ABSTAIN')">弃权</el-button>
      </div>
      <div class="row" v-if="isInitiator" style="margin-top: 12px">
        <el-button v-if="item.status === 'PENDING'" @click="withdraw">撤回</el-button>
        <el-button v-if="['REJECTED', 'WITHDRAWN'].includes(item.status)" type="primary" @click="openResubmit">修改后重新提交</el-button>
      </div>
    </div>
    <div class="card" v-else>
      <el-empty description="决议不存在或无权查看" />
    </div>

    <el-dialog v-model="showResubmit" title="重新提交决议" width="560px">
      <el-input v-model="form.title" placeholder="标题" maxlength="200" />
      <el-input v-model="form.content" type="textarea" :rows="5" placeholder="内容" style="margin-top: 10px" />
      <el-select v-model="form.approval_flow_id" placeholder="审批流程" style="margin-top: 10px; width: 100%">
        <el-option v-for="f in flows" :key="f.id" :label="`${f.name}（${f.mode === 'HALF_MAJORITY' ? '半数同意' : '指定负责人'}）`" :value="f.id" />
      </el-select>
      <el-date-picker
        v-if="needDeadline"
        v-model="form.vote_deadline"
        type="datetime"
        placeholder="表决截止时间（半数同意必填）"
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
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { approvalApi, resolutionApi } from '@/shared/api'
import { apiUrl } from '@/shared/http'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'

const route = useRoute()
const auth = useAuthStore()
const item = ref(null)
const flows = ref([])
const showResubmit = ref(false)
const form = reactive({ title: '', content: '', approval_flow_id: null, vote_deadline: null })

const isInitiator = computed(() => item.value && auth.me?.profile?.id === item.value.initiator?.id)
const needDeadline = computed(() => flows.value.find((f) => f.id === form.approval_flow_id)?.mode === 'HALF_MAJORITY')

async function load() {
  try {
    item.value = await resolutionApi.detail(route.params.id)
  } catch (e) {
    ElMessage.error(errorText(e))
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
