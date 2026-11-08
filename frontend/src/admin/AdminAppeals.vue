<template>
  <div class="page">
    <div class="card">
      <h3 class="title">产权申诉审核</h3>
      <el-select v-model="status" placeholder="全部状态" clearable style="width: 180px" @change="load">
        <el-option label="待审核" value="PENDING" />
        <el-option label="已通过" value="APPROVED" />
        <el-option label="已拒绝" value="REJECTED" />
      </el-select>
    </div>
    <div class="card">
      <el-empty v-if="!items.length" description="暂无申诉" />
      <div v-for="item in items" :key="item.id" style="padding: 10px 0; border-bottom: 1px solid #f0f1f3">
        <div class="row" style="justify-content: space-between">
          <div>
            <strong>#{{ item.id }}</strong>
            <span class="muted" style="margin-left: 8px">{{ item.applicant?.nickname || item.applicant_id }} → {{ item.unit?.specific_part || item.unit_id }}</span>
            <el-tag size="small" style="margin-left: 8px">{{ item.status }}</el-tag>
          </div>
          <div class="row" v-if="item.status === 'PENDING'">
            <el-button size="small" type="success" @click="decide(item.id, 'APPROVE')">通过</el-button>
            <el-button size="small" type="danger" @click="decide(item.id, 'REJECT')">拒绝</el-button>
          </div>
        </div>
        <p class="muted">{{ item.reason }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import { errorText } from '@/shared/format'

const items = ref([])
const status = ref('PENDING')

async function load() {
  try {
    const data = await admin.appeals(status.value ? { status: status.value } : undefined)
    items.value = data.results || data || []
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function decide(id, action) {
  try {
    await admin.decideAppeal(id, action)
    ElMessage.success('已处理')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
