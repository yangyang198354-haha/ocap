<template>
  <div class="page">
    <PageHead title="审批流程">
      <el-button type="primary" @click="openCreate">新建流程</el-button>
    </PageHead>
    <div class="card">
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
        <el-table-column label="步骤数" width="90">
          <template #default="{ row }">{{ row.step_count || 0 }}</template>
        </el-table-column>
        <el-table-column label="启用" width="90">
          <template #default="{ row }">{{ yesNo(row.is_active) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260">
          <template #default="{ row }">
            <el-button size="small" @click="openDetail(row)">查看详情</el-button>
            <el-button size="small" @click="toggle(row)">{{ row.is_active ? '停用' : '启用' }}</el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <PagerBar :total="total" :page="page" :page-size="pageSize" @change="gotoPage" />
    </div>

    <el-dialog v-model="showCreate" title="新建审批流程" width="640px">
      <el-input v-model="form.name" placeholder="流程名称" maxlength="60" />
      <el-select v-model="form.scope" style="width: 100%; margin-top: 8px" @change="onScopeChange">
        <el-option label="决议" value="RESOLUTION" />
        <el-option label="财务（报销/备用金）" value="EXPENSE" />
        <el-option label="收入表" value="INCOME" />
      </el-select>
      <el-select v-model="form.mode" style="width: 100%; margin-top: 8px" @change="onModeChange">
        <el-option label="指定负责人审批" value="DESIGNATED" />
        <el-option v-if="form.scope === 'RESOLUTION'" label="半数以上参与者同意" value="HALF_MAJORITY" />
      </el-select>
      <div v-if="isHalfMajority" style="margin-top: 8px">
        <p class="muted">半数以上参与者同意：由全体业委会成员投票判定，无需设置审批人。</p>
        <p class="muted">无需设置审批人</p>
      </div>
      <template v-else>
        <StepsEditor :steps="createSteps" @add="addStep(createSteps)" @remove="(i) => removeStep(createSteps, i)"
                     @move="(i, d) => moveStep(createSteps, i, d)"
                     @add-approver="(i, u) => addStepApprover(createSteps[i], u)"
                     @remove-approver="(i, id) => removeStepApprover(createSteps[i], id)" />
        <el-button size="small" style="margin-top: 8px" @click="addStep(createSteps)">添加步骤</el-button>
      </template>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDetail" title="审批流程详情" width="680px">
      <template v-if="detailRow">
        <el-form label-width="96px">
          <el-form-item label="名称">
            <el-input v-model="editForm.name" :disabled="!editing" maxlength="60" />
          </el-form-item>
          <el-form-item label="适用范围">
            <el-select v-model="editForm.scope" :disabled="!editing" style="width: 100%">
              <el-option label="决议" value="RESOLUTION" />
              <el-option label="财务（报销/备用金）" value="EXPENSE" />
              <el-option label="收入表" value="INCOME" />
            </el-select>
          </el-form-item>
          <el-form-item label="审批方式">
            <el-select v-model="editForm.mode" :disabled="!editing" style="width: 100%">
              <el-option label="指定负责人审批" value="DESIGNATED" />
              <el-option v-if="editForm.scope === 'RESOLUTION'" label="半数以上参与者同意" value="HALF_MAJORITY" />
            </el-select>
          </el-form-item>
          <el-form-item label="启用">
            <el-switch v-model="editForm.is_active" :disabled="!editing" />
          </el-form-item>
          <el-form-item v-if="editForm.mode !== 'HALF_MAJORITY'" label="审批步骤">
            <div style="width: 100%">
              <div v-if="!editing">
                <div v-for="step in editSteps" :key="step.order" class="list-item">
                  <span><b>第 {{ step.order }} 步 · {{ step.name }}</b></span>
                  <span class="muted">{{ textOf(STEP_STRATEGY_LABELS, step.strategy) }} · {{ step.approvers.length }} 人</span>
                </div>
                <p v-if="!editSteps.length" class="muted">暂无步骤</p>
              </div>
              <template v-else>
                <StepsEditor :steps="editSteps" @add="addStep(editSteps)" @remove="(i) => removeStep(editSteps, i)"
                             @move="(i, d) => moveStep(editSteps, i, d)"
                             @add-approver="(i, u) => addStepApprover(editSteps[i], u)"
                             @remove-approver="(i, id) => removeStepApprover(editSteps[i], id)" />
                <el-button size="small" style="margin-top: 8px" @click="addStep(editSteps)">添加步骤</el-button>
              </template>
            </div>
          </el-form-item>
          <el-form-item v-else label="审批人">
            <div class="muted">无需设置审批人</div>
          </el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="showDetail = false">关闭</el-button>
        <el-button v-if="!editing" type="primary" @click="startEdit">编辑</el-button>
        <template v-else>
          <el-button @click="editing = false">取消编辑</el-button>
          <el-button type="primary" @click="saveEdit">保存</el-button>
        </template>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import PageHead from '@/shared/PageHead.vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import PagerBar from '@/shared/PagerBar.vue'
