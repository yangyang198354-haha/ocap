<template>
  <view>
    <view class="card">
      <view class="title">业委会决议</view>
      <view class="muted">仅公开决议可在此查看；内部决议请登录后在 Web 端查看。</view>
    </view>
    <view class="card">
      <view v-if="!items.length" class="muted">暂无决议</view>
      <view v-for="item in items" :key="item.id" style="padding: 16rpx 0; border-bottom: 1px solid #f0f1f3" @click="open(item)">
        <text>{{ item.title }}</text>
        <text class="muted" style="margin-left: 12rpx">{{ item.status }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '@/utils/api'

const items = ref([])

async function load() {
  try {
    const data = await api.resolutions('public')
    items.value = data.results || data || []
  } catch (e) {
    items.value = []
  }
}

function open(item) {
  uni.navigateTo({ url: `/pages/resolutions/detail?id=${item.id}` })
}

onShow(load)
</script>
