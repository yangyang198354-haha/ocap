<template>
  <div class="page">
    <div class="card">
      <h3 class="title">产权申诉审核</h3>
      <el-select v-model="status" placeholder="全部状态" clearable style="width: 180px" @change="resetAndLoad">
        <el-option label="待审核" value="PENDING" />
        <el-option label="已通过" value="APPROVED" />
        <el-option label="已驳回" value="REJECTED" />
        <el-option label="已关闭（申请人已注销）" value="CLOSED" />
      </el-select>
    </div>
    <div class="card">
      <el-empty v-if="!items.length" description="暂无申诉" />
      <div v-for="item in items" :key="item.id" class="list-item">
        <div class="row" style="justify-content: space-between">
          <div>
            <strong>#{{ item.id }}</strong>
            <span class="muted" style="margin-left: 8px">{{ item.applicant?.account_no || item.applicant?.id }} → {{ item.unit?.specific_part || item.unit_id }}</span>
            <el-tag size="small" style="margin-left: 8px">{{ statusLabel('appeal', item.status) }}</el-tag>
          </div>
          <div class="row" v-if="item.status === 'PENDING'">
            <el-button size="small" type="success" @click="decide(item.id, 'APPROVE')">通过</el-button>
            <el-button size="small" type="danger" @click="decide(item.id, 'REJECT')">拒绝</el-button>
          </div>
        </div>
        <div class="row" v-if="item.proof?.length">
          <el-link v-for="p in item.proof" :key="p.id" @click="openProof(p)">{{ p.name }}</el-link>
        </div>
        <p class="muted" v-if="item.reject_reason">拒绝原因：{{ item.reject_reason }}</p>
      </div>
      <PagerBar :total="total" :page="page" :page-size="pageSize" @change="gotoPage" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { admin } from '@/shared/api'
import PagerBar from '@/shared/PagerBar.vue'
import { errorText } from '@/shared/format'
import { statusLabel } from '@/shared/labels'
import { usePaging } from '@/shared/usePaging'

const status = ref('PENDING')
const filters = computed(() => (status.value ? { status: status.value } : {}))
const { items, total, page, pageSize, reload, goto, resetAndLoad: pagingReset } = usePaging({
  fetch: (params) => admin.appeals(params), filters
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

// 附件下载需要 Authorization 头，用 axios 取 blob 后在新窗口打开
async function openProof(proof) {
  try {
    const blob = await admin.downloadAttachment(proof.id)
    window.open(URL.createObjectURL(blob), '_blank')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function decide(id, decision) {
  try {
    let rejectReason
    if (decision === 'REJECT') {
      const { value } = await ElMessageBox.prompt('请输入拒绝原因（必填，≤500 字）', '拒绝申诉', { inputPattern: /\S+/, inputErrorMessage: '必填' })
      rejectReason = value
    }
    await admin.decideAppeal(id, decision, rejectReason)
    ElMessage.success('已处理')
    load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
