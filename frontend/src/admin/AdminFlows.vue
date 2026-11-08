<template>
  <div class="page">
    <div class="card">
      <div class="row" style="justify-content: space-between">
        <h3 class="title" style="margin: 0">审批流程</h3>
        <el-button type="primary" @click="showCreate = true">新建流程</el-button>
      </div>
      <p class="muted">审批人只能从业委会成员中选择；财务类（报销/备用金/收入）不得自审，决议不回避。</p>
    </div>
    <div class="card">
      <el-table :data="flows" size="small">
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column prop="scope" label="适用" width="130" />
        <el-table-column prop="mode" label="方式" width="150" />
        <el-table-column prop="is_active" label="启用" width="90" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="toggle(row)">{{ row.is_active ? '停用' : '启用' }}</el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="showCreate" title="新建审批流程" width="520px">
      <el-input v-model="form.name" placeholder="流程名称" />
      <el-select v-model="form.scope" style="width: 100%; margin-top: 8px">
        <el-option label="决议" value="RESOLUTION" />
        <el-option label="财务（报销/备用金）" value="EXPENSE" />
        <el-option label="收入表" value="INCOME" />
      </el-select>
      <el-select v-model="form.mode" style="width: 100%; margin-top: 8px">
        <el-option label="指定负责人审批" value="DESIGNATED" />
        <el-option label="半数人员同意" value="HALF_MAJORITY" />
      </el-select>
      <el-input v-model="approversText" placeholder="审批人用户 ID，逗号分隔" style="margin-top: 8px" />
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import { errorText } from '@/shared/format'

const flows = ref([])
const showCreate = ref(false)
const approversText = ref('')
const form = reactive({ name: '', scope: 'RESOLUTION', mode: 'DESIGNATED' })

async function load() {
  try {
    const data = await admin.flows()
    flows.value = data.results || data || []
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function create() {
  const approver_ids = approversText.value.split(',').map((x) => Number(x.trim())).filter(Boolean)
  try {
    await admin.createFlow({ ...form, approver_ids })
    showCreate.value = false
    ElMessage.success('已创建')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function toggle(row) {
  try {
    await admin.updateFlow(row.id, { is_active: !row.is_active })
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function remove(row) {
  try {
    await admin.deleteFlow(row.id)
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
