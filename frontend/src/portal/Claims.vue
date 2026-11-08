<template>
  <div class="page">
    <div class="card">
      <div class="row" style="justify-content: space-between">
        <h3 class="title" style="margin: 0">报销 / 备用金</h3>
        <el-button type="primary" @click="showCreate = true">新建申请</el-button>
      </div>
      <p class="muted">报销凭发票；备用金为预借现金，办完后核销，实际支出再凭票报销。</p>
    </div>
    <div class="card">
      <el-empty v-if="!items.length" description="暂无申请" />
      <div v-for="item in items" :key="item.id" style="padding: 10px 0; border-bottom: 1px solid #f0f1f3">
        <div class="row" style="justify-content: space-between">
          <div>
            <strong>{{ typeLabel(item.type) }} ¥{{ item.amount }}</strong>
            <span class="muted" style="margin-left: 8px">{{ item.reason }}</span>
          </div>
          <div class="row">
            <el-tag>{{ item.status }}</el-tag>
            <el-button v-if="item.status === 'PENDING'" size="small" @click="withdraw(item.id)">撤回</el-button>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="showCreate" title="新建申请" width="560px">
      <el-select v-model="form.type" style="width: 100%">
        <el-option label="报销" value="REIMBURSEMENT" />
        <el-option label="备用金预借" value="ADVANCE" />
      </el-select>
      <el-input v-model="form.amount" placeholder="金额（最多两位小数）" style="margin-top: 10px" />
      <el-input v-model="form.reason" type="textarea" :rows="3" placeholder="事由（1~500 字）" style="margin-top: 10px" />
      <el-select v-model="form.approval_flow_id" placeholder="审批流程" style="margin-top: 10px; width: 100%">
        <el-option v-for="f in flows" :key="f.id" :label="`${f.name}（${f.mode}）`" :value="f.id" />
      </el-select>
      <div class="row" style="margin-top: 10px">
        <el-upload :show-file-list="false" :http-request="uploadInvoice" accept="image/*,application/pdf">
          <el-button>上传发票</el-button>
        </el-upload>
        <span class="muted">{{ invoiceIds.length }} 个附件</span>
      </div>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { approvalApi, attachmentApi, claimApi } from '@/shared/api'
import { errorText } from '@/shared/format'

const items = ref([])
const flows = ref([])
const invoiceIds = ref([])
const showCreate = ref(false)
const form = reactive({ type: 'REIMBURSEMENT', amount: '', reason: '', approval_flow_id: null })

const typeLabel = (t) => ({ REIMBURSEMENT: '报销', ADVANCE: '备用金', SETTLEMENT: '核销' }[t] || t)

async function load() {
  try {
    const data = await claimApi.mine()
    items.value = data.results || data || []
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function uploadInvoice({ file }) {
  try {
    const uploaded = await attachmentApi.upload(file, 'INVOICE')
    invoiceIds.value.push(uploaded.id)
    ElMessage.success('已上传')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function create() {
  try {
    await claimApi.create({ ...form, invoice_ids: invoiceIds.value })
    showCreate.value = false
    invoiceIds.value = []
    ElMessage.success('已提交审批')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function withdraw(id) {
  try {
    await claimApi.withdraw(id)
    ElMessage.success('已撤回')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(async () => {
  load()
  try {
    const data = await approvalApi.flows('EXPENSE')
    flows.value = data.results || data || []
  } catch (e) {
    flows.value = []
  }
})
</script>
