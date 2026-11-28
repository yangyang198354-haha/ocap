<template>
  <ThemeRoot>
  <view>
    <view v-if="!timeline" class="card">
      <view class="title">审批详情</view>
      <view class="muted">正在加载审批过程…</view>
    </view>
    <view v-if="timeline" class="card">
      <view class="row" style="justify-content: space-between">
        <view class="title">{{ timeline.subject_title }}</view>
        <text class="muted">{{ textOf(APPROVAL_STATUS_LABELS, timeline.status) }}</text>
      </view>
      <view class="muted">提交于 {{ formatDateTime(timeline.submitted_at) }}</view>
    </view>
    <view v-for="step in timeline?.steps || []" :key="step.order" class="card">
      <view class="row" style="justify-content: space-between">
        <text class="title">第 {{ step.order }} 步 · {{ step.name }}</text>
        <text class="muted">{{ textOf(STEP_STATUS_LABELS, step.status) }}</text>
      </view>
      <view class="muted">{{ textOf(STEP_STRATEGY_LABELS, step.strategy) }} · 到达：{{ step.reached_at ? formatDateTime(step.reached_at) : '未开始' }}</view>
      <view v-for="(action, index) in step.actions" :key="index" class="list-item">
        <view>
          <text>{{ action.actor_label }} · {{ textOf(APPROVAL_ACTION_LABELS, action.action) }}</text>
          <view class="muted">{{ formatDateTime(action.acted_at) }}</view>
          <view v-if="action.comment" class="muted">备注：{{ action.comment }}</view>
        </view>
      </view>
    </view>

    <view v-if="canDecide" class="card">
      <view class="title">审批处理</view>
      <textarea v-model="comment" placeholder="审批意见（可选，最多 500 字）" class="field" style="width: 100%" />
      <view class="muted">{{ comment.length }} / 500</view>
      <view class="row" style="margin-top: 16rpx">
        <button class="btn" @click="decide('APPROVE')">通过</button>
        <button class="btn btn--danger" style="margin-left: 16rpx" @click="decide('REJECT')">拒绝</button>
      </view>
    </view>
  </view>
  </ThemeRoot>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api } from '@/utils/api'
import {
  APPROVAL_ACTION_LABELS, APPROVAL_STATUS_LABELS, STEP_STATUS_LABELS, STEP_STRATEGY_LABELS, formatDateTime
} from '@/utils/labels'
import ThemeRoot from '@/components/ThemeRoot.vue'

const textOf = (table, code) => table[code] || code

const instanceId = ref(null)
const timeline = ref(null)
const canDecide = ref(false)
const comment = ref('')

async function load() {
  try {
    timeline.value = await api.instance(instanceId.value)
    canDecide.value = timeline.value.status === 'PENDING'
  } catch (e) {
    timeline.value = null
    canDecide.value = false
  }
}

async function decide(action) {
  try {
    timeline.value = await api.decide(instanceId.value, action, comment.value)
    comment.value = ''
    canDecide.value = timeline.value.status === 'PENDING'
    uni.showToast({ title: '已处理' })
  } catch (e) {
    uni.showToast({ title: e?.message || '处理失败', icon: 'none' })
  }
}

onLoad((options) => {
  instanceId.value = Number(options?.id || 0)
  load()
})
</script>
