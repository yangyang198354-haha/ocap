<template>
  <ThemeRoot>
    <view class="page">
      <view class="page-head">
        <view class="page-eyebrow">INFORMATION</view>
        <view class="page-title">信息公开</view>
        <view class="page-desc">公告、公示与小区动态</view>
      </view>
      <view v-if="!items.length" class="muted">暂无公开信息</view>
      <view v-for="item in items" :key="item.id" class="list-item" @click="open(item)">
        <text>{{ item.title }}</text>
        <text class="muted">{{ item.published_at }}</text>
      </view>
    </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { api } from '@/utils/api'

const items = ref([])
async function load() {
  try {
    const data = await api.infoPosts()
    items.value = data.results || []
  } catch (e) {
    items.value = []
  }
}
function open(item) {
  uni.navigateTo({ url: `/pages/info/detail?id=${item.id}` })
}
onShow(load)
</script>