import { errorText } from '@/shared/format'
import { confirmDanger } from '@/shared/confirm'
import { APPROVAL_MODE_TEXT, FLOW_SCOPE_TEXT, STEP_STRATEGY_LABELS, textOf, yesNo } from '@/shared/labels'
import { usePaging } from '@/shared/usePaging'
import StepsEditor from './parts/StepsEditor.vue'

const { items: flows, total, page, pageSize, reload, goto } = usePaging({ fetch: (params) => admin.flows(params) })
const showCreate = ref(false)
const form = reactive({ name: '', scope: 'RESOLUTION', mode: 'DESIGNATED' })
const createSteps = ref([newStep()])
const isHalfMajority = computed(() => form.mode === 'HALF_MAJORITY')

const showDetail = ref(false)
const editing = ref(false)
const detailRow = ref(null)
const editForm = reactive({ name: '', scope: 'RESOLUTION', mode: 'DESIGNATED', is_active: true })
const editSteps = ref([])

function newStep() {
  return { name: '', strategy: 'ANY', approvers: [] }
}

function addStep(list) {
  if (Array.isArray(list)) list.push(newStep())
  else list.value.push(newStep())
}

function removeStep(list, index) {
  const rows = Array.isArray(list) ? list : list.value
  rows.splice(index, 1)
}

function moveStep(list, index, delta) {
  const rows = Array.isArray(list) ? list : list.value
  const target = index + delta
  if (target < 0 || target >= rows.length) return
  const [row] = rows.splice(index, 1)
  rows.splice(target, 0, row)
}

function addStepApprover(step, user) {
  if (user && !step.approvers.some((a) => a.id === user.id)) step.approvers.push(user)
}

function removeStepApprover(step, id) {
  step.approvers = step.approvers.filter((a) => a.id !== id)
}

function openCreate() {
  form.name = ''
  form.scope = 'RESOLUTION'
  form.mode = 'DESIGNATED'
  createSteps.value = [newStep()]
  showCreate.value = true
}

function openDetail(row) {
  detailRow.value = row
  editing.value = false
  editForm.name = row.name
  editForm.scope = row.scope
  editForm.mode = row.mode
  editForm.is_active = row.is_active
  editSteps.value = (row.steps || []).map((s, i) => ({
    order: s.order ?? i + 1,
    name: s.name, strategy: s.strategy, approvers: (s.approvers || []).map((a) => ({ ...a }))
  }))
  if (!editSteps.value.length && row.approvers?.length) {
    editSteps.value = [{ order: 1, name: row.name, strategy: 'ANY', approvers: row.approvers.map((a) => ({ ...a })) }]
  }
  showDetail.value = true
}

function startEdit() {
  editing.value = true
}

// 切到半数以上参与者同意：清空步骤；非决议范围不支持该方式
function onModeChange() {
  if (isHalfMajority.value) createSteps.value = []
}

function onScopeChange() {
  if (form.scope !== 'RESOLUTION' && form.mode === 'HALF_MAJORITY') form.mode = 'DESIGNATED'
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

function stepsPayload(rows) {
  return rows.map((s) => ({ name: s.name, strategy: s.strategy, approver_ids: s.approvers.map((a) => a.id) }))
}

async function create() {
  const payload = { ...form }
  if (form.mode === 'DESIGNATED') payload.steps = stepsPayload(createSteps.value)
  else payload.approver_ids = []
  try {
    await admin.createFlow(payload)
    showCreate.value = false
    ElMessage.success('已创建')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function saveEdit() {
  const payload = {
    name: editForm.name,
    scope: editForm.scope,
    mode: editForm.mode,
    is_active: editForm.is_active
  }
  if (editForm.mode === 'DESIGNATED') payload.steps = stepsPayload(editSteps.value)
  try {
    await admin.updateFlow(detailRow.value.id, payload)
    ElMessage.success('已保存')
    editing.value = false
    showDetail.value = false
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
    ElMessage.success('已删除')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>


