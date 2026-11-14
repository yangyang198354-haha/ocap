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
          </div>
          <div class="row">
            <el-button size="small" type="success" @click="decide(task, 'APPROVE')">同意</el-button>
            <el-button size="small" type="danger" @click="decide(task, 'REJECT')">拒绝</el-button>
          </div>
        </div>
      </div>
      <PagerBar :total="total" :page="page" :page-size="pageSize" @change="gotoPage" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { approvalApi } from '@/shared/api'
import PagerBar from '@/shared/PagerBar.vue'
import { errorText, formatDateTime } from '@/shared/format'
import { FLOW_SCOPE_TEXT, textOf } from '@/shared/labels'
import { usePaging } from '@/shared/usePaging'

const scope = ref('')
const filters = computed(() => ({ scope: scope.value || undefined }))
const { items: tasks, total, page, pageSize, reload, goto, resetAndLoad: pagingReset } = usePaging({
  fetch: ({ scope: s, ...params }) => approvalApi.tasks(s, params), filters
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

async function decide(task, action) {
  try {
    await approvalApi.decide(task.instance_id, action)
    ElMessage.success('已处理')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
