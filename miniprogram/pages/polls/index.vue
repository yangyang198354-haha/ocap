<template>
  <view>
    <view class="card">
      <view class="title">投票 / 调查</view>
      <view class="muted">截止后统一汇总，结果公开。</view>
    </view>
    <view class="card">
      <view v-if="!items.length" class="muted">暂无投票或调查</view>
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
    const data = await api.polls()
    items.value = data.results || data || []
  } catch (e) {
    items.value = []
  }
}

function open(item) {
  uni.navigateTo({ url: `/pages/polls/detail?id=${item.id}` })
}

onShow(load)
</script>
