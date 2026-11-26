<template>
  <div class="page">
    <PageHead :title="title || '信息公开'" />
    <div v-if="failed" class="card info-missing">
      <p>内容不存在或已下线</p>
      <router-link to="/info" class="link">返回列表</router-link>
    </div>
    <template v-else>
      <div class="muted" style="margin-bottom: 12px">{{ formatDateTime(publishedAt) }}</div>
      <div v-html="pageHtml" />
      <div v-if="pageCount > 1" class="row" style="margin-top: 16px">
        <el-button :disabled="pageIndex === 0" @click="pageIndex -= 1">上一页</el-button>
        <span class="muted">{{ pageIndex + 1 }} / {{ pageCount }}</span>
        <el-button :disabled="pageIndex >= pageCount - 1" @click="pageIndex += 1">下一页</el-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import PageHead from '@/shared/PageHead.vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { infoApi } from '@/shared/api'
import { formatDateTime } from '@/shared/format'

const route = useRoute()
const title = ref('')
const publishedAt = ref('')
const pages = ref([])
const pageIndex = ref(0)
const failed = ref(false)
const pageCount = computed(() => pages.value.length)
const pageHtml = computed(() => pages.value[pageIndex.value]?.html || '')

onMounted(async () => {
  try {
    const data = await infoApi.detail(route.params.id, 'html')
    title.value = data.title
    publishedAt.value = data.published_at
    pages.value = data.pages || []
  } catch (e) {
    failed.value = true // 404 或任意错误：显示"内容不存在或已下线"，不留空白（REQ-FUNC-160）
  }
})
</script>
