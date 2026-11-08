<template>
  <div class="page">
    <div class="card">
      <div class="row" style="justify-content: space-between">
        <h3 class="title" style="margin: 0">报销 / 备用金</h3>
        <div class="row">
          <el-button type="primary" @click="openCreate">新建申请</el-button>
          <el-button v-if="auth.isCommittee" @click="openSettle">备用金核销</el-button>
        </div>
      </div>
      <p class="muted">报销凭发票；备用金为预借现金，办完后核销，实际支出再凭票报销；核销按差额调整支出，多退少补。</p>
      <el-radio-group v-model="scope" style="margin-top: 8px" @change="load">
        <el-radio-button value="mine">我提交的</el-radio-button>
        <el-radio-button value="todo">待我审批</el-radio-button>
      </el-radio-group>
    </div>
    <div class="card">
      <el-empty v-if="!items.length" description="暂无申请" />
      <div v-for="item in items" :key="item.id" style="padding: 10px 0; border-bottom: 1px solid #f0f1f3">
        <div class="row" style="justify-content: space-between">
          <div>
            <strong>{{ typeLabel(item.type) }} ¥{{ item.amount }}</strong>
            <span v-if="item.type === 'SETTLEMENT'" class="muted" style="margin-left: 8px">
              {{ Number(item.amount) < 0 ? '多退（退回现金）' : '差额补发' }}
            </span>
            <span class="muted" style="margin-left: 8px">{{ item.reason }}</span>
            <span v-if="item.type === 'ADVANCE'" class="muted" style="margin-left: 8px">
              {{ item.settlement_id ? '已核销' : '未核销' }}
            </span>
          </div>
          <div class="row">
            <el-tag>{{ item.status }}</el-tag>
            <el-button v-if="scope === 'mine' && item.status === 'PENDING'" size="small" @click="withdraw(item.id)">撤回</el-button>
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
      <template v-if="form.type === 'REIMBURSEMENT'">
        <el-date-picker v-model="form.occurred_on" type="date" value-format="YYYY-MM-DD" placeholder="费用发生日期" style="margin-top: 10px; width: 100%" />
        <div class="row" style="margin-top: 10px">
          <el-upload :show-file-list="false" :http-request="uploadInvoice" accept="image/*,application/pdf">
            <el-button>上传发票（至少 1 张）</el-button>
          </el-upload>
          <span class="muted">{{ invoiceIds.length }} 个附件</span>
        </div>
      </template>
      <template v-else>
        <el-input v-model="form.expected_usage" placeholder="预计用途（1~200 字）" style="margin-top: 10px" />
        <el-date-picker v-model="form.expected_settle_on" type="date" value-format="YYYY-MM-DD" placeholder="预计核销日期（须晚于今日）" style="margin-top: 10px; width: 100%" />
      </template>
      <el-select v-model="form.approval_flow_id" placeholder="审批流程" style="margin-top: 10px; width: 100%">
        <el-option v-for="f in flows" :key="f.id" :label="`${f.name}（${f.mode === 'HALF_MAJORITY' ? '半数同意' : '指定负责人'}）`" :value="f.id" />
      </el-select>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showSettle" title="备用金核销" width="600px">
      <el-select v-model="settle.advance_id" placeholder="选择已通过且未核销的备用金" style="width: 100%">
        <el-option v-for="a in advances" :key="a.id" :label="`#${a.id} ¥${a.amount} ${a.reason}`" :value="a.id" />
      </el-select>
      <el-select v-model="settle.reimbursement_ids" multiple placeholder="选择关联的凭票报销单（已通过、未核销）" style="margin-top: 10px; width: 100%">
        <el-option v-for="r in reimbursements" :key="r.id" :label="`#${r.id} ¥${r.amount} ${r.reason}`" :value="r.id" />
      </el-select>
      <p class="muted" style="margin: 10px 0 0">
        差额 = 关联报销合计 − 预借额：{{ diffText }}
      </p>
      <el-input v-model="settle.reason" type="textarea" :rows="2" placeholder="核销说明（1~500 字）" style="margin-top: 10px" />
      <el-select v-model="settle.approval_flow_id" placeholder="审批流程" style="margin-top: 10px; width: 100%">
        <el-option v-for="f in flows" :key="f.id" :label="`${f.name}（${f.mode === 'HALF_MAJORITY' ? '半数同意' : '指定负责人'}）`" :value="f.id" />
      </el-select>
      <template #footer>
        <el-button @click="showSettle = false">取消</el-button>
        <el-button type="primary" @click="submitSettle">提交核销</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { approvalApi, attachmentApi, claimApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'

const auth = useAuthStore()
const scope = ref('mine')
const items = ref([])
const flows = ref([])
const invoiceIds = ref([])
const advances = ref([])
const reimbursements = ref([])
const showCreate = ref(false)
const showSettle = ref(false)
const form = reactive({
  type: 'REIMBURSEMENT', amount: '', reason: '', occurred_on: '',
  expected_usage: '', expected_settle_on: '', approval_flow_id: null
})
const settle = reactive({ advance_id: null, reimbursement_ids: [], reason: '', approval_flow_id: null })

const typeLabel = (t) => ({ REIMBURSEMENT: '报销', ADVANCE: '备用金', SETTLEMENT: '核销' }[t] || t)

// 金额均为后端返回的两位小数字符串，这里仅做展示用的分（整数）运算，避免浮点误差
const cents = (v) => Math.round(Number(v) * 100)
const diffText = computed(() => {
  const advance = advances.value.find((a) => a.id === settle.advance_id)
  if (!advance || !settle.reimbursement_ids.length) return '-'
  const total = reimbursements.value
    .filter((r) => settle.reimbursement_ids.includes(r.id))
    .reduce((sum, r) => sum + cents(r.amount), 0)
  const diff = total - cents(advance.amount)
  const text = (Math.abs(diff) / 100).toFixed(2)
  if (diff < 0) return `多退 ¥${text}（登记退回现金，冲减支出）`
  if (diff > 0) return `少补 ¥${text}（不足部分补发，计入支出）`
  return '刚好核销，支出不变'
})

async function load() {
  try {
    const data = await claimApi.list({ scope: scope.value })
    items.value = data.results || data || []
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function loadFlows() {
  try {
    const data = await approvalApi.flows('EXPENSE')
    flows.value = data.results || data || []
  } catch (e) {
    flows.value = []
  }
}

function openCreate() {
  showCreate.value = true
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
    if (form.type === 'REIMBURSEMENT') {
      await claimApi.createReimbursement({
        amount: form.amount, reason: form.reason, occurred_on: form.occurred_on,
        invoice_ids: invoiceIds.value, approval_flow_id: form.approval_flow_id
      })
    } else {
      await claimApi.createAdvance({
        amount: form.amount, reason: form.reason, expected_usage: form.expected_usage,
        expected_settle_on: form.expected_settle_on, approval_flow_id: form.approval_flow_id
      })
    }
    showCreate.value = false
    invoiceIds.value = []
    ElMessage.success('已提交审批')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function openSettle() {
  try {
    const [adv, reimb] = await Promise.all([
      claimApi.list({ scope: 'mine', type: 'ADVANCE', status: 'APPROVED', page_size: 100 }),
      claimApi.list({ scope: 'mine', type: 'REIMBURSEMENT', status: 'APPROVED', page_size: 100 })
    ])
    advances.value = (adv.results || []).filter((a) => !a.settlement_id)
    reimbursements.value = (reimb.results || []).filter((r) => !r.settlement_id)
    Object.assign(settle, { advance_id: null, reimbursement_ids: [], reason: '', approval_flow_id: null })
    showSettle.value = true
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function submitSettle() {
  try {
    await claimApi.createSettlement({ ...settle })
    showSettle.value = false
    ElMessage.success('核销已提交审批')
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
  await auth.fetchMe().catch(() => null)
  load()
  loadFlows()
})
</script>
