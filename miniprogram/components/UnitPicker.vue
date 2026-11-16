<!-- MOD-085 / IFC-284：逐级选择房屋（楼栋、单元、楼层、房号），不出现任何内部编号输入框；逻辑自 pages/units 抽出 -->
<template>
  <view>
    <picker mode="selector" :range="buildings" @change="pickBuilding">
      <view class="muted">楼栋：{{ picked.building || '请选择' }}</view>
    </picker>
    <picker v-if="show.unit" mode="selector" :range="unitLabels" @change="pickUnit">
      <view class="muted">{{ levelLabel }}：{{ picked.unitNo || '请选择' }}</view>
    </picker>
    <picker v-if="show.floor" mode="selector" :range="floorLabels" @change="pickFloor">
      <view class="muted">楼层：{{ picked.floor || '请选择' }}</view>
    </picker>
    <picker mode="selector" :range="roomLabels" @change="pickRoom">
      <view class="muted">房号：{{ picked.roomLabel || '请选择' }}</view>
    </picker>
    <view v-if="skipHint" class="muted">{{ skipHint }}</view>
  </view>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '@/utils/api'

defineProps({ modelValue: { type: Number, default: null } })
const emit = defineEmits(['update:modelValue', 'change'])

const buildings = ref([])
const unitChoices = ref([])
const floorChoices = ref([])
const rooms = ref([])
const show = reactive({ unit: false, floor: false })
const skipHint = ref('')
const levelLabel = ref('单元') // IFC-300：商铺第二级由接口返回 level_label（"楼栋/门牌"），其余为"单元"
const picked = reactive({ building: '', unitNo: '', floor: '', roomLabel: '', unitId: null })
// 选项：[{ value, label }]；has_empty 时插入“未划分”项（IFC-152）
const unitLabels = computed(() => unitChoices.value.map((c) => c.label))
const floorLabels = computed(() => floorChoices.value.map((c) => c.label))
const roomLabels = computed(() => rooms.value.map((r) => r.label || r.value))

function toast(title) {
  uni.showToast({ title, icon: 'none' })
}

async function load(params = {}) {
  try {
    return await api.options(params)
  } catch (e) {
    toast(e.message)
    return {}
  }
}

const values = (data) => (data.options || []).map((o) => o.value)

async function init() {
  buildings.value = values(await load({}))
}

function clearSelection() {
  picked.roomLabel = ''
  picked.unitId = null
  rooms.value = []
  emit('update:modelValue', null)
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
  clearSelection()
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
    levelLabel.value = '单元'
  }
  if (level === 'unit') {
    picked.floor = ''
    floorChoices.value = []
    show.floor = false
  }
  clearSelection()
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
      levelLabel.value = data.level_label || '单元'
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
  picked.unitId = room?.unit_id ?? null
  picked.roomLabel = room?.label || room?.value || ''
  emit('update:modelValue', picked.unitId)
  if (picked.unitId) {
    emit('change', { unit_id: picked.unitId, specific_part: picked.roomLabel, label: picked.roomLabel })
  }
}

onMounted(init)
</script>
