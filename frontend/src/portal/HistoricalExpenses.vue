<!-- MOD-210：历史支出批量导入（仅业委会成员；导入后提交审批，通过后写入台账） -->
<template>
  <div class="page" v-if="auth.isCommittee">
    <PageHead title="历史支出导入">
      <el-button @click="downloadTemplate('xlsx')">下载 xlsx 模板</el-button>
      <el-button @click="downloadTemplate('csv')">下载 csv 模板</el-button>
    </PageHead>
    <div class="card">
      <div class="row" style="margin-top: 10px">
        <AccountSelect v-model="accountId" placeholder="入账账户" style="width: 220px" />
        <el-select v-model="flowId" placeholder="审批流程" style="width: 240px">
          <el-option
            v-for="f in flows"
            :key="f.id"
            :label="`${f.name}（${f.mode === 'HALF_MAJORITY' ? '半数以上参与者同意' : '指定负责人'}）`"
            :value="f.id"
          />
        </el-select>
        <el-upload :show-file-list="false" :http-request="uploadFile" accept=".csv,.xlsx">
          <el-button type="primary">批量导入</el-button>
        </el-upload>
      </div>
      <p class="muted">
        仅用于补录系统上线前的历史支出：导入后提交审批，审批通过后才写入台账，不生成报销单/备用金申请。
        如导入有误，请撤回或等待驳回后重新导入。模板列：日期、金额、支出类别、用途/事由、备注。
      </p>
    </div>

    <div v-if="result" class="card">
      <div class="row" style="justify-content: space-between">
        <h2 class="title title-flat" style="margin: 0">最近一次导入结果</h2>
        <el-button size="small" @click="result = null">关闭</el-button>
      </div>
      <p class="muted" style="margin-top: 8px">
        总行数 {{ result.total_rows }}；
        <template v-if="result.batch">
          有效 {{ result.batch.imported_rows }}、重复 {{ result.batch.skipped_rows }}、失败 {{ result.batch.failed_rows }}，
          金额合计 ¥{{ result.batch.total_amount }}，已提交审批
        </template>
        <template v-else>没有可导入的有效行，未创建批次</template>
      </p>
      <el-table v-if="result.errors && result.errors.length" :data="result.errors" size="small">
        <el-table-column prop="row" label="行号" width="80" />
        <el-table-column prop="reason" label="类型" width="100">
          <template #default="{ row }">{{ row.reason === 'DUPLICATE' ? '重复' : '错误' }}</template>
        </el-table-column>
        <el-table-column prop="detail" label="原因" />
      </el-table>
    </div>

    <div class="card">
      <el-table :data="items" size="small">
        <el-table-column label="导入时间" width="150">
          <template #default="{ row }">{{ datetime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="file_name" label="文件" min-width="180" />
        <el-table-column label="入账账户" min-width="140">
          <template #default="{ row }">{{ row.account_name || '默认账户' }}</template>
        </el-table-column>
        <el-table-column prop="imported_by_label" label="操作人" width="120" />
        <el-table-column prop="total_rows" label="总行数" width="80" />
        <el-table-column prop="imported_rows" label="成功" width="70" />
        <el-table-column prop="skipped_rows" label="重复" width="70" />
        <el-table-column prop="failed_rows" label="失败" width="70" />
        <el-table-column label="金额合计" min-width="120" align="right" class-name="business-money">
          <template #default="{ row }">¥{{ row.total_amount }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openDetail(row)">明细</el-button>
            <el-button v-if="row.status === 'PENDING'" size="small" @click="withdraw(row)">撤回</el-button>
            <el-button v-if="row.status === 'IMPORTED'" size="small" type="danger" @click="openVoid(row)">整批作废</el-button>
          </template>
        </el-table-column>
      </el-table>
      <PagerBar :total="total" :page="page" :page-size="pageSize" @change="gotoPage" />
    </div>

    <el-dialog v-model="showDetail" title="历史支出批次明细" width="860px">
      <template v-if="detail">
        <p class="muted">
          {{ detail.file_name }} · {{ datetime(detail.created_at) }} · 操作人 {{ detail.imported_by_label }}
          · 账户 {{ detail.account_name || '默认账户' }} · 状态 {{ statusText(detail.status) }}
          · 金额合计 ¥{{ detail.total_amount }}
          <template v-if="detail.status === 'VOIDED'"> · 已作废：{{ detail.void_reason }}</template>
        </p>
        <el-table :data="detail.rows || []" size="small" max-height="460">
          <el-table-column prop="line_no" label="#" width="60" />
          <el-table-column prop="occurred_on" label="日期" width="110" />
          <el-table-column prop="amount" label="金额" min-width="115" align="right" class-name="business-money" />
          <el-table-column prop="category" label="支出类别" width="110" />
          <el-table-column prop="purpose" label="用途/事由" min-width="160" />
          <el-table-column prop="remark" label="备注" min-width="120" />
          <el-table-column label="结果" width="100">
            <template #default="{ row }">
              <el-tag :type="rowStatusTagType(row.status)" size="small">{{ rowStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="error_message" label="原因" min-width="150" />
        </el-table>
      </template>
    </el-dialog>

    <el-dialog v-model="showVoid" title="整批作废" width="440px">
      <p class="muted">作废后该批次写入的台账明细将失效，受影响的已生成报表会标记为过期；可重新导入同一批数据。</p>
      <el-input v-model="voidReason" type="textarea" :rows="3" maxlength="200" placeholder="作废原因（1~200 字，必填）" />
      <template #footer>
        <el-button @click="showVoid = false">取消</el-button>
        <el-button type="danger" @click="confirmVoid">确认作废</el-button>
      </template>
    </el-dialog>
  </div>
  <div v-else class="card">
    <el-empty description="仅主任、副主任或委员可使用历史支出导入" />
  </div>
</template>

<script setup>
import PageHead from '@/shared/PageHead.vue'
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { approvalApi, historicalExpenseApi } from '@/shared/api'
import PagerBar from '@/shared/PagerBar.vue'
import AccountSelect from '@/shared/AccountSelect.vue'
import { datetime, errorText } from '@/shared/format'
import { confirmDanger } from '@/shared/confirm'
import { usePaging } from '@/shared/usePaging'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const { items, total, page, pageSize, reload, goto } = usePaging({
  fetch: (params) => historicalExpenseApi.batches(params)
})
const result = ref(null)
const accountId = ref(null)
const flowId = ref(null)
const flows = ref([])
const showDetail = ref(false)
const detail = ref(null)
const showVoid = ref(false)
const voidTarget = ref(null)
const voidReason = ref('')

function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

async function downloadTemplate(fileType) {
  try {
    const blob = await historicalExpenseApi.template(fileType)
    saveBlob(blob, `历史支出导入模板.${fileType}`)
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function uploadFile({ file }) {
  if (!accountId.value) return ElMessage.warning('请选择入账账户')
  if (!flowId.value) return ElMessage.warning('请选择审批流程')
  try {
    result.value = await historicalExpenseApi.importFile(file, {
      accountId: accountId.value, flowId: flowId.value
    })
    if (result.value.batch) ElMessage.success('已导入并提交审批')
    else ElMessage.warning('没有可导入的有效行')
    reload()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

const STATUS_TEXT = {
  PENDING: '审批中', IMPORTED: '已入账', REJECTED: '已驳回', WITHDRAWN: '已撤回', VOIDED: '已作废'
}
const STATUS_TAG = {
  PENDING: 'warning', IMPORTED: 'success', REJECTED: 'danger', WITHDRAWN: 'info', VOIDED: 'info'
}
const statusText = (status) => STATUS_TEXT[status] || status
const statusTagType = (status) => STATUS_TAG[status] || 'info'
const ROW_TEXT = { PENDING: '待入账', IMPORTED: '成功', DUPLICATE: '重复', ERROR: '错误' }
const ROW_TAG = { PENDING: 'info', IMPORTED: 'success', DUPLICATE: 'warning', ERROR: 'danger' }
const rowStatusText = (status) => ROW_TEXT[status] || status
const rowStatusTagType = (status) => ROW_TAG[status] || 'info'

async function withdraw(row) {
  if (!(await confirmDanger('withdrawHistoricalExpense'))) return
  try {
    await historicalExpenseApi.withdrawBatch(row.id)
    ElMessage.success('已撤回')
    reload()
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

async function openDetail(row) {
  try {
    detail.value = await historicalExpenseApi.batchDetail(row.id)
    showDetail.value = true
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

function openVoid(row) {
  voidTarget.value = row
  voidReason.value = ''
  showVoid.value = true
}

async function confirmVoid() {
  const reason = voidReason.value.trim()
  if (!reason) return ElMessage.warning('请填写作废原因')
  try {
    await historicalExpenseApi.voidBatch(voidTarget.value.id, reason)
    ElMessage.success('已作废')
    showVoid.value = false
    reload()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(async () => {
  await auth.fetchMe().catch(() => null)
  if (!auth.isCommittee) return // AC-338-02：无权限不发起导入请求
  try {
    await reload()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
  try {
    const data = await approvalApi.flows('INCOME')
    flows.value = data.results || data || []
  } catch (e) {
    flows.value = []
  }
})
</script>
