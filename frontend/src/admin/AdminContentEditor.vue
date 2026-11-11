<template>
  <div class="page">
    <div class="row" style="justify-content: space-between; margin-bottom: 12px">
      <h2>编辑内容</h2>
      <div class="row">
        <el-button @click="$router.push('/admin/content/posts')">返回列表</el-button>
        <el-button @click="saveDraft" :loading="saving">保存草稿</el-button>
        <el-button type="success" @click="publish">发布</el-button>
        <el-button @click="confirmText">确认文案</el-button>
        <el-button @click="preview">预览</el-button>
      </div>
    </div>

    <el-input v-model="title" placeholder="标题" maxlength="200" show-word-limit style="margin-bottom: 12px" />
    <div class="row" style="margin-bottom: 12px">
      <el-select v-model="styleKey" style="width: 220px" placeholder="版式样式">
        <el-option v-for="item in styles" :key="item.key" :label="item.name" :value="item.key" />
      </el-select>
      <el-select v-model="llm" style="width: 220px" placeholder="生成模型" clearable>
        <el-option v-for="item in llms" :key="item.service_type"
                   :label="`${item.label}（${item.model}）`" :value="item.service_type" />
      </el-select>
      <el-tag v-if="confirmed" type="success">文案已确认</el-tag>
    </div>

    <div class="editor-layout">
      <div>
        <RichEditor ref="rich" v-model="doc" :media-urls="mediaUrls"
                    @pick-media="openPicker" />
      </div>
      <aside class="side-panel">
        <h3>AI 生成</h3>
        <el-select v-model="promptTemplate" placeholder="提示词模板" clearable style="width: 100%; margin-bottom: 8px"
                   @change="applyTemplate">
          <el-option v-for="item in prompts" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-input v-model="prompt" type="textarea" :rows="4" placeholder="输入提示词" />
        <div class="row" style="margin-top: 8px">
          <el-button type="primary" size="small" :disabled="busy" @click="generateText">生成文案</el-button>
          <el-button size="small" @click="savePrompt">保存为模板</el-button>
        </div>
        <div class="row" style="margin-top: 8px">
          <el-input v-model="imagePrompt" size="small" placeholder="配图描述" />
          <el-button size="small" :disabled="busy" @click="generateImage">配图</el-button>
        </div>
        <div class="row" style="margin-top: 8px">
          <el-button size="small" :disabled="busy" @click="generateVideo">生成视频</el-button>
        </div>
        <el-alert v-if="jobMessage" :title="jobMessage" :type="jobError ? 'error' : 'info'" :closable="false"
                  style="margin-top: 8px" />
        <div v-if="generatedText" class="generated">
          <div class="generated-text">{{ generatedText }}</div>
          <el-button size="small" type="primary" @click="insertText">放入编辑器</el-button>
        </div>
        <div v-if="generatedImages.length" class="generated-images">
          <div v-for="item in generatedImages" :key="item.id" class="generated-image">
            <video v-if="item.media_type === 'VIDEO'" :src="item.url" controls />
            <img v-else :src="item.url" alt="" />
            <div class="row">
              <el-button size="small" @click="insertMedia(item.media_type === 'VIDEO' ? 'video' : 'image', item.id, item.url)">插入</el-button>
              <el-button size="small" @click="saveCandidate(item.id)">存入素材库</el-button>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <div class="row" style="margin-top: 16px">
      <el-button type="primary" @click="openDrafts">一键保存到草稿箱</el-button>
      <el-button @click="openHistory">保存历史</el-button>
    </div>

    <MediaPicker ref="picker" @selected="onMedia" />

    <el-dialog v-model="previewVisible" title="预览" width="800px">
      <div v-for="page in previewPages" :key="page.index" class="preview-page" v-html="page.html" />
    </el-dialog>

    <el-dialog v-model="draftVisible" title="一键保存到草稿箱" width="680px">
      <el-checkbox-group v-model="selectedAccounts">
        <el-checkbox v-for="item in platforms" :key="item.account?.id"
                     :value="item.account?.id" :disabled="!item.account">
          {{ item.label }}{{ item.account ? `（${item.account.display_name}）` : '（未配置账户）' }}
        </el-checkbox>
      </el-checkbox-group>
      <div class="row" style="margin-top: 12px">
        <el-button type="primary" :disabled="!selectedAccounts.length" @click="pushDrafts">开始保存</el-button>
      </div>
      <el-table :data="pushResults" border style="margin-top: 12px">
        <el-table-column prop="platform" label="平台" width="120" />
        <el-table-column prop="status" label="结果" width="130" />
        <el-table-column prop="error_message" label="原因" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button v-if="row.status === 'FAILED' || row.status === 'UNKNOWN'" size="small" @click="retry(row)">重试</el-button>
            <el-button v-if="row.mode === 'MANUAL'" size="small" @click="exportPack(row.platform)">内容包</el-button>
            <el-button v-if="row.mode === 'MANUAL'" size="small" @click="copyPack(row.platform)">复制</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-for="row in pushResults" :key="`u-${row.id}`">
        <el-tag v-if="row.unsupported?.length" type="warning" style="margin-top: 6px">
          {{ row.platform }} 不能保留：{{ row.unsupported.join('、') }}
        </el-tag>
      </div>
    </el-dialog>

    <el-dialog v-model="historyVisible" title="保存历史" width="720px">
      <el-table :data="historyRows" border>
        <el-table-column prop="platform" label="平台" width="120" />
        <el-table-column prop="status" label="结果" width="120" />
        <el-table-column prop="operator" label="操作人" width="120" />
        <el-table-column prop="created_at" label="时间" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { admin } from '@/shared/api'
