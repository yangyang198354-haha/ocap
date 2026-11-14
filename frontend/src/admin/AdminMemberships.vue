<template>
  <div class="page">
    <div class="card">
      <h3 class="title">用户房屋关系</h3>
      <el-select v-model="role" placeholder="全部身份" clearable style="width: 180px" @change="resetAndLoad">
        <el-option label="户主" value="HEAD" />
        <el-option label="产权业主" value="OWNER" />
        <el-option label="同住人" value="RESIDENT" />
      </el-select>
      <p class="muted">撤销产权业主认证时按接任规则处理户主：最早认证的其他产权业主接任，无则暂无户主。</p>
    </div>
    <div class="card">
      <el-empty v-if="!items.length" description="暂无记录" />
      <el-table :data="items" size="small">
        <el-table-column label="用户" width="160">
          <template #default="{ row }">{{ row.user?.nickname || row.user?.account_no }}（#{{ row.user?.id }}）</template>
        </el-table-column>
        <el-table-column prop="specific_part" label="专有部分" width="160" />
        <el-table-column label="身份" width="120">
          <template #default="{ row }">{{ ROLE_LABELS[row.role] || row.role }}</template>
        </el-table-column>
        <el-table-column label="认证时间" width="180">
          <template #default="{ row }">{{ formatDateTime(row.certified_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button v-if="row.role !== 'RESIDENT'" size="small" type="danger" @click="revoke(row)">撤销认证</el-button>
          </template>
        </el-table-column>
      </el-table>
      <PagerBar :total="total" :page="page" :page-size="pageSize" @change="gotoPage" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import PagerBar from '@/shared/PagerBar.vue'
import { errorText, formatDateTime } from '@/shared/format'
import { confirmDanger } from '@/shared/confirm'
import { ROLE_LABELS } from '@/shared/labels'
import { usePaging } from '@/shared/usePaging'

const role = ref('')
const filters = computed(() => (role.value ? { role: role.value } : {}))
const { items, total, page, pageSize, reload, goto, resetAndLoad: pagingReset } = usePaging({
  fetch: (params) => admin.memberships(params), filters
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

async function revoke(row) {
  if (!(await confirmDanger('revokeMembership', { name: `${row.user?.nickname || row.user?.account_no} · ${row.specific_part}` }))) return
  try {
    const result = await admin.revokeMembership(row.user.id, row.unit_id)
    ElMessage.success(result.was_head && result.new_head_id ? '已撤销，户主已由最早认证的产权业主接任' : '已撤销')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
