<template>
  <div class="page">
    <h2>内容中心参数</h2>
    <el-table :data="items" border>
      <el-table-column prop="key" label="参数" min-width="260" />
      <el-table-column label="值" width="260">
        <template #default="{ row }">
          <el-switch v-if="row.type === 'bool'" v-model="row.value" />
          <el-input v-else-if="row.type === 'int'" v-model.number="row.value" />
          <el-input v-else-if="row.type === 'list'" :model-value="JSON.stringify(row.value)"
                    @update:model-value="row.value = parseList($event)" />
          <el-input v-else v-model="row.value" />
        </template>
      </el-table-column>
      <el-table-column prop="default" label="缺省" width="160" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.confirmed ? 'success' : 'warning'">{{ row.confirmed ? '已确认' : '待确认' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="note" label="说明" />
    </el-table>
    <div class="row" style="margin-top: 12px">
      <el-button type="primary" @click="save">保存</el-button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'

const items = ref([])
function parseList(value) {
  try { return JSON.parse(value) } catch { return value }
}
async function load() {
  items.value = await admin.contentSettings()
}
async function save() {
  const values = Object.fromEntries(items.value.map((item) => [item.key, item.value]))
  try {
    items.value = await admin.updateContentSettings(values)
    ElMessage.success('已保存')
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
  }
}
onMounted(load)
</script>
