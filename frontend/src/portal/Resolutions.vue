<template>
  <div class="page">
    <div class="card">
      <div class="row" style="justify-content: space-between">
        <h3 class="title" style="margin: 0">业委会决议</h3>
        <el-button v-if="auth.isChairOrVice" type="primary" @click="showCreate = true">发起决议</el-button>
      </div>
      <p class="section-title">{{ sectionTitle }}</p>
    </div>

    <div v-if="!items.length" class="card">
      <el-empty description="暂无决议" />
    </div>
    <template v-else>
      <section v-for="group in displayGroups" :key="group.key" class="res-section">
        <h4 v-if="group.title" class="res-section-title">{{ group.title }}（{{ group.items.length }}）</h4>
        <div class="res-grid">
      <article v-for="item in group.items" :key="item.id" class="card res-card">
        <div class="res-top">
          <div>
            <div class="res-idx mono">{{ resNo(item.id) }}</div>
            <router-link class="res-title" :to="`/resolutions/${item.id}`">{{ item.title }}</router-link>
          </div>
          <div class="res-state">
            <span v-if="item.status === 'PENDING'" class="res-progress-tag">进行中</span>
            <template v-else-if="item.status === 'APPROVED' || item.status === 'REJECTED'">
              <span class="res-ended-tag">已结束</span>
              <StatusTag :status="item.status" />
            </template>
            <StatusTag v-else :status="item.status" />
          </div>
        </div>
        <template v-if="item.vote_counts">
          <div v-if="part(item).empty" class="vote-legend"><span>暂无表决人</span></div>
          <template v-else>
            <div class="vote-bar" role="img" :aria-label="`已参与 ${part(item).voted} / ${part(item).expected}，同意 ${part(item).agree}，反对 ${part(item).disagree}，弃权 ${part(item).abstain}`">
              <i class="vote-agree" :style="{ width: part(item).agreePct + '%' }" />
              <i class="vote-disagree" :style="{ width: part(item).disagreePct + '%' }" />
              <i class="vote-abstain" :style="{ width: part(item).abstainPct + '%' }" />
            </div>
            <div class="vote-legend">
              <span class="res-participation">已参与 <b class="mono">{{ part(item).voted }} / {{ part(item).expected }} · {{ part(item).pct }}%</b></span>
              <span>同意 <b class="mono">{{ part(item).agree }}</b></span>
              <span>反对 <b class="mono">{{ part(item).disagree }}</b></span>
              <span>弃权 <b class="mono">{{ part(item).abstain }}</b></span>
            </div>
          </template>
        </template>
        <div v-else class="vote-legend"><span>{{ modeText(item.approval_mode) }}：由指定负责人审批</span></div>
        <div class="res-foot">
          <span class="res-initiator">
            发起人：<router-link v-if="item.initiator?.id" :to="`/users/${item.initiator.id}/profile`">{{ item.initiator?.display_name || '—' }}</router-link><template v-else>{{ item.initiator?.display_name || '—' }}</template><template v-if="(item.initiator?.labels || []).length"> · {{ item.initiator.labels.join('、') }}</template>
            <span class="mode-tag">{{ modeText(item.approval_mode) }}</span>
          </span>
          <span class="mono">{{ item.vote_deadline ? `截止 ${datetime(item.vote_deadline)}` : '无截止时间' }}</span>
        </div>
      </article>
        </div>
      </section>
    </template>
    <div class="card"><PagerBar :total="total" :page="page" :page-size="pageSize" @change="gotoPage" /></div>

    <el-dialog v-model="showCreate" title="发起决议" width="560px">
      <p v-if="limits && limits.vote_min_window_minutes" class="muted">半数同意决议：表决窗口不少于 {{ limits.vote_min_window_minutes }} 分钟</p>
      <p v-if="originId" class="muted">重新发起自 {{ resNo(originId) }}（原决议已结束，本决议独立审批）</p>
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
        <div class="form-actions-sticky">
          <el-button @click="showCreate = false">取消</el-button>
          <el-button type="primary" @click="create">提交</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { approvalApi, attachmentApi, meApi, resolutionApi } from '@/shared/api'
