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
      <button v-if="hasMore" style="margin-top: 16rpx" @click="more">加载更多</button>
      <view v-else-if="items.length" class="muted">没有更多了，共 {{ total }} 条</view>
    </view>
  </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import StatusTag from '@/components/StatusTag.vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '@/utils/api'
import { usePaging } from '@/utils/paging'

const { items, total, hasMore, loadMore, reset } = usePaging({ fetch: (params) => api.polls(params) })

async function load() {
  try {
    await reset()
  } catch (e) {
    items.value = []
  }
}

async function more() {
  try {
    await loadMore()
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

function open(item) {
  uni.navigateTo({ url: `/pages/polls/detail?id=${item.id}` })
}

onShow(load)
</script>
