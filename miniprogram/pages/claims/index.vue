<template>
  <view>
    <view class="card">
      <view class="title">报销 / 备用金</view>
      <view class="muted">发票上传请在 Web 端完成；此处用于快速提交与查询。</view>
    </view>
    <view class="card">
      <view class="title">新建申请</view>
      <picker :range="typeLabels" @change="pickType">
        <view class="muted">类型：{{ typeLabels[typeIndex] }}</view>
      </picker>
      <input v-model="amount" placeholder="金额" style="border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx; margin-top: 16rpx" />
      <textarea v-model="reason" placeholder="事由" style="border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx; margin-top: 16rpx; width: 100%" />
      <input v-model="flowId" placeholder="审批流程 ID" style="border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx; margin-top: 16rpx" />
      <button class="btn" style="margin-top: 20rpx" @click="create">提交</button>
    </view>
    <view class="card">
      <view class="title">我的申请</view>
      <view v-if="!items.length" class="muted">暂无申请</view>
      <view v-for="item in items" :key="item.id" style="padding: 16rpx 0; border-bottom: 1px solid #f0f1f3">
        <text>{{ label(item.type) }} ¥{{ item.amount }}</text>
        <text class="muted" style="margin-left: 12rpx">{{ item.status }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '@/utils/api'

const typeKeys = ['REIMBURSEMENT', 'ADVANCE']
const typeLabels = ['报销', '备用金预借']
const typeIndex = ref(0)
const amount = ref('')
const reason = ref('')
const flowId = ref('')
const items = ref([])

const label = (t) => ({ REIMBURSEMENT: '报销', ADVANCE: '备用金', SETTLEMENT: '核销' }[t] || t)

function pickType(e) {
  typeIndex.value = Number(e.detail.value)
}

async function load() {
  try {
    const data = await api.claimsMine()
    items.value = data.results || data || []
  } catch (e) {
    items.value = []
  }
}

async function create() {
  try {
    await api.createClaim({
      type: typeKeys[typeIndex.value],
      amount: amount.value,
      reason: reason.value,
      approval_flow_id: Number(flowId.value)
    })
    uni.showToast({ title: '已提交', icon: 'none' })
    amount.value = ''
    reason.value = ''
    load()
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

onShow(load)
</script>
