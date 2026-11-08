<template>
  <div class="page">
    <div class="card">
      <h3 class="title">财务（报销 / 备用金）</h3>
      <p class="muted">
        管理员可查看全部报销、备用金与核销申请。收入表录入/审批与财务报表生成属于业委会成员权限，
        请在用户端“收入表”“财务报表”页面使用业委会成员账号操作。
      </p>
      <div class="row">
        <el-select v-model="type" placeholder="全部类型" clearable style="width: 160px" @change="load">
          <el-option label="报销" value="REIMBURSEMENT" /><el-option label="备用金" value="ADVANCE" /><el-option label="核销" value="SETTLEMENT" />
        </el-select>
        <el-select v-model="status" placeholder="全部状态" clearable style="width: 160px" @change="load">
          <el-option label="审批中" value="PENDING" /><el-option label="通过" value="APPROVED" />
          <el-option label="拒绝" value="REJECTED" /><el-option label="已撤回" value="WITHDRAWN" />
        </el-select>
      </div>
    </div>
    <div class="card">
      <el-table :data="claims" size="small">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="type" label="类型" width="130" />
        <el-table-column prop="amount" label="金额" width="120" />
        <el-table-column prop="reason" label="事由" min-width="180" />
        <el-table-column prop="status" label="状态" width="110" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import { errorText } from '@/shared/format'

const claims = ref([])
const type = ref('')
const status = ref('')

async function load() {
  try {
    const data = await admin.claims({ type: type.value || undefined, status: status.value || undefined })
    claims.value = data.results || data || []
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
