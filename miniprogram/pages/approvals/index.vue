<template>
  <ThemeRoot>
  <view>
    <view class="card">
      <view class="title">待我审批</view>
      <view class="muted">只显示当前轮到你的审批步骤。</view>
    </view>
    <view class="card">
      <view v-if="!tasks.length" class="muted">暂无待办</view>
      <view v-for="task in tasks" :key="task.instance_id" class="list-item" @click="open(task)">
        <view>
          <text>{{ task.subject_title || task.subject_type }}</text>
          <view class="muted">第 {{ task.step_order }} 步 · {{ task.step_name }}（{{ textOf(STEP_STRATEGY_LABELS, task.step_strategy) }}）</view>
          <view class="muted">{{ formatDateTime(task.submitted_at) }}</view>
        </view>
        <text class="muted" aria-hidden="true">›</text>
      </view>
    </view>
  </view>
  </ThemeRoot>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '@/utils/api'
import { STEP_STRATEGY_LABELS, formatDateTime } from '@/utils/labels'

const textOf = (table, code) => table[code] || code
import ThemeRoot from '@/components/ThemeRoot.vue'

const tasks = ref([])

async function load() {
  try {
    const data = await api.tasks({})
    tasks.value = data.results || []
  } catch (e) {
    tasks.value = []
  }
}

function open(task) {
  uni.navigateTo({ url: `/pages/approvals/detail?id=${task.instance_id}` })
}

onShow(load)
</script>
