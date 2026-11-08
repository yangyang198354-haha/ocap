<template>
  <view>
    <view class="card">
      <view class="title">业主清册认证</view>
      <picker mode="selector" :range="buildings" @change="pickBuilding">
        <view class="muted">楼栋：{{ picked.building || '请选择' }}</view>
      </picker>
      <picker mode="selector" :range="units" @change="pickUnit">
        <view class="muted">单元：{{ picked.unitNo || '请选择' }}</view>
      </picker>
      <picker mode="selector" :range="floors" @change="pickFloor">
        <view class="muted">楼层：{{ picked.floor || '请选择' }}</view>
      </picker>
      <picker mode="selector" :range="roomLabels" @change="pickRoom">
        <view class="muted">房号：{{ picked.roomLabel || '请选择' }}</view>
      </picker>
      <button class="btn" style="margin-top: 20rpx" @click="certify">认证</button>
    </view>
    <view class="card">
      <view class="title">认证申诉</view>
      <textarea v-model="appealReason" placeholder="申诉说明" style="border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx; width: 100%" />
      <button style="margin-top: 16rpx" @click="submitAppeal">提交申诉</button>
      <view class="muted">申诉需管理员审核，上传产权证明请在 Web 端完成。</view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api } from '@/utils/api'

const buildings = ref([])
const units = ref([])
const floors = ref([])
const rooms = ref([])
const picked = reactive({ building: '', unitNo: '', floor: '', roomLabel: '', unitId: null })
const appealReason = ref('')
const roomLabels = computed(() => rooms.value.map((r) => r.room || r.specific_part))

function toast(title) {
  uni.showToast({ title, icon: 'none' })
}

async function load(params = {}) {
  try {
    const data = await api.options(params)
    return data
  } catch (e) {
    toast(e.message)
    return {}
  }
}

async function init() {
  const data = await load({})
  buildings.value = data.buildings || []
}

async function pickBuilding(e) {
  picked.building = buildings.value[Number(e.detail.value)]
  const data = await load({ building: picked.building })
  units.value = data.units || []
}

async function pickUnit(e) {
  picked.unitNo = units.value[Number(e.detail.value)]
  const data = await load({ building: picked.building, unit_no: picked.unitNo })
  floors.value = data.floors || []
}

async function pickFloor(e) {
  picked.floor = floors.value[Number(e.detail.value)]
  const data = await load({ building: picked.building, unit_no: picked.unitNo, floor: picked.floor })
  rooms.value = data.rooms || []
}

function pickRoom(e) {
  const room = rooms.value[Number(e.detail.value)]
  picked.unitId = room?.id
  picked.roomLabel = roomLabels.value[Number(e.detail.value)]
}

async function certify() {
  try {
    const result = await api.certify(picked.unitId)
    toast(`认证成功：${result.role}`)
  } catch (e) {
    toast(e.message)
  }
}

async function submitAppeal() {
  try {
    await api.createAppeal({ unit_id: picked.unitId, reason: appealReason.value })
    toast('申诉已提交')
  } catch (e) {
    toast(e.message)
  }
}

onLoad(init)
</script>
