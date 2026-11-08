<template>
  <view>
    <view class="card">
      <view class="title">报销 / 备用金</view>
      <view class="muted">报销凭发票；备用金为预借现金，办完后核销，核销按差额调整支出（多退少补）。</view>
    </view>
    <view class="card">
      <view class="title">新建申请</view>
      <picker :range="typeLabels" @change="pickType">
        <view class="muted">类型：{{ typeLabels[typeIndex] }}</view>
      </picker>
      <picker :range="flowLabels" @change="pickFlow">
        <view class="muted">审批流程：{{ flowLabels[flowIndex] || '请选择' }}</view>
      </picker>
      <input v-model="amount" placeholder="金额（最多两位小数）" style="border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx; margin-top: 16rpx" />
      <textarea v-model="reason" placeholder="事由（1~500 字）" style="border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx; margin-top: 16rpx; width: 100%" />
      <template v-if="typeIndex === 0">
        <picker mode="date" :value="occurredOn" @change="(e) => (occurredOn = e.detail.value)">
          <view class="muted">费用发生日期：{{ occurredOn || '请选择' }}</view>
        </picker>
        <button style="margin-top: 16rpx" @click="chooseInvoice">上传发票（已选 {{ invoiceIds.length }} 张）</button>
      </template>
      <template v-else>
        <input v-model="expectedUsage" placeholder="预计用途" style="border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx; margin-top: 16rpx" />
        <picker mode="date" :value="expectedSettleOn" @change="(e) => (expectedSettleOn = e.detail.value)">
          <view class="muted">预计核销日期：{{ expectedSettleOn || '请选择（须晚于今日）' }}</view>
        </picker>
      </template>
      <button class="btn" style="margin-top: 20rpx" @click="create">提交</button>
    </view>
    <view class="card">
      <view class="title">备用金核销</view>
      <picker :range="advanceLabels" @change="(e) => (settle.advanceIndex = Number(e.detail.value))">
        <view class="muted">备用金：{{ advanceLabels[settle.advanceIndex] || '请选择已通过且未核销的备用金' }}</view>
      </picker>
      <view class="muted" style="margin-top: 12rpx">关联凭票报销单（已通过、未核销）：</view>
      <checkbox-group @change="(e) => (settle.reimbursementIds = e.detail.value.map(Number))">
        <label v-for="r in reimbursements" :key="r.id" style="display: block; padding: 8rpx 0">
          <checkbox :value="String(r.id)" />
          <text>#{{ r.id }} ¥{{ r.amount }} {{ r.reason }}</text>
        </label>
      </checkbox-group>
      <view class="muted" style="margin-top: 12rpx">差额：{{ diffText }}</view>
      <input v-model="settle.reason" placeholder="核销说明" style="border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx; margin-top: 16rpx" />
      <button class="btn" style="margin-top: 20rpx" @click="submitSettle">提交核销</button>
    </view>
    <view class="card">
      <view class="title">我的申请</view>
      <view v-if="!items.length" class="muted">暂无申请</view>
      <view v-for="item in items" :key="item.id" style="padding: 16rpx 0; border-bottom: 1px solid #f0f1f3">
        <text>{{ label(item.type) }} ¥{{ item.amount }}</text>
        <text class="muted" style="margin-left: 12rpx">{{ item.status }}</text>
        <button v-if="item.status === 'PENDING'" size="mini" style="margin-left: 12rpx" @click="withdraw(item.id)">撤回</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '@/utils/api'

const typeLabels = ['报销', '备用金预借']
const typeIndex = ref(0)
const flows = ref([])
const flowIndex = ref(-1)
const amount = ref('')
const reason = ref('')
const occurredOn = ref('')
const expectedUsage = ref('')
const expectedSettleOn = ref('')
const invoiceIds = ref([])
const items = ref([])
const advances = ref([])
const reimbursements = ref([])
const settle = reactive({ advanceIndex: -1, reimbursementIds: [], reason: '' })

