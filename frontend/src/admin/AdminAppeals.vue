<template>
  <div class="page">
    <PageHead title="产权申诉审核" />
    <div class="card">
      <el-select v-model="status" placeholder="全部状态" clearable style="width: 180px" @change="resetAndLoad">
        <el-option label="待审核" value="PENDING" />
        <el-option label="已通过" value="APPROVED" />
        <el-option label="已驳回" value="REJECTED" />
        <el-option label="已关闭（申请人已注销）" value="CLOSED" />
      </el-select>
    </div>
    <div class="card">
      <el-table :data="items" size="small" empty-text="暂无申诉" class="appeal-table">
        <el-table-column label="申诉编码" width="100">
          <template #default="{ row }"><span class="mono">#{{ row.id }}</span></template>
        </el-table-column>
        <el-table-column label="申请人" width="230">
          <template #default="{ row }">
            <div class="applicant">
              <img :src="avatarOf(row.applicant)" :alt="row.applicant?.nickname || '申请人头像'" class="avatar" />
              <div class="applicant-text">
                <span class="applicant-name">{{ row.applicant?.nickname || '未设置' }}</span>
                <span class="muted">{{ row.applicant?.account_no || row.applicant?.id }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="联系电话" width="180">
          <template #default="{ row }">
            <div>{{ row.applicant?.phone || '未绑定' }}</div>
            <div v-if="row.status === 'PENDING' && row.applicant?.has_phone === false" class="muted hint">
              通过后清册只写姓名、不写联系电话
            </div>
          </template>
        </el-table-column>
        <el-table-column label="产权人姓名" width="120">
          <template #default="{ row }">{{ row.owner_name || '未提供' }}</template>
        </el-table-column>
        <el-table-column label="专有部分" min-width="180">
          <template #default="{ row }">{{ row.unit?.specific_part || row.unit_id }}</template>
        </el-table-column>
        <el-table-column label="申诉时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.submitted_at) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }"><el-tag size="small">{{ statusLabel('appeal', row.status) }}</el-tag></template>
        </el-table-column>
        <el-table-column label="证明材料" width="340">
          <template #default="{ row }">
            <ProofThumbs v-if="row.proof?.length" :proofs="row.proof" :max="3" />
            <span v-else class="muted">无</span>
          </template>
        </el-table-column>
        <el-table-column label="拒绝原因" width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.reject_reason || '—' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <div v-if="row.status === 'PENDING'" class="row-actions">
              <el-input v-model="notes[row.id]" maxlength="500" size="small" placeholder="处理备注（选填）"
                        style="width: 130px; margin-bottom: 6px" />
              <div>
                <el-button size="small" type="success" @click="decide(row.id, 'APPROVE')">通过</el-button>
                <el-button size="small" type="danger" @click="decide(row.id, 'REJECT')">拒绝</el-button>
              </div>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <PagerBar :total="total" :page="page" :page-size="pageSize" sizable
                @change="gotoPage" @update:page-size="changePageSize" />
    </div>
  </div>
</template>

<script setup>
import PageHead from '@/shared/PageHead.vue'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { admin } from '@/shared/api'
import PagerBar from '@/shared/PagerBar.vue'
import { errorText, formatDateTime } from '@/shared/format'
import { statusLabel } from '@/shared/labels'
import { usePaging } from '@/shared/usePaging'
import avatarDefault from '@/assets/avatar-default.svg'
import ProofThumbs from './parts/ProofThumbs.vue'

const status = ref('PENDING')
const notes = reactive({})
const filters = computed(() => (status.value ? { status: status.value } : {}))
const { items, total, page, pageSize, reload, goto, resetAndLoad: pagingReset, setPageSize } = usePaging({
  fetch: (params) => admin.appeals(params), filters
})

// REQ-FUNC-286：管理端带令牌取头像，失败或无头像回退内置默认头像
const avatarUrls = reactive({})
const loadingAvatars = new Set()
const avatarId = (url) => {
  const match = /\/attachments\/([^/]+)\/download/.exec(url || '')
  return match ? match[1] : ''
}
const avatarOf = (applicant) => {
  const id = avatarId(applicant?.avatar_url)
  return (id && avatarUrls[id]) || avatarDefault
}

async function loadAvatars(rows) {
  for (const item of rows) {
    const id = avatarId(item.applicant?.avatar_url)
    if (!id || avatarUrls[id] !== undefined || loadingAvatars.has(id)) continue
    loadingAvatars.add(id)
    try {
      const blob = await admin.downloadAttachment(id)
      avatarUrls[id] = URL.createObjectURL(blob)
    } catch (e) {
      avatarUrls[id] = ''
    } finally {
      loadingAvatars.delete(id)
    }
  }
}

watch(items, (rows) => { loadAvatars(rows) })
onBeforeUnmount(() => {
  for (const url of Object.values(avatarUrls)) if (url) URL.revokeObjectURL(url)
})

function changePageSize(n) {
  setPageSize(n).catch((e) => ElMessage.error(errorText(e)))
}

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

async function decide(id, decision) {
  try {
    const note = (notes[id] || '').trim() || undefined
    if (note && note.length > 500) {
      ElMessage.warning('备注不超过 500 字')
      return
    }
    let rejectReason
    if (decision === 'REJECT') {
      const { value } = await ElMessageBox.prompt('请输入拒绝原因（必填，≤500 字）', '拒绝申诉', { inputPattern: /\S+/, inputErrorMessage: '必填' })
      rejectReason = value
    }
    const result = await admin.decideAppeal(id, decision, rejectReason, note)
    ElMessage.success('已处理')
    delete notes[id]
    if (result?.registry_update?.notice) ElMessage.warning(result.registry_update.notice)
    load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>

<style scoped>
.appeal-table :deep(.cell) { padding: 6px 10px; }
.applicant { display: flex; align-items: center; gap: 8px; min-width: 0; }
.avatar { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; flex: none; }
.applicant-text { display: flex; flex-direction: column; min-width: 0; }
.applicant-name { font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hint { font-size: 12px; line-height: 1.3; }
.row-actions { white-space: nowrap; }
</style>
