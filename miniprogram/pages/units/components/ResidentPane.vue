<!-- MOD-179 / IFC-398：小程序“我的同住人申请”面板；发起申请 + 申请记录（ADR-169） -->
<template>
  <view>
    <view class="card">
      <view class="title">我的同住人申请</view>
      <view class="muted">申请成为同住人无需输入姓名，同住人须先有产权业主，由产权业主审批。</view>
      <UnitPicker v-model="applyUnitId" />
      <button style="margin-top: 16rpx" @click="applyResident">申请成为同住人</button>
      <view v-if="!myApplications.length" class="muted">暂无同住人申请</view>
      <view v-for="item in myApplications" :key="item.id" class="list-item">
        <text>{{ item.unit?.specific_part }}</text>
        <text class="muted" style="margin-left: 12rpx">{{ statusLabel('application', item.status) }}</text>
        <view class="muted">提交 {{ formatDateTime(item.created_at) }}<text v-if="item.decided_at"> · 处理 {{ formatDateTime(item.decided_at) }}</text></view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import UnitPicker from '@/components/UnitPicker.vue'
import { api } from '@/utils/api'
import { formatDateTime, statusLabel } from '@/utils/labels'

const emit = defineEmits(['refresh'])

const applyUnitId = ref(null)
const myApplications = ref([])

function toast(title) {
  uni.showToast({ title, icon: 'none' })
}

const listOf = (data) => data?.results || data || []

async function loadMyApplications() {
  try {
    myApplications.value = listOf(await api.myResidentApplications())
  } catch (e) {
    toast(e.message)
  }
}

async function applyResident() {
  if (!applyUnitId.value) return toast('请先选择房号')
  try {
    await api.createResidentApplication({ unit_id: applyUnitId.value })
    toast('申请已提交，等待产权业主审批')
    await loadMyApplications()
    emit('refresh')
  } catch (e) {
    toast(e.message)
  }
}

onMounted(loadMyApplications)
</script>
