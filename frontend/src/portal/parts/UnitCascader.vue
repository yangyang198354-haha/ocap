<!-- MOD-082 / IFC-280：逐级选择房屋（楼栋、单元、楼层、户号），不出现任何内部编号输入框 -->
<template>
  <div class="unit-cascader">
    <div class="row">
      <el-select
        v-model="picked.building" placeholder="楼栋" filterable no-data-text="无匹配项"
        :filter-method="onFilter('building')" @visible-change="onVisible('building', $event)" @change="onBuildingChange"
      >
        <el-option v-for="b in shown.building" :key="b.value" :label="b.value" :value="b.value" />
      </el-select>
      <el-select
        v-if="visibility.unit" v-model="picked.unit_no" :placeholder="levelLabel" filterable no-data-text="无匹配项"
        :filter-method="onFilter('unit')" @visible-change="onVisible('unit', $event)" @change="onUnitChange"
      >
        <el-option v-for="u in shown.unit" :key="u.value" :label="u.label || u.value" :value="u.value" />
      </el-select>
      <el-select
        v-if="visibility.floor" v-model="picked.floor" placeholder="楼层" filterable no-data-text="无匹配项"
        :filter-method="onFilter('floor')" @visible-change="onVisible('floor', $event)" @change="onFloorChange"
      >
        <el-option v-for="f in shown.floor" :key="f.value" :label="f.label || f.value" :value="f.value" />
      </el-select>
      <el-select
        v-if="visibility.room" v-model="pickedUnitId" placeholder="户号" filterable no-data-text="无匹配项"
        :filter-method="onFilter('room')" @visible-change="onVisible('room', $event)" @change="onRoomChange"
      >
        <el-option v-for="r in shown.room" :key="r.unit_id" :label="r.label || r.value" :value="r.unit_id" />
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
import { rankOptions } from '@/shared/unitSearch'

// fetcher：选项取数函数（缺省成员端 unitApi.options；管理端传 admin.unitOptions，IFC-364）
const props = defineProps({ modelValue: { type: Number, default: null }, fetcher: { type: Function, default: null } })
const emit = defineEmits(['update:modelValue', 'change'])

const buildingOptions = ref([])
const unitOptions = ref([])
const floorOptions = ref([])
const roomOptions = ref([])
const skippedTips = ref([])
const levelLabel = ref('单元') // IFC-300：商铺第二级由接口返回 level_label（"楼栋/门牌"），其余为"单元"
const visibility = reactive({ unit: false, floor: false, room: false })
const picked = reactive({ building: null, unit_no: null, floor: null })
const pickedUnitId = ref(props.modelValue)

// 下拉输入检索（REQ-FUNC-241）：只过滤当前下拉的已加载候选，不改变逐级关系与已选结果
const queries = reactive({ building: '', unit: '', floor: '', room: '' })
const shown = computed(() => ({
  building: rankOptions(buildingOptions.value, queries.building),
  unit: rankOptions(unitOptions.value, queries.unit),
  floor: rankOptions(floorOptions.value, queries.floor),
  room: rankOptions(roomOptions.value, queries.room)
}))
const onFilter = (level) => (query) => {
  queries[level] = query || ''
}
const onVisible = (level, visible) => {
  if (!visible) queries[level] = '' // 关闭下拉后恢复全部选项，保证已选项可显示
}

const selectedUnit = computed(() => roomOptions.value.find((item) => item.unit_id === pickedUnitId.value) || null)
const selectedUnitText = computed(() => {
  if (!selectedUnit.value) return ''
  const parts = [selectedUnit.value.unit_type_label || '类型未登记']
  parts.push(selectedUnit.value.area ? `${selectedUnit.value.area} ㎡` : '面积未登记')
  return parts.join(' · ')
})

async function loadOptions(params) {
  try {
    return await (props.fetcher || unitApi.options)(params)
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
    levelLabel.value = '单元'
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
      levelLabel.value = data.level_label || '单元'
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
