<template>
  <div class="page">
    <div class="card">
      <h3 class="title">用户房屋关系</h3>
      <el-select v-model="role" placeholder="全部身份" clearable style="width: 180px" @change="load">
        <el-option label="户主" value="HEAD" />
        <el-option label="产权业主" value="OWNER" />
        <el-option label="同住人" value="RESIDENT" />
      </el-select>
      <p class="muted">撤销产权业主认证时按接任规则处理户主：最早认证的其他产权业主接任，无则暂无户主。</p>
    </div>
    <div class="card">
      <el-empty v-if="!items.length" description="暂无记录" />
      <el-table :data="items" size="small">
        <el-table-column prop="user_id" label="用户" width="100" />
        <el-table-column prop="unit_id" label="专有部分" width="120" />
        <el-table-column prop="role" label="身份" width="120" />
        <el-table-column prop="certified_at" label="认证时间" width="180" />
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button v-if="row.role !== 'RESIDENT'" size="small" type="danger" @click="revoke(row)">撤销认证</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import { errorText } from '@/shared/format'

const items = ref([])
const role = ref('')

async function load() {
  try {
    const data = await admin.memberships(role.value ? { role: role.value } : undefined)
    items.value = data.results || data || []
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function revoke(row) {
  try {
    await admin.revokeMembership(row.id)
    ElMessage.success('已撤销')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
