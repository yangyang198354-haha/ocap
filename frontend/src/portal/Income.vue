<template>
  <div class="page">
    <div class="card">
      <h3 class="title">收入表</h3>
      <p class="muted">
        支持逐条录入（一次最多 {{ limits.income_manual_max_records || 500 }} 条），也支持 CSV / xlsx 批量导入（≤5MB、≤{{ limits.income_import_max_rows || 5000 }} 行）。导入时重复行与错误行会被跳过并提示行号，其余行照常导入；
        录入后提交审批，通过后生效。<template v-if="amountMax">单笔金额上限 ¥{{ amountMax }}。</template>
      </p>
      <div class="row">
        <el-button type="primary" @click="openCreate">逐条录入</el-button>
        <el-upload :show-file-list="false" :http-request="importFile" accept=".csv,.xlsx">
          <el-button>批量导入</el-button>
        </el-upload>
        <el-select v-model="flowId" placeholder="审批流程（提交时使用）" style="width: 240px">
          <el-option v-for="f in flows" :key="f.id" :label="`${f.name}（${f.mode === 'HALF_MAJORITY' ? '半数同意' : '指定负责人'}）`" :value="f.id" />
        </el-select>
      </div>
      <div v-if="skipped.length" style="margin-top: 10px">
        <p class="muted" style="margin: 0">已跳过 {{ skipped.length }} 行：</p>
        <div v-for="(s, i) in skipped" :key="i" class="muted">第 {{ s.row }} 行：{{ s.reason === 'DUPLICATE' ? '重复' : '错误' }}（{{ s.detail }}）</div>
      </div>
    </div>
    <div class="card">
      <el-empty v-if="!items.length" description="暂无收入表" />
      <div v-for="item in items" :key="item.id" class="list-item">
        <div class="row" style="justify-content: space-between">
          <div>
            <strong>¥{{ item.total_amount }}</strong>
            <span class="muted" style="margin-left: 8px">{{ item.period_start }} ~ {{ item.period_end }}</span>
            <el-tag size="small" style="margin-left: 8px">{{ textOf(INCOME_STATUS_TEXT, item.status) }}</el-tag>
          </div>
          <div class="row">
            <el-button size="small" @click="showDetail(item.id)">明细</el-button>
            <el-button v-if="item.status === 'DRAFT'" size="small" @click="submit(item)">提交</el-button>
            <el-button v-if="item.status === 'WITHDRAWN'" size="small" @click="submit(item)">重新提交</el-button>
            <el-button v-if="item.status === 'REJECTED'" size="small" @click="openReissue(item)">重新发起</el-button>
            <el-button v-if="item.status === 'PENDING'" size="small" @click="withdraw(item.id)">撤回</el-button>
            <el-button v-if="item.status === 'EFFECTIVE' && item.can_void" size="small" type="danger" @click="voidSheet(item.id)">作废</el-button>
          </div>
        </div>
        <div v-if="item.status === 'REJECTED' || item.origin_id || item.reopened_by_id" class="muted" style="margin-top: 4px">
          <span v-if="item.status === 'REJECTED'">该收入表已结束（审批未通过），如需再次提交请新建。</span>
          <span v-if="item.origin_id">重新发起自 #{{ item.origin_id }}</span>
          <span v-if="item.reopened_by_id">已由 #{{ item.reopened_by_id }} 重新发起</span>
        </div>
      </div>
      <PagerBar :total="total" :page="page" :page-size="pageSize" @change="gotoPage" />
    </div>

    <el-dialog v-model="showCreate" title="逐条录入收入" width="560px">
      <p v-if="originId" class="muted">重新发起自 #{{ originId }}（原收入表已结束，本表独立审批）</p>
      <div v-for="(r, i) in form.records" :key="i" class="list-item" style="padding-top: 0; margin-bottom: 8px">
        <el-date-picker v-model="r.occurred_on" type="date" value-format="YYYY-MM-DD" placeholder="日期" style="width: 100%" />
        <el-input v-model="r.amount" placeholder="金额（最多两位小数）" style="margin-top: 6px" />
        <el-input v-model="r.category" placeholder="收入类别" maxlength="32" style="margin-top: 6px" />
        <el-input v-model="r.source_note" placeholder="来源说明（勿含个人姓名/手机号）" maxlength="200" style="margin-top: 6px" />
        <el-input v-model="r.remark" placeholder="备注（选填）" maxlength="200" style="margin-top: 6px" />
        <el-button v-if="form.records.length > 1" size="small" style="margin-top: 6px" @click="form.records.splice(i, 1)">删除此条</el-button>
      </div>
      <el-button size="small" @click="form.records.push(newRecord())">再加一条</el-button>
      <div class="row" style="margin-top: 10px">
        <el-upload :show-file-list="false" :http-request="uploadVoucher" accept="image/*,application/pdf">
          <el-button>上传凭证附件</el-button>
        </el-upload>
        <span class="muted">{{ voucherIds.length }} 个附件</span>
      </div>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">保存为草稿</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDetailDialog" title="收入表明细" width="640px">
      <p v-if="detail?.status === 'REJECTED'" class="muted">该收入表已结束（审批未通过），如需再次提交请新建。</p>
      <p v-if="detail?.origin_id" class="muted">重新发起自 #{{ detail.origin_id }}</p>
      <p v-if="detail?.reopened_by_id" class="muted">已由 #{{ detail.reopened_by_id }} 重新发起</p>
      <el-table :data="detail?.records || []" size="small">
        <el-table-column prop="line_no" label="#" width="50" />
        <el-table-column prop="occurred_on" label="日期" width="110" />
        <el-table-column prop="amount" label="金额" width="100" />
        <el-table-column prop="category" label="类别" width="100" />
        <el-table-column prop="source_note" label="来源说明" min-width="120" />
      </el-table>
      <div class="row" v-if="detail?.attachments?.length" style="margin-top: 8px">
        <el-link v-for="a in detail.attachments" :key="a.id" :href="apiUrl(`/attachments/${a.id}/download`)" target="_blank">{{ a.name }}</el-link>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { approvalApi, attachmentApi, incomeApi, meApi } from '@/shared/api'