const label = (t) => ({ REIMBURSEMENT: '报销', ADVANCE: '备用金', SETTLEMENT: '核销' }[t] || t)
const flowLabels = computed(() => flows.value.map((f) => f.name))
const advanceLabels = computed(() => advances.value.map((a) => `#${a.id} ¥${a.amount} ${a.reason}`))

// 金额为后端返回的两位小数字符串，这里按分（整数）计算，仅用于展示
const cents = (v) => Math.round(Number(v) * 100)
const diffText = computed(() => {
  const advance = advances.value[settle.advanceIndex]
  if (!advance || !settle.reimbursementIds.length) return '-'
  const total = reimbursements.value
    .filter((r) => settle.reimbursementIds.includes(r.id))
    .reduce((sum, r) => sum + cents(r.amount), 0)
  const diff = total - cents(advance.amount)
  const text = (Math.abs(diff) / 100).toFixed(2)
  if (diff < 0) return `多退 ¥${text}`
  if (diff > 0) return `少补 ¥${text}`
  return '刚好核销'
})

function toast(title) {
  uni.showToast({ title, icon: 'none' })
}

function pickType(e) {
  typeIndex.value = Number(e.detail.value)
}

function pickFlow(e) {
  flowIndex.value = Number(e.detail.value)
}

async function load() {
  try {
    const data = await api.claims({ scope: 'mine' })
    items.value = data.results || data || []
    const adv = await api.claims({ scope: 'mine', type: 'ADVANCE', status: 'APPROVED', page_size: 100 })
    advances.value = (adv.results || []).filter((a) => !a.settlement_id)
    const reimb = await api.claims({ scope: 'mine', type: 'REIMBURSEMENT', status: 'APPROVED', page_size: 100 })
    reimbursements.value = (reimb.results || []).filter((r) => !r.settlement_id)
  } catch (e) {
    items.value = []
  }
  try {
    // 审批流程选项仅业委会成员可取；非成员后端返回 403，此时不能提交申请
    const list = await api.flows('EXPENSE')
    flows.value = list.results || list || []
  } catch (e) {
    flows.value = []
  }
}

function chooseInvoice() {
  uni.chooseImage({
    count: 1,
    success: async ({ tempFilePaths }) => {
      try {
        const uploaded = await api.upload(tempFilePaths[0], 'INVOICE')
        invoiceIds.value.push(uploaded.id)
        toast('已上传')
      } catch (e) {
        toast(e.message)
      }
    }
  })
}

function chosenFlowId() {
  const flow = flows.value[flowIndex.value]
  if (!flow) toast('请选择审批流程')
  return flow?.id
}

async function create() {
  const flowId = chosenFlowId()
  if (!flowId) return
  try {
    if (typeIndex.value === 0) {
      await api.createReimbursement({
        amount: amount.value, reason: reason.value, occurred_on: occurredOn.value,
        invoice_ids: invoiceIds.value, approval_flow_id: flowId
      })
    } else {
      await api.createAdvance({
        amount: amount.value, reason: reason.value, expected_usage: expectedUsage.value,
        expected_settle_on: expectedSettleOn.value, approval_flow_id: flowId
      })
    }
    toast('已提交')
    amount.value = ''
    reason.value = ''
    invoiceIds.value = []
    load()
  } catch (e) {
    toast(e.message)
  }
}

async function submitSettle() {
  const flowId = chosenFlowId()
  const advance = advances.value[settle.advanceIndex]
  if (!flowId) return
  if (!advance) return toast('请选择备用金')
  try {
    await api.createSettlement({
      advance_id: advance.id, reimbursement_ids: settle.reimbursementIds,
      reason: settle.reason, approval_flow_id: flowId
    })
    toast('核销已提交')
    settle.advanceIndex = -1
    settle.reimbursementIds = []
    settle.reason = ''
    load()
  } catch (e) {
    toast(e.message)
  }
}

async function withdraw(id) {
  try {
    await api.withdrawClaim(id)
    toast('已撤回')
    load()
  } catch (e) {
    toast(e.message)
  }
}

onShow(load)
</script>
