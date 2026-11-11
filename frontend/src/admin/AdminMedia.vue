<template>
  <div class="page">
    <div class="row" style="justify-content: space-between">
      <h2>素材库</h2>
      <el-upload :show-file-list="false" :auto-upload="false" :on-change="upload">
        <el-button type="primary">上传素材</el-button>
      </el-upload>
    </div>
    <div class="row" style="margin: 12px 0">
      <el-select v-model="mediaType" placeholder="全部类型" clearable style="width: 140px" @change="load">
        <el-option label="图片" value="IMAGE" />
        <el-option label="视频" value="VIDEO" />
      </el-select>
      <el-select v-model="source" placeholder="全部来源" clearable style="width: 160px" @change="load">
        <el-option label="上传" value="UPLOAD" />
        <el-option label="AI 生成" value="AI_GENERATED" />
      </el-select>
    </div>
    <el-empty v-if="!items.length" description="素材库为空" />
    <div class="media-grid">
      <div v-for="item in items" :key="item.id" class="media-card">
        <img v-if="item.media_type === 'IMAGE'" :src="item.url" alt="" />
        <div v-else class="video-placeholder">视频</div>
        <div class="media-title">{{ item.title }}</div>
        <div class="row">
          <el-button size="small" @click="rename(item)">重命名</el-button>
          <el-button size="small" type="danger" @click="remove(item)">删除</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { admin } from '@/shared/api'

const items = ref([])
const mediaType = ref('')
const source = ref('')

async function load() {
  const data = await admin.mediaList({ media_type: mediaType.value || undefined, source: source.value || undefined, page_size: 100 })
  items.value = data.results || []
}
async function upload(file) {
  try {
    await admin.uploadMedia(file.raw, file.name)
    ElMessage.success('已上传')
    await load()
  } catch (err) {
    ElMessage.error(err.message || '上传失败')
  }
}
async function rename(item) {
  try {
    const { value } = await ElMessageBox.prompt('新名称', '重命名', { inputValue: item.title })
    await admin.renameMedia(item.id, value)
    await load()
  } catch { /* cancelled */ }
}
async function remove(item) {
  try {
    await ElMessageBox.confirm(`确认删除「${item.title}」？`, '删除确认', { type: 'warning' })
  } catch { return }
  try {
    await admin.deleteMedia(item.id)
    ElMessage.success('已删除')
    await load()
  } catch (err) {
    const posts = err.details?.posts || []
    ElMessage.error(posts.length ? `素材正在使用：${posts.map((p) => p.title).join('、')}` : err.message)
  }
}
onMounted(load)
</script>

<style scoped>
.media-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.media-card { border: 1px solid var(--line); border-radius: 8px; padding: 8px; }
.media-card img { width: 100%; height: 120px; object-fit: cover; }
.video-placeholder { height: 120px; display: flex; align-items: center; justify-content: center; background: var(--glass); }
.media-title { font-size: 13px; margin: 6px 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
