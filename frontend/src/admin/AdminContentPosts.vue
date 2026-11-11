<template>
  <div class="page">
    <div class="row" style="justify-content: space-between">
      <h2>信息公开</h2>
      <el-button type="primary" @click="create">新建内容</el-button>
    </div>
    <div class="row" style="margin: 12px 0">
      <el-select v-model="status" placeholder="全部状态" clearable style="width: 140px" @change="load">
        <el-option label="草稿" value="DRAFT" />
        <el-option label="已发布" value="PUBLISHED" />
        <el-option label="已下线" value="OFFLINE" />
      </el-select>
      <el-input v-model="q" placeholder="搜索标题" style="width: 220px" clearable @change="load" />
    </div>
    <el-table :data="items" border>
      <el-table-column prop="title" label="标题" min-width="220" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">{{ statusText(row.status) }}</template>
      </el-table-column>
      <el-table-column prop="published_at" label="发布时间" width="180" />
      <el-table-column prop="updated_at" label="更新时间" width="180" />
      <el-table-column label="操作" width="260">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/admin/content/posts/${row.id}`)">编辑</el-button>
          <el-button v-if="row.status !== 'PUBLISHED'" size="small" type="success" @click="publish(row)">发布</el-button>
          <el-button v-else size="small" @click="offline(row)">下线</el-button>
          <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :total="count" :page-size="20" layout="prev, pager, next, total"
                   style="margin-top: 12px" @current-change="load" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { admin } from '@/shared/api'

const router = useRouter()
const items = ref([])
const status = ref('')
const q = ref('')
const page = ref(1)
const count = ref(0)

function statusText(value) {
  return { DRAFT: '草稿', PUBLISHED: '已发布', OFFLINE: '已下线' }[value] || value
}
async function load() {
  const data = await admin.contentPosts({ status: status.value || undefined, q: q.value || undefined, page: page.value })
  items.value = data.results || []
  count.value = data.count || 0
}
async function create() {
  const post = await admin.createContentPost({ title: '未命名内容', doc: { type: 'doc', content: [] } })
  router.push(`/admin/content/posts/${post.id}`)
}
async function publish(row) {
  try {
    await admin.publishContentPost(row.id)
    ElMessage.success('已发布')
    await load()
  } catch (err) {
    ElMessage.error(err.message || '发布失败')
  }
}
async function offline(row) {
  await admin.offlineContentPost(row.id)
  ElMessage.success('已下线')
  await load()
}
async function remove(row) {
  try {
    await ElMessageBox.confirm(`确认删除「${row.title}」？`, '删除确认', { type: 'warning' })
  } catch { return }
  await admin.deleteContentPost(row.id)
  ElMessage.success('已删除')
  await load()
}
onMounted(load)
</script>