import { apiUrl } from '@/shared/http'
import PagerBar from '@/shared/PagerBar.vue'
import { errorText, moneyText } from '@/shared/format'
import { INCOME_STATUS_TEXT, textOf } from '@/shared/labels'
import { confirmDanger } from '@/shared/confirm'
import { usePaging } from '@/shared/usePaging'

const { items, total, page, pageSize, reload, goto } = usePaging({ fetch: (params) => incomeApi.adminList(params) })
const limits = ref({})
const amountMax = ref('')
const flows = ref([])
const flowId = ref(null)
const skipped = ref([])
const showCreate = ref(false)
const showDetailDialog = ref(false)
const detail = ref(null)
const originId = ref(null)
const voucherIds = ref([])
const newRecord = () => ({ occurred_on: '', amount: '', category: '', source_note: '', remark: '' })
const form = reactive({ records: [newRecord()] })

async function load() {
  try {
    await reload()
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

async function loadLimits() {
  try {
    const data = await meApi.limits()
    limits.value = data && !Array.isArray(data) ? data : {}
    amountMax.value = moneyText(limits.value.claim_amount_max)
  } catch (e) {
    limits.value = {}
  }
}

function openCreate() {
  form.records = [newRecord()]
  voucherIds.value = []
  originId.value = null
  showCreate.value = true
}

// 失败收入表只能新建：复制原表明细作为新表初始内容（REQ-FUNC-271/273）
async function openReissue(item) {
  try {
    const origin = await incomeApi.adminDetail(item.id)
    form.records = (origin.records || []).map((r) => ({
      occurred_on: r.occurred_on, amount: r.amount, category: r.category,
      source_note: r.source_note, remark: r.remark
    }))
    if (!form.records.length) form.records = [newRecord()]
    voucherIds.value = []
    originId.value = item.id
    showCreate.value = true
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function uploadVoucher({ file }) {
  try {
    const uploaded = await attachmentApi.upload(file, 'INCOME_VOUCHER')
    voucherIds.value.push(uploaded.id)
    ElMessage.success('已上传')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function create() {
  try {
    await incomeApi.create({ records: form.records, voucher_ids: voucherIds.value,
      origin_id: originId.value || undefined })
    showCreate.value = false
    originId.value = null
    ElMessage.success('已保存为草稿，请选择审批流程后提交')
    load()
  } catch (e) {
    const rows = e.details?.errors
    ElMessage.error(rows?.length ? `第 ${rows[0].row} 条：${rows[0].detail}` : errorText(e))
  }
}

async function importFile({ file }) {
  try {
    const data = await incomeApi.importFile(file)
    const summary = data.import_summary || {}
    skipped.value = summary.errors || []
    if (!summary.imported) ElMessage.warning('全部行均被跳过，未创建收入表')
    else ElMessage.success(`导入 ${summary.imported} 行，跳过 ${summary.failed} 行`)
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function showDetail(id) {
  try {
    detail.value = await incomeApi.adminDetail(id)
    showDetailDialog.value = true
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function submit(item) {
  if (!flowId.value) return ElMessage.warning('请选择审批流程')
  try {
    if (item.status === 'WITHDRAWN') await incomeApi.resubmit(item.id, flowId.value)
    else await incomeApi.submit(item.id, flowId.value)
    ElMessage.success('已提交审批')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function withdraw(id) {
  if (!(await confirmDanger('withdrawIncome'))) return
  try {
    await incomeApi.withdraw(id)
    ElMessage.success('已撤回')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function voidSheet(id) {
  if (!(await confirmDanger('voidIncome'))) return
  try {
    await incomeApi.voidSheet(id)
    ElMessage.success('已作废')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(async () => {
  load()
  loadLimits()
  try {
    const data = await approvalApi.flows('INCOME')
    flows.value = data.results || data || []
  } catch (e) {
    flows.value = []
  }
})
</script>
