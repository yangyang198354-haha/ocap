<template>
  <ThemeRoot>
  <view>
    <view class="card">
      <view class="title">业主清册认证</view>
      <picker mode="selector" :range="buildings" @change="pickBuilding">
        <view class="muted">楼栋：{{ picked.building || '请选择' }}</view>
      </picker>
      <picker v-if="show.unit" mode="selector" :range="unitLabels" @change="pickUnit">
        <view class="muted">单元：{{ picked.unitNo || '请选择' }}</view>
      </picker>
      <picker v-if="show.floor" mode="selector" :range="floorLabels" @change="pickFloor">
        <view class="muted">楼层：{{ picked.floor || '请选择' }}</view>
      </picker>
      <picker mode="selector" :range="roomLabels" @change="pickRoom">
        <view class="muted">房号：{{ picked.roomLabel || '请选择' }}</view>
      </picker>
      <view v-if="skipHint" class="muted">{{ skipHint }}</view>
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
const unitChoices = ref([])
const floorChoices = ref([])
const rooms = ref([])
const show = reactive({ unit: false, floor: false })
const skipHint = ref('')
const picked = reactive({ building: '', unitNo: '', floor: '', roomLabel: '', unitId: null })
const proofId = ref('')
// 选项：[{ value, label }]；has_empty 时插入“未划分”项（IFC-152）
const unitLabels = computed(() => unitChoices.value.map((c) => c.label))
const floorLabels = computed(() => floorChoices.value.map((c) => c.label))
const roomLabels = computed(() => rooms.value.map((r) => r.label || r.value))

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
  resetBelow('building')
  await apply(await load({ building: picked.building }), 'unit')
}

async function pickUnit(e) {
  picked.unitNo = unitChoices.value[Number(e.detail.value)].value
  resetBelow('unit')
  await apply(await load({ building: picked.building, unit_no: picked.unitNo }), 'floor')
}

async function pickFloor(e) {
  picked.floor = floorChoices.value[Number(e.detail.value)].value
  picked.roomLabel = ''
  picked.unitId = null
  rooms.value = []
  const data = await load({ building: picked.building, unit_no: picked.unitNo, floor: picked.floor })
  if (data.level === 'room') rooms.value = data.options || []
}

function resetBelow(level) {
  if (level === 'building') {
    picked.unitNo = ''
    picked.floor = ''
    unitChoices.value = []
    floorChoices.value = []
    show.unit = false
    show.floor = false
    skipHint.value = ''
  }
  if (level === 'unit') {
    picked.floor = ''
    floorChoices.value = []
    show.floor = false
  }
  picked.roomLabel = ''
  picked.unitId = null
  rooms.value = []
}

// 服务端返回 level/skipped：空串表示该层为空（IFC-152）
async function apply(data, stage) {
  if (data.level === 'room') {
    rooms.value = data.options || []
    return
  }
  if (stage === 'unit') {
    if (data.level === 'unit_no') {
      show.unit = true
      unitChoices.value = data.has_empty
        ? [{ value: '', label: '未划分单元' }, ...(data.options || [])]
        : (data.options || [])
      return
    }
    picked.unitNo = ''
    skipHint.value = '该楼栋没有分单元，已自动跳过'
    return apply(await load({ building: picked.building, unit_no: '' }), 'floor')
  }
  if (data.level === 'floor') {
    show.floor = true
    floorChoices.value = data.has_empty
      ? [{ value: '', label: '未划分楼层' }, ...(data.options || [])]
      : (data.options || [])
    return
  }
  picked.floor = ''
  skipHint.value = `${skipHint.value}该单元没有分楼层，已自动跳过`
  rooms.value = (await load({ building: picked.building, unit_no: picked.unitNo, floor: '' })).options || []
}

function pickRoom(e) {
  const room = rooms.value[Number(e.detail.value)]
  picked.unitId = room?.unit_id
  picked.roomLabel = room?.label || room?.value
}

async function certify() {
  if (!picked.unitId) return toast('请先选择房号')
  try {
    const result = await api.certify(picked.unitId)
    toast(`认证成功：${result.role}`)
  } catch (e) {
    if (e?.code === 'PHONE_NOT_IN_REGISTRY') {
      return toast('手机号与清册不一致，可提交产权申诉')
    }
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
