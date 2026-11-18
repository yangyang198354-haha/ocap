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
        <el-table-column label="适用" width="130">
          <template #default="{ row }">{{ textOf(FLOW_SCOPE_TEXT, row.scope) }}</template>
        </el-table-column>
        <el-table-column label="方式" width="150">
          <template #default="{ row }">{{ textOf(APPROVAL_MODE_TEXT, row.mode) }}</template>
        </el-table-column>
        <el-table-column label="启用" width="90">
          <template #default="{ row }">{{ yesNo(row.is_active) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="toggle(row)">{{ row.is_active ? '停用' : '启用' }}</el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <PagerBar :total="total" :page="page" :page-size="pageSize" @change="gotoPage" />
    </div>

    <el-dialog v-model="showCreate" title="新建审批流程" width="520px">
      <el-input v-model="form.name" placeholder="流程名称" />
      <el-select v-model="form.scope" style="width: 100%; margin-top: 8px" @change="onScopeChange">
        <el-option label="决议" value="RESOLUTION" />
        <el-option label="财务（报销/备用金）" value="EXPENSE" />
        <el-option label="收入表" value="INCOME" />
      </el-select>
      <el-select v-model="form.mode" style="width: 100%; margin-top: 8px" @change="onModeChange">
        <el-option label="指定负责人审批" value="DESIGNATED" />
        <el-option v-if="form.scope === 'RESOLUTION'" label="半数人员同意" value="HALF_MAJORITY" />
      </el-select>
      <div v-if="isHalfMajority" style="margin-top: 8px">
        <p class="muted">半数同意决议由全体业委会成员投票判定，无需设置审批人。</p>
      </div>
      <div v-else style="margin-top: 8px">
        <p class="muted">审批人（须是现任业委会成员，可多选）：</p>
        <p v-for="a in approvers" :key="a.id" class="row">
          <b>{{ a.nickname || a.account_no }}</b><el-tag size="small" type="info">{{ a.identity_label }}</el-tag>
          <el-button size="small" link @click="removeApprover(a.id)">移除</el-button>
        </p>
        <UserPicker :model-value="null" placeholder="搜索并添加审批人" @change="addApprover" />
      </div>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import PagerBar from '@/shared/PagerBar.vue'
import { errorText } from '@/shared/format'
import { confirmDanger } from '@/shared/confirm'
import { APPROVAL_MODE_TEXT, FLOW_SCOPE_TEXT, textOf, yesNo } from '@/shared/labels'
import { usePaging } from '@/shared/usePaging'
import UserPicker from './parts/UserPicker.vue'

const { items: flows, total, page, pageSize, reload, goto } = usePaging({ fetch: (params) => admin.flows(params) })
const showCreate = ref(false)
const approvers = ref([])
const form = reactive({ name: '', scope: 'RESOLUTION', mode: 'DESIGNATED' })
const isHalfMajority = computed(() => form.mode === 'HALF_MAJORITY')

// 切到半数同意：清空已选审批人（半数同意不设审批人）
function onModeChange() {
  if (isHalfMajority.value) approvers.value = []
}

// 非决议范围不支持半数同意：切走时回退为指定负责人
function onScopeChange() {
  if (form.scope !== 'RESOLUTION' && form.mode === 'HALF_MAJORITY') form.mode = 'DESIGNATED'
}

function addApprover(user) {
  if (user && !approvers.value.some((a) => a.id === user.id)) approvers.value.push(user)
}

function removeApprover(id) {
  approvers.value = approvers.value.filter((a) => a.id !== id)
}

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

async function create() {
  const approver_ids = isHalfMajority.value ? [] : approvers.value.map((a) => a.id)
  try {
    await admin.createFlow({ ...form, approver_ids })
    showCreate.value = false
    approvers.value = []
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
  if (!(await confirmDanger('deleteFlow', { name: row.name }))) return
  try {
    await admin.deleteFlow(row.id)
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
