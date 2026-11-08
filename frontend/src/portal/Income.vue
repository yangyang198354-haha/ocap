<template>
  <div class="page">
    <div class="card">
      <h3 class="title">收入表</h3>
      <p class="muted">支持 CSV / xlsx 导入（≤5MB、≤5000 行，错误率超过 2% 将拒绝导入）。导入后提交审批，通过后生效。</p>
      <div class="row">
        <el-upload :show-file-list="false" :http-request="importFile" accept=".csv,.xlsx">
          <el-button type="primary">导入收入表</el-button>
        </el-upload>
        <el-select v-model="flowId" placeholder="审批流程" style="width: 220px">
          <el-option v-for="f in flows" :key="f.id" :label="`${f.name}（${f.mode}）`" :value="f.id" />
        </el-select>
      </div>
    </div>
    <div class="card">
      <el-empty v-if="!items.length" description="暂无收入表" />
      <div v-for="item in items" :key="item.id" style="padding: 10px 0; border-bottom: 1px solid #f0f1f3">
        <div class="row" style="justify-content: space-between">
          <div>
            <strong>¥{{ item.total_amount }}</strong>
            <span class="muted" style="margin-left: 8px">{{ item.period_start }} ~ {{ item.period_end }}</span>
            <el-tag size="small" style="margin-left: 8px">{{ item.status }}</el-tag>
          </div>
          <div class="row">
            <el-button v-if="['DRAFT', 'REJECTED'].includes(item.status)" size="small" @click="submit(item.id)">
              {{ item.status === 'DRAFT' ? '提交' : '重新提交' }}
            </el-button>
            <el-button v-if="item.status === 'PENDING'" size="small" @click="withdraw(item.id)">撤回</el-button>
            <el-button v-if="item.status === 'APPROVED'" size="small" type="danger" @click="voidSheet(item.id)">作废</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { approvalApi, incomeApi } from '@/shared/api'
import { errorText } from '@/shared/format'

const items = ref([])
const flows = ref([])
const flowId = ref(null)

async function load() {
  try {
    const data = await incomeApi.adminList()
    items.value = data.results || data || []
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function importFile({ file }) {
  try {
    const sheet = await incomeApi.importFile(file)
    ElMessage.success(`导入成功，合计 ¥${sheet.total_amount}`)
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function submit(id) {
  if (!flowId.value) return ElMessage.warning('请选择审批流程')
  try {
    await incomeApi.submit(id, flowId.value)
    ElMessage.success('已提交审批')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function withdraw(id) {
  try {
    await incomeApi.withdraw(id)
    ElMessage.success('已撤回')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function voidSheet(id) {
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
  try {
    const data = await approvalApi.flows('INCOME')
    flows.value = data.results || data || []
  } catch (e) {
    flows.value = []
  }
})
</script>
