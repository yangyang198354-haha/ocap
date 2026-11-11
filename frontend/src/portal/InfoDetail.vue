<template>
  <div class="page">
    <h2>{{ title }}</h2>
    <div class="muted" style="margin-bottom: 12px">{{ publishedAt }}</div>
    <div v-html="pageHtml" />
    <div v-if="pageCount > 1" class="row" style="margin-top: 16px">
      <el-button :disabled="pageIndex === 0" @click="pageIndex -= 1">上一页</el-button>
      <span class="muted">{{ pageIndex + 1 }} / {{ pageCount }}</span>
      <el-button :disabled="pageIndex >= pageCount - 1" @click="pageIndex += 1">下一页</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { infoApi } from '@/shared/api'

const route = useRoute()
const title = ref('')
const publishedAt = ref('')
const pages = ref([])
const pageIndex = ref(0)
const pageCount = computed(() => pages.value.length)
const pageHtml = computed(() => pages.value[pageIndex.value]?.html || '')

onMounted(async () => {
  const data = await infoApi.detail(route.params.id, 'html')
  title.value = data.title
  publishedAt.value = data.published_at
  pages.value = data.pages || []
})
</script>
