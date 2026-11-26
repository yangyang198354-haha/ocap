<!-- MOD-123：认证申诉，自带房屋选择（Q-BL-21=A）；MOD-146：选文件只在页面内暂存，点提交时一次发送 -->
<template>
  <div id="appeal">
    <h2 class="title">认证申诉</h2>
    <p class="muted">姓名与手机号未能通过清册核对时，可选择房屋、填写产权人名字并选择 1~5 份产权证明（jpg/png/pdf，单个不超过 10MB），点击“提交申诉”后一并提交，由管理员审核。</p>
    <UnitCascader :key="cascaderKey" v-model="appealUnitId" />
    <div class="row" style="margin-top: 10px">
      <el-input v-model="appeal.ownerName" maxlength="64" placeholder="产权人名字" style="width: 220px" />
    </div>
    <div class="row" style="margin-top: 10px">
      <el-upload
        ref="uploadRef"
        :show-file-list="false"
        :auto-upload="false"
        :on-change="onPick"
        multiple
        accept=".jpg,.jpeg,.png,.pdf"
      >
        <el-button>选择产权证明</el-button>
      </el-upload>
      <span class="muted">已选 {{ staged.length }} 份（最多 {{ MAX_FILES }} 份，提交前不会上传）</span>
    </div>
    <ul v-if="staged.length" class="staged-list">
      <li v-for="entry in staged" :key="entry.id" class="staged-item">
        <span>{{ entry.file.name }}</span>
        <span class="muted">{{ typeText(entry.file) }} · {{ sizeText(entry.file) }}</span>
        <el-button size="small" link @click="removeStaged(entry.id)">移除</el-button>
      </li>
    </ul>
    <div class="row" style="margin-top: 10px">
      <el-button type="primary" :loading="submitting" @click="submitAppeal">提交申诉</el-button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { unitApi } from '@/shared/api'
import { errorText } from '@/shared/format'
import { useHousingStore } from '@/stores/housing'
import UnitCascader from '../parts/UnitCascader.vue'

const props = defineProps({ prefill: { type: Object, default: null } })
const emit = defineEmits(['submitted'])

const MAX_FILES = 5
const MAX_BYTES = 10 * 1024 * 1024
const ALLOWED_EXT = ['jpg', 'jpeg', 'png', 'pdf']
const OWNER_NAME_MAX = 64

const store = useHousingStore()
const appealUnitId = ref(null)
const cascaderKey = ref(0)
const appeal = reactive({ ownerName: '' })
// 页面内暂存（刷新即空，Q-B18-30=A）：选择阶段不向服务器发送任何文件
const staged = ref([])
const previousAppealId = ref(null)
const uploadRef = ref(null)
const submitting = ref(false)
let seq = 0

function applyPrefill(value) {
  if (!value || !value.nonce) return
  appealUnitId.value = value.unitId || null
  appeal.ownerName = value.ownerName || ''
  previousAppealId.value = value.previousAppealId || null
  cascaderKey.value += 1
}

watch(() => props.prefill, applyPrefill, { deep: true })

const extOf = (file) => {
  const name = String(file?.name || '')
  const dot = name.lastIndexOf('.')
  return dot >= 0 ? name.slice(dot + 1).toLowerCase() : ''
}
const typeText = (file) => extOf(file).toUpperCase() || '未知'
const sizeText = (file) => {
  const size = Number(file?.size) || 0
  return size >= 1024 * 1024 ? `${(size / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(size / 1024))} KB`
}

function onPick(uploadFile) {
  const file = uploadFile?.raw
  if (!file || uploadFile.status !== 'ready') return
  if (staged.value.length >= MAX_FILES) return ElMessage.warning(`最多 ${MAX_FILES} 份`)
  if (!ALLOWED_EXT.includes(extOf(file))) return ElMessage.warning('仅支持 jpg/png/pdf')
  if (file.size > MAX_BYTES) return ElMessage.warning('单个文件不超过10MB')
  staged.value.push({ id: ++seq, file })
  uploadRef.value?.clearFiles?.()
}

function removeStaged(id) {
  staged.value = staged.value.filter((entry) => entry.id !== id)
}

async function submitAppeal() {
  const ownerName = appeal.ownerName.trim()
  if (!appealUnitId.value) return ElMessage.warning('请选择到具体户')
  if (!ownerName) return ElMessage.warning('请输入产权人名字')
  if (ownerName.length > OWNER_NAME_MAX) return ElMessage.warning(`产权人名字不超过 ${OWNER_NAME_MAX} 字`)
  if (!staged.value.length) return ElMessage.warning('请至少选择 1 份产权证明')
  const form = new FormData()
  form.append('unit_id', String(appealUnitId.value))
  form.append('owner_name', ownerName)
  if (previousAppealId.value) form.append('previous_appeal_id', String(previousAppealId.value))
  staged.value.forEach((entry) => form.append('files', entry.file))
  submitting.value = true
  try {
    await unitApi.submitAppeal(form)
    ElMessage.success('申诉已提交，等待管理员审核')
    staged.value = []
    appeal.ownerName = ''
    appealUnitId.value = null
    previousAppealId.value = null
    cascaderKey.value += 1
    await store.loadLists()
    emit('submitted')
  } catch (e) {
    // 失败保留专有部分、名字与暂存文件，便于修改后重新提交
    ElMessage.error(errorText(e))
  } finally {
    submitting.value = false
  }
}

// 认证页失败转来时，姓名由仓库带入（只带姓名，房屋需重新选择）
onMounted(() => {
  const name = store.consumePrefillOwnerName()
  if (name) appeal.ownerName = name
  applyPrefill(props.prefill)
})
</script>

<style scoped>
.staged-list { list-style: none; margin: 10px 0 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.staged-item { display: flex; align-items: center; gap: 12px; }
</style>
