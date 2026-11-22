<template>
  <div class="page">
    <div class="card">
      <h3 class="title">审批待办</h3>
      <el-select v-model="scope" placeholder="全部类型" clearable style="width: 180px" @change="resetAndLoad">
        <el-option label="决议" value="RESOLUTION" />
        <el-option label="报销/备用金" value="EXPENSE" />
        <el-option label="收入表" value="INCOME" />
      </el-select>
    </div>
    <div class="card">
      <el-empty v-if="!tasks.length" description="暂无待办" />
      <div v-for="task in tasks" :key="task.instance_id" class="list-item">
        <div class="row" style="justify-content: space-between">
          <div>
            <strong>{{ task.title || task.subject_title || textOf(FLOW_SCOPE_TEXT, task.scope) }}</strong>
            <span class="muted" style="margin-left: 8px">{{ textOf(FLOW_SCOPE_TEXT, task.scope) }} · {{ formatDateTime(task.submitted_at) }}</span>
            <div class="muted">当前第 {{ task.step_order }} 步 · {{ task.step_name }}（{{ textOf(STEP_STRATEGY_LABELS, task.step_strategy) }}）</div>
          </div>
          <div class="row">
            <el-button size="small" @click="openTimeline(task)">查看进度</el-button>
            <el-button size="small" type="success" @click="openDecide(task, 'APPROVE')">同意</el-button>
            <el-button size="small" type="danger" @click="openDecide(task, 'REJECT')">拒绝</el-button>
          </div>
        </div>
      </div>
      <PagerBar :total="total" :page="page" :page-size="pageSize" @change="gotoPage" />
    </div>

    <el-dialog v-model="showDecide" :title="pendingAction === 'APPROVE' ? '通过审批' : '拒绝审批'" width="480px">
      <p v-if="currentTask" class="muted">{{ currentTask.subject_title }} · 第 {{ currentTask.step_order }} 步 {{ currentTask.step_name }}</p>
      <el-input v-model="comment" type="textarea" :rows="3" maxlength="500" show-word-limit
                placeholder="审批意见（可选，最多 500 字）" />
      <template #footer>
        <el-button @click="showDecide = false">取消</el-button>
        <el-button type="primary" @click="submitDecision">确认</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showTimeline" title="审批过程" width="640px">
      <ApprovalTimeline v-if="timelineId" :instance-id="timelineId" />
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { approvalApi } from '@/shared/api'
import ApprovalTimeline from './ApprovalTimeline.vue'
import PagerBar from '@/shared/PagerBar.vue'
import { errorText, formatDateTime } from '@/shared/format'
import { FLOW_SCOPE_TEXT, STEP_STRATEGY_LABELS, textOf } from '@/shared/labels'
import { usePaging } from '@/shared/usePaging'

const scope = ref('')
const filters = computed(() => ({ scope: scope.value || undefined }))
const { items: tasks, total, page, pageSize, reload, goto, resetAndLoad: pagingReset } = usePaging({
  fetch: ({ scope: s, ...params }) => approvalApi.tasks(s, params), filters
})

const showDecide = ref(false)
const showTimeline = ref(false)
const currentTask = ref(null)
const pendingAction = ref('APPROVE')
const comment = ref('')
const timelineId = ref(null)

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

function openDecide(task, action) {
  currentTask.value = task
  pendingAction.value = action
  comment.value = ''
  showDecide.value = true
}

function openTimeline(task) {
  timelineId.value = task.instance_id
  showTimeline.value = true
}

async function submitDecision() {
  try {
    await approvalApi.decide(currentTask.value.instance_id, pendingAction.value, comment.value)
    showDecide.value = false
    ElMessage.success('已处理')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
