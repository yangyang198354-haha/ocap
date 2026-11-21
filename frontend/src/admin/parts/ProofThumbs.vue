<!-- MOD-117 / IFC-315：申诉资料缩略图（可视区懒加载、并发 ≤3、降采样后丢弃原图）与点击弹出大图 / pdf 预览 -->
<template>
  <div class="proof-thumbs">
    <div
      v-for="(p, index) in visibleProofs"
      :key="p.id"
      ref="cells"
      class="proof-cell"
      :data-proof-id="p.id"
      :title="p.name"
      @click="openAt(index)"
    >
      <template v-if="isPdf(p)">
        <span class="proof-icon">PDF</span>
        <span class="proof-name">{{ p.name }}</span>
      </template>
      <template v-else>
        <img v-if="thumbs[p.id]?.url" :src="thumbs[p.id].url" :alt="p.name" class="proof-img" />
        <span v-else-if="thumbs[p.id]?.error" class="proof-error">{{ thumbs[p.id].error }}</span>
        <span v-else class="proof-name">加载中…</span>
      </template>
    </div>
    <div v-if="overflow > 0" class="proof-cell proof-more" :title="`还有 ${overflow} 份证明材料`" @click="openAt(visibleProofs.length)">
      +{{ overflow }}
    </div>

    <el-dialog v-model="visible" :title="current ? current.name : '产权证明'" width="720px" @closed="onClosed">
      <div class="proof-viewer">
        <p v-if="viewer.error" class="proof-error">预览失败：{{ viewer.error }}</p>
        <img v-else-if="viewer.url && current && !isPdf(current)" :src="viewer.url" :alt="current.name" class="proof-large" />
        <iframe v-else-if="viewer.url && current && isPdf(current)" :src="viewer.url" class="proof-frame" title="pdf 预览" />
        <p v-else class="muted">加载中…</p>
        <p v-if="current && isPdf(current) && viewer.url">
          无法预览时请
          <a :href="viewer.url" :download="current.name">下载查看</a>
        </p>
      </div>
      <template #footer>
        <el-button :disabled="index <= 0" @click="openAt(index - 1)">上一份</el-button>
        <span class="muted">{{ index + 1 }} / {{ proofs.length }}</span>
        <el-button :disabled="index >= proofs.length - 1" @click="openAt(index + 1)">下一份</el-button>
        <el-button @click="visible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { admin } from '@/shared/api'
import { errorText } from '@/shared/format'

const props = defineProps({
  proofs: { type: Array, default: () => [] },
  // REQ-FUNC-286：表格内最多展示 N 份，超出显示 +N
  max: { type: Number, default: 0 }
})

const MAX_CONCURRENT = 3
const THUMB_WIDTH = 160

const visibleProofs = computed(() => (props.max > 0 ? props.proofs.slice(0, props.max) : props.proofs))
const overflow = computed(() => (props.max > 0 ? Math.max(props.proofs.length - props.max, 0) : 0))

const cells = ref([])
const thumbs = reactive({}) // id -> { url?, error? }（按 id 缓存）
const visible = ref(false)
const index = ref(0)
const viewer = reactive({ url: '', error: '' })
const current = computed(() => props.proofs[index.value] || null)

let observer = null
let active = 0
const queue = []
const queued = new Set()
let viewToken = 0

const isPdf = (p) => (p.content_type || '').includes('pdf')

function pump() {
  while (active < MAX_CONCURRENT && queue.length) {
    const proof = queue.shift()
    active += 1
    loadThumb(proof).finally(() => {
      active -= 1
      pump()
    })
  }
}

function enqueue(proof) {
  if (isPdf(proof) || thumbs[proof.id] || queued.has(proof.id)) return
  queued.add(proof.id)
  queue.push(proof)
  pump()
}

// 取 Blob → 降采样为缩略图后丢弃原 Blob；不支持 createImageBitmap 时降级为直接用 Blob（由 <img> 缩放）
async function loadThumb(proof) {
  try {
    const blob = await admin.downloadAttachment(proof.id)
    let url = ''
    if (typeof createImageBitmap === 'function' && typeof document !== 'undefined') {
      try {
        const bitmap = await createImageBitmap(blob, { resizeWidth: THUMB_WIDTH })
        const canvas = document.createElement('canvas')
        canvas.width = bitmap.width
        canvas.height = bitmap.height
        canvas.getContext('2d').drawImage(bitmap, 0, 0)
        bitmap.close?.()
        const small = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.8))
        if (small) url = URL.createObjectURL(small)
      } catch {
        url = ''
      }
    }
    thumbs[proof.id] = { url: url || URL.createObjectURL(blob) }
  } catch (e) {
    thumbs[proof.id] = { error: errorText(e) }
  }
}

function observeAll() {
  const list = props.proofs
  if (typeof IntersectionObserver === 'undefined') {
    list.forEach(enqueue)
    return
  }
  observer?.disconnect()
  observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue
      const proof = list.find((p) => p.id === entry.target.dataset.proofId)
      if (proof) enqueue(proof)
      observer.unobserve(entry.target)
    }
  })
  for (const el of cells.value || []) observer.observe(el)
}

function clearViewer() {
  if (viewer.url) URL.revokeObjectURL(viewer.url)
  viewer.url = ''
  viewer.error = ''
}

async function openAt(i) {
  if (i < 0 || i >= props.proofs.length) return
  index.value = i
  visible.value = true
  clearViewer()
  viewToken += 1
  const token = viewToken
  const proof = props.proofs[i]
  try {
    const blob = await admin.downloadAttachment(proof.id)
    if (token !== viewToken) return // 已切换或关闭
    viewer.url = URL.createObjectURL(blob)
  } catch (e) {
    if (token === viewToken) viewer.error = errorText(e)
  }
}

function onClosed() {
  viewToken += 1
  clearViewer()
}

onMounted(async () => {
  await nextTick()
  observeAll()
})
watch(() => props.proofs, async () => {
  await nextTick()
  observeAll()
})
onBeforeUnmount(() => {
  observer?.disconnect()
  viewToken += 1
  clearViewer()
  for (const item of Object.values(thumbs)) if (item.url) URL.revokeObjectURL(item.url)
})
</script>

<style scoped>
.proof-thumbs { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.proof-cell {
  width: 96px; height: 96px; display: flex; flex-direction: column; align-items: center; justify-content: center;
  border-style: solid; border-width: 1px; border-color: var(--line); border-radius: 8px;
  cursor: pointer; overflow: hidden; padding: 4px;
}
.proof-more { font-weight: 700; color: var(--accent-text); }
.proof-img { max-width: 100%; max-height: 100%; object-fit: cover; }
.proof-icon { font-weight: 700; }
.proof-name { font-size: 12px; word-break: break-all; text-align: center; }
.proof-error { font-size: 12px; }
.proof-viewer { text-align: center; }
.proof-large { max-width: 100%; max-height: 70vh; }
.proof-frame { width: 100%; height: 70vh; border-width: 0; }
</style>
