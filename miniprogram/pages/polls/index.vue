<template>
  <ThemeRoot>
  <view>
    <view class="card">
      <view class="title">投票 / 调查</view>
      <view class="muted">截止后统一汇总，结果公开。</view>
    </view>
    <view class="card">
      <view v-if="!items.length" class="muted">暂无投票或调查</view>
      <view v-for="item in items" :key="item.id" class="list-item" @click="open(item)">
        <text>{{ item.title }}</text>
        <StatusTag class="muted-gap" :status="item.status" />
      </view>
    </view>
  </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import StatusTag from '@/components/StatusTag.vue'
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
