<template>
  <div class="page">
    <div class="card">
      <h3 class="title">财务（报销 / 备用金）</h3>
      <p class="muted">
        管理员可查看全部报销、备用金与核销申请。收入表录入/审批与财务报表生成属于业委会成员权限，
        请在用户端“收入表”“财务报表”页面使用业委会成员账号操作。
      </p>
      <div class="row">
        <el-select v-model="type" placeholder="全部类型" clearable style="width: 160px" @change="resetAndLoad">
          <el-option label="报销" value="REIMBURSEMENT" /><el-option label="备用金" value="ADVANCE" /><el-option label="核销" value="SETTLEMENT" />
        </el-select>
        <el-select v-model="status" placeholder="全部状态" clearable style="width: 160px" @change="resetAndLoad">
          <el-option label="审批中" value="PENDING" /><el-option label="通过" value="APPROVED" />
          <el-option label="拒绝" value="REJECTED" /><el-option label="已撤回" value="WITHDRAWN" />
        </el-select>
      </div>
    </div>
    <div class="card amount-limit-card">
      <h3 class="title">金额上限</h3>
      <p class="muted">报销、备用金与收入表共用的单笔金额上限（元，正数、最多两位小数）；修改后对此后的新提交立即生效，已提交的记录不受影响。</p>
      <div class="row">
        <el-input v-model="amountMax" placeholder="金额上限" style="max-width: 220px" />
        <el-button type="primary" @click="saveAmountMax">保存</el-button>
      </div>
    </div>
    <div class="card">
      <el-table :data="claims" size="small">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="类型" width="130">
          <template #default="{ row }">{{ textOf(CLAIM_TYPE_TEXT, row.type) }}</template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="120" />
        <el-table-column prop="reason" label="事由" min-width="180" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">{{ textOf(CLAIM_STATUS_TEXT, row.status) }}</template>
        </el-table-column>
      </el-table>
      <PagerBar :total="total" :page="page" :page-size="pageSize" @change="gotoPage" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import PagerBar from '@/shared/PagerBar.vue'
import { errorText, moneyText } from '@/shared/format'
import { textOf } from '@/shared/labels'
import { CLAIM_STATUS_TEXT, CLAIM_TYPE_TEXT } from '@/shared/adminText'
import { usePaging } from '@/shared/usePaging'

const type = ref('')
const status = ref('')
const amountMax = ref('')
const filters = computed(() => ({ type: type.value || undefined, status: status.value || undefined }))
const { items: claims, total, page, pageSize, reload, goto, resetAndLoad: pagingReset } = usePaging({
  fetch: (params) => admin.claims(params), filters
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

async function loadConfig() {
  try {
    const data = await admin.systemConfigAll()
    amountMax.value = moneyText(data?.['claim.amount_max'])
  } catch (e) {
    amountMax.value = ''
  }
}

// 非法输入由后端 INVALID_VALUE 文案提示，原值不变（REQ-FUNC-161）
async function saveAmountMax() {
  try {
    const result = await admin.updateSystemConfig('claim.amount_max', amountMax.value)
    amountMax.value = moneyText(result?.value)
    ElMessage.success('金额上限已保存')
  } catch (e) {
    ElMessage.error(errorText(e))
    await loadConfig()
  }
}

onMounted(() => {
  load()
  loadConfig()
})
</script>