import StatusTag from './StatusTag.vue'
import PagerBar from '@/shared/PagerBar.vue'
import { useAuthStore } from '@/stores/auth'
import { datetime, errorText } from '@/shared/format'
import { usePaging } from '@/shared/usePaging'
import { participationShare } from '@/shared/voteShare'

// 分区由路由 props 决定（MOD-124 / IFC-324）：public 公开决议 / mine 我发起的 / todo 待我表决
const props = defineProps({ section: { type: String, default: 'public' } })
const SECTION_TITLES = { public: '公开决议', mine: '我发起的', todo: '待我表决' }
const route = useRoute()
const auth = useAuthStore()
const scope = computed(() => (SECTION_TITLES[props.section] ? props.section : 'public'))
const sectionTitle = computed(() => SECTION_TITLES[scope.value])
const filters = computed(() => ({ scope: scope.value }))
const { items, total, page, pageSize, reload, goto, resetAndLoad: pagingReset } = usePaging({
  fetch: ({ scope: s, ...params }) => resolutionApi.list(s, params), filters
})
const limits = ref(null)
const flows = ref([])
const showCreate = ref(false)
const originId = ref(null)
const form = reactive({ title: '', content: '', approval_flow_id: null, vote_deadline: null })
const attachmentIds = ref([])
const needDeadline = computed(() => flows.value.find((f) => f.id === form.approval_flow_id)?.mode === 'HALF_MAJORITY')

// 卡片展示用：编号由 id 派生（接口无决议编号字段）；比例见 shared/voteShare
const resNo = (id) => `R-${String(id).padStart(4, '0')}`
const modeText = (mode) => (mode === 'HALF_MAJORITY' ? '半数同意' : mode === 'DESIGNATED' ? '指定负责人' : mode)
const part = (item) => participationShare(item)

// REQ-FUNC-278 / REQ-FUNC-280：公开决议按进行中/已结束分区；其余分区保持单列表
const displayGroups = computed(() => {
  if (scope.value !== 'public') return [{ key: 'all', title: '', items: items.value }]
  return [
    { key: 'active', title: '进行中', items: items.value.filter((item) => item.status === 'PENDING') },
    { key: 'ended', title: '已结束', items: items.value.filter((item) => item.status !== 'PENDING') }
  ].filter((group) => group.items.length)
})

async function load() {
  try {
    await reload()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function resetAndLoad() {
  try {
    await pagingReset()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function gotoPage(n) {
  try {
    await goto(n)
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
    const body = { title: form.title, content: form.content, approval_flow_id: form.approval_flow_id,
      attachment_ids: attachmentIds.value,
      origin_id: originId.value || undefined }
    if (needDeadline.value) body.vote_deadline = form.vote_deadline ? new Date(form.vote_deadline).toISOString() : null
    await resolutionApi.create(body)
    attachmentIds.value = []
    originId.value = null
    showCreate.value = false
    ElMessage.success('已提交审批')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

// 从失败决议详情跳转而来：带 origin 参数预填并直接打开发起框（REQ-FUNC-271/273）
async function prefillFromOrigin() {
  const id = Number(route.query.origin)
  if (!id) return
  try {
    const origin = await resolutionApi.detail(id)
    form.title = origin.title
    form.content = origin.content
    originId.value = id
    showCreate.value = true
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

// 兄弟路由复用同一实例，分区变化时重新加载
watch(scope, resetAndLoad)

onMounted(async () => {
  await auth.fetchMe().catch(() => null)
  load()
  prefillFromOrigin()
  try {
    limits.value = await meApi.limits()
  } catch (e) {
    limits.value = null
  }
  try {
    const data = await approvalApi.flows('RESOLUTION')
    flows.value = data.results || data || []
  } catch (e) {
    flows.value = []
  }
})
</script>

<style scoped>
.res-section-title { margin: 4px 2px 10px; font-size: 14px; font-weight: 650; color: var(--muted); }
.res-section + .res-section { margin-top: 8px; }
</style>
