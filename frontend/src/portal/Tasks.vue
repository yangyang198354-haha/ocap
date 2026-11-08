<template>
  <div class="page">
    <div class="card">
      <h3 class="title">审批待办</h3>
      <el-select v-model="scope" placeholder="全部类型" clearable style="width: 180px" @change="load">
        <el-option label="决议" value="RESOLUTION" />
        <el-option label="报销/备用金" value="EXPENSE" />
        <el-option label="收入表" value="INCOME" />
      </el-select>
    </div>
    <div class="card">
      <el-empty v-if="!tasks.length" description="暂无待办" />
      <div v-for="task in tasks" :key="task.instance_id" style="padding: 10px 0; border-bottom: 1px solid #f0f1f3">
        <div class="row" style="justify-content: space-between">
          <div>
            <strong>{{ task.title || task.subject_title || task.scope }}</strong>
            <span class="muted" style="margin-left: 8px">{{ task.scope }} · {{ task.submitted_at || '' }}</span>
          </div>
          <div class="row">
            <el-button size="small" type="success" @click="decide(task, 'APPROVE')">同意</el-button>
            <el-button size="small" type="danger" @click="decide(task, 'REJECT')">拒绝</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { approvalApi } from '@/shared/api'
import { errorText } from '@/shared/format'

const scope = ref('')
const tasks = ref([])

async function load() {
  try {
    const data = await approvalApi.tasks(scope.value || undefined)
    tasks.value = data.results || data || []
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
