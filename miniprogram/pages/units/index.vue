<template>
  <ThemeRoot>
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
      <view class="muted">微信登录且未绑定手机号时，请先到“我的 → 绑定/更换手机号”完成绑定。</view>
    </view>
    <view class="card">
      <view class="title">认证申诉</view>
      <view class="muted">清册手机号与当前手机号不一致时，上传产权证明提交申诉，由管理员审核。</view>
      <button style="margin-top: 16rpx" @click="chooseProof">{{ proofId ? '已上传，重新选择' : '上传产权证明' }}</button>
      <button style="margin-top: 16rpx" @click="submitAppeal">提交申诉</button>
    </view>
  </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api } from '@/utils/api'

const buildings = ref([])
const units = ref([])
const floors = ref([])
const rooms = ref([])
const picked = reactive({ building: '', unitNo: '', floor: '', roomLabel: '', unitId: null })
const proofId = ref('')
// 房号选项：[{ value: 房号, unit_id }]
const roomLabels = computed(() => rooms.value.map((r) => r.value))

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

const values = (data) => (data.options || []).map((o) => o.value)

async function init() {
  buildings.value = values(await load({}))
}

async function pickBuilding(e) {
  picked.building = buildings.value[Number(e.detail.value)]
  units.value = values(await load({ building: picked.building }))
}

async function pickUnit(e) {
  picked.unitNo = units.value[Number(e.detail.value)]
  floors.value = values(await load({ building: picked.building, unit_no: picked.unitNo }))
}

async function pickFloor(e) {
  picked.floor = floors.value[Number(e.detail.value)]
  const data = await load({ building: picked.building, unit_no: picked.unitNo, floor: picked.floor })
  rooms.value = data.options || []
}

function pickRoom(e) {
  const room = rooms.value[Number(e.detail.value)]
  picked.unitId = room?.unit_id
  picked.roomLabel = room?.value
}

async function certify() {
  if (!picked.unitId) return toast('请先选择房号')
  try {
    const result = await api.certify(picked.unitId)
    toast(`认证成功：${result.role}`)
  } catch (e) {
    toast(e.message)
  }
}

function chooseProof() {
  uni.chooseImage({
    count: 1,
    success: async ({ tempFilePaths }) => {
      try {
        const uploaded = await api.upload(tempFilePaths[0], 'APPEAL_PROOF')
        proofId.value = uploaded.id
        toast('已上传')
      } catch (e) {
        toast(e.message)
      }
    }
  })
}

async function submitAppeal() {
  if (!picked.unitId) return toast('请先选择房号')
  if (!proofId.value) return toast('请先上传产权证明')
  try {
    await api.createAppeal({ unit_id: picked.unitId, proof_ids: [proofId.value] })
    toast('申诉已提交')
  } catch (e) {
    toast(e.message)
  }
}

onLoad(init)
</script>
