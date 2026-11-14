<!-- MOD-082 / IFC-280：逐级选择房屋（楼栋、单元、楼层、户号），不出现任何内部编号输入框 -->
<template>
  <div class="unit-cascader">
    <div class="row">
      <el-select v-model="picked.building" placeholder="楼栋" @change="onBuildingChange">
        <el-option v-for="b in buildingOptions" :key="b.value" :label="b.value" :value="b.value" />
      </el-select>
      <el-select v-if="visibility.unit" v-model="picked.unit_no" placeholder="单元" @change="onUnitChange">
        <el-option v-for="u in unitOptions" :key="u.value" :label="u.label || u.value" :value="u.value" />
      </el-select>
      <el-select v-if="visibility.floor" v-model="picked.floor" placeholder="楼层" @change="onFloorChange">
        <el-option v-for="f in floorOptions" :key="f.value" :label="f.label || f.value" :value="f.value" />
      </el-select>
      <el-select v-if="visibility.room" v-model="pickedUnitId" placeholder="户号" @change="onRoomChange">
        <el-option v-for="r in roomOptions" :key="r.unit_id" :label="r.label || r.value" :value="r.unit_id" />
      </el-select>
    </div>
    <p v-for="tip in skippedTips" :key="tip" class="muted">{{ tip }}</p>
    <p v-if="selectedUnitText" class="muted">{{ selectedUnitText }}</p>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { unitApi } from '@/shared/api'
import { errorText } from '@/shared/format'

const props = defineProps({ modelValue: { type: Number, default: null } })
const emit = defineEmits(['update:modelValue', 'change'])

const buildingOptions = ref([])
const unitOptions = ref([])
const floorOptions = ref([])
const roomOptions = ref([])
const skippedTips = ref([])
const visibility = reactive({ unit: false, floor: false, room: false })
const picked = reactive({ building: null, unit_no: null, floor: null })
const pickedUnitId = ref(props.modelValue)

const selectedUnit = computed(() => roomOptions.value.find((item) => item.unit_id === pickedUnitId.value) || null)
const selectedUnitText = computed(() => {
  if (!selectedUnit.value) return ''
  const parts = [selectedUnit.value.unit_type_label || '类型未登记']
  parts.push(selectedUnit.value.area ? `${selectedUnit.value.area} ㎡` : '面积未登记')
  return parts.join(' · ')
})

async function loadOptions(params) {
  try {
    return await unitApi.options(params)
  } catch (e) {
    ElMessage.error(errorText(e))
    return {}
  }
}

async function loadBuildings() {
  const data = await loadOptions({})
  buildingOptions.value = data.options || []
}

function clearSelection() {
  pickedUnitId.value = null
  emit('update:modelValue', null)
  emit('change', null)
}

function resetBelow(level) {
  if (level === 'building') {
    picked.unit_no = null
    picked.floor = null
    visibility.unit = false
    visibility.floor = false
    unitOptions.value = []
    floorOptions.value = []
    skippedTips.value = []
  }
  if (level === 'unit') {
    picked.floor = null
    visibility.floor = false
    floorOptions.value = []
  }
  visibility.room = false
  roomOptions.value = []
  clearSelection()
}

async function onBuildingChange() {
  resetBelow('building')
  if (picked.building === null) return
  await applyLevel(await loadOptions({ building: picked.building }), 'unit')
}

async function onUnitChange() {
  resetBelow('unit')
  if (picked.unit_no === null) return
  await applyLevel(await loadOptions({ building: picked.building, unit_no: picked.unit_no }), 'floor')
}

async function onFloorChange() {
  resetBelow('floor')
  if (picked.floor === null) return
  showRooms(await loadOptions({ building: picked.building, unit_no: picked.unit_no, floor: picked.floor }))
}

async function applyLevel(data, stage) {
  if (data.level === 'room') {
    showRooms(data)
    return
  }
  if (stage === 'unit') {
    if (data.level === 'unit_no') {
      visibility.unit = true
      unitOptions.value = data.has_empty
        ? [{ value: '', label: '未划分单元' }, ...(data.options || [])]
        : (data.options || [])
      return
    }
    picked.unit_no = ''
    skippedTips.value = ['该楼栋没有分单元，已自动跳过']
    await loadFloorsAfterSkip()
    return
  }
  if (data.level === 'floor') {
    visibility.floor = true
    floorOptions.value = data.has_empty
      ? [{ value: '', label: '未划分楼层' }, ...(data.options || [])]
      : (data.options || [])
    return
  }
  picked.floor = ''
  skippedTips.value = [...skippedTips.value, '该单元没有分楼层，已自动跳过']
  showRooms(await loadOptions({ building: picked.building, unit_no: picked.unit_no, floor: '' }))
}

async function loadFloorsAfterSkip() {
  applyLevel(await loadOptions({ building: picked.building, unit_no: '' }), 'floor')
}

function showRooms(data) {
  visibility.room = true
  roomOptions.value = data.options || []
}

function onRoomChange(unitId) {
  const room = roomOptions.value.find((item) => item.unit_id === unitId)
  emit('update:modelValue', unitId)
  emit('change', {
    unit_id: unitId,
    specific_part: `${picked.building ?? ''}${picked.unit_no ?? ''}${picked.floor ?? ''}${room?.value ?? ''}`,
    label: room?.label || ''
  })
}

loadBuildings()
</script>
