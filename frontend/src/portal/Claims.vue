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
      <div v-for="item in items" :key="item.id" class="list-item">
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
            <StatusTag :status="item.status" />
            <el-button v-if="scope === 'mine' && item.status === 'PENDING'" size="small" @click="withdraw(item.id)">撤回</el-button>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="showCreate" title="新建申请" width="760px">
      <div class="claim-form-wrap">
        <div class="claim-form">
          <div class="field-block">
            <label class="field-label">申请类型</label>
            <div class="type-cards" role="radiogroup" aria-label="申请类型">
              <button
                v-for="t in TYPE_CARDS" :key="t.value" type="button" class="type-card" role="radio"
                :class="{ 'is-selected': form.type === t.value }" :aria-checked="form.type === t.value" @click="form.type = t.value"
              >
                <span class="type-card-icon"><UiIcon :name="t.icon" /></span>
                <span><b>{{ t.label }}</b><small>{{ t.hint }}</small></span>
              </button>
            </div>
          </div>
          <div class="field-block">
            <label class="field-label" for="claim-amount">金额</label>
            <div class="money-input">
              <span class="money-cur">¥</span>
              <input id="claim-amount" v-model="form.amount" class="mono" inputmode="decimal" placeholder="0.00" aria-label="金额" />
            </div>
            <span class="field-hint">最多两位小数</span>
          </div>
          <div class="field-block">
            <label class="field-label">事由</label>
            <el-input v-model="form.reason" type="textarea" :rows="3" placeholder="事由（1~500 字）" />
            <span class="field-hint mono field-count">{{ form.reason.length }} / 500</span>
          </div>
          <template v-if="form.type === 'REIMBURSEMENT'">
            <div class="field-block">
              <label class="field-label">费用发生日期</label>
              <el-date-picker v-model="form.occurred_on" type="date" value-format="YYYY-MM-DD" placeholder="费用发生日期" style="width: 100%" />
            </div>
            <div class="field-block">
              <label class="field-label">附件（发票，至少 1 张）</label>
              <el-upload drag class="drop-zone" :show-file-list="false" :http-request="uploadInvoice" accept="image/*,application/pdf">
                <UiIcon name="upload" class="drop-icon" />
                <div class="drop-title">拖拽文件到这里，或点击上传</div>
                <div class="field-hint">支持图片 / PDF</div>
              </el-upload>
              <div class="file-list">
                <div v-for="f in invoiceFiles" :key="f.id" class="file-row">
                  <UiIcon name="clip" />
                  <span class="file-name">{{ f.name }}</span>
                  <span class="muted mono">{{ fileSize(f.size) }}</span>
                  <button type="button" class="file-remove" :aria-label="`删除 ${f.name}`" @click="removeInvoice(f.id)"><UiIcon name="close" /></button>
                </div>
              </div>
              <span class="muted">{{ invoiceIds.length }} 个附件</span>
            </div>
          </template>
          <template v-else>
            <div class="field-block">
              <label class="field-label">预计用途</label>
              <el-input v-model="form.expected_usage" placeholder="预计用途（1~200 字）" />
            </div>
            <div class="field-block">
              <label class="field-label">预计核销日期</label>
              <el-date-picker v-model="form.expected_settle_on" type="date" value-format="YYYY-MM-DD" placeholder="预计核销日期（须晚于今日）" style="width: 100%" />
            </div>
          </template>
          <div class="field-block">
            <label class="field-label">审批流程</label>
            <el-select v-model="form.approval_flow_id" placeholder="审批流程" style="width: 100%">
              <el-option v-for="f in flows" :key="f.id" :label="`${f.name}（${f.mode === 'HALF_MAJORITY' ? '半数同意' : '指定负责人'}）`" :value="f.id" />
            </el-select>
          </div>
        </div>
        <aside class="claim-aside">
          <div class="claim-flow">
            <div class="card-head"><h4 class="title title-flat">审批流程预览</h4><span v-if="selectedFlow" class="mode-tag">{{ flowModeText(selectedFlow.mode) }}</span></div>
            <ol class="claim-steps">
              <li class="claim-step is-done">
                <span class="claim-step-node"><UiIcon name="check" /></span>
                <span><b>提交申请</b><small>提交后、审批前可撤回</small></span>
              </li>
              <li class="claim-step is-current">
                <span class="claim-step-node">2</span>
                <span><b>{{ selectedFlow ? selectedFlow.name : '审批' }}</b><small>不可审批本人提交的申请</small></span>
              </li>
              <li class="claim-step">
                <span class="claim-step-node">3</span>
                <span><b>审批结果</b><small>通过或未通过</small></span>
              </li>
            </ol>
          </div>
          <div class="claim-summary">
            <div class="label">本次申请</div>
            <div class="claim-summary-amount mono grad-text">¥{{ form.amount || '0.00' }}</div>
            <div class="muted">{{ typeLabel(form.type) }}<template v-if="form.type === 'REIMBURSEMENT'"> · {{ invoiceIds.length }} 个附件</template><template v-if="selectedFlow"> · {{ selectedFlow.name }}</template></div>
          </div>
        </aside>
      </div>
      <template #footer>
        <div class="form-actions-sticky">
          <el-button @click="showCreate = false">取消</el-button>
          <el-button type="primary" @click="create">提交</el-button>
        </div>
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
        <div class="form-actions-sticky">
          <el-button @click="showSettle = false">取消</el-button>
          <el-button type="primary" @click="submitSettle">提交核销</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { approvalApi, attachmentApi, claimApi } from '@/shared/api'
import StatusTag from './StatusTag.vue'
import UiIcon from './UiIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'

const auth = useAuthStore()
const scope = ref('mine')
const items = ref([])
const flows = ref([])
const invoiceIds = ref([])
// 附件列表仅用于展示文件名 / 大小，提交仍用 invoiceIds
const invoiceFiles = ref([])
const TYPE_CARDS = [
  { value: 'REIMBURSEMENT', label: '报销', hint: '已垫付费用，凭票报销', icon: 'receipt' },
  { value: 'ADVANCE', label: '备用金预借', hint: '先借后用，事后核销', icon: 'coin' }
]
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
const selectedFlow = computed(() => flows.value.find((f) => f.id === form.approval_flow_id) || null)
const flowModeText = (mode) => (mode === 'HALF_MAJORITY' ? '半数同意' : '指定负责人')
const fileSize = (n) => (n >= 1048576 ? `${(n / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round((n || 0) / 1024))} KB`)

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
    invoiceFiles.value.push({ id: uploaded.id, name: file.name, size: file.size })
    ElMessage.success('已上传')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

function removeInvoice(id) {
  invoiceIds.value = invoiceIds.value.filter((x) => x !== id)
  invoiceFiles.value = invoiceFiles.value.filter((f) => f.id !== id)
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
    invoiceFiles.value = []
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
