<template>
  <el-dialog v-model="visible" title="从素材库选择" width="720px" @open="load">
    <div class="row" style="margin-bottom: 12px">
      <el-radio-group v-model="kind" @change="load">
        <el-radio-button label="IMAGE">图片</el-radio-button>
        <el-radio-button label="VIDEO">视频</el-radio-button>
      </el-radio-group>
      <el-upload :show-file-list="false" :auto-upload="false" :on-change="upload">
        <el-button size="small">上传素材</el-button>
      </el-upload>
    </div>
    <el-empty v-if="!items.length" description="素材库为空" />
    <div class="media-grid">
      <div v-for="item in items" :key="item.id" class="media-card" @click="choose(item)">
        <img v-if="item.media_type === 'IMAGE'" :src="item.url" alt="" />
        <div v-else class="video-placeholder">视频</div>
        <div class="media-title">{{ item.title }}</div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'

const props = defineProps({ modelValue: Boolean, type: { type: String, default: 'IMAGE' } })
const emit = defineEmits(['update:modelValue', 'selected'])
const visible = ref(false)
const kind = ref(props.type)
const items = ref([])

async function load() {
  const data = await admin.mediaList({ media_type: kind.value, page_size: 100 })
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
function choose(item) {
  emit('selected', { kind: item.media_type.toLowerCase(), mediaId: item.id, url: item.url })
  visible.value = false
  emit('update:modelValue', false)
}
defineExpose({ open: (type) => { kind.value = type || 'IMAGE'; visible.value = true; load() } })
</script>

<style scoped>
.media-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
.media-card { border: 1px solid var(--line); border-radius: 8px; padding: 8px; cursor: pointer; }
.media-card img { width: 100%; height: 100px; object-fit: cover; }
.video-placeholder { height: 100px; display: flex; align-items: center; justify-content: center; background: var(--glass); }
.media-title { font-size: 12px; margin-top: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
