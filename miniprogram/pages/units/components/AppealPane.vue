<!-- MOD-179 / IFC-398：小程序“我的认证与申述”面板；内含“认证申诉/我的申诉”子 Tab（ADR-169） -->
<template>
  <view>
    <view class="sub-tabs">
      <view class="sub-tab" :class="{ 'is-active': subTab === 'appeal' }" @click="subTab = 'appeal'">认证申诉</view>
      <view class="sub-tab" :class="{ 'is-active': subTab === 'mine' }" @click="subTab = 'mine'">我的申诉</view>
    </view>

    <view v-show="subTab === 'appeal'" class="card">
      <view class="title">认证申诉</view>
      <view class="muted">姓名与手机号未能通过清册核对时，填写产权人名字并上传 1~5 张产权证明图片提交申诉，由管理员审核。</view>
      <UnitPicker v-model="pickedUnitId" />
      <input v-model="ownerName" class="field mt-16" maxlength="64" placeholder="产权人名字" />
      <button style="margin-top: 16rpx" @click="chooseProof">{{ proofIds.length ? `已上传 ${proofIds.length} 张，继续添加` : '上传产权证明' }}</button>
      <button v-if="proofIds.length" size="mini" style="margin-top: 16rpx" @click="proofIds = []">清空</button>
      <button style="margin-top: 16rpx" @click="submitAppeal">提交申诉</button>
    </view>

    <view v-show="subTab === 'mine'" class="card">
      <view class="title">我的申诉</view>
      <view v-if="!myAppeals.length" class="muted">暂无申诉</view>
      <view v-for="item in myAppeals" :key="item.id" class="list-item">
        <text>{{ item.unit?.specific_part }}</text>
        <text class="muted" style="margin-left: 12rpx">{{ statusLabel('appeal', item.status) }}</text>
        <view class="muted">提交 {{ formatDateTime(item.submitted_at) }}<text v-if="item.decided_at"> · 处理 {{ formatDateTime(item.decided_at) }}</text></view>
        <view v-if="item.status === 'REJECTED' && item.reject_reason" class="muted">驳回原因：{{ item.reject_reason }}</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import UnitPicker from '@/components/UnitPicker.vue'
import { api } from '@/utils/api'
import { formatDateTime, statusLabel } from '@/utils/labels'

const props = defineProps({ prefillName: { type: String, default: '' } })
const emit = defineEmits(['submitted'])

const subTab = ref('appeal')
const pickedUnitId = ref(null)
const ownerName = ref('')
const proofIds = ref([])
const myAppeals = ref([])
const MAX_PROOFS = 5

function toast(title) {
  uni.showToast({ title, icon: 'none' })
}

const listOf = (data) => data?.results || data || []

async function loadMyAppeals() {
  try {
    myAppeals.value = listOf(await api.myAppeals())
  } catch (e) {
    toast(e.message)
  }
}

// 小程序申诉资料本批仅支持图片（OQ-06）；一次最多再选 5 - 已选数 张
function chooseProof() {
  const remaining = MAX_PROOFS - proofIds.value.length
  if (remaining <= 0) return toast('最多上传 5 张产权证明')
  uni.chooseImage({
    count: remaining,
    success: async ({ tempFilePaths }) => {
      try {
        for (const path of tempFilePaths.slice(0, remaining)) {
          const uploaded = await api.upload(path, 'APPEAL_PROOF')
          proofIds.value.push(uploaded.id)
        }
        toast('已上传')
      } catch (e) {
        toast(e.message)
      }
    }
  })
}

async function submitAppeal() {
  if (!pickedUnitId.value) return toast('请先选择房号')
  const name = ownerName.value.trim()
  if (!name) return toast('请输入产权人名字')
  if (!proofIds.value.length) return toast('请先上传产权证明')
  try {
    await api.createAppeal({ unit_id: pickedUnitId.value, owner_name: name, proof_ids: [...proofIds.value] })
    toast('申诉已提交')
    proofIds.value = []
    await loadMyAppeals()
    subTab.value = 'mine'
    emit('submitted')
  } catch (e) {
    toast(e.message)
  }
}

// 认证产权未匹配时带入姓名，切换到“认证申诉”
watch(() => props.prefillName, (name) => {
  if (!name) return
  ownerName.value = name
  subTab.value = 'appeal'
})

onMounted(loadMyAppeals)
</script>

<style scoped>
.sub-tabs { display: flex; gap: 8rpx; margin-bottom: 16rpx; }
.sub-tab {
  flex: 1; text-align: center; padding: 16rpx 0; font-size: 26rpx; color: var(--muted);
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-md);
}
.sub-tab.is-active { color: var(--accent-text); font-weight: 650; border-color: currentColor; }
</style>
