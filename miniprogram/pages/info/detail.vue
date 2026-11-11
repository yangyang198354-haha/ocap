<template>
  <ThemeRoot>
    <view class="page">
      <view class="title">{{ title || '信息公开' }}</view>
      <view class="muted">{{ publishedAt || '加载中…' }}</view>
      <rich-blocks :blocks="pages[index]?.blocks || []" :theme="theme" :api-base="apiBase" />
      <view v-if="pages.length > 1" class="row" style="margin-top: 24rpx">
        <button size="mini" :disabled="index === 0" @click="index -= 1">上一页</button>
        <text class="muted">{{ index + 1 }} / {{ pages.length }}</text>
        <button size="mini" :disabled="index >= pages.length - 1" @click="index += 1">下一页</button>
      </view>
    </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api } from '@/utils/api'
import RichBlocks from '@/components/RichBlocks.vue'

const title = ref('')
const publishedAt = ref('')
const pages = ref([])
const theme = ref({})
const index = ref(0)
const apiBase = import.meta.env.VITE_API_BASE || '/api/v1'

onLoad(async (options) => {
  try {
    const data = await api.infoPost(options.id)
    title.value = data.title
    publishedAt.value = data.published_at
    pages.value = data.pages || []
    theme.value = data.theme || {}
  } catch (e) {
    uni.showToast({ title: e.message || '加载失败', icon: 'none' })
  }
})
</script>
