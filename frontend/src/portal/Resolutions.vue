<template>
  <div class="page">
    <div class="card">
      <div class="row" style="justify-content: space-between">
        <h3 class="title" style="margin: 0">业委会决议</h3>
        <el-button v-if="auth.isChairOrVice" type="primary" @click="showCreate = true">发起决议</el-button>
      </div>
      <el-radio-group v-model="scope" style="margin-top: 12px" @change="load">
        <el-radio-button value="public">公开决议</el-radio-button>
        <el-radio-button value="mine">我发起的</el-radio-button>
        <el-radio-button value="todo">待我表决</el-radio-button>
      </el-radio-group>
    </div>

    <div class="card">
      <el-empty v-if="!items.length" description="暂无决议" />
      <div v-for="item in items" :key="item.id" style="padding: 10px 0; border-bottom: 1px solid #f0f1f3">
        <router-link :to="`/resolutions/${item.id}`">{{ item.title }}</router-link>
        <span class="muted" style="margin-left: 8px">{{ item.status }} · {{ item.approval_mode }}</span>
        <span class="muted" style="margin-left: 8px">{{ (item.initiator?.labels || []).join('、') }}</span>
      </div>
    </div>

    <el-dialog v-model="showCreate" title="发起决议" width="560px">
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
      <div class="row" style="margin-top: 10px">
        <el-upload :show-file-list="false" :http-request="uploadAttachment" accept=".pdf,.jpg,.jpeg,.png,.docx,.xlsx">
          <el-button>上传附件</el-button>
        </el-upload>
        <span class="muted">{{ attachmentIds.length }} 个附件</span>
      </div>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { approvalApi, attachmentApi, resolutionApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'

const auth = useAuthStore()
const scope = ref('public')
const items = ref([])
const flows = ref([])
const showCreate = ref(false)
const form = reactive({ title: '', content: '', approval_flow_id: null, vote_deadline: null })
const attachmentIds = ref([])
const needDeadline = computed(() => flows.value.find((f) => f.id === form.approval_flow_id)?.mode === 'HALF_MAJORITY')

async function load() {
  try {
    const data = await resolutionApi.list(scope.value)
    items.value = data.results || data || []
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function uploadAttachment({ file }) {
  try {
    const uploaded = await attachmentApi.upload(file, 'RESOLUTION')
    attachmentIds.value.push(uploaded.id)
    ElMessage.success('已上传')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function create() {
  try {
    const body = { title: form.title, content: form.content, approval_flow_id: form.approval_flow_id, attachment_ids: attachmentIds.value }
    if (needDeadline.value) body.vote_deadline = form.vote_deadline ? new Date(form.vote_deadline).toISOString() : null
    await resolutionApi.create(body)
    attachmentIds.value = []
    showCreate.value = false
    ElMessage.success('已提交审批')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(async () => {
  await auth.fetchMe().catch(() => null)
  load()
  try {
    const data = await approvalApi.flows('RESOLUTION')
    flows.value = data.results || data || []
  } catch (e) {
    flows.value = []
  }
})
</script>