import RichEditor from './editor/RichEditor.vue'
import MediaPicker from './editor/MediaPicker.vue'

const route = useRoute()
const postId = Number(route.params.id)
const rich = ref(null)
const picker = ref(null)
const title = ref('')
const doc = ref({ type: 'doc', content: [] })
const styleKey = ref('builtin:classic')
const styles = ref([])
const mediaUrls = ref({})
const confirmed = ref(false)
const llms = ref([])
const llm = ref('')
const prompts = ref([])
const promptTemplate = ref(null)
const prompt = ref('')
const imagePrompt = ref('')
const savedPrompt = ref({})
const busy = ref(false)
const saving = ref(false)
const jobMessage = ref('')
const jobError = ref(false)
const generatedText = ref('')
const generatedImages = ref([])
const previewVisible = ref(false)
const previewPages = ref([])
const draftVisible = ref(false)
const platforms = ref([])
const selectedAccounts = ref([])
const pushResults = ref([])
const historyVisible = ref(false)
const historyRows = ref([])
let pollTimer = null

async function load() {
  const post = await admin.contentPost(postId)
  title.value = post.title
  doc.value = post.doc || { type: 'doc', content: [] }
  styleKey.value = post.style_key
  mediaUrls.value = post.media_urls || {}
  confirmed.value = post.text_confirmed
  styles.value = await admin.styleTemplates()
  llms.value = await admin.llmOptions()
  prompts.value = await admin.promptTemplates()
  if (!llm.value && llms.value.length) llm.value = llms.value[0].service_type
}
async function saveDraft() {
  saving.value = true
  try {
    await admin.updateContentPost(postId, { title: title.value, doc: doc.value, style_key: styleKey.value })
    ElMessage.success('已保存')
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    saving.value = false
  }
}
async function publish() {
  try {
    await saveDraft()
    await admin.publishContentPost(postId)
    ElMessage.success('已发布')
  } catch (err) {
    ElMessage.error(err.message || '发布失败')
  }
}
async function confirmText() {
  try {
    await saveDraft()
    await admin.confirmContentText(postId)
    confirmed.value = true
    ElMessage.success('文案已确认')
  } catch (err) {
    ElMessage.error(err.message || '确认失败')
  }
}
async function preview() {
  const data = await admin.previewContent({ doc: doc.value, style_key: styleKey.value })
  previewPages.value = data.pages || []
  previewVisible.value = true
}
function openPicker(kind) {
  picker.value?.open(kind === 'video' ? 'VIDEO' : 'IMAGE')
}
function onMedia(item) {
  rich.value?.insertMedia(item.kind, item.mediaId, item.url)
}
function insertMedia(kind, id, url) {
  rich.value?.insertMedia(kind, id, url)
}
async function saveCandidate(id) {
  await admin.saveMedia(id)
  ElMessage.success('已存入素材库')
}
function applyTemplate(id) {
  const row = prompts.value.find((item) => item.id === id)
  if (row) prompt.value = row.prompt
}
async function savePrompt() {
  if (!prompt.value.trim()) {
    ElMessage.error('请输入提示词')
    return
  }
  try {
    const { value } = await ElMessageBox.prompt('模板名称', '保存为模板')
    const row = await admin.createPromptTemplate({ name: value, prompt: prompt.value })
    prompts.value = await admin.promptTemplates()
    promptTemplate.value = row.id
    ElMessage.success('已保存模板')
  } catch (err) {
    if (err !== 'cancel') ElMessage.error(err.message || '保存失败')
  }
}
function textToDoc(text) {
  const blocks = String(text).split(/\n\n+/).filter(Boolean).map((part) => ({
    type: 'paragraph',
    content: [{ type: 'text', text: part }]
  }))
  return { type: 'doc', content: blocks }
}
async function insertText() {
  if (JSON.stringify(doc.value?.content || []) !== '[]') {
    try {
      await ElMessageBox.confirm('将覆盖当前正文，是否继续？', '提示', { type: 'warning' })
    } catch { return }
  }
  doc.value = textToDoc(generatedText.value)
}
function poll(jobId, onSuccess) {
  busy.value = true
  jobError.value = false
  jobMessage.value = '生成中…'
  const started = Date.now()
  pollTimer = setInterval(async () => {
    if (Date.now() - started > 10 * 60 * 1000) {
      stopPoll()
      jobError.value = true
      jobMessage.value = '生成超时，请刷新任务列表查看'
      return
    }
    const job = await admin.contentJob(jobId)
    if (job.status === 'SUCCEEDED') {
      stopPoll()
      jobMessage.value = '生成成功'
      onSuccess(job.result || {})
    } else if (job.status === 'FAILED') {
      stopPoll()
      jobError.value = true
      jobMessage.value = `生成失败：${job.error_message || job.error_code}`
    }
  }, 2000)
}
function stopPoll() {
  busy.value = false
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = null
}
async function generateText() {
  if (!prompt.value.trim()) {
    ElMessage.error('请输入提示词')
    return
  }
  try {
    const job = await admin.aiText({ prompt: prompt.value, service_type: llm.value || undefined })
    poll(job.id, (result) => { generatedText.value = result.text || '' })
  } catch (err) {
    jobError.value = true
    jobMessage.value = err.message || '生成失败'
    if (err.code === 'LLM_NOT_CONFIGURED') jobMessage.value = '请先配置大语言模型'
  }
}
async function generateImage() {
  if (!imagePrompt.value.trim()) {
    ElMessage.error('请输入配图描述')
    return
  }
  try {
    const job = await admin.aiImage({ prompt: imagePrompt.value })
    poll(job.id, (result) => { generatedImages.value = result.media || [] })
  } catch (err) {
    jobError.value = true
    jobMessage.value = err.message || '生成失败'
  }
}
async function generateVideo() {
  try {
    const job = await admin.aiVideo({ post_id: postId })
    poll(job.id, (result) => {
      generatedImages.value = result.media || []
      ElMessage.success('视频已生成并存入素材库')
    })
  } catch (err) {
    jobError.value = true
    jobMessage.value = err.message || '生成失败'
    if (err.code === 'TEXT_NOT_CONFIRMED') jobMessage.value = '请先确认文案'
  }
}
async function openDrafts() {
  platforms.value = await admin.platformAccounts()
  pushResults.value = []
  selectedAccounts.value = []
  draftVisible.value = true
}
async function pushDrafts() {
  try {
    const data = await admin.pushDrafts(postId, selectedAccounts.value)
    pushResults.value = data.pushes || []
    if (data.job_id) {
      poll(data.job_id, async () => {
        const history = await admin.draftHistory(postId, { batch_id: data.batch_id })
        pushResults.value = history.results || pushResults.value
      })
    }
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
  }
}
async function retry(row) {
  const data = await admin.retryDraft(row.id)
  poll(data.job_id, async () => {
    const history = await admin.draftHistory(postId)
    pushResults.value = history.results || pushResults.value
  })
}
async function openHistory() {
  const data = await admin.draftHistory(postId)
  historyRows.value = data.results || []
  historyVisible.value = true
}
async function exportPack(platform) {
  const blob = await admin.exportPack(postId, platform)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `content_${postId}_${platform}.zip`
  link.click()
  URL.revokeObjectURL(url)
}
async function copyPack(platform) {
  const data = await admin.copyPack(postId, platform)
  try {
    await navigator.clipboard.writeText(data.text)
    ElMessage.success('已复制')
  } catch {
    ElMessage.warning('复制失败，请从内容包获取')
  }
}
onMounted(load)
onBeforeUnmount(stopPoll)
</script>

<style scoped>
.editor-layout { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 16px; }
.side-panel { border: 1px solid var(--line); border-radius: 8px; padding: 12px; }
.generated { margin-top: 12px; border-top: 1px solid var(--line); padding-top: 8px; }
.generated-text { max-height: 180px; overflow: auto; white-space: pre-wrap; font-size: 13px; margin-bottom: 8px; }
.generated-images { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 12px; }
.generated-image img, .generated-image video { width: 100%; height: 90px; object-fit: cover; }
.preview-page { margin-bottom: 16px; }
</style>
